"""
Generador de código ARM64 (AArch64) para OxigenNative.

Recorre el AST YA ANOTADO por el semántico y produce el texto de un
archivo ensamblador (.s) para el ensamblador GNU, que se enlaza con
la biblioteca de C (`gcc -static`) para poder usar printf.

Convenciones del generador (importantes para entender todo el código):

  * El resultado de cada expresión queda en un registro fijo:
        x0  -> i32, bool, char y String (String = puntero al texto)
        d0  -> f64
  * Cada variable vive en la pila, en [x29, #offset]. El offset lo
    calculó la tabla de símbolos (siempre negativo).
  * Los valores temporales se guardan en la pila con push/pop
    (se usarán desde G2 en las operaciones binarias).
  * main es una función normal: termina con `ret` (NO con la llamada
    al sistema exit) para que la biblioteca de C vacíe el búfer de
    printf antes de salir.
"""
from compiler import ast_nodes as ast
from compiler.tipos import (es_arreglo, es_estatico, es_dinamico, elemento,
                            longitud, tipo_base, total_elementos, tamano)

I32, F64, BOOL, CHAR, STRING = 'i32', 'f64', 'bool', 'char', 'String'
ERROR = 'None'

# Relacional -> condición de ARM64 para `cset` (después de un `cmp`)
CONDICION = {'==': 'eq', '!=': 'ne', '<': 'lt', '>': 'gt', '<=': 'le', '>=': 'ge'}

# Lo mismo después de un `fcmp` (f64). Para < y <= se usan 'mi' y 'ls'
# porque con NaN 'lt' y 'le' darían true, y cualquier comparación con
# NaN debe ser false.
CONDICION_F64 = {'==': 'eq', '!=': 'ne', '<': 'mi', '>': 'gt', '<=': 'ls', '>=': 'ge'}

# Operador aritmético -> instrucción de punto flotante
OPERACION_F64 = {'+': 'fadd', '-': 'fsub', '*': 'fmul', '/': 'fdiv'}

# Operador compuesto -> operador aritmético
COMPUESTOS = {'+=': '+', '-=': '-', '*=': '*', '/=': '/', '%=': '%'}

# Especificador de printf para cada tipo (ver visit_Print).
# f64 y char se convierten antes a texto con una rutina de apoyo.
ESPECIFICADOR = {
    I32: '%d',
    F64: '%s',      # __oxi_f64_str
    STRING: '%s',
    CHAR: '%s',     # __oxi_char_str
    BOOL: '%s',     # se pasa el texto "true" o "false"
}


