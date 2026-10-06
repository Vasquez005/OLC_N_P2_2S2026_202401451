"""
Prueba del parser.
"""
import sys

from compiler.errors import ErrorList
from compiler.parser import Parser


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    ruta = args[0] if args else 'tests/01_variables.rs'
    debug = '--debug' in sys.argv

    with open(ruta, encoding='utf-8') as f:
        codigo = f.read()

    errores = ErrorList()
    ast = Parser(errores, debug=debug).parse(codigo)

    if ast is not None:
        print(ast.pretty())

    print("\n--- Errores ---" if errores.hay_errores() else "\nSin errores.")
    for e in errores:
        print(e)


if __name__ == "__main__":
    main()