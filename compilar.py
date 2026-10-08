"""
Compila y ejecuta un archivo desde la terminal (sin la interfaz web).

El ensamblador generado queda en build/programa.s
"""
import sys

from compiler.compilador import compilar


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    if not args:
        print(__doc__)
        return
    with open(args[0], encoding='utf-8') as f:
        codigo = f.read()

    r = compilar(codigo)

    if '--asm' in sys.argv and r['asm']:
        print("========== ARM64 ==========")
        print(r['asm'])

    if r['errores'].hay_errores():
        print("========== Errores ==========")
        for e in r['errores']:
            print(e)

    print("========== Salida ==========")
    print(r['salida'], end='')
    if r['error_ejecucion']:
        print(f"\n[Error de ejecución] {r['error_ejecucion']}")


if __name__ == "__main__":
    main()