class Arm64Generator:

    def __init__(self):
        self.text = []          # instrucciones de la sección .text
        self.data = []          # constantes de la sección .data
        self.cadenas = {}       # texto -> etiqueta (para no repetir cadenas)
        self.decimales = {}     # valor f64 -> etiqueta
        self.contador = 0       # para crear etiquetas únicas
        # Pila de ciclos activos. Cada elemento es un diccionario:
        #   {'etiqueta': 'outer' o None,
        #    'continuar': etiqueta ARM64 a la que salta `continue`,
        #    'salir':     etiqueta ARM64 a la que salta `break`}
        self.ciclos = []
        self.rutinas = set()    # rutinas de apoyo que el programa usa

    # ==================================================================
    # Utilidades para emitir código
    # ==================================================================

    def emit(self, instruccion, comentario=None):
        linea = f"    {instruccion}"
        if comentario:
            linea = f"{linea:<40}// {comentario}"
        self.text.append(linea)

    def etiqueta(self, nombre):
        self.text.append(f"{nombre}:")

    def comentario(self, texto):
        self.text.append(f"    // {texto}")

    def nueva_etiqueta(self, prefijo):
        self.contador += 1
        return f".L{prefijo}_{self.contador}"

    # --- Constantes en .data ----------------------------------------------

    def cadena(self, texto):
        """Guarda un texto en .data (una sola vez) y devuelve su etiqueta."""
        if texto not in self.cadenas:
            etiqueta = f"str_{len(self.cadenas)}"
            self.cadenas[texto] = etiqueta
            self.data.append(f'{etiqueta}: .asciz "{escapar_asm(texto)}"')
        return self.cadenas[texto]

    def decimal(self, valor):
        """Guarda un f64 en .data (alineado a 8 bytes) y devuelve su etiqueta."""
        if valor not in self.decimales:
            etiqueta = f"dbl_{len(self.decimales)}"
            self.decimales[valor] = etiqueta
            self.data.append("    .balign 8")
            self.data.append(f"{etiqueta}: .double {valor!r}")
        return self.decimales[valor]

    def direccion(self, reg, etiqueta):
        """reg = dirección de una etiqueta de .data (adrp + add)."""
        self.emit(f"adrp {reg}, {etiqueta}")
        self.emit(f"add {reg}, {reg}, :lo12:{etiqueta}")

    def cargar_inmediato(self, reg, valor):
        """Carga un entero de 32 bits con signo en un registro x."""
        if -65536 < valor < 65536:
            self.emit(f"mov {reg}, #{valor}")
        else:
            # Valores grandes: se arman por partes de 16 bits
            w = 'w' + reg[1:]
            sin_signo = valor & 0xFFFFFFFF
            self.emit(f"movz {w}, #{sin_signo & 0xFFFF}")
            self.emit(f"movk {w}, #{sin_signo >> 16}, lsl #16")
            self.emit(f"sxtw {reg}, {w}", "extender el signo a 64 bits")

    # --- Pila de temporales ------------------------------------------
    # Para evaluar `a + b` hay que guardar el valor de `a` mientras se
    # calcula `b`. Se guarda en la pila. Se mueven 16 bytes (aunque el
    # dato ocupe 8) porque ARM64 exige que sp sea múltiplo de 16.

    def push(self, reg="x0"):
        self.emit(f"str {reg}, [sp, #-16]!", f"push {reg}")

    def pop(self, reg="x1"):
        self.emit(f"ldr {reg}, [sp], #16", f"pop {reg}")

    def push_valor(self, tipo):
        """Guarda el resultado actual: d0 si es f64, x0 en otro caso."""
        self.push("d0" if tipo == F64 else "x0")

    def llamar(self, rutina):
        """bl a una rutina de apoyo y la marca para agregarla al .s
        (junto con las rutinas que ella misma usa)."""
        self.rutinas.add(rutina)
        self.rutinas.update(DEPENDENCIAS.get(rutina, ()))
        self.emit(f"bl {rutina}")

    # --- Acceso a variables en la pila ---------------------------------

    def _memoria(self, offset):
        """Operando de memoria para [x29 + offset].
        ldr/str con offset negativo solo alcanzan hasta -256; más lejos
        se calcula la dirección en x9."""
        if offset >= -256:
            return f"[x29, #{offset}]"
        self.emit(f"sub x9, x29, #{-offset}")
        return "[x9]"

    def guardar_variable(self, simbolo, tipo_valor):
        """Guarda el resultado actual (x0 o d0) en la variable."""
        if simbolo.tipo == F64:
            if tipo_valor == I32:
                self.emit("scvtf d0, x0", "promoción i32 -> f64")
            self.emit(f"str d0, {self._memoria(simbolo.offset)}",
                      f"{simbolo.nombre} = d0")
        else:
            self.emit(f"str x0, {self._memoria(simbolo.offset)}",
                      f"{simbolo.nombre} = x0")

    def cargar_variable(self, simbolo):
        if simbolo.tipo == F64:
            self.emit(f"ldr d0, {self._memoria(simbolo.offset)}",
                      f"d0 = {simbolo.nombre}")
        else:
            self.emit(f"ldr x0, {self._memoria(simbolo.offset)}",
                      f"x0 = {simbolo.nombre}")

    # ==================================================================
    # Recorrido del AST
    # ==================================================================

    def generar(self, programa):
        for fn in programa.funciones:
            if not getattr(fn, 'omitir', False):
                self.visitar(fn)

        # Rutinas de apoyo usadas (en orden fijo para que el .s sea estable)
        for nombre in sorted(self.rutinas):
            self.text.append("")
            self.text.extend(RUTINAS[nombre](self).strip('\n').split('\n'))

        salida = [
            "// Generado por OxigenNative",
            "    .global main",
            "    // Funciones de la biblioteca de C que se usan",
            "    .extern printf, snprintf, malloc, calloc, memcpy, strlen,",
            "    .extern strcpy, strcat, strcmp, exit, strstr, strncat, rand, srand, time,",
            "    .extern setvbuf, stdout",
            "",
            "    .section .data",
            *self.data,
            "",
            "    .section .bss",
            "    .balign 8",
            "buf_f64:  .skip 64                     // texto de un f64 al imprimir",
            "buf_char: .skip 8                      // texto UTF-8 de un char",
            "oxi_semilla: .skip 8                   // 1 si ya se inicializó random",
            "",
            "    .section .text",
            *self.text,
            "",
        ]
        return "\n".join(salida)

    def visitar(self, nodo):
        if getattr(nodo, 'omitir', False):
            return None     # instrucción con error semántico: se salta
        metodo = getattr(self, f"visit_{type(nodo).__name__}", None)
        if metodo is None:
            raise NotImplementedError(
                f"El generador ARM64 aún no maneja nodos {type(nodo).__name__} "
                f"(línea {nodo.linea})")
        return metodo(nodo)

    # --- Funciones -------------------------------------------------------

    def visit_Function(self, nodo):
        sym = nodo.simbolo
        # Las funciones del usuario llevan prefijo para no chocar con
        # nombres de la biblioteca de C (printf, exit, puts...).
        nombre = 'main' if nodo.nombre == 'main' else f"fn_{nodo.nombre}"
        self.fin_funcion = self.nueva_etiqueta(f"fin_{nodo.nombre}")

        self.text.append("")
        self.etiqueta(nombre)
        # Prólogo: guardar el marco anterior y reservar espacio
        self.emit("stp x29, x30, [sp, #-16]!", "guardar x29 (marco) y x30 (retorno)")
        self.emit("mov x29, sp", "x29 = base del nuevo marco")
        if sym.tamano_frame > 0:
            self.emit(f"sub sp, sp, #{sym.tamano_frame}",
                      f"espacio para variables ({sym.tamano_frame} bytes)")

        # Los argumentos llegan en registros (x0-x7 enteros, d0-d7 f64):
        # se copian a su lugar en el marco para usarlos como variables.
        for prm, reg in zip(sym.params, registros_parametros(sym.tipos_params)):
            self.emit(f"str {reg}, {self._memoria(prm.offset)}",
                      f"parámetro {prm.nombre} = {reg}")

        if nodo.nombre == 'main':
            # La salida se escribe línea por línea (no al final del programa):
            # si la ejecución se corta (ciclo infinito, error de ejecución),
            # no se pierde lo que ya se imprimió.
            #   setvbuf(stdout, NULL, _IOLBF, 0)
            self.emit("adrp x0, stdout")
            self.emit("ldr x0, [x0, :lo12:stdout]", "x0 = stdout")
            self.emit("mov x1, #0")
            self.emit("mov x2, #1", "_IOLBF: vaciar en cada salto de línea")
            self.emit("mov x3, #0")
            self.emit("bl setvbuf")

        self.tipo_retorno = nodo.tipo_retorno
        self.visit_Block(nodo.cuerpo)

        # Si el cuerpo termina sin `return`, se retorna el valor por defecto
        if nodo.nombre != 'main' and nodo.tipo_retorno is not None:
            self.valor_por_defecto(nodo.tipo_retorno)

        # Epílogo
        self.etiqueta(self.fin_funcion)
        if nodo.nombre == 'main':
            self.emit("mov w0, #0", "return 0")
        self.emit("mov sp, x29", "liberar las variables")
        self.emit("ldp x29, x30, [sp], #16", "restaurar marco y retorno")
        self.emit("ret")

    def visit_Block(self, nodo):
        for ins in nodo.instrucciones:
            self.visitar(ins)

    # --- Declaraciones -----------------------------------------------------

    def visit_VarDecl(self, nodo):
        sym = nodo.simbolo
        if sym.tipo == ERROR:
            return      # variable con tipo inválido: siempre se imprime None

        mut = 'mut ' if nodo.mutable else ''
        self.comentario(f"let {mut}{nodo.nombre}: {sym.tipo}  (línea {nodo.linea})")

        if nodo.usar_defecto:
            self.valor_por_defecto(sym.tipo)
            tipo_valor = sym.tipo
        else:
            tipo_valor = self.visitar(nodo.valor)
            self.copiar_si_es_variable(nodo.valor, tipo_valor)
        self.guardar_variable(sym, tipo_valor)

    def valor_por_defecto(self, tipo):
        if es_dinamico(tipo):
            self.emit("mov x0, #1")
            self.emit("mov x1, #8")
            self.emit("bl calloc", "arreglo dinámico vacío (largo 0)")
        elif es_arreglo(tipo):
            # calloc deja todo en 0: sirve para i32, f64 (0.0), bool y char
            self.emit("mov x0, #1")
            self.cargar_inmediato("x1", tamano(tipo))
            self.emit("bl calloc", f"arreglo {tipo} lleno de ceros")
            if tipo_base(tipo) == STRING:
                # Los String por defecto son "" (no un puntero nulo)
                ciclo, fin = self.nueva_etiqueta("vacios"), self.nueva_etiqueta("vacios_fin")
                self.emit("mov x10, x0")
                self.direccion("x11", self.cadena(""))
                self.cargar_inmediato("x12", total_elementos(tipo))
                self.etiqueta(ciclo)
                self.emit(f"cbz x12, {fin}")
                self.emit("str x11, [x10], #8", 'elemento = ""')
                self.emit("sub x12, x12, #1")
                self.emit(f"b {ciclo}")
                self.etiqueta(fin)
        elif tipo == F64:
            self.emit("fmov d0, xzr", "0.0")
        elif tipo == STRING:
            self.direccion("x0", self.cadena(""))
        else:
            self.emit("mov x0, #0", "0 / false / '\\0'")

    # --- Asignaciones ------------------------------------------------------

    def visit_Assignment(self, nodo):
        sym = nodo.simbolo
        if isinstance(nodo.objetivo, ast.Index):
            return self.asignar_elemento(nodo)
        self.comentario(f"{sym.nombre} {nodo.op} ...  (línea {nodo.linea})")

        if nodo.op == '=':
            tipo_valor = self.visitar(nodo.valor)
            self.copiar_si_es_variable(nodo.valor, tipo_valor)
            self.guardar_variable(sym, tipo_valor)
            return

        # x += v   se calcula como   x = x + v
        op = COMPUESTOS[nodo.op]
        self.cargar_variable(sym)                   # x0/d0 = x
        self.push_valor(sym.tipo)
        tipo_valor = self.visitar(nodo.valor)       # x0/d0 = v
        resultado = self.aplicar(op, sym.tipo, tipo_valor)
        self.guardar_variable(sym, resultado)

    # --- Control de flujo --------------------------------------------------

    def condicion_valida(self, nodo, sentencia):
        """Si la condición tuvo error semántico (no es bool), la sentencia
        completa se salta: no hay forma segura de decidir qué rama correr."""
        if nodo.condicion.tipo_resultado == BOOL:
            return True
        self.comentario(f"{sentencia} omitido: condición inválida (línea {nodo.linea})")
        return False

    def visit_If(self, nodo):
        """if c { A } else { B }   se traduce como

                <evaluar c en x0>
                cbz x0, .Lif_sino      // c es false -> ir a B
                <A>
                b .Lif_fin
            .Lif_sino:
                <B>                     // otro If si es `else if`
            .Lif_fin:
        """
        if not self.condicion_valida(nodo, 'if'):
            return
        sino = self.nueva_etiqueta("if_sino")
        fin = self.nueva_etiqueta("if_fin")

        self.comentario(f"if  (línea {nodo.linea})")
        self.visitar(nodo.condicion)
        self.emit(f"cbz x0, {sino if nodo.sino else fin}", "condición false -> saltar")
        self.visit_Block(nodo.entonces)

        if nodo.sino is not None:
            self.emit(f"b {fin}", "terminar el if")
            self.etiqueta(sino)
            self.visitar(nodo.sino)     # Block o If (else if)
        self.etiqueta(fin)

    def visit_While(self, nodo):
        """while c { A }   se traduce como

            .Lwhile_inicio:             // aquí salta `continue`
                <evaluar c en x0>
                cbz x0, .Lwhile_fin     // c es false -> salir
                <A>
                b .Lwhile_inicio
            .Lwhile_fin:                // aquí salta `break`
        """
        if not self.condicion_valida(nodo, 'while'):
            return
        inicio = self.nueva_etiqueta("while_inicio")
        fin = self.nueva_etiqueta("while_fin")

        self.comentario(f"while  (línea {nodo.linea})")
        self.etiqueta(inicio)
        self.visitar(nodo.condicion)
        self.emit(f"cbz x0, {fin}", "condición false -> salir del while")
        self.cuerpo_ciclo(nodo, continuar=inicio, salir=fin)
        self.emit(f"b {inicio}", "volver a evaluar la condición")
        self.etiqueta(fin)

    def visit_Loop(self, nodo):
        """loop { A }   se traduce como

            .Lloop_inicio:              // aquí salta `continue`
                <A>
                b .Lloop_inicio
            .Lloop_fin:                 // aquí salta `break`
        """
        inicio = self.nueva_etiqueta("loop_inicio")
        fin = self.nueva_etiqueta("loop_fin")

        self.comentario(f"loop  (línea {nodo.linea})")
        self.etiqueta(inicio)
        self.cuerpo_ciclo(nodo, continuar=inicio, salir=fin)
        self.emit(f"b {inicio}", "repetir")
        self.etiqueta(fin)

    def cuerpo_ciclo(self, nodo, continuar, salir):
        """Genera el cuerpo con el ciclo registrado en la pila, para que
        los break/continue de adentro sepan a dónde saltar."""
        self.ciclos.append({'etiqueta': nodo.etiqueta,
                            'continuar': continuar, 'salir': salir})
        self.visit_Block(nodo.cuerpo)
        self.ciclos.pop()

    def buscar_ciclo(self, etiqueta):
        """Sin etiqueta: el ciclo más interno (el último de la pila).
        Con etiqueta: el más interno que tenga ese nombre."""
        if etiqueta is None:
            return self.ciclos[-1]
        for ciclo in reversed(self.ciclos):
            if ciclo['etiqueta'] == etiqueta:
                return ciclo

    def visit_Break(self, nodo):
        ciclo = self.buscar_ciclo(nodo.etiqueta)
        nombre = f" '{nodo.etiqueta}" if nodo.etiqueta else ""
        self.emit(f"b {ciclo['salir']}", f"break{nombre}  (línea {nodo.linea})")

    def visit_Continue(self, nodo):
        ciclo = self.buscar_ciclo(nodo.etiqueta)
        nombre = f" '{nodo.etiqueta}" if nodo.etiqueta else ""
        self.emit(f"b {ciclo['continuar']}", f"continue{nombre}  (línea {nodo.linea})")

    # --- Funciones: return, llamadas e instrucciones-expresión -------------

    def visit_Return(self, nodo):
        """return v;  ->  v queda en x0 (o d0 si es f64) y se salta al
        epílogo de la función, que restaura el marco y hace `ret`."""
        if nodo.valor is not None:
            tipo = self.visitar(nodo.valor)
            if self.tipo_retorno == F64 and tipo == I32:
                self.emit("scvtf d0, x0", "promoción i32 -> f64 del retorno")
        self.emit(f"b {self.fin_funcion}", f"return  (línea {nodo.linea})")

    def visit_ExprStmt(self, nodo):
        self.visitar(nodo.expr)     # el resultado (x0/d0) simplemente se ignora

    def visit_Call(self, nodo):
        """f(a, b, c) se traduce como

            <evaluar a> ; push      // se evalúan todos primero porque
            <evaluar b> ; push      // evaluar uno puede llamar a otra
            <evaluar c> ; push      // función y borrar x0-x7
            pop -> registro de c    // luego se sacan en orden inverso
            pop -> registro de b    // a su registro: x0..x7 o d0..d7
            pop -> registro de a
            bl fn_f                 // el resultado vuelve en x0 o d0
        """
        if getattr(nodo, 'embebida', None):
            return self.funcion_embebida(nodo)
        sym = nodo.simbolo
        self.comentario(f"llamada a {nodo.nombre}()  (línea {nodo.linea})")
        tipos = sym.tipos_params
        for arg, tipo_param in zip(nodo.args, tipos):
            tipo = self.visitar(arg)
            self.copiar_si_es_variable(arg, tipo)   # los arreglos se pasan por copia
            if tipo_param == F64 and tipo == I32:
                self.emit("scvtf d0, x0", "promoción del argumento i32 -> f64")
            self.push_valor(tipo_param)
        for reg in reversed(registros_parametros(tipos)):
            self.pop(reg)
        self.emit(f"bl fn_{nodo.nombre}")
        return nodo.tipo_resultado

    # --- println! ----------------------------------------------------------

    def visit_Print(self, nodo):
        """Se hace un printf por cada marcador {}:
            println!("a = {}, b = {}", a, b)
        se traduce como
            printf("a = %d", a); printf(", b = %.15g", b); printf("\\n");
        Así cada llamada lleva a lo más un valor y no hay límite de
        argumentos."""
        self.comentario(f"println!  (línea {nodo.linea})")
        texto = ""
        args = iter(nodo.args)
        for parte in nodo.partes:
            if parte is not None:
                texto += parte.replace('%', '%%')
                continue
            arg = next(args, None)
            tipo = getattr(arg, 'tipo_resultado', ERROR) if arg else ERROR
            if tipo == ERROR:
                texto += "None"         # resiliencia: valor inválido
                continue
            if es_arreglo(tipo):
                self.visitar(arg)       # x0 = puntero al arreglo
                if texto:
                    self.push()
                    self.printf(texto)
                    self.pop("x0")
                self.imprimir_arreglo(tipo)
                texto = ""
                continue
            self.visitar(arg)           # deja el valor en x0 o d0
            self.printf(texto + ESPECIFICADOR[tipo], tipo)
            texto = ""
        self.printf(texto + "\n")

    def printf(self, formato, tipo=None):
        """Llama a printf(formato, valor). El valor ya está en x0 o d0."""
        if tipo == BOOL:
            # x1 = x0 ? "true" : "false"
            self.direccion("x1", self.cadena("true"))
            self.direccion("x2", self.cadena("false"))
            self.emit("cmp x0, #0")
            self.emit("csel x1, x1, x2, ne", "x1 = texto del bool")
        elif tipo == F64:
            self.llamar("__oxi_f64_str")            # x0 = texto del decimal
            self.emit("mov x1, x0", "x1 = valor a imprimir")
        elif tipo == CHAR:
            self.llamar("__oxi_char_str")           # x0 = texto UTF-8
            self.emit("mov x1, x0", "x1 = valor a imprimir")
        elif tipo in (I32, STRING):
            self.emit("mov x1, x0", "x1 = valor a imprimir")
        self.direccion("x0", self.cadena(formato))
        self.emit("bl printf")

    # --- Expresiones -------------------------------------------------------
    # Cada visit_ deja el resultado en x0 (o d0) y devuelve el tipo.

    def visit_Literal(self, nodo):
        tipo = nodo.tipo_resultado
        if tipo == I32:
            self.cargar_inmediato("x0", nodo.valor)
        elif tipo == BOOL:
            self.emit(f"mov x0, #{1 if nodo.valor else 0}",
                      "true" if nodo.valor else "false")
        elif tipo == CHAR:
            self.cargar_inmediato("x0", ord(nodo.valor))
        elif tipo == F64:
            etiqueta = self.decimal(nodo.valor)
            self.emit(f"adrp x9, {etiqueta}")
            self.emit(f"ldr d0, [x9, :lo12:{etiqueta}]", f"d0 = {nodo.valor}")
        elif tipo == STRING:
            self.direccion("x0", self.cadena(nodo.valor))
        return tipo

    def visit_Identifier(self, nodo):
        self.cargar_variable(nodo.simbolo)
        return nodo.tipo_resultado

    # --- Operaciones unarias ----------------------------------------------

    def visit_UnaryOp(self, nodo):
        tipo = self.visitar(nodo.expr)
        if nodo.op == '!':
            self.emit("eor x0, x0, #1", "!x  (1 -> 0, 0 -> 1)")
        elif tipo == F64:
            self.emit("fneg d0, d0", "-x (f64)")
        else:
            self.emit("neg w0, w0", "-x")
            self.emit("sxtw x0, w0", "extender el signo a 64 bits")
        return nodo.tipo_resultado

    # --- Operaciones binarias ---------------------------------------------

    def visit_BinaryOp(self, nodo):
        op = nodo.op

        # && y || no siempre evalúan los dos lados (cortocircuito)
        if op in ('&&', '||'):
            return self.logica_cortocircuito(nodo)

        # Patrón general: evaluar izq, guardarlo, evaluar der, operar
        tipo_izq = self.visitar(nodo.izq)
        self.push_valor(tipo_izq)
        tipo_der = self.visitar(nodo.der)
        return self.aplicar(op, tipo_izq, tipo_der)

    def aplicar(self, op, tipo_izq, tipo_der):
        """Aplica `izq op der`. Al entrar, der está en x0/d0 y izq en el
        tope de la pila. Deja el resultado en x0/d0 y devuelve su tipo.
        Se elige el código según los tipos (las mismas tablas del
        semántico): f64, String o enteros."""

        # ---- f64 (si cualquiera de los dos lo es, se opera en f64) ----
        if F64 in (tipo_izq, tipo_der):
            if tipo_der == I32:
                self.emit("scvtf d0, x0", "promoción der i32 -> f64")
            if tipo_izq == F64:
                self.pop("d1")
            else:
                self.pop("x1")
                self.emit("scvtf d1, x1", "promoción izq i32 -> f64")

            if op in CONDICION_F64:
                self.emit("fcmp d1, d0")
                self.emit(f"cset x0, {CONDICION_F64[op]}",
                          f"x0 = (izq {op} der) ? 1 : 0")
                return BOOL
            if op == '%':
                # a % b = a - trunc(a / b) * b
                self.emit("fdiv d2, d1, d0", "d2 = a / b")
                self.emit("frintz d2, d2", "d2 = trunc(a / b)")
                self.emit("fmsub d0, d2, d0, d1", "d0 = a - d2 * b")
            else:
                self.emit(f"{OPERACION_F64[op]} d0, d1, d0", f"d0 = izq {op} der")
            return F64

        # ---- String ------------------------------------------------------
        if STRING in (tipo_izq, tipo_der):
            self.pop("x1")                          # x1 = izq, x0 = der
            if op == '*' and tipo_izq == I32:
                # n * "ab": x0 ya es el texto y x1 la cantidad
                self.llamar("__oxi_repetir")
                return STRING
            # Las demás rutinas reciben (x0 = izq, x1 = der)
            self.emit("mov x2, x0")
            self.emit("mov x0, x1", "x0 = izq")
            self.emit("mov x1, x2", "x1 = der")
            if op in CONDICION:
                # strcmp devuelve <0, 0 o >0 (orden alfabético)
                self.emit("bl strcmp")
                self.emit("cmp w0, #0")
                self.emit(f"cset x0, {CONDICION[op]}", f"x0 = (izq {op} der) ? 1 : 0")
                return BOOL
            if op == '+':
                self.llamar("__oxi_concat")
            else:                                   # "ab" * n
                self.llamar("__oxi_repetir")
            return STRING

        # ---- Enteros (i32, bool, char) ----------------------------------
        self.pop("x1")                              # x1 = izq, x0 = der
        if op in CONDICION:
            self.emit("cmp x1, x0")
            self.emit(f"cset x0, {CONDICION[op]}", f"x0 = (izq {op} der) ? 1 : 0")
            return BOOL
        self.operar_enteros(op)
        return I32

    def operar_enteros(self, op):
        """x0 = x1 <op> x0 con aritmética de 32 bits (i32).
        Se usan los registros w (32 bits) para que un desbordamiento dé
        la vuelta como un i32 real; luego sxtw copia el signo a x0."""
        if op == '+':
            self.emit("add w0, w1, w0")
        elif op == '-':
            self.emit("sub w0, w1, w0")
        elif op == '*':
            self.emit("mul w0, w1, w0")
        elif op == '/':
            self.emit("sdiv w0, w1, w0", "división entera con signo")
        elif op == '%':
            # ARM64 no tiene instrucción de módulo:  a % b = a - (a / b) * b
            self.emit("sdiv w2, w1, w0", "w2 = a / b")
            self.emit("msub w0, w2, w0, w1", "w0 = a - (a / b) * b")
        self.emit("sxtw x0, w0", "extender el signo a 64 bits")

    def logica_cortocircuito(self, nodo):
        """a && b:  si a es false, el resultado es false y b NO se evalúa.
           a || b:  si a es true,  el resultado es true  y b NO se evalúa.
        Si no se corta, el resultado es simplemente el valor de b."""
        fin = self.nueva_etiqueta("logico_fin")
        self.visitar(nodo.izq)
        if nodo.op == '&&':
            self.emit(f"cbz x0, {fin}", "izq es false -> resultado false")
        else:
            self.emit(f"cbnz x0, {fin}", "izq es true -> resultado true")
        self.visitar(nodo.der)
        self.etiqueta(fin)
        return BOOL



    # ==================================================================
    # Arreglos (pasos 6 y 7)
    # ESTÁTICO "[T; N]": un bloque contiguo en el heap (row-major) con
    #   8 bytes por valor; el elemento i está en  base + i * tamaño.
    # DINÁMICO "[T]" (resultado de split): el bloque empieza con el
    #   largo:  [ largo | e0 | e1 | ... ]; el elemento i está en
    #   base + 8 + i * 8.
    # La variable siempre guarda el PUNTERO al bloque.
    # ==================================================================

    def sumar_inmediato(self, destino, origen, valor):
        """destino = origen + valor (valor puede no caber en un add)."""
        if valor == 0:
            if destino != origen:
                self.emit(f"mov {destino}, {origen}")
        elif valor < 4096:
            self.emit(f"add {destino}, {origen}, #{valor}")
        else:
            self.cargar_inmediato("x12", valor)
            self.emit(f"add {destino}, {origen}, x12")

    def copiar_si_es_variable(self, nodo, tipo):
        """Los arreglos se copian al asignarlos (como en Rust, `let b = a;`
        crea un arreglo nuevo). Si el valor ya es un arreglo nuevo
        (literal, slice, split, retorno de función) no hace falta copiar."""
        if not (es_arreglo(tipo) and isinstance(nodo, (ast.Identifier, ast.Index))):
            return
        if es_dinamico(tipo):
            self.emit("ldr x1, [x0]", "largo del arreglo dinámico")
            self.emit("lsl x1, x1, #3")
            self.emit("add x1, x1, #8", "bytes = 8 + largo * 8")
        else:
            self.cargar_inmediato("x1", tamano(tipo))
        self.llamar("__oxi_copiar")                 # x0 = copia nueva

    def visit_ArrayLiteral(self, nodo):
        """[e1, e2, ...]: malloc del bloque completo y se guarda cada valor
        en su posición. Los literales anidados ([[1, 2], [3, 4]]) se
        escriben directo en el mismo bloque (aplanados)."""
        tipo = nodo.tipo_resultado
        self.comentario(f"arreglo {tipo}  (línea {nodo.linea})")
        self.cargar_inmediato("x0", tamano(tipo))
        self.emit("bl malloc", f"reservar {tamano(tipo)} bytes en el heap")
        self.push()                                 # [sp] = bloque
        self.llenar(nodo, tipo, 0)
        self.pop("x0")                              # x0 = puntero al arreglo
        return tipo

    def llenar(self, nodo, tipo, desplazamiento):
        tipo_elem = elemento(tipo)
        paso = tamano(tipo_elem)
        for k, e in enumerate(nodo.elementos):
            pos = desplazamiento + k * paso
            if es_estatico(tipo_elem):
                if isinstance(e, ast.ArrayLiteral):
                    self.llenar(e, tipo_elem, pos)  # se aplana en el mismo bloque
                    continue
                self.visitar(e)                     # x0 = otro arreglo
                self.emit("mov x1, x0", "origen")
                self.emit("ldr x0, [sp]")
                self.sumar_inmediato("x0", "x0", pos)
                self.cargar_inmediato("x2", paso)
                self.emit("bl memcpy", "copiar el sub-arreglo")
            else:
                # Valor simple (o puntero a un arreglo dinámico)
                t = self.visitar(e)
                if tipo_elem == F64 and t == I32:
                    self.emit("scvtf d0, x0")
                self.emit("ldr x10, [sp]", "x10 = bloque")
                self.sumar_inmediato("x10", "x10", pos)
                reg = "d0" if tipo_elem == F64 else "x0"
                self.emit(f"str {reg}, [x10]", f"elemento en el byte {pos}")

    def visit_ArrayRepeat(self, nodo):
        """[valor; N]: se evalúa el valor una vez y se copia N veces."""
        tipo = nodo.tipo_resultado
        tipo_elem = elemento(tipo)
        paso = tamano(tipo_elem)
        ciclo, fin = self.nueva_etiqueta("repetir"), self.nueva_etiqueta("repetir_fin")
        self.comentario(f"arreglo {tipo} con [valor; {nodo.cantidad}]  (línea {nodo.linea})")
        self.cargar_inmediato("x0", tamano(tipo))
        self.emit("bl malloc")
        self.push()                                 # [sp+32] = bloque
        self.visitar(nodo.valor)
        self.push_valor(tipo_elem)                  # [sp+16] = valor
        self.emit("str xzr, [sp, #-16]!", "[sp] = i = 0")
        self.etiqueta(ciclo)
        self.emit("ldr x11, [sp]")
        self.cargar_inmediato("x12", nodo.cantidad)
        self.emit("cmp x11, x12")
        self.emit(f"b.ge {fin}")
        self.emit("ldr x10, [sp, #32]")
        self.cargar_inmediato("x12", paso)
        self.emit("madd x10, x11, x12, x10", "x10 = bloque + i * tamaño")
        if es_estatico(tipo_elem):
            self.emit("mov x0, x10")
            self.emit("ldr x1, [sp, #16]")
            self.cargar_inmediato("x2", paso)
            self.emit("bl memcpy")
        else:
            self.emit("ldr x0, [sp, #16]")
            self.emit("str x0, [x10]")
        self.emit("ldr x11, [sp]")
        self.emit("add x11, x11, #1")
        self.emit("str x11, [sp]")
        self.emit(f"b {ciclo}")
        self.etiqueta(fin)
        self.emit("add sp, sp, #32", "quitar i y el valor")
        self.pop("x0")
        return tipo

    def puntero_arreglo(self, nodo):
        """x0 = puntero al bloque del arreglo que representa `nodo`.
        Si nodo es m[i] y la fila es estática, la "fila" es la dirección
        donde empieza dentro del bloque; si es dinámica, se lee el puntero."""
        if isinstance(nodo, ast.Index):
            self.direccion_elemento(nodo)
            if es_dinamico(nodo.tipo_resultado):
                self.emit("ldr x0, [x0]", "puntero al arreglo dinámico")
        else:
            self.visitar(nodo)

    def direccion_elemento(self, nodo):
        """Deja en x0 la DIRECCIÓN de base[indice].
        Para m[i][j] primero se calcula la dirección de la fila m[i] y
        luego se le suma j:  base + (i * columnas + j) * 8  (row-major)."""
        base = nodo.base
        tipo_arr = base.tipo_resultado
        paso = tamano(elemento(tipo_arr))
        self.puntero_arreglo(base)

        if nodo.indice_constante is not None:       # límites revisados al compilar
            self.sumar_inmediato("x0", "x0", nodo.indice_constante * paso)
            return

        self.push()                                 # guardar la base
        self.visitar(nodo.indice)                   # x0 = índice
        ok = self.nueva_etiqueta("indice_ok")
        if es_dinamico(tipo_arr):
            self.emit("ldr x1, [sp]")
            self.emit("ldr x12, [x1]", "x12 = largo (guardado en el bloque)")
        else:
            self.cargar_inmediato("x12", longitud(tipo_arr))
        self.emit("cmp x0, x12")
        # Comparación SIN signo: un índice negativo se ve como un número
        # enorme, así una sola instrucción revisa 0 <= i < largo.
        self.emit(f"b.lo {ok}", "0 <= índice < largo")
        self.emit("mov x2, x0")
        self.emit("mov x3, x12")
        self.cargar_inmediato("x0", nodo.linea)
        self.cargar_inmediato("x1", nodo.columna)
        self.llamar("__oxi_fuera_limites")          # no regresa
        self.etiqueta(ok)
        self.pop("x1")                              # x1 = base
        if es_dinamico(tipo_arr):
            self.emit("add x1, x1, #8", "saltar el largo")
        self.cargar_inmediato("x12", paso)
        self.emit("madd x0, x0, x12, x1", "x0 = base + índice * tamaño")

    def visit_Index(self, nodo):
        self.direccion_elemento(nodo)
        tipo = nodo.tipo_resultado
        if es_estatico(tipo):
            return tipo                             # m[i] es la dirección de la fila
        if tipo == F64:
            self.emit("ldr d0, [x0]", "leer el elemento")
        else:
            self.emit("ldr x0, [x0]", "leer el elemento")
        return tipo

    def asignar_elemento(self, nodo):
        """a[i] = v,  m[i][j] += v, ..."""
        objetivo = nodo.objetivo
        tipo_elem = objetivo.tipo_resultado
        self.comentario(f"elemento {nodo.op} ...  (línea {nodo.linea})")
        self.direccion_elemento(objetivo)
        self.push()                                 # [sp] = dirección del elemento
        if nodo.op == '=':
            tipo_valor = self.visitar(nodo.valor)
            if es_dinamico(tipo_elem):
                self.copiar_si_es_variable(nodo.valor, tipo_valor)
        else:
            self.emit("ldr x0, [sp]")
            if tipo_elem == F64:
                self.emit("ldr d0, [x0]", "valor actual")
            else:
                self.emit("ldr x0, [x0]", "valor actual")
            self.push_valor(tipo_elem)
            tipo_valor = self.visitar(nodo.valor)
            tipo_valor = self.aplicar(COMPUESTOS[nodo.op], tipo_elem, tipo_valor)
        if tipo_elem == F64 and tipo_valor == I32:
            self.emit("scvtf d0, x0", "promoción i32 -> f64")
        self.pop("x10")                             # x10 = dirección
        if es_estatico(tipo_elem):                  # m[0] = [1, 2, 3]: copiar la fila
            self.emit("mov x1, x0")
            self.emit("mov x0, x10")
            self.cargar_inmediato("x2", tamano(tipo_elem))
            self.emit("bl memcpy")
        elif tipo_elem == F64:
            self.emit("str d0, [x10]", "guardar el elemento")
        else:
            self.emit("str x0, [x10]", "guardar el elemento")

    def visit_Slice(self, nodo):
        """&a[i..j]: arreglo nuevo con una copia de los elementos i..j-1."""
        tipo_arr = nodo.base.tipo_resultado
        paso = tamano(elemento(tipo_arr))
        n = nodo.hasta - nodo.desde
        self.comentario(f"slice [{nodo.desde}..{nodo.hasta}]  (línea {nodo.linea})")
        self.puntero_arreglo(nodo.base)
        if es_estatico(tipo_arr):
            self.sumar_inmediato("x0", "x0", nodo.desde * paso)
            self.cargar_inmediato("x1", n * paso)
            self.llamar("__oxi_copiar")
            return nodo.tipo_resultado

        # Dinámico: el fin se revisa al ejecutar contra el largo guardado
        ok = self.nueva_etiqueta("slice_ok")
        self.emit("ldr x12, [x0]", "largo del arreglo")
        self.cargar_inmediato("x11", nodo.hasta)
        self.emit("cmp x11, x12")
        self.emit(f"b.ls {ok}", "fin <= largo")
        self.emit("mov x2, x11")
        self.emit("mov x3, x12")
        self.cargar_inmediato("x0", nodo.linea)
        self.cargar_inmediato("x1", nodo.columna)
        self.llamar("__oxi_fuera_limites")
        self.etiqueta(ok)
        self.push()                                 # [sp+16] = origen
        self.cargar_inmediato("x0", 8 + n * 8)
        self.emit("bl malloc")
        self.cargar_inmediato("x1", n)
        self.emit("str x1, [x0]", "largo del slice")
        self.push()                                 # [sp] = nuevo
        self.emit("add x0, x0, #8")
        self.emit("ldr x1, [sp, #16]")
        self.sumar_inmediato("x1", "x1", 8 + nodo.desde * 8)
        self.cargar_inmediato("x2", n * 8)
        self.emit("bl memcpy", "copiar los elementos")
        self.pop("x0")
        self.emit("add sp, sp, #16", "quitar el origen")
        return nodo.tipo_resultado

    # --- Métodos embebidos (sección 3.3.13) -------------------------------

    def visit_MethodCall(self, nodo):
        """Métodos embebidos. El objeto (y los argumentos) se evalúan y se
        llama a la instrucción o rutina que corresponde."""
        m, tipo = nodo.metodo, nodo.tipo_objeto
        self.comentario(f".{m}()  (línea {nodo.linea})")

        if es_arreglo(tipo):
            if m == 'len':
                if es_estatico(tipo):
                    self.cargar_inmediato("x0", longitud(tipo))   # constante
                else:
                    self.puntero_arreglo(nodo.objeto)
                    self.emit("ldr x0, [x0]", "largo guardado en el bloque")
            elif m == 'reverse':
                self.puntero_arreglo(nodo.objeto)               # se invierte en su lugar
                if es_estatico(tipo):
                    self.cargar_inmediato("x1", longitud(tipo))
                else:
                    self.emit("ldr x1, [x0]")
                    self.emit("add x0, x0, #8")
                self.cargar_inmediato("x2", tamano(elemento(tipo)))
                self.llamar("__oxi_invertir")
            elif m == 'collect':
                self.puntero_arreglo(nodo.objeto)               # ya es un arreglo
            elif m == 'contains':
                self.contiene_en_arreglo(nodo)
            return nodo.tipo_resultado

        # ---- String ----
        self.visitar(nodo.objeto)                   # x0 = texto
        if m == 'len':
            self.emit("bl strlen", "largo en bytes (igual que Rust)")
        elif m in ('to_uppercase', 'to_lowercase'):
            self.emit(f"mov x1, #{1 if m == 'to_uppercase' else 0}")
            self.llamar("__oxi_mayusculas")
        elif m == 'split_whitespace':
            self.llamar("__oxi_split_ws")
        elif m in ('contains', 'split'):
            self.push()
            self.visitar(nodo.args[0])              # x0 = lo que se busca / separador
            self.emit("mov x1, x0")
            self.pop("x0")
            if m == 'split':
                self.llamar("__oxi_split")
            else:
                self.emit("bl strstr", "puntero a la primera aparición o 0")
                self.emit("cmp x0, #0")
                self.emit("cset x0, ne", "true si se encontró")
        elif m == 'replace':
            self.push()                             # texto
            self.visitar(nodo.args[0])
            self.push()                             # lo que se reemplaza
            self.visitar(nodo.args[1])              # x0 = reemplazo
            self.emit("mov x2, x0")
            self.pop("x1")
            self.pop("x0")
            self.llamar("__oxi_replace")
        return nodo.tipo_resultado

    def contiene_en_arreglo(self, nodo):
        """arreglo.contains(v): recorre el arreglo comparando cada elemento
        con v (con la misma comparación que ==)."""
        tipo = nodo.tipo_objeto
        tipo_elem = elemento(tipo)
        ciclo, si, no, salida = (self.nueva_etiqueta("contiene"),
                                 self.nueva_etiqueta("contiene_si"),
                                 self.nueva_etiqueta("contiene_no"),
                                 self.nueva_etiqueta("contiene_fin"))
        self.puntero_arreglo(nodo.objeto)
        self.empezar_recorrido(tipo)                # [sp+32] = datos, [sp+16] = largo
        tipo_v = self.visitar(nodo.args[0])
        if tipo_elem == F64 and tipo_v == I32:
            self.emit("scvtf d0, x0")
        # el valor buscado ocupa el lugar de i; i va arriba
        self.push_valor(tipo_elem)                  # [sp] = valor
        self.emit("str xzr, [sp, #-16]!", "[sp] = i = 0  ([sp+16] = valor)")
        self.etiqueta(ciclo)
        self.emit("ldr x11, [sp]")
        self.emit("ldr x12, [sp, #32]", "largo")
        self.emit("cmp x11, x12")
        self.emit(f"b.ge {no}", "se recorrió todo: no está")
        self.emit("ldr x10, [sp, #48]", "datos")
        self.emit("ldr x0, [x10, x11, lsl #3]", "x0 = arreglo[i]")
        if tipo_elem == F64:
            self.emit("fmov d0, x0")
            self.emit("ldr d1, [sp, #16]")
            self.emit("fcmp d0, d1")
            self.emit(f"b.eq {si}")
        elif tipo_elem == STRING:
            self.emit("ldr x1, [sp, #16]")
            self.emit("bl strcmp")
            self.emit(f"cbz w0, {si}", "strcmp == 0: son iguales")
        else:
            self.emit("ldr x1, [sp, #16]")
            self.emit("cmp x0, x1")
            self.emit(f"b.eq {si}")
        self.emit("ldr x11, [sp]")
        self.emit("add x11, x11, #1")
        self.emit("str x11, [sp]")
        self.emit(f"b {ciclo}")
        self.etiqueta(si)
        self.emit("mov x0, #1", "encontrado: true")
        self.emit(f"b {salida}")
        self.etiqueta(no)
        self.emit("mov x0, #0", "no encontrado: false")
        self.etiqueta(salida)
        self.emit("add sp, sp, #64", "quitar i, valor, largo y datos")
        return BOOL

    def empezar_recorrido(self, tipo):
        """Con x0 = puntero al arreglo, deja en la pila (en este orden):
            [sp+16] = dirección del primer elemento
            [sp]    = cantidad de elementos
        Sirve igual para estáticos y dinámicos."""
        if es_dinamico(tipo):
            self.emit("ldr x1, [x0]", "largo")
            self.emit("add x0, x0, #8", "datos después del largo")
        else:
            self.cargar_inmediato("x1", longitud(tipo))
        self.push("x0")
        self.push("x1")

    def funcion_embebida(self, nodo):
        if nodo.embebida == 'typeof':
            # El tipo se conoce al compilar: es un texto constante
            self.direccion("x0", self.cadena(nodo.texto_tipo))
            return STRING
        # random(min, max)
        self.visitar(nodo.args[0])
        self.push()
        self.visitar(nodo.args[1])
        self.emit("mov x1, x0", "x1 = max")
        self.pop("x0")                              # x0 = min
        self.llamar("__oxi_random")
        return I32

    # --- for ---------------------------------------------------------------

    def visit_For(self, nodo):
        """for i in a..b { C }  se traduce como

                <a> ; push                  // [sp+16] = actual
                <b> ; push                  // [sp]    = fin
            .Lfor:
                actual >= fin ? -> .Lfin    // con ..= se usa  actual > fin
                i = actual ; <C>
            .Lsiguiente:                    // aquí salta continue
                actual += 1 ; b .Lfor
            .Lfin:                          // aquí salta break
                quitar actual y fin

        for x in arreglo { C }  es igual, pero con un índice que recorre
        los elementos y x = arreglo[índice] en cada vuelta."""
        sym = nodo.simbolo
        ciclo = self.nueva_etiqueta("for")
        siguiente = self.nueva_etiqueta("for_siguiente")
        fin = self.nueva_etiqueta("for_fin")
        self.comentario(f"for {nodo.variable}  (línea {nodo.linea})")

        if nodo.iterable is None:
            self.visitar(nodo.inicio)
            self.push()                             # actual
            self.visitar(nodo.fin)
            self.push()                             # fin
            self.etiqueta(ciclo)
            self.emit("ldr x0, [sp, #16]", "actual")
            self.emit("ldr x1, [sp]", "fin")
            self.emit("cmp x0, x1")
            self.emit(f"{'b.gt' if nodo.inclusivo else 'b.ge'} {fin}",
                      "se terminó el rango")
            self.guardar_variable(sym, I32)
            self.cuerpo_ciclo(nodo, continuar=siguiente, salir=fin)
            self.etiqueta(siguiente)
            self.emit("ldr x0, [sp, #16]")
            self.emit("add x0, x0, #1")
            self.emit("str x0, [sp, #16]", "actual += 1")
            self.emit(f"b {ciclo}")
            self.etiqueta(fin)
            self.emit("add sp, sp, #32", "quitar actual y fin")
            return

        tipo = nodo.iterable.tipo_resultado
        tipo_elem = elemento(tipo)
        paso = tamano(tipo_elem)
        self.puntero_arreglo(nodo.iterable)
        self.empezar_recorrido(tipo)                # [sp+16] = datos, [sp] = largo
        self.emit("str xzr, [sp, #-16]!", "[sp] = i = 0")
        self.etiqueta(ciclo)
        self.emit("ldr x11, [sp]")
        self.emit("ldr x12, [sp, #16]", "largo")
        self.emit("cmp x11, x12")
        self.emit(f"b.ge {fin}", "se recorrieron todos")
        self.emit("ldr x10, [sp, #32]", "datos")
        self.cargar_inmediato("x12", paso)
        self.emit("madd x0, x11, x12, x10", "x0 = dirección del elemento i")
        if es_estatico(tipo_elem):
            self.cargar_inmediato("x1", paso)
            self.llamar("__oxi_copiar")             # la variable recibe su copia
        elif tipo_elem == F64:
            self.emit("ldr d0, [x0]")
        else:
            self.emit("ldr x0, [x0]")
        self.guardar_variable(sym, tipo_elem)
        self.cuerpo_ciclo(nodo, continuar=siguiente, salir=fin)
        self.etiqueta(siguiente)
        self.emit("ldr x11, [sp]")
        self.emit("add x11, x11, #1")
        self.emit("str x11, [sp]", "i += 1")
        self.emit(f"b {ciclo}")
        self.etiqueta(fin)
        self.emit("add sp, sp, #48", "quitar i, largo y datos")

    # --- match -------------------------------------------------------------

    def visit_Match(self, nodo):
        """match v { p1 => A, p2 => B, _ => C }  se traduce como una
        cadena de comparaciones (igual que if / else if / else):

                <evaluar v> ; push           // v se guarda una sola vez
                v == p1 ?  no -> .Lsig_1
                quitar v ; <A> ; b .Lfin
            .Lsig_1:
                v == p2 ?  no -> .Lsig_2
                quitar v ; <B> ; b .Lfin
            .Lsig_2:
                quitar v ; <C>               // comodín
            .Lfin:
        v se quita de la pila ANTES de cada cuerpo, así un break o
        continue dentro del brazo no deja la pila desbalanceada."""
        tipo = nodo.tipo_valor
        fin = self.nueva_etiqueta("match_fin")
        self.comentario(f"match  (línea {nodo.linea})")
        self.visitar(nodo.valor)
        self.push_valor(tipo)
        for brazo in nodo.brazos:
            if brazo.comodin:
                self.comentario("_ =>")
                self.emit("add sp, sp, #16", "quitar el valor del match")
                self.cuerpo_brazo(brazo)
                break
            siguiente = self.nueva_etiqueta("match_sig")
            self.emit(f"ldr {'d0' if tipo == F64 else 'x0'}, [sp]", "valor del match")
            self.push_valor(tipo)
            tipo_patron = self.visitar(brazo.patron)
            self.aplicar('==', tipo, tipo_patron)   # x0 = (valor == patrón)
            self.emit(f"cbz x0, {siguiente}", "no coincide: probar el siguiente")
            self.emit("add sp, sp, #16", "quitar el valor del match")
            self.cuerpo_brazo(brazo)
            self.emit(f"b {fin}")
            self.etiqueta(siguiente)
        else:
            self.emit("add sp, sp, #16", "ningún brazo coincidió")
        self.etiqueta(fin)

    def cuerpo_brazo(self, brazo):
        if isinstance(brazo.cuerpo, ast.Block):
            self.visit_Block(brazo.cuerpo)
        else:
            self.visitar(brazo.cuerpo)

    # --- Impresión de arreglos ----------------------------------------------

    def imprimir_arreglo(self, tipo):
        """Imprime el arreglo apuntado por x0 como [a, b, c] (las matrices
        como [[1, 2], [3, 4]]). Usa un ciclo en ensamblador; el índice,
        el largo y los datos se guardan en la pila porque printf borra
        los registros."""
        tipo_elem = elemento(tipo)
        paso = tamano(tipo_elem)
        ciclo = self.nueva_etiqueta("imprimir")
        fin = self.nueva_etiqueta("imprimir_fin")
        sin_coma = self.nueva_etiqueta("sin_coma")

        self.empezar_recorrido(tipo)                # [sp+16] = datos, [sp] = largo
        self.emit("str xzr, [sp, #-16]!", "[sp] = i = 0")
        self.printf("[")
        self.etiqueta(ciclo)
        self.emit("ldr x11, [sp]")
        self.emit("ldr x12, [sp, #16]", "largo")
        self.emit("cmp x11, x12")
        self.emit(f"b.ge {fin}")
        self.emit(f"cbz x11, {sin_coma}", "antes del primero no va coma")
        self.printf(", ")
        self.etiqueta(sin_coma)
        self.emit("ldr x11, [sp]")
        self.emit("ldr x10, [sp, #32]", "datos")
        self.cargar_inmediato("x12", paso)
        self.emit("madd x0, x11, x12, x10", "x0 = dirección del elemento i")
        if es_estatico(tipo_elem):
            self.imprimir_arreglo(tipo_elem)
        elif es_dinamico(tipo_elem):
            self.emit("ldr x0, [x0]")
            self.imprimir_arreglo(tipo_elem)
        else:
            self.emit(f"ldr {'d0' if tipo_elem == F64 else 'x0'}, [x0]")
            formato = {STRING: '"%s"', CHAR: "'%s'"}.get(tipo_elem, ESPECIFICADOR[tipo_elem])
            self.printf(formato, tipo_elem)
        self.emit("ldr x11, [sp]")
        self.emit("add x11, x11, #1")
        self.emit("str x11, [sp]", "i += 1")
        self.emit(f"b {ciclo}")
        self.etiqueta(fin)
        self.printf("]")
        self.emit("add sp, sp, #48", "quitar i, largo y datos")


