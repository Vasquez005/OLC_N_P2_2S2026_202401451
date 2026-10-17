"""
Ensambla, enlaza y ejecuta el código ARM64 generado.

    archivo .s  --gcc -static-->  ejecutable ELF  --qemu-aarch64-->  salida

"""
import os
import platform
import subprocess

CARPETA_BUILD = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'build')
TIEMPO_LIMITE = 5   # segundos; evita que un ciclo infinito congele el servidor


def compilador_c():
    if os.environ.get('OXIGEN_GCC'):
        return os.environ['OXIGEN_GCC']
    if platform.machine() in ('aarch64', 'arm64'):
        return 'gcc'
    return 'aarch64-linux-gnu-gcc'


def ejecutar_asm(codigo_asm, nombre='programa'):
    """Devuelve un diccionario:
        ok      True si se ensambló y ejecutó sin problemas
        salida  lo que imprimió el programa
        error   mensaje si falló el ensamblado, el enlace o la ejecución
    """
    os.makedirs(CARPETA_BUILD, exist_ok=True)
    ruta_s = os.path.join(CARPETA_BUILD, f'{nombre}.s')
    ruta_exe = os.path.join(CARPETA_BUILD, nombre)

    with open(ruta_s, 'w', encoding='utf-8') as f:
        f.write(codigo_asm)

    # 1) Ensamblar y enlazar
    gcc = [compilador_c(), '-static', ruta_s, '-o', ruta_exe]
    try:
        r = subprocess.run(gcc, capture_output=True, text=True, timeout=30)
    except FileNotFoundError:
        return {'ok': False, 'salida': '',
                'error': f"No se encontró '{gcc[0]}'. ¿Está instalado?"}
    if r.returncode != 0:
        return {'ok': False, 'salida': '',
                'error': f"Error al ensamblar/enlazar:\n{r.stderr}"}

    # 2) Ejecutar con QEMU
    try:
        r = subprocess.run(['qemu-aarch64', ruta_exe], capture_output=True,
                           text=True, timeout=TIEMPO_LIMITE)
    except subprocess.TimeoutExpired as e:
        parcial = e.stdout.decode('utf-8', 'replace') if e.stdout else ''
        return {'ok': False, 'salida': parcial,
                'error': f"La ejecución superó {TIEMPO_LIMITE} s (¿ciclo infinito?)."}
    except FileNotFoundError:
        return {'ok': False, 'salida': '',
                'error': "No se encontró 'qemu-aarch64'. Instale qemu-user."}

    error = None
    if r.returncode != 0:
        error = f"El programa terminó con código {r.returncode}.\n{r.stderr}".strip()
    return {'ok': r.returncode == 0, 'salida': r.stdout, 'error': error}
