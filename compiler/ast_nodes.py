"""
Nodos del Árbol de Sintaxis Abstracta (AST) de OxigenNative.

Cada clase representa una construcción del lenguaje. Todas heredan de
Node, que guarda la línea y columna para reportar errores semánticos.

Paso 1: programa, funciones (sin parámetros), bloques, declaraciones
        de variables y literales.
Paso 2: operaciones binarias y unarias.
Paso 3: asignaciones y println!.
Paso 4: if / else if / else, while, loop, break y continue (con etiquetas).
Paso 5: funciones con parámetros y tipo de retorno, return, llamadas y
        expresiones usadas como instrucción (por ejemplo `saludar(x);`).
"""


class Node:
    def __init__(self, linea=0, columna=0):
        self.linea = linea
        self.columna = columna

    def hijos(self):
        """Devuelve (nombre_atributo, valor) de todo excepto la posición.
        Lo usarán el impresor de pruebas y el reporte Graphviz."""
        return [(k, v) for k, v in vars(self).items()
                if k not in ('linea', 'columna') and not k.startswith('_')]

    def pretty(self, nivel=0):
        """Representación en texto del árbol, para depurar."""
        sangria = '  ' * nivel
        lineas = [f"{sangria}{type(self).__name__}  (L{self.linea}:C{self.columna})"]
        for nombre, valor in self.hijos():
            if isinstance(valor, Node):
                lineas.append(f"{sangria}  {nombre}:")
                lineas.append(valor.pretty(nivel + 2))
            elif isinstance(valor, list):
                lineas.append(f"{sangria}  {nombre}: [{len(valor)}]")
                for item in valor:
                    if isinstance(item, Node):
                        lineas.append(item.pretty(nivel + 2))
                    else:
                        lineas.append(f"{sangria}    {item!r}")
            else:
                lineas.append(f"{sangria}  {nombre} = {valor!r}")
        return '\n'.join(lineas)


# ----------------------------------------------------------------------
# Estructura del programa
# ----------------------------------------------------------------------

class Program(Node):
    def __init__(self, funciones):
        super().__init__(1, 1)
        self.funciones = funciones      # list[Function]


class Function(Node):
    def __init__(self, nombre, params, tipo_retorno, cuerpo, linea, columna):
        super().__init__(linea, columna)
        self.nombre = nombre
        self.params = params            # list[Param]
        self.tipo_retorno = tipo_retorno  # str o None si no retorna
        self.cuerpo = cuerpo            # Block


class Param(Node):
    """Parámetro de una función:  [mut] nombre: tipo"""

    def __init__(self, nombre, tipo, mutable, linea, columna):
        super().__init__(linea, columna)
        self.nombre = nombre
        self.tipo = tipo
        self.mutable = mutable


class Block(Node):
    def __init__(self, instrucciones, linea, columna):
        super().__init__(linea, columna)
        self.instrucciones = instrucciones   # list[Node]


# ----------------------------------------------------------------------
# Instrucciones
# ----------------------------------------------------------------------

class VarDecl(Node):
    """let [mut] id [: tipo] [= expresion];"""

    def __init__(self, nombre, mutable, tipo, valor, linea, columna):
        super().__init__(linea, columna)
        self.nombre = nombre
        self.mutable = mutable      # bool
        self.tipo = tipo            # str ('i32', 'f64', ...) o None (inferido)
        self.valor = valor          # Node o None (sin inicializar)


class Assignment(Node):
    """objetivo <op> valor;   con op en '=', '+=', '-=', '*=', '/=', '%='.

    `objetivo` es un nodo (no solo un nombre) para que en el paso 6
    también pueda ser un acceso a arreglo: matriz[i][j] = 5;
    """

    def __init__(self, objetivo, op, valor, linea, columna):
        super().__init__(linea, columna)
        self.objetivo = objetivo    # Identifier (o acceso a arreglo, paso 6)
        self.op = op
        self.valor = valor