def registros_parametros(tipos):
    """Registro de cada parámetro según la convención AArch64:
    los enteros/punteros usan x0, x1, ... y los f64 usan d0, d1, ...
    con contadores separados.  (i32, f64, i32) -> [x0, d0, x1]"""
    enteros = decimales = 0
    registros = []
    for tipo in tipos:
        if tipo == F64:
            registros.append(f"d{decimales}")
            decimales += 1
        else:
            registros.append(f"x{enteros}")
            enteros += 1
    return registros


def escapar_asm(texto):
    """Convierte un texto a una cadena válida para .asciz.
    Los caracteres no ASCII (á, ñ, emojis) se escriben como bytes UTF-8
    en octal, así el ensamblador no tiene problemas con ellos."""
    partes = []
    for byte in texto.encode('utf-8'):
        c = chr(byte)
        if c == '"':
            partes.append('\\"')
        elif c == '\\':
            partes.append('\\\\')
        elif c == '\n':
            partes.append('\\n')
        elif c == '\t':
            partes.append('\\t')
        elif 32 <= byte < 127:
            partes.append(c)
        else:
            partes.append(f"\\{byte:03o}")
    return ''.join(partes)


# ======================================================================
# Rutinas de apoyo en ensamblador
# Cada una es una función normal de ARM64: recibe sus datos en x0/x1/d0
# y devuelve el resultado en x0. Las que llaman a otras funciones
# guardan x29/x30 y los registros x19-x22 que usan (callee-saved).
# ======================================================================

