"""
Une todas las fases del compilador en una sola función.

    código .rs -> lexer/parser -> AST -> semántico -> ARM64 -> gcc -> QEMU

"""
from compiler.errors import ErrorList, LEXICO, SINTACTICO
from compiler.parser import Parser
from compiler.semantic import Semantic
from compiler.codegen.arm64 import Arm64Generator
from compiler.runner import ejecutar_asm


def compilar(codigo, ejecutar=True):
    """Devuelve un diccionario con todo lo que la interfaz necesita:
        errores   lista de CompilerError (léxicos, sintácticos, semánticos)
        tabla     filas del reporte de tabla de símbolos
        ast       raíz del AST (para el reporte Graphviz)
        asm       texto del archivo .s ('' si no se generó)
        salida    lo que imprimió el programa en QEMU
        error_ejecucion  mensaje si falló gcc o QEMU
    """
    errores = ErrorList()
    resultado = {'errores': errores, 'tabla': [], 'ast': None,
                 'asm': '', 'salida': '', 'error_ejecucion': None}

    # 1) Análisis léxico y sintáctico
    arbol = Parser(errores).parse(codigo)
    resultado['ast'] = arbol
    if arbol is None:
        return resultado

    # 2) Análisis semántico
    tabla = Semantic(errores).analizar(arbol)
    resultado['tabla'] = tabla.reporte()

    if any(e.tipo in (LEXICO, SINTACTICO) for e in errores):
        return resultado

    # 3) Generación de ARM64
    try:
        resultado['asm'] = Arm64Generator().generar(arbol)
    except NotImplementedError as e:
        resultado['error_ejecucion'] = str(e)
        return resultado

    # 4) Ensamblar, enlazar y ejecutar
    if ejecutar:
        r = ejecutar_asm(resultado['asm'])
        resultado['salida'] = r['salida']
        resultado['error_ejecucion'] = r['error']
    return resultado