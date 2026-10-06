"""
Analizador sintáctico
Construye el AST definido en ast_nodes.py.
 
Paso 1: programa con funciones sin parámetros, bloques,
        declaraciones de variables y literales. 
Uso:
    from compiler.parser import Parser
    ast = Parser(errores).parse(codigo)
"""
import ply.yacc as yacc
 
from compiler.lexer import Lexer
from compiler.errors import ErrorList, SINTACTICO
from compiler import ast_nodes as ast
 
 
class Parser:
 
    # PLY necesita la misma lista de tokens que el lexer
    tokens = Lexer.tokens
 
    # Precedencia de operadores
    precedence = ()

    def __init__(self, errores=None, debug=False):
        self.errores = errores if errores is not None else ErrorList()
        self.lexer = Lexer(self.errores)
        self.lexer.build()

        self.parser = yacc.yacc(
            module=self,
            start='programa',
            write_tables=False,
            debug=debug,
            errorlog=yacc.PlyLogger(__import__('sys').stderr) if debug
            else yacc.NullLogger(),
        )

    def parse(self, codigo):
        self.lexer.input(codigo)
        return self.parser.parse(lexer=self.lexer.lexer)
        
    # ------------------------------------------------------------------
    # Utilidad: posición (línea, columna) del símbolo n de la producción
    # ------------------------------------------------------------------
    def _pos(self, p, n):
        return p.lineno(n), self.lexer.find_column(p.lexpos(n))

    # ==================================================================
    # GRAMÁTICA
    # La primera línea del docstring de cada función es la producción.
    # ==================================================================

    # --- Programa ------------------------------------------------------
 
    def p_programa(self, p):
        'programa : funciones'
        p[0] = ast.Program(p[1])

    def p_funciones(self, p):
        'funciones : funciones funcion'
        p[0] = p[1] + [p[2]]

    def p_funciones_una(self, p):
        'funciones : funcion'
        p[0] = [p[1]]

    # --- Funciones (parámetros y retorno PENDIENTES) -------
 
    def p_funcion(self, p):
        'funcion : FN ID LPAREN RPAREN bloque'
        linea, col = self._pos(p, 1)
        p[0] = ast.Function(p[2], [], None, p[5], linea, col) # el "ast.Function" sirve para ciertas reglas sintacticas, como funciones y bloques, y crea un nodo en el AST con la información de la función, incluyendo su nombre, parámetros, tipo de retorno y cuerpo.

    # --- Bloques --------------------------------------------------------

    def p_bloque(self, p):
        'bloque : LBRACE instrucciones RBRACE'
        linea, col = self._pos(p, 1)
        p[0] = ast.Block(p[2], linea, col) # el "ast.Block" sirve para ciertas reglas sintacticas, como bloques de código, y crea un nodo en el AST con la información del bloque, incluyendo las declaraciones que contiene.

    def p_bloque_vacio(self, p):
        'bloque : LBRACE RBRACE'
        linea, col = self._pos(p, 1)
        p[0] = ast.Block([], linea, col) # el "ast.Block" sirve para ciertas reglas sintacticas, como bloques de código, y crea un nodo en el AST con la información del bloque, incluyendo las declaraciones que contiene.

    def p_instrucciones_lista(self, p):
        'instrucciones : instrucciones instruccion'
        p[0] = p[1] + [p[2]]
 
    def p_instrucciones_una(self, p):
        'instrucciones : instruccion'
        p[0] = [p[1]]
 
    def p_instruccion(self, p):
        'instruccion : declaracion SEMI'
        p[0] = p[1]

    # --- Declaración de variables ------------------------------------
    #   let [mut] id [: tipo] [= expresion]

    def p_declaracion(self, p):
        'declaracion : LET mut_opt ID tipo_opt init_opt'
        linea, col = self._pos(p, 1)
        p[0] = ast.VarDecl(p[3], p[2], p[4], p[5], linea, col)

    def p_mut_opt(self, p):
        '''mut_opt : MUT
                   | empty'''
        p[0] = p[1] == 'mut'
 
    def p_tipo_opt(self, p):
        '''tipo_opt : COLON tipo
                    | empty'''
        p[0] = p[2] if len(p) == 3 else None
 
    def p_init_opt(self, p):
        '''init_opt : ASSIGN expresion
                    | empty'''
        p[0] = p[2] if len(p) == 3 else None
 
    # --- Tipos (los arreglos [T; N] PENDIENTES) -----------

    def p_tipo(self, p):
        '''tipo : T_I32
                | T_F64
                | T_BOOL
                | T_CHAR
                | T_STRING'''
        p[0] = p[1]

    # --- Expresiones (operadores en el paso 2) -------------------------
 
    def p_expresion(self, p):
        'expresion : primario'
        p[0] = p[1]
 
    def p_primario_int(self, p):
        'primario : INT'
        linea, col = self._pos(p, 1)
        p[0] = ast.Literal(p[1], 'i32', linea, col)
 
    def p_primario_float(self, p):
        'primario : FLOAT'
        linea, col = self._pos(p, 1)
        p[0] = ast.Literal(p[1], 'f64', linea, col)
 
    def p_primario_bool(self, p):
        '''primario : TRUE
                    | FALSE'''
        linea, col = self._pos(p, 1)
        p[0] = ast.Literal(p[1] == 'true', 'bool', linea, col)
 
    def p_primario_char(self, p):
        'primario : CHAR'
        linea, col = self._pos(p, 1)
        p[0] = ast.Literal(p[1], 'char', linea, col)
 
    def p_primario_string(self, p):
        'primario : STRING'
        linea, col = self._pos(p, 1)
        p[0] = ast.Literal(p[1], 'String', linea, col)
 
    def p_primario_string_from(self, p):
        'primario : T_STRING DCOLON ID LPAREN STRING RPAREN'
        linea, col = self._pos(p, 1)
        if p[3] != 'from':
            self.errores.agregar(SINTACTICO,
                                 f"Función 'String::{p[3]}' no reconocida.",
                                 *self._pos(p, 3))
        p[0] = ast.Literal(p[5], 'String', linea, col)
 
    def p_primario_string_new(self, p):
        'primario : T_STRING DCOLON ID LPAREN RPAREN'
        linea, col = self._pos(p, 1)
        if p[3] != 'new':
            self.errores.agregar(SINTACTICO,
                                 f"Función 'String::{p[3]}' no reconocida.",
                                 *self._pos(p, 3))
        p[0] = ast.Literal("", 'String', linea, col)
 
    def p_primario_id(self, p):
        'primario : ID'
        linea, col = self._pos(p, 1)
        p[0] = ast.Identifier(p[1], linea, col)

    # --- Producción vacía ----------------------------------------------
 
    def p_empty(self, p):
        'empty :'
        p[0] = None

    # --- Errores sintácticos (recuperación completa PENDIENTE) -------
 
    def p_error(self, tok):
        if tok is None:
            linea = self.lexer.lexer.lineno
            self.errores.agregar(SINTACTICO,
                                 "Fin de archivo inesperado.", linea, 1)
            return
        col = self.lexer.find_column(tok.lexpos)
        self.errores.agregar(SINTACTICO,
                             f"Token inesperado '{tok.value}'.",
                             tok.lineno, col)