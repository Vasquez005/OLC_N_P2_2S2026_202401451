"""
Genera los diagramas de la documentación con Graphviz (archivos .dot y .png
en docs/diagramas/). Los diagramas de clases se construyen leyendo las
clases REALES del compilador, así coinciden siempre con el código.

    python docs/generar_diagramas.py
"""
import html
import inspect
import os
import subprocess
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

from compiler import ast_nodes as ast                       # noqa: E402
from compiler.lexer import Lexer                           # noqa: E402
from compiler.parser import Parser                         # noqa: E402
from compiler.semantic import Semantic                     # noqa: E402
from compiler.symbol_table import SymbolTable, Scope, Symbol  # noqa: E402
from compiler.errors import ErrorList, CompilerError       # noqa: E402
from compiler.codegen.arm64 import Arm64Generator          # noqa: E402

SALIDA = os.path.join(RAIZ, 'docs', 'diagramas')

ESTILO = '''
    graph [fontname="Helvetica", fontsize=12, bgcolor="white", pad=0.3, nodesep=0.35, ranksep=0.5];
    node  [fontname="Helvetica", fontsize=11];
    edge  [fontname="Helvetica", fontsize=10, color="#475569", fontcolor="#475569"];
'''


def guardar(nombre, contenido):
    ruta_dot = os.path.join(SALIDA, f'{nombre}.dot')
    with open(ruta_dot, 'w', encoding='utf-8') as f:
        f.write(contenido)
    subprocess.run(['dot', '-Tpng', '-Gdpi=110', ruta_dot, '-o',
                    os.path.join(SALIDA, f'{nombre}.png')], check=True)
    print(f'docs/diagramas/{nombre}.png')


# ----------------------------------------------------------------------
# Utilidades para clases tipo UML
# ----------------------------------------------------------------------

def tabla_uml(titulo, atributos, metodos, color='#e0e7ff'):
    filas = [f'<tr><td bgcolor="{color}"><b>{html.escape(titulo)}</b></td></tr>']
    if atributos:
        filas.append('<tr><td align="left" balign="left">' +
                     '<br/>'.join(html.escape(a) for a in atributos) + '</td></tr>')
    if metodos:
        filas.append('<tr><td align="left" balign="left">' +
                     '<br/>'.join(html.escape(m) for m in metodos) + '</td></tr>')
    return ('<<table border="0" cellborder="1" cellspacing="0" cellpadding="5">'
            + ''.join(filas) + '</table>>')


def parametros_init(clase):
    firma = inspect.signature(clase.__init__)
    return [p for p in firma.parameters if p not in ('self', 'linea', 'columna')]


def metodos_publicos(clase, excluir=(), resumir_visit=False):
    nombres = [n for n, f in inspect.getmembers(clase, inspect.isfunction)
               if f.__qualname__.startswith(clase.__name__ + '.')
               and not n.startswith('_') and n not in excluir]
    visit = [n for n in nombres if n.startswith('visit_')]
    otros = [n for n in nombres if not n.startswith('visit_') and not n.startswith('p_')
             and not n.startswith('t_')]
    lineas = [f'+ {n}()' for n in sorted(otros)]
    if resumir_visit and visit:
        lineas.append(f'+ visit_*(nodo)   [{len(visit)} métodos: uno por nodo]')
    return lineas


# ----------------------------------------------------------------------
# 1. Arquitectura (sección 3.1.1)
# ----------------------------------------------------------------------

def arquitectura():
    guardar('arquitectura', f'''digraph arquitectura {{
{ESTILO}
    rankdir=LR;
    node [shape=box, style="rounded,filled", fillcolor="#f8fafc", color="#64748b"];

    subgraph cluster_cliente {{
        label="1. Capa de presentación (navegador)"; style="rounded,dashed"; color="#94a3b8";
        ui [label="Interfaz web\\nindex.html · app.css · app.js\\n\\neditor · consola · ARM64 · reportes", fillcolor="#e0f2fe"];
    }}

    subgraph cluster_servidor {{
        label="Servidor Linux (monolito Django)"; style="rounded"; color="#64748b";

        api [label="2. Capa de lógica y servicios\\nAPI REST (backend/api/views.py)\\nPOST /api/compilar → JSON", fillcolor="#ede9fe"];

        subgraph cluster_lenguaje {{
            label="3. Definición e implementación del lenguaje"; style="rounded"; color="#a78bfa";
            lex [label="Lexer\\n(PLY lex)", fillcolor="#f5f3ff"];
            par [label="Parser\\n(PLY yacc)", fillcolor="#f5f3ff"];
            sem [label="Análisis semántico\\n+ tabla de símbolos", fillcolor="#f5f3ff"];
            gen [label="Generador ARM64\\n(visitor)", fillcolor="#f5f3ff"];
            rep [label="Reportes\\n(HTML · Graphviz)", fillcolor="#f5f3ff"];
        }}

        subgraph cluster_arm {{
            label="4. Entorno ARM64"; style="rounded"; color="#22c55e";
            gcc [label="gcc -static\\n(ensamblar + enlazar)", fillcolor="#dcfce7"];
            qemu [label="qemu-aarch64\\n(QEMU user mode)", fillcolor="#dcfce7"];
        }}
    }}

    ui -> api [label="HTTP POST\\n{{codigo}}"];
    api -> ui [label="JSON: salida, asm,\\nerrores, tabla, AST"];
    api -> lex;
    lex -> par [label="tokens"];
    par -> sem [label="AST"];
    sem -> gen [label="AST anotado"];
    gen -> gcc [label=".s"];
    gcc -> qemu [label="ELF ARM64"];
    qemu -> api [label="stdout"];
    sem -> rep [style=dashed, label="errores, tabla, AST"];
}}
''')


