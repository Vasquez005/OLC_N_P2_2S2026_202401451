"""
Vistas de la API REST del compilador OxigenNative.

La interfaz web manda el código fuente en JSON y recibe todo lo que
necesita mostrar: salida de QEMU, ARM64 generado, errores, tabla de
símbolos, AST (SVG) y tiempos.
"""
import json
import os
import traceback

from django.http import FileResponse, Http404, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from compiler.compilador import compilar
from compiler.reports import (CARPETA_REPORTES, ast_a_dot, dot_a_svg,
                              filas_errores, guardar_reportes)

# Tamaño máximo del código recibido (evita peticiones enormes)
MAX_CODIGO = 200_000

# nombre en la URL -> (archivo en build/reportes, tipo de contenido)
REPORTES = {
    'errores': ('errores.html', 'text/html; charset=utf-8'),
    'tabla': ('tabla_simbolos.html', 'text/html; charset=utf-8'),
    'ast': ('ast.svg', 'image/svg+xml'),
    'ast.dot': ('ast.dot', 'text/plain; charset=utf-8'),
}


@require_GET
def estado(request):
    return JsonResponse({'ok': True, 'mensaje': 'API de OxigenNative lista.'})


@csrf_exempt            # API local sin sesiones ni formularios de Django
@require_POST
def compilar_codigo(request):
    """Recibe  {"codigo": "fn main() { ... }"}
    Devuelve  {
        "ok":               true si compiló y ejecutó sin errores,
        "salida":           texto que imprimió el programa,
        "error_ejecucion":  mensaje de gcc/QEMU o null,
        "asm":              código ARM64 generado,
        "errores":          [{no, tipo, descripcion, linea, columna, fragmento}],
        "tabla":            [{no, identificador, categoria, tipo, ambito, linea, columna, valor}],
        "ast_svg":          imagen del AST en SVG (o null),
        "ast_dot":          texto DOT del AST,
        "tiempos":          {analisis, generacion, ensamblado, ejecucion, total} en ms
    }"""
    # 1) Leer el JSON de la petición
    try:
        datos = json.loads(request.body.decode('utf-8'))
        codigo = datos['codigo']
        if not isinstance(codigo, str):
            raise ValueError
    except (ValueError, KeyError, UnicodeDecodeError):
        return JsonResponse({'ok': False, 'error_interno':
                             'Se esperaba un JSON con el campo "codigo" (texto).'},
                            status=400)
    if len(codigo) > MAX_CODIGO:
        return JsonResponse({'ok': False, 'error_interno':
                             'El código es demasiado grande.'}, status=400)

    # 2) Compilar. Un error inesperado del compilador no debe tumbar el
    #    servidor: se devuelve el mensaje para mostrarlo en la consola.
    try:
        r = compilar(codigo)
    except Exception as e:
        traceback.print_exc()
        return JsonResponse({'ok': False,
                             'error_interno': f'Error interno del compilador: {e}'})

    # 3) Reportes: se guardan en build/reportes (el enunciado pide que se
    #    generen automáticamente) y además se mandan en la respuesta.
    ast_dot, ast_svg = '', None
    if r['ast'] is not None:
        ast_dot = ast_a_dot(r['ast'])
        ast_svg, _ = dot_a_svg(ast_dot)
    try:
        guardar_reportes(r, codigo)
    except OSError:
        pass        # no poder escribir archivos no impide mostrar resultados

    errores = filas_errores(r['errores'], codigo)
    return JsonResponse({
        'ok': not errores and not r['error_ejecucion'],
        'salida': r['salida'],
        'error_ejecucion': r['error_ejecucion'],
        'asm': r['asm'],
        'errores': errores,
        'tabla': r['tabla'],
        'ast_svg': ast_svg,
        'ast_dot': ast_dot,
        'tiempos': r['tiempos'],
    })


@require_GET
def reporte(request, nombre):
    """Sirve el último reporte guardado (para abrirlo en otra pestaña o
    descargarlo). Agregar ?descargar=1 a la URL para descargarlo."""
    if nombre not in REPORTES:
        raise Http404('Reporte no encontrado.')
    archivo, tipo = REPORTES[nombre]
    ruta = os.path.join(CARPETA_REPORTES, archivo)
    if not os.path.exists(ruta):
        raise Http404('Todavía no se ha generado este reporte. Compile primero.')
    return FileResponse(open(ruta, 'rb'), content_type=tipo,
                        as_attachment=request.GET.get('descargar') == '1',
                        filename=archivo)
