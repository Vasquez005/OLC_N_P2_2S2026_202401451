"""
Corre todos los programas de prueba (tests/*.rs) de punta a punta y
muestra un resumen: errores por tipo y si el programa se ejecutó.

    python tests/correr_todo.py
"""
import glob
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

from compiler.compilador import compilar          # noqa: E402


def main():
    archivos = sorted(glob.glob(os.path.join(RAIZ, 'tests', '*.rs')))
    print(f"{'Archivo':<28}{'Léx':>5}{'Sint':>6}{'Sem':>5}  {'Ejecución':<12}Líneas de salida")
    print('-' * 75)
    for ruta in archivos:
        with open(ruta, encoding='utf-8') as f:
            r = compilar(f.read())
        cuenta = {'Léxico': 0, 'Sintáctico': 0, 'Semántico': 0}
        for e in r['errores']:
            cuenta[e.tipo] += 1
        if not r['asm']:
            estado = 'no generada'
        elif r['error_ejecucion']:
            estado = 'error'
        else:
            estado = 'ok'
        print(f"{os.path.basename(ruta):<28}{cuenta['Léxico']:>5}{cuenta['Sintáctico']:>6}"
              f"{cuenta['Semántico']:>5}  {estado:<12}{len(r['salida'].splitlines())}")


if __name__ == '__main__':
    main()