class Print(Node):
    """println!("texto {} más texto {}", a, b);

    `partes` es el formato ya separado: los textos son str y cada
    marcador {} o {:?} se guarda como None. Por ejemplo:
        "x = {}, y = {}"  ->  ['x = ', None, ', y = ', None]
    El generador de código recorre `partes` e imprime un argumento
    en cada None. Así no tiene que volver a analizar el texto.
    """

    def __init__(self, formato, partes, args, linea, columna):
        super().__init__(linea, columna)
        self.formato = formato      # texto original (para reportes)
        self.partes = partes        # list[str | None]
        self.args = args            # list[Node]

    def num_marcadores(self):
        return sum(1 for p in self.partes if p is None)


# ----------------------------------------------------------------------
# Control de flujo (paso 4)
# ----------------------------------------------------------------------

class If(Node):
    """if cond { ... } [else { ... } | else if ...]

    `else if` se modela como un If dentro de la rama `sino`, tal como
    pide el enunciado ("continuación del else"):
        if a {..} else if b {..} else {..}
        ->  If(a, sino=If(b, sino=Block))
    """

    def __init__(self, condicion, entonces, sino, linea, columna):
        super().__init__(linea, columna)
        self.condicion = condicion
        self.entonces = entonces    # Block
        self.sino = sino            # Block, If o None


class While(Node):
    def __init__(self, condicion, cuerpo, etiqueta, linea, columna):
        super().__init__(linea, columna)
        self.condicion = condicion
        self.cuerpo = cuerpo        # Block
        self.etiqueta = etiqueta    # str sin apóstrofo ('outer') o None


class Loop(Node):
    def __init__(self, cuerpo, etiqueta, linea, columna):
        super().__init__(linea, columna)
        self.cuerpo = cuerpo        # Block
        self.etiqueta = etiqueta    # str o None


class Break(Node):
    def __init__(self, etiqueta, linea, columna):
        super().__init__(linea, columna)
        self.etiqueta = etiqueta    # None = el ciclo más interno


class Continue(Node):
    def __init__(self, etiqueta, linea, columna):
        super().__init__(linea, columna)
        self.etiqueta = etiqueta


# ----------------------------------------------------------------------
# Funciones (paso 5)
# ----------------------------------------------------------------------

class Return(Node):
    """return [expresion];"""

    def __init__(self, valor, linea, columna):
        super().__init__(linea, columna)
        self.valor = valor          # Node o None


class ExprStmt(Node):
    """Expresión usada como instrucción; su valor se descarta.
    Ejemplos:  saludar(10);     flag && saludar(10);"""

    def __init__(self, expr, linea, columna):
        super().__init__(linea, columna)
        self.expr = expr


# ----------------------------------------------------------------------
# Expresiones
# ----------------------------------------------------------------------

class Literal(Node):
    """Valor constante: 10, 3.14, true, 'a', "hola", String::from("hola")."""

    def __init__(self, valor, tipo, linea, columna):
        super().__init__(linea, columna)
        self.valor = valor
        self.tipo = tipo            # 'i32', 'f64', 'bool', 'char', 'String'


class Identifier(Node):
    """Uso de una variable dentro de una expresión."""

    def __init__(self, nombre, linea, columna):
        super().__init__(linea, columna)
        self.nombre = nombre


class BinaryOp(Node):
    """izq <op> der   (aritméticos, relacionales y lógicos)."""

    def __init__(self, op, izq, der, linea, columna):
        super().__init__(linea, columna)
        self.op = op                # '+', '-', '*', '/', '%', '==', '&&', ...
        self.izq = izq
        self.der = der


class UnaryOp(Node):
    """<op> expr   (negación aritmética '-' y lógica '!')."""

    def __init__(self, op, expr, linea, columna):
        super().__init__(linea, columna)
        self.op = op                # '-' o '!'
        self.expr = expr


class Call(Node):
    """Llamada a función:  nombre(arg1, arg2, ...)"""

    def __init__(self, nombre, args, linea, columna):
        super().__init__(linea, columna)
        self.nombre = nombre
        self.args = args            # list[Node]