def _rutina_f64_str(gen):
    """d0 -> x0 = texto del decimal.
    Si el número no tiene parte decimal se imprime con ".0" (3.0, 0.0),
    como muestra el enunciado; si la tiene, con hasta 15 cifras
    significativas (12.5, 3.1416, 0.3)."""
    limite = gen.decimal(1e15)
    entero = gen.cadena("%.1f")
    general = gen.cadena("%.15g")
    return f"""
// ---- __oxi_f64_str: d0 -> x0 = texto del f64 ----
__oxi_f64_str:
    stp x29, x30, [sp, #-16]!
    mov x29, sp
    adrp x2, {general}
    add x2, x2, :lo12:{general}         // formato "%.15g" por defecto
    frintz d1, d0                       // d1 = parte entera
    fcmp d1, d0
    b.ne .Lf64_formato                  // tiene decimales -> "%.15g"
    fabs d1, d0
    adrp x9, {limite}
    ldr d2, [x9, :lo12:{limite}]
    fcmp d1, d2
    b.ge .Lf64_formato                  // número enorme -> "%.15g"
    adrp x2, {entero}
    add x2, x2, :lo12:{entero}          // entero -> "%.1f" (3.0)
.Lf64_formato:
    adrp x0, buf_f64
    add x0, x0, :lo12:buf_f64
    mov x1, #64
    bl snprintf                         // snprintf(buf, 64, formato, d0)
    adrp x0, buf_f64
    add x0, x0, :lo12:buf_f64
    ldp x29, x30, [sp], #16
    ret
"""


