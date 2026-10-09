"""
Generador de código ARM64

Recorre el AST YA ANOTADO por el semántico y produce el texto de un
archivo ensamblador (.s) para el ensamblador GNU, que se enlaza con
la biblioteca de C (`gcc -static`) para poder usar printf

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

# Operador compuesto -> operador aritmético
COMPUESTOS = {'+=': '+', '-=': '-', '*=': '*', '/=': '/', '%=': '%'}

# Especificador de printf para cada tipo (ver visit_Print)
ESPECIFICADOR = {
    I32: '%d',
    F64: '%.15g',   # 12.5 -> 12.5, 7.0 -> 7, 0.1+0.2 -> 0.3
    STRING: '%s',
    CHAR: '%c',
    BOOL: '%s',     # se pasa el texto "true" o "false"
}


class Arm64Generator:

    def __init__(self):
        self.text = []          # instrucciones de la sección .text
        self.data = []          # constantes de la sección .data
        self.cadenas = {}       # texto -> etiqueta (para no repetir cadenas)
        self.decimales = {}     # valor f64 -> etiqueta
        self.contador = 0       # para crear etiquetas únicas
        self.ciclos = []           # pila de etiquetas de ciclos activos (break/continue)

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
    # calcula `b`. Se guarda en la pila. Se mueven 16 bytes
 
    def push(self, reg="x0"):
        self.emit(f"str {reg}, [sp, #-16]!", f"push {reg}")
 
    def pop(self, reg="x1"):
        self.emit(f"ldr {reg}, [sp], #16", f"pop {reg}")

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

        salida = [
            "// Generado por OxigenNative",
            "    .global main",
            "    .extern printf",
            "",
            "    .section .data",
            *self.data,
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

        self.visit_Block(nodo.cuerpo)

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
        self.revisar_soportado(sym.tipo, nodo.valor.tipo_resultado, nodo)
        self.cargar_variable(sym)          # x0 = x
        self.push()
        self.visitar(nodo.valor)           # x0 = v
        self.pop("x1")                     # x1 = x
        self.operar_enteros(op)            # x0 = x1 op x0
        self.guardar_variable(sym, sym.tipo)

    # --- Control de flujo --------------------------------------------------

    def condicion_valida(self, nodo, sentencia):
        """Si la condicion tuvo error semantic (no es bool), la sentencia 
        completa se salta: no hay forma segura de decidir que rama recorrer"""
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
        elif tipo in (I32, CHAR, STRING):
            self.emit("mov x1, x0", "x1 = valor a imprimir")
        # f64: el valor ya está en d0, que es donde printf lo espera
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
        elif tipo == I32:
            self.emit("neg w0, w0", "-x")
            self.emit("sxtw x0, w0", "extender el signo a 64 bits")
        else:
            raise NotImplementedError(
                f"El negativo de un {tipo} se agrega en G4 (línea {nodo.linea})")
        return nodo.tipo_resultado

    # --- Operaciones binarias ---------------------------------------------
 
    def visit_BinaryOp(self, nodo):
        op = nodo.op
 
        # && y || no siempre evalúan los dos lados (cortocircuito)
        if op in ('&&', '||'):
            return self.logica_cortocircuito(nodo)
 
        self.revisar_soportado(nodo.izq.tipo_resultado,
                               nodo.der.tipo_resultado, nodo)
 
        # Patrón general:  x1 = izquierda,  x0 = derecha
        self.visitar(nodo.izq)
        self.push()
        self.visitar(nodo.der)
        self.pop("x1")
 
        if op in CONDICION:
            self.emit("cmp x1, x0")
            self.emit(f"cset x0, {CONDICION[op]}", f"x0 = (izq {op} der) ? 1 : 0")
        else:
            self.operar_enteros(op)
        return nodo.tipo_resultado
 
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
 
    def revisar_soportado(self, izq, der, nodo):
        if F64 in (izq, der) or STRING in (izq, der):
            raise NotImplementedError(
                f"Las operaciones con f64 y String se agregan en G4 "
                f"(línea {nodo.linea})")
 
 
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
 