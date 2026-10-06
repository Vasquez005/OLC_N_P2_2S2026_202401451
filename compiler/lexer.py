"""
Analizador léxico usando PLY 
 
Se implementa como clase para que cada compilación tenga su propio
lexer y su propia lista de errores
 
Uso:
    from compiler.lexer import Lexer
    lx = Lexer(errores)          # errores es un ErrorList
    lx.build()
    for tok in lx.tokenize(codigo): ...
"""
import ply.lex as lex

from compiler.errors import ErrorList, LEXICO

class Lexer:

    # ------------------------------------------------------------------
    # 1. Palabras reservadas
    #    Se reconocen primero como ID y luego se buscan en este diccionario.
    # ------------------------------------------------------------------
    reserved = {
        'fn': 'FN',
        'let': 'LET',
        'mut': 'MUT',
        'if': 'IF',
        'else': 'ELSE',
        'while': 'WHILE',
        'loop': 'LOOP',
        'match': 'MATCH',
        'break': 'BREAK',
        'continue': 'CONTINUE',
        'return': 'RETURN',
        'true': 'TRUE',
        'false': 'FALSE',
        # Tipos
        'i32': 'T_I32',
        'f64': 'T_F64',
        'bool': 'T_BOOL',
        'char': 'T_CHAR',
        'String': 'T_STRING',
        # Reservadas aunque no se usen (el enunciado las menciona)
        'struct': 'STRUCT',
        'for': 'FOR',
    }

    # ------------------------------------------------------------------
    # 2. Lista de tokens 
    # ------------------------------------------------------------------
    tokens = [
        # Literales e identificadores
        'ID', 'INT', 'FLOAT', 'STRING', 'CHAR', 'LABEL', 'UNDERSCORE',
        # impresion
        'PRINTLN',
        # aritemiticos
        'PLUS', 'MINUS', 'TIMES', 'DIVIDE', 'MOD',
        # asignacion
        'ASSIGN', 'PLUS_ASSIGN', 'MINUS_ASSIGN', 'TIMES_ASSIGN',
        'DIVIDE_ASSIGN', 'MOD_ASSIGN',
        # relaciones
        'EQ', 'NE', 'GT', 'GE', 'LT', 'LE',
        # logicos
        'AND', 'OR', 'NOT',
        # Delimitadores y otros símbolos
        'LPAREN', 'RPAREN', 'LBRACE', 'RBRACE', 'LBRACKET', 'RBRACKET',
        'SEMI', 'COMMA', 'COLON', 'DCOLON', 'DOT', 'DOTDOT',
        'ARROW', 'FATARROW', 'AMP',
    ] + list(set(reserved.values())) # -> lista de tokens finales que setean los reservados

    # ------------------------------------------------------------------
    # 3. Tokens simples (strings)
    #    PLY los ordena automáticamente de la expresión más larga a la más corta
    # ------------------------------------------------------------------
    t_PLUS_ASSIGN = r'\+='
    t_MINUS_ASSIGN = r'-='
    t_TIMES_ASSIGN = r'\*='
    t_DIVIDE_ASSIGN = r'/='
    t_MOD_ASSIGN = r'%='
 
    t_EQ = r'=='
    t_NE = r'!='
    t_GE = r'>='
    t_LE = r'<='
    t_GT = r'>'
    t_LT = r'<'
 
    t_AND = r'&&'
    t_OR = r'\|\|'
    t_NOT = r'!'
 
    t_ARROW = r'->'
    t_FATARROW = r'=>'
    t_DCOLON = r'::'
    t_DOTDOT = r'\.\.'
 
    t_PLUS = r'\+'
    t_MINUS = r'-'
    t_TIMES = r'\*'
    t_DIVIDE = r'/'
    t_MOD = r'%'
    t_ASSIGN = r'='
 
    t_LPAREN = r'\('
    t_RPAREN = r'\)'
    t_LBRACE = r'\{'
    t_RBRACE = r'\}'
    t_LBRACKET = r'\['
    t_RBRACKET = r'\]'
    t_SEMI = r';'
    t_COMMA = r','
    t_COLON = r':'
    t_DOT = r'\.'
    t_AMP = r'&'
 
    # Espacios y tabulaciones se ignoran (los saltos de línea aparte)
    t_ignore = ' \t\r'

    # ------------------------------------------------------------------
    # 4. Tokens con función
    #    PLY prueba las funciones EN EL ORDEN en que están
    #    escritas. Por ejemplo, los comentarios van antes que DIVIDE, los raw
    #    strings antes que ID, CHAR antes que LABEL, FLOAT antes que INT
    # ------------------------------------------------------------------

    def __init__(self, errores:ErrorList):
        self.errores = errores if errores is not None else ErrorList()
        self.lexer = None
        self.data = ""

    # --- Comentarios -------------------------------------------------
 
    def t_COMMENT_BLOCK(self, t):
        r'/\*(.|\n)*?\*/'
        t.lexer.lineno += t.value.count('\n') # no se hace return de nada, se ignora el token

    def t_COMMENT_BLOCK_UNCLOSED(self, t):
        r'/\*(.|\n)*'
        self._error(t, "Comentario de bloque sin cierre: se esperaba '*/'.")
        t.lexer.lineno += t.value.count('\n') # consume todo el bloque de comentario, aunque esté mal cerrado

    def t_COMMENT_LINE(self, t):
        r'//[^\n]*'
        pass

    # --- Macro println! ----------------------------------------------
 
    def t_PRINTLN(self, t):
        r'println!' # la r en los tokens especiales significan que no se puede usar un raw string, sino que es un token literal
        return t
    #t_PRINTLN funciona tal que: toma la cadena "println!" y la devuelve como un token de tipo PRINTLN

    # --- Strings -----------------------------------------------------
 
    def t_RAW_STRING_HASH(self, t):
        r'r\#"(.|\n)*?"\#' # r#"..."#  -> se toma literal, puede contener comillas
        t.lexer.lineno += t.value.count('\n')
        t.value = t.value[3:-2]
        t.type = 'STRING'
        return t
    #t_RAW_STRING_HASH funciona tal que: toma la cadena "r#"..."#" como por ejemplo r#"Hello, World!"# y la devuelve como un token de tipo STRING
 
    def t_RAW_STRING(self, t):
        r'r"[^"]*"' # r"..."  -> sin procesar secuencias de escape
        t.lexer.lineno += t.value.count('\n')
        t.value = t.value[2:-1] # [2:-1] significa que se quitan los primeros 2 caracteres (r") y el último (")
        t.type = 'STRING'
        return t
    #t_RAW_STRING funciona tal que: toma la cadena "r"..."r" como por ejemplo r"Hello, World!"r" y la devuelve como un token de tipo STRING
 
    def t_STRING(self, t):
        r'"([^"\\\n]|\\.)*"'
        t.value = self._procesar_escapes(t.value[1:-1], t)
        return t
    #t_STRING funciona tal que: toma la cadena "..." como por ejemplo "Hello, World!" y la devuelve como un token de tipo STRING, procesando las secuencias de escape como \n, \t, etc.
 
    def t_STRING_UNCLOSED(self, t):
        r'"([^"\\\n]|\\.)*'
        self._error(t, "Cadena sin cerrar: se esperaba '\"'.") # Se descarta hasta el final de la línea
    #t_STRING_UNCLOSED funciona tal que: toma la cadena "..." sin cerrar como por ejemplo "Hello, World! y genera un error léxico indicando que se esperaba un cierre de comillas.

    # --- Caracteres y etiquetas ----------------------------------------
 
    def t_CHAR(self, t):
        r"'([^'\\\n]|\\.)'"
        t.value = self._procesar_escapes(t.value[1:-1], t)
        return t
    #t_CHAR funciona tal que: toma la cadena '...' como por ejemplo 'a' y la devuelve como un token de tipo CHAR, procesando las secuencias de escape como \n, \t, etc.
 
    def t_LABEL(self, t):
        r"'[A-Za-z_][A-Za-z0-9_]*" # Etiquetas de ciclos: 'outer, 'inner
        t.value = t.value[1:]   # se guarda sin el apóstrofo
        return t
    #t_LABEL funciona tal que: toma la cadena '...' como por ejemplo 'outer y la devuelve como un token de tipo LABEL, sin el apóstrofo inicial.

    # --- Números -------------------------------------------------------
 
    def t_FLOAT(self, t):
        r'\d+\.\d+' # Exige dígitos a ambos lados del punto para que 1..4 no sea float
        t.value = float(t.value)
        return t
    #t_FLOAT funciona tal que: toma la cadena "..." como por ejemplo "3.14" y la devuelve como un token de tipo FLOAT.

    def t_INT(self, t):
        r'\d+'
        t.value = int(t.value)
        return t
    #t_INT funciona tal que: toma la cadena "..." como por ejemplo "42" y la devuelve como un token de tipo INT.

    # --- Identificadores -----------------------------------------------
 
    def t_ID(self, t):
        r'[A-Za-z_][A-Za-z0-9_]*'
        if t.value == '_':
            t.type = 'UNDERSCORE'      # comodín del match, un underscore es un token especial como por ejemplo 'if', 'else', etc.
        else:
            t.type = self.reserved.get(t.value, 'ID')
        return t
    #t_ID funciona tal que: toma la cadena "..." como por ejemplo "variable1" y la devuelve como un token de tipo ID, a menos que sea una palabra reservada como 'if', 'else', etc., 
    # en cuyo caso se devuelve como un token del tipo correspondiente.
 
    # --- Saltos de línea -----------------------------------------------
 
    def t_newline(self, t):
        r'\n+'
        t.lexer.lineno += len(t.value)
 
    # --- Error: carácter no reconocido ---------------------------------
 
    def t_error(self, t):
        self._error(t, f"Carácter no reconocido '{t.value[0]}'.")
        t.lexer.skip(1)   # se recupera y sigue analizando
 
    # ------------------------------------------------------------------
    # 5. Utilidades
    # ------------------------------------------------------------------

    def find_column(self, lexpos):
        """Columna (empezando en 1) a partir de la posición absoluta."""
        inicio_linea = self.data.rfind('\n', 0, lexpos) + 1
        return (lexpos - inicio_linea) + 1
 
    def _error(self, t, descripcion):
        self.errores.agregar(LEXICO, descripcion, t.lineno,
                             self.find_column(t.lexpos))
 
    ESCAPES = {'n': '\n', 't': '\t', 'r': '\r', '0': '\0',
               '\\': '\\', '"': '"', "'": "'"}
 
    def _procesar_escapes(self, texto, t):
        resultado = []
        i = 0
        while i < len(texto):
            c = texto[i]
            if c == '\\' and i + 1 < len(texto):
                sig = texto[i + 1]
                if sig in self.ESCAPES:
                    resultado.append(self.ESCAPES[sig])
                else:
                    self._error(t, f"Secuencia de escape no válida '\\{sig}'.")
                    resultado.append(sig)
                i += 2
            else:
                resultado.append(c)
                i += 1
        return ''.join(resultado)
 
    # ------------------------------------------------------------------
    # 6. Construcción y uso
    # ------------------------------------------------------------------
 
    def build(self, **kwargs):
        self.lexer = lex.lex(module=self, **kwargs)
        return self.lexer
 
    def input(self, data):
        self.data = data
        self.lexer.lineno = 1
        self.lexer.input(data)
 
    def tokenize(self, data):
        """Genera todos los tokens; útil para pruebas."""
        self.input(data)
        while True:
            tok = self.lexer.token()
            if not tok:
                break
            tok.column = self.find_column(tok.lexpos)
            yield tok
 