# ----------------------------------------------------------------------
# 2. Flujo de procesamiento
# ----------------------------------------------------------------------

def flujo():
    guardar('flujo_procesamiento', f'''digraph flujo {{
{ESTILO}
    node [shape=box, style="rounded,filled", fillcolor="#f8fafc", color="#64748b"];

    inicio  [label="Código fuente OxigenNative (.rs)", shape=note, fillcolor="#fef9c3"];
    lexer   [label="Análisis léxico — compiler/lexer.py\\ntokens con línea y columna\\nerrores léxicos (carácter no reconocido, cadena sin cerrar...)"];
    parser  [label="Análisis sintáctico — compiler/parser.py\\nconstruye el AST (compiler/ast_nodes.py)\\nrecuperación: inserta ; ) ] }} , faltantes o descarta hasta ; }}"];
    sem     [label="Análisis semántico — compiler/semantic.py\\n1ª pasada: registra funciones · 2ª pasada: cuerpos\\nllena la tabla de símbolos (ámbitos, offsets, marcos)\\nanota tipo_resultado y simbolo en cada nodo"];
    dec     [label="¿Errores léxicos\\no sintácticos?", shape=diamond, fillcolor="#fee2e2"];
    gen     [label="Generación ARM64 — compiler/codegen/arm64.py\\nvisitor: prólogo/epílogo, x0/d0, push/pop, etiquetas\\nlas partes con error semántico se omiten o imprimen None"];
    gcc     [label="Ensamblado y enlace — compiler/runner.py\\ngcc -static programa.s -o programa"];
    qemu    [label="Ejecución — qemu-aarch64 ./programa\\n(límite de 5 s)"];
    rep     [label="Reportes — compiler/reports.py\\nerrores.html · tabla_simbolos.html · ast.dot/.svg", fillcolor="#e0e7ff"];
    resp    [label="Respuesta JSON a la interfaz\\nsalida · asm · errores · tabla · AST · tiempos", shape=note, fillcolor="#dcfce7"];

    inicio -> lexer -> parser -> sem -> dec;
    dec -> gen [label="no"];
    dec -> rep [label="sí: no se genera código"];
    gen -> gcc -> qemu -> rep;
    rep -> resp;
}}
''')


# ----------------------------------------------------------------------
# 3. Flujo de la tabla de símbolos
# ----------------------------------------------------------------------

