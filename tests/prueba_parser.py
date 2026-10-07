"""
Prueba del parser. Ejecutar desde la raíz del proyecto:
    python -m tests.prueba_parser                        # usa tests/01_variables.rs
    python -m tests.prueba_parser tests/04_control.rs
    python -m tests.prueba_parser tests/04_control.rs --arbol   # árbol completo
    python -m tests.prueba_parser tests/04_control.rs --debug   # conflictos
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
        if n.tipo in ('String', 'char'):
            return repr(n.valor)
        if n.tipo == 'bool':
            return str(n.valor).lower()
        return str(n.valor)
    if isinstance(n, ast.Identifier):
        return n.nombre
    return type(n).__name__


def etiqueta(e):
    return f"'{e}: " if e else ''


def mostrar(ins, nivel=1):
    """Imprime una instrucción (y sus bloques internos) con sangría."""
    s = '  ' * nivel
    pos = f"L{ins.linea:<3}"

    if isinstance(ins, ast.VarDecl):
        mut = 'mut ' if ins.mutable else ''
        tipo = f": {ins.tipo}" if ins.tipo else ''
        print(f"{pos}{s}let {mut}{ins.nombre}{tipo} = {infijo(ins.valor)}")
    elif isinstance(ins, ast.Assignment):
        print(f"{pos}{s}{infijo(ins.objetivo)} {ins.op} {infijo(ins.valor)}")
    elif isinstance(ins, ast.Print):
        args = ', '.join(infijo(a) for a in ins.args)
        print(f"{pos}{s}println partes={ins.partes} args=[{args}]")
    elif isinstance(ins, ast.If):
        print(f"{pos}{s}if {infijo(ins.condicion)}")
        mostrar_bloque(ins.entonces, nivel + 1)
        if isinstance(ins.sino, ast.If):
            print(f"{'':4}{s}else ->")
            mostrar(ins.sino, nivel + 1)
        elif ins.sino is not None:
            print(f"{'':4}{s}else")
            mostrar_bloque(ins.sino, nivel + 1)
    elif isinstance(ins, ast.While):
        print(f"{pos}{s}{etiqueta(ins.etiqueta)}while {infijo(ins.condicion)}")
        mostrar_bloque(ins.cuerpo, nivel + 1)
    elif isinstance(ins, ast.Loop):
        print(f"{pos}{s}{etiqueta(ins.etiqueta)}loop")
        mostrar_bloque(ins.cuerpo, nivel + 1)
    elif isinstance(ins, (ast.Break, ast.Continue)):
        nombre = 'break' if isinstance(ins, ast.Break) else 'continue'
        et = f" '{ins.etiqueta}" if ins.etiqueta else ''
        print(f"{pos}{s}{nombre}{et}")
    else:
        print(f"{pos}{s}{type(ins).__name__}")


def mostrar_bloque(bloque, nivel):
    if not bloque.instrucciones:
        print(f"{'':4}{'  ' * nivel}(bloque vacío)")
    for ins in bloque.instrucciones:
        mostrar(ins, nivel)


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
                mostrar_bloque(fn.cuerpo, 1)

    print("\n--- Errores ---" if errores.hay_errores() else "\nSin errores.")
    for e in errores:
        print(e)


if __name__ == "__main__":
    main()