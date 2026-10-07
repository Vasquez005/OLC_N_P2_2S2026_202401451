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
    #   left     -> a - b - c  se agrupa como (a - b) - c
    #   right    -> !!a        se agrupa como !(!a)
    precedence = (
        ('left', 'OR'),
        ('left', 'AND'),
        ('nonassoc', 'EQ', 'NE', 'LT', 'GT', 'LE', 'GE'),
        ('left', 'PLUS', 'MINUS'),
        ('left', 'TIMES', 'DIVIDE', 'MOD'),
        ('right', 'NOT', 'UMINUS'),
    )

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
        p[0] = p[1] + [p[2]] if p[2] is not None else p[1]
 
    def p_instrucciones_una(self, p):
        'instrucciones : instruccion'
        p[0] = [p[1]] if p[1] is not None else []
 
    def p_instruccion(self, p):
        '''instruccion : declaracion SEMI
                       | asignacion SEMI
                       | impresion SEMI
                       | sentencia_if
                       | sentencia_while
                       | sentencia_loop
                       | sentencia_break SEMI
                       | sentencia_continue SEMI'''
        p[0] = p[1]

    def p_instruccion_vacia(self, p):
        'instruccion : SEMI' # Permitimos cosas como `};` o `;;` sin generar nodos
        p[0] = None

    # --- if / else if / else ------------------------------------------
    # No hay ambigüedad del "else colgante" porque los bloques siempre
    # llevan llaves.

    def p_sentencia_if(self, p):
        'sentencia_if : IF expresion bloque'
        self._revisar_condicion(p[2])
        linea, col = self._pos(p, 1)
        p[0] = ast.If(p[2], p[3], None, linea, col) #dejamos None como base porque puede que no haya un else, y si hay un else, se agregará en la siguiente regla de producción.

    def p_sentencia_if_else(self, p):
        '''sentencia_if : IF expresion bloque ELSE bloque
                        | IF expresion bloque ELSE sentencia_if'''
        self._revisar_condicion(p[2])
        linea, col = self._pos(p, 1)
        p[0] = ast.If(p[2], p[3], None, linea, col)

    # --- while ----------------------------------------------------------

    def p_sentencia_while(self, p):
        '''sentencia_while : WHILE expresion bloque'''
        self._revisar_condicion(p[2])
        linea, col = self._pos(p, 1)
        p[0] = ast.While(p[2], p[3], None, linea, col)

    def p_sentencia_while_etiqueta(self, p):
        'sentencia_while : LABEL COLON WHILE expresion bloque'
        self._revisar_condicion(p[4]) #revisamos la expresion de la sentencia while para asegurarnos de que sea una expresión booleana válida.  
        linea, col = self._pos(p, 1)
        p[0] = ast.While(p[4], p[5], p[1], linea, col)

    # --- loop -----------------------------------------------------------

    def p_sentencia_loop(self, p):
        'sentencia_loop : LOOP bloque'
        linea, col = self._pos(p, 1)
        p[0] = ast.Loop(p[2], None, linea, col) #sera None porque no hay etiqueta en esta regla de producción.

    def p_sentencia_loop_etiqueta(self, p):
        'sentencia_loop : LABEL COLON LOOP bloque'
        linea, col = self._pos(p, 1)
        p[0] = ast.Loop(p[4], p[1], linea, col) 

    # --- break / continue --------------------------------------------
 
    def p_sentencia_break(self, p):
        '''sentencia_break : BREAK
                           | BREAK LABEL'''
        linea, col = self._pos(p, 1)
        p[0] = ast.Break(p[2] if len(p) == 3 else None, linea, col)
 
    def p_sentencia_continue(self, p):
        '''sentencia_continue : CONTINUE
                              | CONTINUE LABEL'''
        linea, col = self._pos(p, 1)
        p[0] = ast.Continue(p[2] if len(p) == 3 else None, linea, col)

    # ----------------------------------------------------------------------
    # Utilidades para revisar condiciones y formatear cadenas
    # ----------------------------------------------------------------------
 
    def _revisar_condicion(self, cond):
        """El enunciado prohíbe paréntesis alrededor de toda la condición:
            if (x > 5) { ... }   -> error
            if (a) && (b) { }    -> válido (los paréntesis no la envuelven toda)
        """
        if getattr(cond, '_parentesis', None):
            linea, col = cond._parentesis
            self.errores.agregar(
                SINTACTICO,
                "No se permiten paréntesis alrededor de la condición.",
                linea, col)

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

    # --- Asignaciones ---------------------------------------------------

    def p_asignacion(self, p):
        '''asignacion : ID ASSIGN expresion
                      | ID PLUS_ASSIGN expresion
                      | ID MINUS_ASSIGN expresion
                      | ID TIMES_ASSIGN expresion
                      | ID DIVIDE_ASSIGN expresion
                      | ID MOD_ASSIGN expresion'''
        linea, col = self._pos(p, 1)
        objetivo = ast.Identifier(p[1], linea, col)
        p[0] = ast.Assignment(objetivo, p[2], p[3], linea, col)

    # --- println! ------------------------------------------------------

    def p_impresion_vacia(self, p):
        'impresion : PRINTLN LPAREN RPAREN'
        linea, col = self._pos(p, 1)
        p[0] = ast.Print("", [], [], linea, col)

    def p_impresion_texto(self, p):
        'impresion : PRINTLN LPAREN STRING RPAREN'
        linea, col = self._pos(p, 1)
        p[0] = ast.Print(p[3], self._partes_formato(p[3]), [], linea, col)

    def p_impresion_args(self, p):
        'impresion : PRINTLN LPAREN STRING COMMA lista_expresiones RPAREN'
        linea, col = self._pos(p, 1)
        p[0] = ast.Print(p[3], self._partes_formato(p[3]), p[5], linea, col)

    def p_lista_expresiones(self, p):
        '''lista_expresiones : lista_expresiones COMMA expresion
                             | expresion'''
        p[0] = p[1] + [p[3]] if len(p) == 4 else [p[1]]

    @staticmethod
    def _partes_formato(texto):
        """Separa el formato en textos y marcadores (None = {})."""
        partes, actual, i = [], [], 0
        while i < len(texto):
            if texto.startswith('{{', i):
                actual.append('{'); i += 2
            elif texto.startswith('}}', i):
                actual.append('}'); i += 2
            elif texto.startswith('{}', i) or texto.startswith('{:?}', i):
                if actual:
                    partes.append(''.join(actual)); actual = []
                partes.append(None)
                i += 2 if texto.startswith('{}', i) else 4
            else:
                actual.append(texto[i]); i += 1
        if actual:
            partes.append(''.join(actual))
        return partes

    
    # --- Tipos (los arreglos [T; N] PENDIENTES) -----------

    def p_tipo(self, p):
        '''tipo : T_I32
                | T_F64
                | T_BOOL
                | T_CHAR
                | T_STRING'''
        p[0] = p[1]

    # --- Expresiones -------------------------
 
    def p_expresion_binaria(self, p):
        '''expresion : expresion OR expresion
                     | expresion AND expresion
                     | expresion EQ expresion
                     | expresion NE expresion
                     | expresion LT expresion
                     | expresion GT expresion
                     | expresion LE expresion
                     | expresion GE expresion
                     | expresion PLUS expresion
                     | expresion MINUS expresion
                     | expresion TIMES expresion
                     | expresion DIVIDE expresion
                     | expresion MOD expresion'''
        linea, col = self._pos(p, 2)
        p[0] = ast.BinaryOp(p[2], p[1], p[3], linea, col)

    def p_expresion_not(self, p):
        'expresion : NOT expresion'
        linea, col = self._pos(p, 1)
        p[0] = ast.UnaryOp('!', p[2], linea, col)
 
    def p_expresion_uminus(self, p):
        'expresion : MINUS expresion %prec UMINUS'
        linea, col = self._pos(p, 1)
        p[0] = ast.UnaryOp('-', p[2], linea, col)
 
    def p_expresion_agrupada(self, p):
        'expresion : LPAREN expresion RPAREN'
        p[0] = p[2]     # los paréntesis no generan nodo: solo agrupan
        p[0]._parentesis = self._pos(p, 1) # marca que la expresión estaba entre paréntesis
 
    def p_expresion_primario(self, p):
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