def flujo_tabla():
    guardar('flujo_tabla_simbolos', f'''digraph tabla {{
{ESTILO}
    node [shape=box, style="rounded,filled", fillcolor="#f8fafc", color="#64748b"];

    p1  [label="Primera pasada (visit_Program)\\ndeclarar_funcion() de TODAS las funciones en el ámbito Global\\n(guarda tipo de retorno y tipos de parámetros)"];
    f   [label="Por cada función: entrar_funcion()\\nabre el ámbito de la función y reinicia el marco (0 bytes)"];
    prm [label="Parámetros: declarar_variable(categoria=Parámetro)\\noffset -8, -16, ...  (llegan en x0-x7 / d0-d7)"];
    ins [label="Recorrer instrucciones del cuerpo", shape=box];
    let [label="let x = ...\\n1) se analiza el valor (así let x = x + 1 usa la x anterior)\\n2) declarar_variable(): nuevo Symbol con offset = -(bytes usados + 8)\\n   (sombreado: el nuevo reemplaza al anterior en el ámbito)"];
    blq [label="Bloque if / while / loop / for / match\\nabrir_scope('main > if') ... cerrar_scope()\\n(la memoria sigue en el marco de la función)"];
    uso [label="Uso de x: buscar('x')\\nsube por los ámbitos padre hasta encontrarla\\nIdentifier.simbolo = Symbol (el generador lee su offset)"];
    err [label="No encontrada → error semántico\\n\\"La variable 'x' no ha sido declarada.\\"", fillcolor="#fee2e2"];
    fin [label="salir_funcion()\\ntamano_frame = bytes usados redondeado a 16\\n(el generador hace sub sp, sp, #tamano_frame)"];
    rep [label="tabla.reporte(): una fila por símbolo\\nNo · Identificador · Categoría · Tipo · Ámbito · Línea · Columna · Valor", fillcolor="#e0e7ff"];

    p1 -> f -> prm -> ins;
    ins -> let [label="declaración"];
    ins -> blq [label="bloque"];
    ins -> uso [label="expresión"];
    uso -> err [label="no existe", style=dashed];
    let -> ins; blq -> ins; uso -> ins;
    ins -> fin [label="fin del cuerpo"];
    fin -> f [label="siguiente función", style=dashed];
    fin -> rep;
}}
''')


# ----------------------------------------------------------------------
# 4. Diagrama de clases del compilador
# ----------------------------------------------------------------------

def clases_compilador():
    nodos = {
        'Lexer': tabla_uml('Lexer', ['reserved: dict', 'tokens: list', 'errores: ErrorList'],
                           metodos_publicos(Lexer) + ['+ t_*()  [reglas de tokens]']),
        'Parser': tabla_uml('Parser', ['tokens = Lexer.tokens', 'precedence: tuple',
                                       'errores: ErrorList', 'lexer: Lexer'],
                            metodos_publicos(Parser) + ['+ p_*()  [reglas de la gramática]',
                                                        '+ p_error(tok)']),
        'ErrorList': tabla_uml('ErrorList', ['errores: list[CompilerError]'],
                               metodos_publicos(ErrorList), '#fee2e2'),
        'CompilerError': tabla_uml('CompilerError', ['tipo: str', 'descripcion: str',
                                                     'linea: int', 'columna: int'],
                                   metodos_publicos(CompilerError), '#fee2e2'),
        'Semantic': tabla_uml('Semantic', ['errores: ErrorList', 'tabla: SymbolTable',
                                           'ciclos: list'],
                              metodos_publicos(Semantic, resumir_visit=True), '#ede9fe'),
        'SymbolTable': tabla_uml('SymbolTable', ['global_scope: Scope', 'actual: Scope',
                                                 'todos: list[Symbol]', 'funcion_actual: Symbol'],
                                 metodos_publicos(SymbolTable), '#dcfce7'),
        'Scope': tabla_uml('Scope', ['nombre: str', 'padre: Scope', 'simbolos: dict'],
                           metodos_publicos(Scope), '#dcfce7'),
        'Symbol': tabla_uml('Symbol', ['nombre, categoria, tipo', 'linea, columna, ambito',
                                       'mutable, valor', 'offset: int (en la pila)',
                                       'params, tipos_params, tamano_frame'],
                            metodos_publicos(Symbol), '#dcfce7'),
        'Arm64Generator': tabla_uml('Arm64Generator', ['text, data: list[str]',
                                                       'cadenas, decimales: dict',
                                                       'ciclos: list', 'rutinas: set'],
                                    metodos_publicos(Arm64Generator, resumir_visit=True)[:14]
                                    + ['+ visit_*(nodo)  [uno por nodo]', '+ ...'], '#fef3c7'),
        'Node': tabla_uml('Node  (AST)', ['linea, columna'],
                          ['+ hijos()', '+ pretty()'], '#e0f2fe'),
        'compilador': tabla_uml('compilador.py', [], ['+ compilar(codigo)'], '#f1f5f9'),
        'runner': tabla_uml('runner.py', [], ['+ ejecutar_asm(asm)', '+ compilador_c()'], '#f1f5f9'),
        'reports': tabla_uml('reports.py', [], ['+ html_errores()', '+ html_tabla_simbolos()',
                                                '+ ast_a_dot()', '+ dot_a_svg()',
                                                '+ guardar_reportes()'], '#f1f5f9'),
    }
    lineas = ['digraph clases {', ESTILO, '    node [shape=plain];', '    rankdir=TB;']
    for nombre, etiqueta in nodos.items():
        lineas.append(f'    "{nombre}" [label={etiqueta}];')
    relaciones = [
        ('compilador', 'Parser', 'usa'), ('compilador', 'Semantic', 'usa'),
        ('compilador', 'Arm64Generator', 'usa'), ('compilador', 'runner', 'usa'),
        ('Parser', 'Lexer', 'tiene'), ('Parser', 'Node', 'crea'),
        ('Lexer', 'ErrorList', 'reporta en'), ('Parser', 'ErrorList', 'reporta en'),
        ('Semantic', 'ErrorList', 'reporta en'), ('ErrorList', 'CompilerError', '1..*'),
        ('Semantic', 'SymbolTable', 'llena'), ('SymbolTable', 'Scope', 'pila de'),
        ('Scope', 'Symbol', 'contiene'), ('Semantic', 'Node', 'anota'),
        ('Arm64Generator', 'Node', 'recorre'), ('Arm64Generator', 'Symbol', 'lee offset'),
        ('reports', 'Node', 'dibuja'), ('reports', 'SymbolTable', 'lee'),
    ]
    for a, b, etiqueta in relaciones:
        lineas.append(f'    "{a}" -> "{b}" [label="{etiqueta}"];')
    lineas.append('}')
    guardar('clases_compilador', '\n'.join(lineas))


