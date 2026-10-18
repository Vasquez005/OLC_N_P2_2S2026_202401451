"""
Ensambla, enlaza y ejecuta el código ARM64 generado.

    archivo .s  --gcc -static-->  ejecutable ELF  --qemu-aarch64-->  salida

"""
import os
import platform
import shutil
import subprocess
import tempfile
import time

CARPETA_BUILD = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'build')
TIEMPO_LIMITE = 5   # segundos; evita que un ciclo infinito congele el servidor


def compilador_c():
    if os.environ.get('OXIGEN_GCC'):
        return os.environ['OXIGEN_GCC']
    if platform.machine() in ('aarch64', 'arm64'):
        return 'gcc'
    return 'aarch64-linux-gnu-gcc'


def _ms(inicio):
    return round((time.perf_counter() - inicio) * 1000, 2)


def ejecutar_asm(codigo_asm):
    """Devuelve un diccionario:
        ok                 True si se ensambló y ejecutó sin problemas
        salida             lo que imprimió el programa
        error              mensaje si falló el ensamblado, el enlace o la ejecución
        tiempo_ensamblado  milisegundos de gcc (ensamblar + enlazar)
        tiempo_ejecucion   milisegundos de QEMU
    """
    resultado = {'ok': False, 'salida': '', 'error': None,
                 'tiempo_ensamblado': 0, 'tiempo_ejecucion': 0}

    # Copia del último .s para poder revisarlo (no afecta la ejecución)
    os.makedirs(CARPETA_BUILD, exist_ok=True)
    with open(os.path.join(CARPETA_BUILD, 'programa.s'), 'w', encoding='utf-8') as f:
        f.write(codigo_asm)

    carpeta = tempfile.mkdtemp(prefix='oxigen_')
    try:
        ruta_s = os.path.join(carpeta, 'programa.s')
        ruta_exe = os.path.join(carpeta, 'programa')
        with open(ruta_s, 'w', encoding='utf-8') as f:
            f.write(codigo_asm)

        # 1) Ensamblar y enlazar
        gcc = [compilador_c(), '-static', ruta_s, '-o', ruta_exe]
        inicio = time.perf_counter()
        try:
            r = subprocess.run(gcc, capture_output=True, text=True, timeout=30)
        except FileNotFoundError:
            resultado['error'] = f"No se encontró '{gcc[0]}'. ¿Está instalado?"
            return resultado
        resultado['tiempo_ensamblado'] = _ms(inicio)
        if r.returncode != 0:
            resultado['error'] = f"Error al ensamblar/enlazar:\n{r.stderr}"
            return resultado

        # 2) Ejecutar con QEMU
        inicio = time.perf_counter()
        try:
            r = subprocess.run(['qemu-aarch64', ruta_exe], capture_output=True,
                               text=True, timeout=TIEMPO_LIMITE)
        except subprocess.TimeoutExpired as e:
            resultado['tiempo_ejecucion'] = _ms(inicio)
            salida = e.stdout or b''
            resultado['salida'] = (salida.decode('utf-8', 'replace')
                                   if isinstance(salida, bytes) else salida)
            resultado['error'] = (f"La ejecución superó {TIEMPO_LIMITE} s "
                                  f"(¿ciclo infinito?).")
            return resultado
        except FileNotFoundError:
            resultado['error'] = "No se encontró 'qemu-aarch64'. Instale qemu-user."
            return resultado
        resultado['tiempo_ejecucion'] = _ms(inicio)

        resultado['salida'] = r.stdout
        resultado['ok'] = r.returncode == 0
        if r.returncode != 0:
            resultado['error'] = (f"El programa terminó con código {r.returncode}.\n"
                                  f"{r.stderr}").strip()
        return resultado
    finally:
        shutil.rmtree(carpeta, ignore_errors=True)
