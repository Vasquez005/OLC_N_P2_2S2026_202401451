"""
Analizador léxico de OxigenNative usando PLY (ply.lex).

Se implementa como clase para que cada compilación tenga su propio
lexer y su propia lista de errores (importante porque el servidor
Django puede recibir varias peticiones).

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
        'in': 'IN',
    }

    # ------------------------------------------------------------------
    # 2. Lista de tokens (PLY la exige con este nombre)
    # ------------------------------------------------------------------
    tokens = [
        # Literales e identificadores
        'ID', 'INT', 'FLOAT', 'STRING', 'CHAR', 'LABEL', 'UNDERSCORE',
        # Macro de impresión
        'PRINTLN',
        # Aritméticos
        'PLUS', 'MINUS', 'TIMES', 'DIVIDE', 'MOD',
        # Asignación
        'ASSIGN', 'PLUS_ASSIGN', 'MINUS_ASSIGN', 'TIMES_ASSIGN',
        'DIVIDE_ASSIGN', 'MOD_ASSIGN',
        # Relacionales
        'EQ', 'NE', 'GT', 'GE', 'LT', 'LE',
        # Lógicos
        'AND', 'OR', 'NOT',
        # Delimitadores y otros símbolos
        'LPAREN', 'RPAREN', 'LBRACE', 'RBRACE', 'LBRACKET', 'RBRACKET',
        'SEMI', 'COMMA', 'COLON', 'DCOLON', 'DOT', 'DOTDOT', 'DOTDOTEQ',
        'ARROW', 'FATARROW', 'AMP',
    ] + list(set(reserved.values()))

    # ------------------------------------------------------------------
    # 3. Tokens simples (strings)
    #    PLY los ordena automáticamente de la expresión más larga a la
    #    más corta, por eso '==' se prueba antes que '=' y '&&' antes que '&'.
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
    t_DOTDOTEQ = r'\.\.='      # rango inclusivo: 0..=5
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
    # ------------------------------------------------------------------

    def __init__(self, errores=None):
        self.errores = errores if errores is not None else ErrorList()
        self.lexer = None
        self.data = ""

    # --- Comentarios -------------------------------------------------

    def t_COMMENT_BLOCK(self, t):
        r'/\*(.|\n)*?\*/'
        t.lexer.lineno += t.value.count('\n')
        # No se retorna nada: el comentario se descarta

    def t_COMMENT_BLOCK_UNCLOSED(self, t):
        r'/\*(.|\n)*'
        self._error(t, "Comentario de bloque sin cierre: se esperaba '*/'.")
        t.lexer.lineno += t.value.count('\n')
        # Consume el resto del archivo: no se puede saber dónde termina

    def t_COMMENT_LINE(self, t):
        r'//[^\n]*'
        pass

    # --- Macro println! ----------------------------------------------

    def t_PRINTLN(self, t):
        r'println!'
        return t

    # --- Strings -----------------------------------------------------

    def t_RAW_STRING_HASH(self, t):
        r'r\#"(.|\n)*?"\#'
        # r#"..."#  -> se toma literal, puede contener comillas
        t.lexer.lineno += t.value.count('\n')
        t.value = t.value[3:-2]
        t.type = 'STRING'
        return t

    def t_RAW_STRING(self, t):
        r'r"[^"]*"'
        # r"..."  -> sin procesar secuencias de escape
        t.lexer.lineno += t.value.count('\n')
        t.value = t.value[2:-1]
        t.type = 'STRING'
        return t

    def t_STRING_TIPOGRAFICO(self, t):
        r'“[^”\n]*”'
        # Comillas “ ” como las que aparecen en el PDF del enunciado
        # (por ejemplo println!(“UNO!”)): se aceptan igual que " ".
        t.value = self._procesar_escapes(t.value[1:-1], t)
        t.type = 'STRING'
        return t

    def t_STRING(self, t):
        r'"([^"\\\n]|\\.)*"'
        t.value = self._procesar_escapes(t.value[1:-1], t)
        return t

    def t_STRING_UNCLOSED(self, t):
        r'"([^"\\\n]|\\.)*'
        self._error(t, "Cadena sin cerrar: se esperaba '\"'.")
        # Se descarta hasta el final de la línea

    # --- Caracteres y etiquetas ----------------------------------------

    def t_CHAR(self, t):
        r"'([^'\\\n]|\\.)'"
        t.value = self._procesar_escapes(t.value[1:-1], t)
        return t

    def t_LABEL(self, t):
        r"'[A-Za-z_][A-Za-z0-9_]*"
        # Etiquetas de ciclos: 'outer, 'inner
        t.value = t.value[1:]   # se guarda sin el apóstrofo
        return t

    # --- Números -------------------------------------------------------

    def t_FLOAT(self, t):
        r'\d+\.\d+'
        # Exige dígitos a ambos lados del punto para que 1..4 no sea float
        t.value = float(t.value)
        return t

    def t_INT(self, t):
        r'\d+'
        t.value = int(t.value)
        return t

    # --- Identificadores -----------------------------------------------

    def t_ID(self, t):
        r'[A-Za-z_][A-Za-z0-9_]*'
        if t.value == '_':
            t.type = 'UNDERSCORE'      # comodín del match
        else:
            t.type = self.reserved.get(t.value, 'ID')
        return t

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