# ----------------------------------------------------------------------
# 5. Jerarquía de clases del AST
# ----------------------------------------------------------------------

GRUPOS_AST = [
    ('Estructura', '#e0e7ff', ['Program', 'Function', 'Param', 'Block']),
    ('Instrucciones', '#f1f5f9', ['VarDecl', 'Assignment', 'Print', 'ExprStmt', 'Return']),
    ('Control de flujo', '#fef3c7', ['If', 'While', 'Loop', 'For', 'Break', 'Continue',
                                     'Match', 'MatchArm']),
    ('Expresiones', '#dcfce7', ['Literal', 'Identifier', 'BinaryOp', 'UnaryOp', 'Call',
                                'MethodCall']),
    ('Arreglos', '#fce7f3', ['ArrayLiteral', 'ArrayRepeat', 'Index', 'Slice']),
]


def clases_ast():
    """Todas las clases heredan de Node. Para que se lea, cada grupo es un
    recuadro y la herencia se dibuja con UNA flecha por grupo."""
    filas = [['Estructura', 'Instrucciones'], ['Control de flujo'], ['Expresiones', 'Arreglos']]
    grupos = {nombre: (color, clases) for nombre, color, clases in GRUPOS_AST}
    lineas = ['digraph ast {', ESTILO, '    compound=true; rankdir=TB; newrank=true;',
              '    node [shape=plain];',
              f'    "Node" [label={tabla_uml("Node  (clase base)", ["linea: int", "columna: int"], ["+ hijos()", "+ pretty()"], "#cbd5e1")}];']
    definidas = set()
    anclas = {}
    for grupo, (color, clases) in grupos.items():
        id_cluster = 'cluster_' + grupo.replace(' ', '_')
        lineas.append(f'    subgraph {id_cluster} {{')
        lineas.append(f'        label="{grupo}"; style="rounded"; color="#94a3b8"; fontsize=13;')
        for nombre in clases:
            clase = getattr(ast, nombre)
            lineas.append(f'        "{nombre}" [label={tabla_uml(nombre, parametros_init(clase), [], color)}];')
            definidas.add(nombre)
        lineas.append('    }')
        anclas[grupo] = (id_cluster, clases[len(clases) // 2])
    faltantes = [n for n, c in inspect.getmembers(ast, inspect.isclass)
                 if issubclass(c, ast.Node) and c is not ast.Node and n not in definidas]
    assert not faltantes, f"Clases del AST sin grupo en el diagrama: {faltantes}"

    # Filas: los grupos de una fila quedan al mismo nivel; cada fila debajo de la anterior
    for i, fila in enumerate(filas):
        mismos = ' '.join(f'"{c}"' for g in fila for c in grupos[g][1])
        lineas.append(f'    {{ rank=same; {mismos} }}')
        if i > 0:
            arriba = grupos[filas[i - 1][0]][1][0]
            lineas.append(f'    "{arriba}" -> "{grupos[fila[0]][1][0]}" [style=invis, weight=10];')
    # Herencia: una flecha (triángulo hacia Node) por grupo
    for grupo, (id_cluster, nodo) in anclas.items():
        lineas.append(f'    "Node" -> "{nodo}" [lhead={id_cluster}, dir=back, arrowtail=empty, '
                      f'label="hereda de Node", minlen=2];')
    lineas.append('}')
    guardar('clases_ast', '\n'.join(lineas))


if __name__ == '__main__':
    os.makedirs(SALIDA, exist_ok=True)
    arquitectura()
    flujo()
    flujo_tabla()
    clases_compilador()
    clases_ast()
