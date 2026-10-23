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
        """bl a una rutina de apoyo y la marca para agregarla al .s."""
        self.rutinas.add(rutina)
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
            "    .extern printf, snprintf, malloc, strlen, strcpy, strcat, strcmp",
            "",
            "    .section .data",
            *self.data,
            "",
            "    .section .bss",
            "    .balign 8",
            "buf_f64:  .skip 64                     // texto de un f64 al imprimir",
            "buf_char: .skip 8                      // texto UTF-8 de un char",
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
        self.guardar_variable(sym, tipo_valor)

    def valor_por_defecto(self, tipo):
        if tipo == F64:
            self.emit("fmov d0, xzr", "0.0")
        elif tipo == STRING:
            self.direccion("x0", self.cadena(""))
        else:
            self.emit("mov x0, #0", "0 / false / '\\0'")

    # --- Asignaciones ------------------------------------------------------

    def visit_Assignment(self, nodo):
        sym = nodo.simbolo
        self.comentario(f"{sym.nombre} {nodo.op} ...  (línea {nodo.linea})")

        if nodo.op == '=':
            tipo_valor = self.visitar(nodo.valor)
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
        sym = nodo.simbolo
        self.comentario(f"llamada a {nodo.nombre}()  (línea {nodo.linea})")
        tipos = sym.tipos_params
        for arg, tipo_param in zip(nodo.args, tipos):
            tipo = self.visitar(arg)
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


RUTINAS = {
    "__oxi_f64_str": _rutina_f64_str,
    "__oxi_char_str": _rutina_char_str,
    "__oxi_concat": _rutina_concat,
    "__oxi_repetir": _rutina_repetir,
}
