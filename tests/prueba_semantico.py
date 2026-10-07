"""
Prueba del análisis semántico. Ejecutar desde la raíz del proyecto:
    python -m tests.prueba_semantico tests/sem_01_correcto.rs
    python -m tests.prueba_semantico tests/sem_02_errores.rs
    python -m tests.prueba_semantico tests/04_control.rs --tipos   # tipos de cada expresión
"""
import sys

from compiler.errors import ErrorList
from compiler.parser import Parser
from compiler.semantic import Semantic
from compiler import ast_nodes as ast


def tipos_de_expresiones(nodo, salida):
    """Junta (línea, columna, clase, tipo_resultado) de cada expresión."""
    if isinstance(nodo, ast.Node):
        if hasattr(nodo, 'tipo_resultado'):
            salida.append((nodo.linea, nodo.columna, type(nodo).__name__,
                           nodo.tipo_resultado))
        for _, valor in nodo.hijos():
            tipos_de_expresiones(valor, salida)
    elif isinstance(nodo, list):
        for item in nodo:
            tipos_de_expresiones(item, salida)
    return salida


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    ruta = args[0] if args else 'tests/sem_01_correcto.rs'
    with open(ruta, encoding='utf-8') as f:
        codigo = f.read()

    errores = ErrorList()
    arbol = Parser(errores).parse(codigo)
    tabla = Semantic(errores).analizar(arbol)

    print(f"{'No':<4}{'Identificador':<16}{'Categoría':<12}{'Tipo':<8}"
          f"{'Ámbito':<22}{'Lín':<5}{'Col':<5}{'Offset':<11}{'Valor'}")
    for s, fila in zip(tabla.todos, tabla.reporte()):
        off = s.offset if s.offset is not None else f"frame={s.tamano_frame}"
        print(f"{fila['no']:<4}{fila['identificador']:<16}{fila['categoria']:<12}"
              f"{fila['tipo']:<8}{fila['ambito']:<22}{fila['linea']:<5}"
              f"{fila['columna']:<5}{off!s:<11}{fila['valor']}")

    if '--tipos' in sys.argv and arbol is not None:
        print("\n--- Tipo de cada expresión ---")
        for linea, col, clase, tipo in tipos_de_expresiones(arbol, []):
            print(f"  L{linea}:C{col:<4} {clase:<12} {tipo}")

    print("\n--- Errores ---" if errores.hay_errores() else "\nSin errores.")
    for e in errores:
        print(e)


if __name__ == "__main__":
    main()