def _rutina_char_str(gen):
    return """
// ---- __oxi_char_str: x0 = código Unicode -> x0 = texto UTF-8 ----
__oxi_char_str:
    adrp x1, buf_char
    add x1, x1, :lo12:buf_char
    cmp x0, #0x80
    b.hs .Lchar_2bytes
    strb w0, [x1]                       // ASCII: 1 byte
    strb wzr, [x1, #1]
    b .Lchar_fin
.Lchar_2bytes:
    cmp x0, #0x800
    b.hs .Lchar_3bytes
    lsr x2, x0, #6                      // 110xxxxx 10xxxxxx  (á, ñ, é...)
    orr x2, x2, #0xC0
    strb w2, [x1]
    and x2, x0, #0x3F
    orr x2, x2, #0x80
    strb w2, [x1, #1]
    strb wzr, [x1, #2]
    b .Lchar_fin
.Lchar_3bytes:
    cmp x0, #0x10, lsl #12              // 0x10000
    b.hs .Lchar_4bytes
    lsr x2, x0, #12                     // 1110xxxx 10xxxxxx 10xxxxxx
    orr x2, x2, #0xE0
    strb w2, [x1]
    lsr x2, x0, #6
    and x2, x2, #0x3F
    orr x2, x2, #0x80
    strb w2, [x1, #1]
    and x2, x0, #0x3F
    orr x2, x2, #0x80
    strb w2, [x1, #2]
    strb wzr, [x1, #3]
    b .Lchar_fin
.Lchar_4bytes:
    lsr x2, x0, #18                     // 11110xxx + 3 bytes (emojis)
    orr x2, x2, #0xF0
    strb w2, [x1]
    lsr x2, x0, #12
    and x2, x2, #0x3F
    orr x2, x2, #0x80
    strb w2, [x1, #1]
    lsr x2, x0, #6
    and x2, x2, #0x3F
    orr x2, x2, #0x80
    strb w2, [x1, #2]
    and x2, x0, #0x3F
    orr x2, x2, #0x80
    strb w2, [x1, #3]
    strb wzr, [x1, #4]
.Lchar_fin:
    mov x0, x1
    ret
"""


