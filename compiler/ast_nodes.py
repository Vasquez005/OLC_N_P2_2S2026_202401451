"""
Nodos del Árbol de Sintaxis Abstracta (AST)
Cada clase representa una construcción del lenguaje. Todas heredan de
Node, que guarda la línea y columna para reportar errores semánticos.

"""

class Node:
    def __init__(self, linea = 0, columa = 0):
        self.linea = linea
        self.columna = columa

    def hijos(self):
        """
        Devuelve (nombre_atributo, valor) de todo excepto la posición.
        Lo usarán el impresor de pruebas y el reporte Graphviz. """
        return [(k, v) for k, v in vars(self).items()
                if k not in ('linea', 'columna')]

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
        self.params = params            # list[Param] PENDIENTE
        self.tipo_retorno = tipo_retorno  # str o None si no retorna
        self.cuerpo = cuerpo            # Block

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
 
    `objetivo` es un nodo (no solo un nombre) para que
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