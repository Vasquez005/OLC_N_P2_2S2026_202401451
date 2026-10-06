"""
Prueba del parser.
"""
import sys

from compiler.errors import ErrorList
from compiler.parser import Parser
from compiler import ast_nodes as ast


def infijo(n):
    """Expresión con paréntesis explícitos para ver la precedencia."""
    if n is None:
        return '(sin valor)'
    if isinstance(n, ast.BinaryOp):
        return f"({infijo(n.izq)} {n.op} {infijo(n.der)})"
    if isinstance(n, ast.UnaryOp):
        return f"({n.op}{infijo(n.expr)})"
    if isinstance(n, ast.Literal):
        return repr(n.valor) if n.tipo in ('String', 'char') else str(n.valor).lower() \
            if n.tipo == 'bool' else str(n.valor)
    if isinstance(n, ast.Identifier):
        return n.nombre
    return type(n).__name__


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    ruta = args[0] if args else 'tests/01_variables.rs'

    with open(ruta, encoding='utf-8') as f:
        codigo = f.read()

    errores = ErrorList()
    arbol = Parser(errores, debug='--debug' in sys.argv).parse(codigo)

    if arbol is not None:
        if '--arbol' in sys.argv:
            print(arbol.pretty())
        else:
            for fn in arbol.funciones:
                print(f"fn {fn.nombre}:")
                for ins in fn.cuerpo.instrucciones:
                    if isinstance(ins, ast.VarDecl):
                        mut = 'mut ' if ins.mutable else ''
                        tipo = f": {ins.tipo}" if ins.tipo else ''
                        print(f"  L{ins.linea:<3} let {mut}{ins.nombre}{tipo} = {infijo(ins.valor)}")

    print("\n--- Errores ---" if errores.hay_errores() else "\nSin errores.")
    for e in errores:
        print(e)


if __name__ == "__main__":
    main()