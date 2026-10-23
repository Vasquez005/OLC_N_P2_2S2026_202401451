"""
Reportes del compilador OxigenNative

    Reporte de errores          -> HTML (tabla)
    Reporte de tabla de símbolos -> HTML (tabla)
    Reporte del AST             -> archivo DOT + imagen SVG (Graphviz)

Cada reporte se puede pedir por separado (la API web los manda en JSON)
o guardarse todos juntos en una carpeta con `guardar_reportes`.
"""
import html
import os
import subprocess

from compiler import ast_nodes as ast

CARPETA_REPORTES = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'build', 'reportes')

# Atributos que agrega el semántico y que NO forman parte del árbol
# (se muestran de otra forma o no aportan al reporte).
ATRIBUTOS_OCULTOS = {'simbolo', 'tipo_resultado', 'usar_defecto', 'omitir', 'partes',
                     'tipo_funcion', 'indice_constante', 'tipo_objeto', 'desde', 'hasta'}


# ======================================================================
# Errores
# ======================================================================

def fragmento(codigo, linea):
    """Texto de la línea donde ocurrió el error (lo pide la sección 3.5.1)."""
    lineas = codigo.split('\n')
    if 1 <= linea <= len(lineas):
        return lineas[linea - 1].strip()
    return ''


def filas_errores(errores, codigo):
    """Lista de diccionarios para la tabla de errores (y para el JSON)."""
    filas = []
    for i, e in enumerate(errores, start=1):
        fila = e.to_dict()
        fila['no'] = i
        fila['fragmento'] = fragmento(codigo, e.linea)
        filas.append(fila)
    return filas


def html_errores(errores, codigo):
    filas = filas_errores(errores, codigo)
    columnas = [('no', 'No.'), ('tipo', 'Tipo'), ('descripcion', 'Descripción'),
                ('linea', 'Línea'), ('columna', 'Columna'), ('fragmento', 'Fragmento')]
    cuerpo = _tabla_html(filas, columnas, vacio="No se encontraron errores.")
    return _pagina_html("Reporte de errores", cuerpo)


# ======================================================================
# Tabla de símbolos
# ======================================================================

def html_tabla_simbolos(filas):
    """`filas` es lo que devuelve SymbolTable.reporte()."""
    columnas = [('no', 'No.'), ('identificador', 'Identificador'),
                ('categoria', 'Categoría'), ('tipo', 'Tipo'), ('ambito', 'Ámbito'),
                ('linea', 'Línea'), ('columna', 'Columna'), ('valor', 'Valor')]
    cuerpo = _tabla_html(filas, columnas, vacio="No hay símbolos registrados.")
    return _pagina_html("Reporte de tabla de símbolos", cuerpo)


# ======================================================================
# AST con Graphviz
# ======================================================================

def ast_a_dot(raiz):
    """Convierte el AST a texto DOT.

    Recorre el árbol de forma genérica con Node.hijos(), así que los
    nodos que se agreguen después (funciones, arreglos, match...) salen
    en el reporte sin tocar este archivo.
      * Atributos simples (nombre, op, tipo...) -> dentro de la caja.
      * Atributos que son nodos -> flecha con el nombre del atributo.
      * Listas de nodos -> una flecha por elemento: instrucciones[0], [1]...
    """
    lineas = [
        'digraph AST {',
        '    graph [fontname="Helvetica", ordering=out, nodesep=0.3, ranksep=0.45];',
        '    node  [shape=box, style="rounded,filled", fontname="Helvetica", '
        'fontsize=11, fillcolor="#eef2ff", color="#6366f1"];',
        '    edge  [fontname="Helvetica", fontsize=9, color="#64748b", fontcolor="#64748b"];',
    ]
    contador = [0]

    def visitar(nodo):
        contador[0] += 1
        nombre = f"n{contador[0]}"
        lineas.append(f'    {nombre} [label="{_escapar_dot(_etiqueta(nodo))}"'
                      f'{_estilo(nodo)}];')

        for atributo, valor in nodo.hijos():
            if atributo in ATRIBUTOS_OCULTOS:
                continue
            if isinstance(valor, ast.Node):
                hijo = visitar(valor)
                lineas.append(f'    {nombre} -> {hijo} [label="{atributo}"];')
            elif isinstance(valor, list):
                for i, item in enumerate(valor):
                    if isinstance(item, ast.Node):
                        hijo = visitar(item)
                        etiqueta = f"{atributo}[{i}]" if len(valor) > 1 else atributo
                        lineas.append(f'    {nombre} -> {hijo} [label="{etiqueta}"];')
        return nombre

    if raiz is not None:
        visitar(raiz)
    lineas.append('}')
    return '\n'.join(lineas)


