"""
Une todas las fases del compilador en una sola función.

    código .rs -> lexer/parser -> AST -> semántico -> ARM64 -> gcc -> QEMU

"""
import time

from compiler.errors import ErrorList, LEXICO, SINTACTICO
from compiler.parser import Parser
from compiler.semantic import Semantic
from compiler.codegen.arm64 import Arm64Generator
from compiler.runner import ejecutar_asm


def _ms(inicio):
    return round((time.perf_counter() - inicio) * 1000, 2)


def compilar(codigo, ejecutar=True):
    """Devuelve un diccionario con todo lo que la interfaz necesita:
        errores          ErrorList (léxicos, sintácticos, semánticos)
        tabla            filas del reporte de tabla de símbolos
        ast              raíz del AST (para el reporte Graphviz)
        asm              texto del archivo .s ('' si no se generó)
        salida           lo que imprimió el programa en QEMU
        error_ejecucion  mensaje si falló gcc o QEMU
        tiempos          milisegundos de cada fase
    """
    errores = ErrorList()
    tiempos = {'analisis': 0, 'generacion': 0, 'ensamblado': 0,
               'ejecucion': 0, 'total': 0}
    resultado = {'errores': errores, 'tabla': [], 'ast': None, 'asm': '',
                 'salida': '', 'error_ejecucion': None, 'tiempos': tiempos}
    inicio_total = time.perf_counter()

    try:
        # 1) Análisis léxico, sintáctico y semántico
        inicio = time.perf_counter()
        arbol = Parser(errores).parse(codigo)
        resultado['ast'] = arbol
        if arbol is None:
            return resultado
        tabla = Semantic(errores).analizar(arbol)
        resultado['tabla'] = tabla.reporte()
        tiempos['analisis'] = _ms(inicio)

        # Con errores léxicos o sintácticos el árbol puede estar incompleto:
        # no se genera código. 
        if any(e.tipo in (LEXICO, SINTACTICO) for e in errores):
            return resultado

        # 2) Generación de ARM64
        inicio = time.perf_counter()
        try:
            resultado['asm'] = Arm64Generator().generar(arbol)
        except NotImplementedError as e:
            resultado['error_ejecucion'] = str(e)
            return resultado
        tiempos['generacion'] = _ms(inicio)

        # 3) Ensamblar, enlazar y ejecutar
        if ejecutar:
            r = ejecutar_asm(resultado['asm'])
            resultado['salida'] = r['salida']
            resultado['error_ejecucion'] = r['error']
            tiempos['ensamblado'] = r['tiempo_ensamblado']
            tiempos['ejecucion'] = r['tiempo_ejecucion']
        return resultado
    finally:
        tiempos['total'] = _ms(inicio_total)