def _rutina_concat(gen):
    return """
// ---- __oxi_concat: x0 = a, x1 = b -> x0 = a + b (nuevo en el heap) ----
__oxi_concat:
    stp x29, x30, [sp, #-48]!
    mov x29, sp
    stp x19, x20, [sp, #16]             // guardar registros que se usan
    str x21, [sp, #32]
    mov x19, x0                         // x19 = a
    mov x20, x1                         // x20 = b
    bl strlen
    mov x21, x0                         // x21 = largo de a
    mov x0, x20
    bl strlen                           // x0 = largo de b
    add x0, x0, x21
    add x0, x0, #1                      // + 1 por el '\\0' final
    bl malloc                           // reservar en el heap
    mov x1, x19
    bl strcpy                           // copiar a
    mov x1, x20
    bl strcat                           // agregar b
    ldp x19, x20, [sp, #16]
    ldr x21, [sp, #32]
    ldp x29, x30, [sp], #48
    ret
"""


def _rutina_repetir(gen):
    return """
// ---- __oxi_repetir: x0 = texto, x1 = n -> x0 = texto repetido n veces ----
__oxi_repetir:
    stp x29, x30, [sp, #-48]!
    mov x29, sp
    stp x19, x20, [sp, #16]
    stp x21, x22, [sp, #32]
    mov x19, x0                         // x19 = texto
    cmp x1, #0
    csel x20, x1, xzr, gt               // x20 = n (si es negativo, 0)
    bl strlen
    mul x0, x0, x20
    add x0, x0, #1
    bl malloc                           // espacio para largo * n + 1
    mov x21, x0                         // x21 = resultado
    strb wzr, [x21]                     // empieza como cadena vacía
    mov x22, #0                         // x22 = contador
.Lrepetir_ciclo:
    cmp x22, x20
    b.ge .Lrepetir_fin
    mov x0, x21
    mov x1, x19
    bl strcat                           // resultado += texto
    add x22, x22, #1
    b .Lrepetir_ciclo
.Lrepetir_fin:
    mov x0, x21
    ldp x19, x20, [sp, #16]
    ldp x21, x22, [sp, #32]
    ldp x29, x30, [sp], #48
    ret
"""