def _etiqueta(nodo):
    """Texto de la caja: nombre de la clase + atributos simples."""
    partes = [type(nodo).__name__]
    for atributo, valor in nodo.hijos():
        if atributo in ATRIBUTOS_OCULTOS:
            continue
        if isinstance(valor, (ast.Node, list)):
            continue
        if valor is None or (valor is False and atributo != 'valor'):
            continue                    # no mostrar "mutable: false", etc.
        if isinstance(valor, str) and atributo in ('valor', 'formato'):
            texto = valor.encode('unicode_escape').decode('ascii', 'replace')
            if len(texto) > 30:
                texto = texto[:27] + '...'
            valor = f'"{texto}"' if getattr(nodo, 'tipo', '') != 'char' else f"'{texto}'"
        elif isinstance(valor, bool):
            valor = 'true' if valor else 'false'
        partes.append(f"{atributo}: {valor}")
    tipo = getattr(nodo, 'tipo_resultado', None)
    if tipo is not None and not isinstance(nodo, ast.Literal):
        partes.append(f"⟶ {tipo}")      # tipo calculado por el semántico
    return '\n'.join(partes)


def _estilo(nodo):
    """Color según la categoría del nodo (solo para que se lea mejor)."""
    if getattr(nodo, 'omitir', False) or getattr(nodo, 'tipo_resultado', None) == 'None':
        return ', fillcolor="#fee2e2", color="#dc2626"'      # con error semántico
    if isinstance(nodo, (ast.Program, ast.Function, ast.Block)):
        return ', fillcolor="#e0e7ff", color="#4338ca"'
    if isinstance(nodo, (ast.Literal, ast.Identifier, ast.BinaryOp, ast.UnaryOp)):
        return ', fillcolor="#ecfdf5", color="#059669"'      # expresiones
    return ''                                                # instrucciones


def _escapar_dot(texto):
    return texto.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')


def dot_a_svg(texto_dot):
    """Ejecuta Graphviz (`dot -Tsvg`). Devuelve (svg, error)."""
    try:
        r = subprocess.run(['dot', '-Tsvg'], input=texto_dot, capture_output=True,
                           text=True, timeout=30)
    except FileNotFoundError:
        return None, "No se encontró Graphviz ('dot'). Instale el paquete graphviz."
    except subprocess.TimeoutExpired:
        return None, "Graphviz tardó demasiado en dibujar el AST."
    if r.returncode != 0:
        return None, f"Error de Graphviz: {r.stderr.strip()}"
    return r.stdout, None


# ======================================================================
# Guardar todos los reportes en archivos
# ======================================================================

def guardar_reportes(resultado, codigo, carpeta=CARPETA_REPORTES):
    """Escribe errores.html, tabla_simbolos.html, ast.dot y ast.svg.
    `resultado` es el diccionario que devuelve compilador.compilar().
    Devuelve la lista de rutas creadas."""
    os.makedirs(carpeta, exist_ok=True)
    archivos = {
        'errores.html': html_errores(resultado['errores'], codigo),
        'tabla_simbolos.html': html_tabla_simbolos(resultado['tabla']),
    }
    if resultado['ast'] is not None:
        dot = ast_a_dot(resultado['ast'])
        archivos['ast.dot'] = dot
        svg, error = dot_a_svg(dot)
        if svg:
            archivos['ast.svg'] = svg
        else:
            print(f"[Aviso] {error}")

    rutas = []
    for nombre, contenido in archivos.items():
        ruta = os.path.join(carpeta, nombre)
        with open(ruta, 'w', encoding='utf-8') as f:
            f.write(contenido)
        rutas.append(ruta)
    return rutas


# ======================================================================
# Utilidades HTML
# ======================================================================

def _tabla_html(filas, columnas, vacio):
    if not filas:
        return f'<p class="vacio">{html.escape(vacio)}</p>'
    encabezado = ''.join(f'<th>{html.escape(t)}</th>' for _, t in columnas)
    cuerpo = []
    for fila in filas:
        celdas = ''.join(f'<td>{html.escape(str(fila.get(c, "")))}</td>'
                         for c, _ in columnas)
        cuerpo.append(f'<tr>{celdas}</tr>')
    return (f'<table><thead><tr>{encabezado}</tr></thead>'
            f'<tbody>{"".join(cuerpo)}</tbody></table>')


def _pagina_html(titulo, cuerpo):
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<title>{html.escape(titulo)}</title>
<style>
  body  {{ font-family: Helvetica, Arial, sans-serif; margin: 2rem; color: #1e293b; }}
  h1    {{ font-size: 1.4rem; }}
  table {{ border-collapse: collapse; width: 100%; font-size: 0.9rem; }}
  th, td {{ border: 1px solid #cbd5e1; padding: 6px 10px; text-align: left; }}
  th    {{ background: #4338ca; color: white; }}
  tr:nth-child(even) td {{ background: #f1f5f9; }}
  .vacio {{ color: #64748b; font-style: italic; }}
</style>
</head>
<body>
<h1>{html.escape(titulo)}</h1>
{cuerpo}
</body>
</html>
"""