def _rutina_copiar(gen):
    return """
// ---- __oxi_copiar: x0 = origen, x1 = bytes -> x0 = copia nueva en el heap ----
__oxi_copiar:
    stp x29, x30, [sp, #-32]!
    mov x29, sp
    stp x19, x20, [sp, #16]
    mov x19, x0                         // x19 = origen
    mov x20, x1                         // x20 = bytes
    mov x0, x20
    bl malloc
    mov x1, x19
    mov x2, x20
    bl memcpy                           // memcpy(nuevo, origen, bytes) -> x0 = nuevo
    ldp x19, x20, [sp, #16]
    ldp x29, x30, [sp], #32
    ret
"""


def _rutina_fuera_limites(gen):
    mensaje = gen.cadena("\n[Error de ejecución] Línea %d, Columna %d: Índice fuera "
                         "de los límites del arreglo (índice %d, longitud %d).\n")
    return f"""
// ---- __oxi_fuera_limites: x0 = línea, x1 = columna, x2 = índice, x3 = largo ----
// Imprime el error y termina el programa con código 1.
__oxi_fuera_limites:
    stp x29, x30, [sp, #-16]!
    mov x29, sp
    mov x4, x3
    mov x3, x2
    mov x2, x1
    mov x1, x0
    adrp x0, {mensaje}
    add x0, x0, :lo12:{mensaje}
    bl printf
    mov w0, #1
    bl exit                             // exit vacía el búfer de printf
"""


def _rutina_replace(gen):
    return """
// ---- __oxi_replace: x0 = texto, x1 = buscar, x2 = reemplazo -> x0 = texto nuevo ----
// Recorre el texto con strstr; copia lo que hay antes de cada aparición
// y luego el reemplazo. El resultado se reserva en el heap.
__oxi_replace:
    stp x29, x30, [sp, #-64]!
    mov x29, sp
    stp x19, x20, [sp, #16]
    stp x21, x22, [sp, #32]
    stp x23, x24, [sp, #48]
    mov x19, x0                         // x19 = posición actual en el texto
    mov x20, x1                         // x20 = buscar
    mov x21, x2                         // x21 = reemplazo
    mov x0, x20
    bl strlen
    mov x22, x0                         // x22 = largo de buscar
    cbz x22, .Lrep_copia                // buscar "" -> devolver una copia
    mov x0, x21
    bl strlen
    mov x23, x0                         // x23 = largo del reemplazo
    mov x0, x19
    bl strlen                           // x0 = largo del texto
    udiv x1, x0, x22                    // máximo de apariciones
    mul x1, x1, x23
    add x0, x0, x1
    add x0, x0, #1                      // tamaño suficiente para el resultado
    bl malloc
    mov x24, x0                         // x24 = resultado
    strb wzr, [x24]                     // empieza vacío
.Lrep_ciclo:
    mov x0, x19
    mov x1, x20
    bl strstr                           // x0 = siguiente aparición (o 0)
    cbz x0, .Lrep_resto
    sub x2, x0, x19                     // caracteres antes de la aparición
    str x2, [sp, #-16]!
    mov x0, x24
    mov x1, x19
    bl strncat                          // resultado += texto[0 .. aparición)
    ldr x2, [sp], #16
    add x19, x19, x2
    add x19, x19, x22                   // saltar lo encontrado
    mov x0, x24
    mov x1, x21
    bl strcat                           // resultado += reemplazo
    b .Lrep_ciclo
.Lrep_resto:
    mov x0, x24
    mov x1, x19
    bl strcat                           // lo que queda del texto
    mov x0, x24
    b .Lrep_fin
.Lrep_copia:
    mov x0, x19
    bl strlen
    add x0, x0, #1
    bl malloc
    mov x1, x19
    bl strcpy
.Lrep_fin:
    ldp x19, x20, [sp, #16]
    ldp x21, x22, [sp, #32]
    ldp x23, x24, [sp, #48]
    ldp x29, x30, [sp], #64
    ret
"""


def _rutina_mayusculas(gen):
    return """
// ---- __oxi_mayusculas: x0 = texto, x1 = 1 (mayúsculas) o 0 (minúsculas) ----
// Devuelve una copia nueva. Cambia las letras a-z / A-Z y también las
// letras con tilde, diéresis y la ñ: en UTF-8 son 2 bytes, C3 xx, y la
// mayúscula y la minúscula solo difieren en 0x20 en el segundo byte
// (á = C3 A1, Á = C3 81;  ñ = C3 B1, Ñ = C3 91).
__oxi_mayusculas:
    stp x29, x30, [sp, #-32]!
    mov x29, sp
    stp x19, x20, [sp, #16]
    mov x19, x0
    mov x20, x1
    bl strlen
    add x0, x0, #1
    bl malloc
    mov x1, x19
    bl strcpy                           // x0 = copia
    mov x2, x0                          // x2 recorre la copia
.Lmay_ciclo:
    ldrb w3, [x2]
    cbz w3, .Lmay_fin
    cmp w3, #0xC3
    b.eq .Lmay_latin
    cbz x20, .Lmay_minus
    sub w4, w3, #97                     // ¿está entre 'a' y 'z'?
    cmp w4, #25
    b.hi .Lmay_sig
    sub w3, w3, #32                     // 'a' -> 'A'
    strb w3, [x2]
    b .Lmay_sig
.Lmay_minus:
    sub w4, w3, #65                     // ¿está entre 'A' y 'Z'?
    cmp w4, #25
    b.hi .Lmay_sig
    add w3, w3, #32                     // 'A' -> 'a'
    strb w3, [x2]
.Lmay_sig:
    add x2, x2, #1
    b .Lmay_ciclo
.Lmay_latin:                            // letra de 2 bytes: C3 xx
    ldrb w3, [x2, #1]
    cbz w3, .Lmay_fin
    cbz x20, .Lmay_latin_minus
    sub w4, w3, #0xA0                   // minúsculas: A0..BE (sin B7 = ÷)
    cmp w4, #0x1E
    b.hi .Lmay_latin_sig
    cmp w3, #0xB7
    b.eq .Lmay_latin_sig
    sub w3, w3, #0x20
    strb w3, [x2, #1]
    b .Lmay_latin_sig
.Lmay_latin_minus:
    sub w4, w3, #0x80                   // mayúsculas: 80..9E (sin 97 = ×)
    cmp w4, #0x1E
    b.hi .Lmay_latin_sig
    cmp w3, #0x97
    b.eq .Lmay_latin_sig
    add w3, w3, #0x20
    strb w3, [x2, #1]
.Lmay_latin_sig:
    add x2, x2, #2
    b .Lmay_ciclo
.Lmay_fin:
    ldp x19, x20, [sp, #16]
    ldp x29, x30, [sp], #32
    ret
"""


def _rutina_invertir(gen):
    return """
// ---- __oxi_invertir: x0 = arreglo, x1 = elementos, x2 = bytes por elemento ----
// Intercambia el primero con el último, el segundo con el penúltimo...
// (en una matriz invierte el orden de las filas).
__oxi_invertir:
    sub x3, x1, #1                      // j = n - 1
    mov x4, #0                          // i = 0
.Linv_ciclo:
    cmp x4, x3
    b.ge .Linv_fin
    madd x5, x4, x2, x0                 // dirección del elemento i
    madd x6, x3, x2, x0                 // dirección del elemento j
    mov x7, #0
.Linv_palabra:                          // intercambiar de 8 en 8 bytes
    cmp x7, x2
    b.ge .Linv_sig
    ldr x8, [x5, x7]
    ldr x9, [x6, x7]
    str x9, [x5, x7]
    str x8, [x6, x7]
    add x7, x7, #8
    b .Linv_palabra
.Linv_sig:
    add x4, x4, #1
    sub x3, x3, #1
    b .Linv_ciclo
.Linv_fin:
    ret
"""


def _rutina_random(gen):
    return """
// ---- __oxi_random: x0 = min, x1 = max -> x0 = entero al azar en [min, max] ----
// La primera vez inicializa la semilla con la hora (srand(time(0))).
__oxi_random:
    stp x29, x30, [sp, #-32]!
    mov x29, sp
    stp x19, x20, [sp, #16]
    mov x19, x0                         // min
    mov x20, x1                         // max
    adrp x9, oxi_semilla
    ldr x10, [x9, :lo12:oxi_semilla]
    cbnz x10, .Lrand_listo
    mov x10, #1
    str x10, [x9, :lo12:oxi_semilla]
    mov x0, #0
    bl time
    bl srand
.Lrand_listo:
    bl rand                             // w0 = 0 .. RAND_MAX
    sub x1, x20, x19
    add x1, x1, #1                      // cantidad de valores posibles
    cmp x1, #0
    b.le .Lrand_min                     // max < min: devolver min
    udiv x2, x0, x1
    msub x0, x2, x1, x0                 // x0 = rand % cantidad
    add x0, x0, x19                     // + min
    b .Lrand_fin
.Lrand_min:
    mov x0, x19
.Lrand_fin:
    ldp x19, x20, [sp, #16]
    ldp x29, x30, [sp], #32
    ret
"""


def _rutina_subcadena(gen):
    return """
// ---- __oxi_subcadena: x0 = inicio, x1 = largo -> x0 = texto nuevo ----
__oxi_subcadena:
    stp x29, x30, [sp, #-32]!
    mov x29, sp
    stp x19, x20, [sp, #16]
    mov x19, x0
    mov x20, x1
    add x0, x20, #1
    bl malloc
    mov x1, x19
    mov x2, x20
    bl memcpy                           // x0 = nuevo
    strb wzr, [x0, x20]                 // terminar con '\\0'
    ldp x19, x20, [sp, #16]
    ldp x29, x30, [sp], #32
    ret
"""


def _rutina_split(gen):
    return """
// ---- __oxi_split: x0 = texto, x1 = separador -> x0 = arreglo dinámico ----
// Resultado en el heap:  [ largo | parte0 | parte1 | ... ]
// Primero cuenta las partes (apariciones + 1), luego copia cada una.
__oxi_split:
    stp x29, x30, [sp, #-64]!
    mov x29, sp
    stp x19, x20, [sp, #16]
    stp x21, x22, [sp, #32]
    stp x23, x24, [sp, #48]
    mov x19, x0                         // x19 = texto
    mov x20, x1                         // x20 = separador
    mov x0, x20
    bl strlen
    mov x21, x0                         // x21 = largo del separador
    cbz x21, .Lspl_uno                  // separador "": una sola parte
    mov x22, #1                         // x22 = cantidad de partes
    mov x23, x19
.Lspl_contar:
    mov x0, x23
    mov x1, x20
    bl strstr
    cbz x0, .Lspl_reservar
    add x22, x22, #1
    add x23, x0, x21
    b .Lspl_contar
.Lspl_reservar:
    lsl x0, x22, #3
    add x0, x0, #8
    bl malloc
    mov x24, x0                         // x24 = arreglo
    str x22, [x24]                      // largo
    mov x22, #0                         // x22 = índice de la parte
    mov x23, x19                        // x23 = inicio de la parte
.Lspl_parte:
    mov x0, x23
    mov x1, x20
    bl strstr                           // x0 = fin de la parte (o 0)
    cbz x0, .Lspl_ultima
    str x0, [sp, #-16]!
    sub x1, x0, x23
    mov x0, x23
    bl __oxi_subcadena
    add x9, x24, #8
    str x0, [x9, x22, lsl #3]           // arreglo[i] = parte
    add x22, x22, #1
    ldr x0, [sp], #16
    add x23, x0, x21                    // la siguiente empieza después del separador
    b .Lspl_parte
.Lspl_ultima:
    mov x0, x23
    bl strlen
    mov x1, x0
    mov x0, x23
    bl __oxi_subcadena
    add x9, x24, #8
    str x0, [x9, x22, lsl #3]
    mov x0, x24
    b .Lspl_fin
.Lspl_uno:
    mov x0, #16
    bl malloc
    mov x24, x0
    mov x1, #1
    str x1, [x24]
    mov x0, x19
    bl strlen
    mov x1, x0
    mov x0, x19
    bl __oxi_subcadena
    str x0, [x24, #8]
    mov x0, x24
.Lspl_fin:
    ldp x19, x20, [sp, #16]
    ldp x21, x22, [sp, #32]
    ldp x23, x24, [sp, #48]
    ldp x29, x30, [sp], #64
    ret
"""


def _rutina_split_ws(gen):
    return """
// ---- __oxi_split_ws: x0 = texto -> x0 = arreglo dinámico de palabras ----
// Separa por espacios, tabuladores y saltos de línea, sin partes vacías.
// Un byte es espacio si es ' ', '\\t', '\\n' o '\\r' (ccmp encadena las 4 comparaciones).
__oxi_split_ws:
    stp x29, x30, [sp, #-64]!
    mov x29, sp
    stp x19, x20, [sp, #16]
    stp x21, x22, [sp, #32]
    stp x23, x24, [sp, #48]
    mov x19, x0
    mov x22, #0                         // cantidad de palabras
    mov x20, #0                         // 1 si se está dentro de una palabra
    mov x23, x19
.Lws_contar:
    ldrb w1, [x23]
    cbz w1, .Lws_reservar
    cmp w1, #32
    ccmp w1, #9, #4, ne
    ccmp w1, #10, #4, ne
    ccmp w1, #13, #4, ne
    b.eq .Lws_contar_espacio
    cbnz x20, .Lws_contar_sig
    mov x20, #1
    add x22, x22, #1                    // empieza una palabra
    b .Lws_contar_sig
.Lws_contar_espacio:
    mov x20, #0
.Lws_contar_sig:
    add x23, x23, #1
    b .Lws_contar
.Lws_reservar:
    lsl x0, x22, #3
    add x0, x0, #8
    bl malloc
    mov x24, x0
    str x22, [x24]                      // largo
    mov x22, #0
    mov x23, x19
.Lws_buscar:                            // saltar espacios
    ldrb w1, [x23]
    cbz w1, .Lws_listo
    cmp w1, #32
    ccmp w1, #9, #4, ne
    ccmp w1, #10, #4, ne
    ccmp w1, #13, #4, ne
    b.ne .Lws_palabra
    add x23, x23, #1
    b .Lws_buscar
.Lws_palabra:
    mov x21, x23                        // x21 recorre hasta el fin de la palabra
.Lws_fin_palabra:
    ldrb w1, [x21]
    cbz w1, .Lws_copiar
    cmp w1, #32
    ccmp w1, #9, #4, ne
    ccmp w1, #10, #4, ne
    ccmp w1, #13, #4, ne
    b.eq .Lws_copiar
    add x21, x21, #1
    b .Lws_fin_palabra
.Lws_copiar:
    mov x0, x23
    sub x1, x21, x23
    bl __oxi_subcadena
    add x9, x24, #8
    str x0, [x9, x22, lsl #3]
    add x22, x22, #1
    mov x23, x21
    b .Lws_buscar
.Lws_listo:
    mov x0, x24
    ldp x19, x20, [sp, #16]
    ldp x21, x22, [sp, #32]
    ldp x23, x24, [sp, #48]
    ldp x29, x30, [sp], #64
    ret
"""


# Rutinas que llaman a otras rutinas de apoyo
DEPENDENCIAS = {
    "__oxi_split": ("__oxi_subcadena",),
    "__oxi_split_ws": ("__oxi_subcadena",),
}


RUTINAS = {
    "__oxi_subcadena": _rutina_subcadena,
    "__oxi_split": _rutina_split,
    "__oxi_split_ws": _rutina_split_ws,
    "__oxi_replace": _rutina_replace,
    "__oxi_mayusculas": _rutina_mayusculas,
    "__oxi_invertir": _rutina_invertir,
    "__oxi_random": _rutina_random,
    "__oxi_copiar": _rutina_copiar,
    "__oxi_fuera_limites": _rutina_fuera_limites,
    "__oxi_f64_str": _rutina_f64_str,
    "__oxi_char_str": _rutina_char_str,
    "__oxi_concat": _rutina_concat,
    "__oxi_repetir": _rutina_repetir,
}
