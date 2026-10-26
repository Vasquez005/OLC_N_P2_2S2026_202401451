"""
Analizador sintáctico de OxigenNative usando PLY (ply.yacc).

Construye el AST definido en ast_nodes.py.

Paso 1: programa con funciones sin parámetros, bloques,
        declaraciones de variables y literales.
Paso 2: expresiones aritméticas, relacionales y lógicas con precedencia.
Paso 3: asignaciones simples y compuestas, println!.
Paso 4: if / else if / else, while, loop, break, continue y etiquetas.
        println! también acepta un solo valor sin formato: println!(x).
Paso 5: funciones con parámetros y tipo de retorno, return, llamadas y
        expresiones como instrucción.
Paso 6: arreglos: tipo [T; N], [a, b], [v; N], a[i][j], asignación a
        un elemento, &a[i..j] y métodos objeto.metodo(args).
Paso 7: match con brazos `patron => instrucción,` o `patron => { ... }`,
        ciclo for (rangos y arreglos) y tipos Vec<&str> / &str.
Paso 8: recuperación de errores sintácticos (ver p_error):
          * si falta ; ) ] o } se reporta "Se esperaba ';'." y se inserta,
            así el análisis sigue sin perder la instrucción;
          * cualquier otro error descarta tokens hasta el siguiente ; o }
            (producciones con `error`) y el análisis continúa.

Uso:
    from compiler.parser import Parser
    ast = Parser(errores).parse(codigo)
"""
import ply.lex as lex
import ply.yacc as yacc

from compiler.lexer import Lexer
from compiler.errors import ErrorList, SINTACTICO
from compiler import ast_nodes as ast


# Tokens que se pueden insertar si faltan, en orden de prioridad
CIERRES = ('SEMI', 'RPAREN', 'RBRACKET', 'RBRACE')

# Tokens con los que empieza un elemento de una lista o un patrón: si
# aparecen donde se esperaba una coma, lo que falta es la coma.
INICIO_ELEMENTO = {'ID', 'INT', 'FLOAT', 'STRING', 'CHAR', 'TRUE', 'FALSE',
                   'LBRACKET', 'MINUS', 'NOT', 'T_STRING', 'AMP', 'UNDERSCORE', 'MUT'}

SIMBOLO = {'SEMI': ';', 'RPAREN': ')', 'RBRACKET': ']', 'RBRACE': '}', 'COMMA': ','}

# Delimitadores: cierre -> apertura
PAREJAS = {'RPAREN': 'LPAREN', 'RBRACKET': 'LBRACKET', 'RBRACE': 'LBRACE'}
CIERRE_DE = {v: k for k, v in PAREJAS.items()}

# Nombre legible de cada token para los mensajes de error
NOMBRES_TOKEN = {
    'SEMI': "';'", 'COMMA': "','", 'COLON': "':'", 'DCOLON': "'::'", 'DOT': "'.'",
    'LPAREN': "'('", 'RPAREN': "')'", 'LBRACE': "'{'", 'RBRACE': "'}'",
    'LBRACKET': "'['", 'RBRACKET': "']'", 'ASSIGN': "'='", 'ARROW': "'->'",
    'FATARROW': "'=>'", 'DOTDOT': "'..'", 'DOTDOTEQ': "'..='", 'AMP': "'&'",
    'ID': 'un identificador', 'INT': 'un número entero', 'FLOAT': 'un número decimal',
    'STRING': 'una cadena', 'CHAR': 'un carácter', 'LABEL': 'una etiqueta',
    'T_I32': "'i32'", 'T_F64': "'f64'", 'T_BOOL': "'bool'", 'T_CHAR': "'char'",
    'T_STRING': "'String'", 'IN': "'in'", 'FN': "'fn'", 'PRINTLN': "'println!'",
}


class Parser:

    # PLY necesita la misma lista de tokens que el lexer
    tokens = Lexer.tokens

    # ------------------------------------------------------------------
    # Precedencia de operadores, de MENOR a MAYOR (igual que en Rust).
    #   left     -> a - b - c  se agrupa como (a - b) - c
    #   right    -> !!a        se agrupa como !(!a)
    #   nonassoc -> a < b < c  es un error de sintaxis (como en Rust)
    # UMINUS no es un token real: solo se usa con %prec para que el
    # menos unario (-x) tenga más prioridad que la resta (a - b).
    # ------------------------------------------------------------------
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
        # debug=True escribe parser.out (útil para revisar conflictos)
        # y muestra advertencias en consola.
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
        self.codigo = codigo
        self.pendientes = []        # tokens que se devuelven después de uno insertado
        self.anterior = None        # token anterior al actual
        self.actual = None          # último token entregado al parser
        self.insertados = set()     # para no insertar dos veces en el mismo lugar
        self.eof_reportados = set() # cierres ya reportados al final del archivo
        self.entregados = []        # tokens entregados al parser (para la pila de { ( [)
        return self.parser.parse(lexer=self.lexer.lexer, tokenfunc=self._siguiente_token)

    def _siguiente_token(self):
        """Entrega los tokens al parser. Primero los que se devolvieron
        después de insertar un token faltante; luego los del lexer.
        Cada token guarda `_fin`: la posición justo después de él."""
        if self.pendientes:
            tok = self.pendientes.pop()
        else:
            tok = self.lexer.lexer.token()
            if tok is not None:
                tok._fin = self.lexer.lexer.lexpos
        if tok is not None:
            self._registrar(tok)
        return tok

    def _registrar(self, tok):
        self.anterior, self.actual = self.actual, tok
        self.entregados.append(tok)

    def _abierto_mas_interno(self):
        """(tipo, es_match) del ( [ { abierto más interno según los tokens
        aceptados. es_match indica si esa { es la de un `match`."""
        pila = []
        match_pendiente = False
        for t in self.entregados:
            if t.type == 'MATCH':
                match_pendiente = True
            elif t.type in CIERRE_DE:
                pila.append((t.type, t.type == 'LBRACE' and match_pendiente))
                if t.type == 'LBRACE':
                    match_pendiente = False
            elif t.type in PAREJAS and any(a == PAREJAS[t.type] for a, _ in pila):
                while pila and pila.pop()[0] != PAREJAS[t.type]:
                    pass
            elif t.type == 'SEMI':
                match_pendiente = False
        return pila[-1] if pila else (None, False)

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

    def p_funciones_lista(self, p):
        'funciones : funciones funcion'
        p[0] = p[1] + [p[2]]

    def p_funciones_una(self, p):
        'funciones : funcion'
        p[0] = [p[1]]

    # --- Funciones -------------------------------------------------------
    #   fn nombre(a: i32, mut b: f64) -> tipo { ... }
    #   fn nombre() { ... }                     (sin retorno)

    def p_funcion(self, p):
        'funcion : FN ID LPAREN parametros_opt RPAREN retorno_opt bloque'
        linea, col = self._pos(p, 1)
        p[0] = ast.Function(p[2], p[4], p[6], p[7], linea, col)

    def p_parametros_opt(self, p):
        '''parametros_opt : parametros
                          | empty'''
        p[0] = p[1] if p[1] is not None else []

    def p_parametros(self, p):
        '''parametros : parametros COMMA parametro
                      | parametro'''
        p[0] = p[1] + [p[3]] if len(p) == 4 else [p[1]]

    def p_parametro(self, p):
        'parametro : mut_opt ID COLON tipo'
        linea, col = self._pos(p, 2)
        p[0] = ast.Param(p[2], p[4], p[1], linea, col)

    def p_retorno_opt(self, p):
        '''retorno_opt : ARROW tipo
                       | empty'''
        p[0] = p[2] if len(p) == 3 else None

    # --- Bloques -------------------------------------------------------

    def p_bloque(self, p):
        'bloque : LBRACE instrucciones RBRACE'
        linea, col = self._pos(p, 1)
        p[0] = ast.Block(p[2], linea, col)

    def p_bloque_error(self, p):
        'bloque : LBRACE error RBRACE'
        # Recuperación: un error que no se pudo arreglar dentro del bloque
        linea, col = self._pos(p, 1)
        p[0] = ast.Block([], linea, col)

    def p_bloque_vacio(self, p):
        'bloque : LBRACE RBRACE'
        linea, col = self._pos(p, 1)
        p[0] = ast.Block([], linea, col)

    # Las instrucciones vacías (un ';' suelto) devuelven None y se filtran.
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
                       | sentencia_match
                       | sentencia_for
                       | sentencia_break SEMI
                       | sentencia_continue SEMI
                       | sentencia_return SEMI'''
        p[0] = p[1]

    def p_instruccion_expresion(self, p):
        'instruccion : expresion SEMI'
        # saludar(10);   flag && saludar(10);
        p[0] = ast.ExprStmt(p[1], p[1].linea, p[1].columna)

    def p_sentencia_return(self, p):
        '''sentencia_return : RETURN expresion
                            | RETURN'''
        linea, col = self._pos(p, 1)
        p[0] = ast.Return(p[2] if len(p) == 3 else None, linea, col)

    def p_instruccion_error(self, p):
        'instruccion : error SEMI'
        # Recuperación en modo pánico: se descarta todo hasta el siguiente ';'
        p[0] = None

    def p_instruccion_vacia(self, p):
        'instruccion : SEMI'
        # Permite cosas como `};` o `;;` sin generar nodos
        p[0] = None

    # --- if / else if / else ------------------------------------------
    # No hay ambigüedad del "else colgante" porque los bloques siempre
    # llevan llaves.

    def p_sentencia_if(self, p):
        'sentencia_if : IF expresion bloque'
        self._revisar_condicion(p[2])
        linea, col = self._pos(p, 1)
        p[0] = ast.If(p[2], p[3], None, linea, col)

    def p_sentencia_if_else(self, p):
        '''sentencia_if : IF expresion bloque ELSE bloque
                        | IF expresion bloque ELSE sentencia_if'''
        self._revisar_condicion(p[2])
        linea, col = self._pos(p, 1)
        p[0] = ast.If(p[2], p[3], p[5], linea, col)

    # --- while ----------------------------------------------------------

    def p_sentencia_while(self, p):
        'sentencia_while : WHILE expresion bloque'
        self._revisar_condicion(p[2])
        linea, col = self._pos(p, 1)
        p[0] = ast.While(p[2], p[3], None, linea, col)

    def p_sentencia_while_etiqueta(self, p):
        'sentencia_while : LABEL COLON WHILE expresion bloque'
        self._revisar_condicion(p[4])
        linea, col = self._pos(p, 1)
        p[0] = ast.While(p[4], p[5], p[1], linea, col)

    # --- loop -----------------------------------------------------------

    def p_sentencia_loop(self, p):
        'sentencia_loop : LOOP bloque'
        linea, col = self._pos(p, 1)
        p[0] = ast.Loop(p[2], None, linea, col)

    def p_sentencia_loop_etiqueta(self, p):
        'sentencia_loop : LABEL COLON LOOP bloque'
        linea, col = self._pos(p, 1)
        p[0] = ast.Loop(p[4], p[1], linea, col)

    # --- for -----------------------------------------------------------
    #   for i in 0..10 { }      for i in 1..=n { }      for x in arreglo { }

    def p_sentencia_for(self, p):
        '''sentencia_for : FOR mut_opt ID IN iterable bloque
                         | LABEL COLON FOR mut_opt ID IN iterable bloque'''
        if len(p) == 7:
            etiqueta, mut, var, iterable, cuerpo, pos = None, p[2], p[3], p[5], p[6], 1
        else:
            etiqueta, mut, var, iterable, cuerpo, pos = p[1], p[4], p[5], p[7], p[8], 1
        linea, col = self._pos(p, pos)
        if iterable[0] == 'rango':
            _, inicio, fin, inclusivo = iterable
            p[0] = ast.For(var, mut, inicio, fin, inclusivo, None, cuerpo, etiqueta, linea, col)
        else:
            p[0] = ast.For(var, mut, None, None, False, iterable[1], cuerpo, etiqueta,
                           linea, col)

    def p_iterable_rango(self, p):
        '''iterable : expresion DOTDOT expresion
                    | expresion DOTDOTEQ expresion'''
        p[0] = ('rango', p[1], p[3], p[2] == '..=')

    def p_iterable_arreglo(self, p):
        'iterable : expresion'
        p[0] = ('arreglo', p[1])

    # --- match ---------------------------------------------------------
    #   match x {
    #       1 => println!("uno"),
    #       2 => { ... }
    #       _ => println!("otro"),
    #   }
    # La coma es obligatoria después de un brazo sin llaves, salvo en el
    # último (como en Rust). Después de un bloque { } es opcional.

    def p_sentencia_match(self, p):
        '''sentencia_match : MATCH expresion LBRACE brazos RBRACE
                           | MATCH expresion LBRACE brazos brazo_final RBRACE
                           | MATCH expresion LBRACE brazo_final RBRACE'''
        linea, col = self._pos(p, 1)
        if len(p) == 6:
            brazos = p[4] if isinstance(p[4], list) else [p[4]]
        else:
            brazos = p[4] + [p[5]]
        p[0] = ast.Match(p[2], brazos, linea, col)

    def p_brazos(self, p):
        '''brazos : brazos brazo
                  | brazo'''
        p[0] = p[1] + [p[2]] if len(p) == 3 else [p[1]]

    def p_brazo_bloque(self, p):
        '''brazo : patron FATARROW bloque
                 | patron FATARROW bloque COMMA'''
        p[0] = self._brazo(p[1], p[3])

    def p_brazo_simple(self, p):
        'brazo : patron FATARROW instruccion_brazo COMMA'
        p[0] = self._brazo(p[1], p[3])

    def p_brazo_final(self, p):
        'brazo_final : patron FATARROW instruccion_brazo'
        p[0] = self._brazo(p[1], p[3])

    def p_instruccion_brazo(self, p):
        '''instruccion_brazo : impresion
                             | asignacion
                             | sentencia_break
                             | sentencia_continue
                             | sentencia_return'''
        p[0] = p[1]

    def p_instruccion_brazo_expresion(self, p):
        'instruccion_brazo : expresion'
        p[0] = ast.ExprStmt(p[1], p[1].linea, p[1].columna)

    def p_patron(self, p):
        '''patron : INT
                  | FLOAT
                  | CHAR
                  | STRING
                  | TRUE
                  | FALSE'''
        linea, col = self._pos(p, 1)
        tipos = {'INT': 'i32', 'FLOAT': 'f64', 'CHAR': 'char', 'STRING': 'String',
                 'TRUE': 'bool', 'FALSE': 'bool'}
        tipo = tipos[p.slice[1].type]
        valor = (p[1] == 'true') if tipo == 'bool' else p[1]
        p[0] = ast.Literal(valor, tipo, linea, col)

    def p_patron_negativo(self, p):
        '''patron : MINUS INT
                  | MINUS FLOAT'''
        linea, col = self._pos(p, 1)
        p[0] = ast.Literal(-p[2], 'i32' if isinstance(p[2], int) else 'f64', linea, col)

    def p_patron_comodin(self, p):
        'patron : UNDERSCORE'
        p[0] = '_'

    def _brazo(self, patron, cuerpo):
        if patron == '_':
            return ast.MatchArm(None, cuerpo, True, cuerpo.linea, cuerpo.columna)
        return ast.MatchArm(patron, cuerpo, False, patron.linea, patron.columna)

    # --- break / continue --------------------------------------------
    # El semántico revisará que estén dentro de un ciclo y que la
    # etiqueta exista.

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
    #   x = 5;   x += 5;   x -= 5;   x *= 5;   x /= 5;   x %= 5;
    # El objetivo se guarda como Identifier; el semántico revisará que
    # la variable exista y sea `mut`.

    def p_asignacion(self, p):
        '''asignacion : primario ASSIGN expresion
                      | primario PLUS_ASSIGN expresion
                      | primario MINUS_ASSIGN expresion
                      | primario TIMES_ASSIGN expresion
                      | primario DIVIDE_ASSIGN expresion
                      | primario MOD_ASSIGN expresion'''
        # El objetivo puede ser una variable (x = 5) o un elemento de un
        # arreglo (matriz[1][2] = 7). Cualquier otra cosa no se puede asignar.
        objetivo = p[1]
        if not isinstance(objetivo, (ast.Identifier, ast.Index)):
            self.errores.agregar(SINTACTICO, "No se puede asignar un valor a esta expresión.",
                                 objetivo.linea, objetivo.columna)
        p[0] = ast.Assignment(objetivo, p[2], p[3], objetivo.linea, objetivo.columna)

    # --- println! ------------------------------------------------------
    #   println!();
    #   println!("texto");
    #   println!("a = {}, b = {}", a, b);

    def p_impresion_vacia(self, p):
        'impresion : PRINTLN LPAREN RPAREN'
        linea, col = self._pos(p, 1)
        p[0] = ast.Print("", [], [], linea, col)

    def p_impresion_una(self, p):
        'impresion : PRINTLN LPAREN expresion RPAREN'
        # Dos casos (los dos aparecen en el enunciado):
        #   println!("Hola {{}}")  -> el texto es el formato
        #   println!(edad)         -> se imprime el valor, como println!("{}", edad)
        #   println!("a" + b)      -> también se imprime el valor
        linea, col = self._pos(p, 1)
        expr = p[3]
        if getattr(expr, '_cadena_directa', False):
            p[0] = ast.Print(expr.valor, self._partes_formato(expr.valor), [], linea, col)
        else:
            p[0] = ast.Print("{}", [None], [expr], linea, col)

    def p_impresion_args(self, p):
        'impresion : PRINTLN LPAREN expresion COMMA lista_expresiones RPAREN'
        linea, col = self._pos(p, 1)
        formato = p[3]
        if not getattr(formato, '_cadena_directa', False):
            self.errores.agregar(
                SINTACTICO,
                "El primer argumento de println! con varios valores debe ser "
                "una cadena de formato, por ejemplo: println!(\"{} {}\", a, b).",
                formato.linea, formato.columna)
            p[0] = ast.Print("", [], [], linea, col)
            return
        p[0] = ast.Print(formato.valor, self._partes_formato(formato.valor),
                         p[5], linea, col)

    def p_lista_expresiones(self, p):
        '''lista_expresiones : lista_expresiones COMMA expresion
                             | expresion'''
        p[0] = p[1] + [p[3]] if len(p) == 4 else [p[1]]

    @staticmethod
    def _partes_formato(texto):
        """Separa el formato en textos y marcadores.
            "x = {}, y = {:?}"  ->  ['x = ', None, ', y = ', None]
        Como en Rust, '{{' y '}}' imprimen una llave literal."""
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

    # --- Tipos (los arreglos [T; N] se agregan en el paso 6) -----------

    def p_tipo(self, p):
        '''tipo : T_I32
                | T_F64
                | T_BOOL
                | T_CHAR
                | T_STRING'''
        p[0] = p[1]

    def p_tipo_vec(self, p):
        'tipo : ID LT tipo GT'
        # Vec<&str> / Vec<String>: arreglo dinámico (lo que devuelve split)
        if p[1] != 'Vec':
            self.errores.agregar(SINTACTICO, f"Tipo '{p[1]}' no reconocido.", *self._pos(p, 1))
        elif p[3].startswith('['):
            self.errores.agregar(SINTACTICO, "Vec solo puede contener valores simples "
                                 "(i32, f64, bool, char o String).", *self._pos(p, 1))
        p[0] = f"[{p[3]}]"

    def p_tipo_str(self, p):
        'tipo : AMP ID'
        # &str se trata igual que String
        if p[2] != 'str':
            self.errores.agregar(SINTACTICO, f"Tipo '&{p[2]}' no reconocido.", *self._pos(p, 2))
        p[0] = 'String'

    def p_tipo_arreglo(self, p):
        'tipo : LBRACKET tipo SEMI INT RBRACKET'
        # [i32; 3] y, por recursión, [[i32; 3]; 2], [[[f64; 2]; 2]; 2]...
        p[0] = f"[{p[2]}; {p[4]}]"

    # --- Expresiones -----------------------------------------------------
    # La gramática es ambigua a propósito: la tabla `precedence` decide
    # cómo agrupar. Así una sola regla cubre todos los operadores binarios.

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
        # La posición del nodo es la del operador (así lo pide el
        # enunciado en los errores de tipos: "Línea 7, Columna 24").
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
        # Se recuerda dónde estaba el '(' para poder reportar
        # "paréntesis alrededor de la condición" en if/while.
        # Empieza con '_' para que no aparezca en el árbol.
        p[0]._parentesis = self._pos(p, 1)

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
        # Marca para println!: un "texto" escrito tal cual es cadena de
        # formato; String::from("...") o una expresión no lo son.
        p[0]._cadena_directa = True

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

    def p_primario_arreglo(self, p):
        'primario : LBRACKET lista_expresiones RBRACKET'
        linea, col = self._pos(p, 1)
        p[0] = ast.ArrayLiteral(p[2], linea, col)

    def p_primario_arreglo_repetido(self, p):
        'primario : LBRACKET expresion SEMI INT RBRACKET'
        linea, col = self._pos(p, 1)
        p[0] = ast.ArrayRepeat(p[2], p[4], linea, col)

    def p_primario_indice(self, p):
        'primario : primario LBRACKET expresion RBRACKET'
        # La posición es la del inicio (numeros[5] -> la de "numeros"),
        # igual que el ejemplo del error 7 del enunciado.
        p[0] = ast.Index(p[1], p[3], p[1].linea, p[1].columna)

    def p_primario_slice(self, p):
        'primario : AMP primario LBRACKET expresion DOTDOT expresion RBRACKET'
        linea, col = self._pos(p, 1)
        p[0] = ast.Slice(p[2], p[4], p[6], linea, col)

    def p_primario_metodo(self, p):
        '''primario : primario DOT ID LPAREN lista_expresiones RPAREN
                    | primario DOT ID LPAREN RPAREN'''
        args = p[5] if len(p) == 7 else []
        p[0] = ast.MethodCall(p[1], p[3], args, p[1].linea, p[1].columna)

    def p_primario_llamada(self, p):
        '''primario : ID LPAREN lista_expresiones RPAREN
                    | ID LPAREN RPAREN'''
        linea, col = self._pos(p, 1)
        args = p[3] if len(p) == 5 else []
        p[0] = ast.Call(p[1], args, linea, col)

    # --- Producción vacía ----------------------------------------------

    def p_empty(self, p):
        'empty :'
        p[0] = None

    # --- Errores sintácticos (recuperación completa en el paso 8) -------

    def p_error(self, tok):
        """Se llama cuando el token `tok` no encaja (None = fin del archivo).

        1) Si el parser esperaba un ; ) ] o } se reporta "Se esperaba ';'."
           justo después del token anterior (como el enunciado, sección
           3.5.1), se INSERTA ese token y `tok` se vuelve a entregar
           después. El análisis sigue como si estuviera escrito.
        2) Si no, se reporta el token inesperado (y qué se esperaba, si son
           pocas opciones) y PLY entra en modo pánico: descarta tokens
           hasta poder usar una regla con `error` (hasta un ; o un })."""
        estado = self.parser.statestack[-1]
        esperados = set(self.parser.action[estado].keys())
        # `tok` todavía no fue aceptado: se saca de la lista de entregados
        if tok is not None and self.entregados and self.entregados[-1] is tok:
            self.entregados.pop()
        # El token anterior al que causó el error
        previo = self.entregados[-1] if self.entregados else None

        candidatos = [c for c in CIERRES if c in esperados]
        # Después de ; { o } la instrucción ya terminó: un ';' ahí solo sería
        # una instrucción vacía, así que lo que falta es otra cosa (p. ej. '}').
        if previo is not None and previo.type in ('SEMI', 'LBRACE', 'RBRACE'):
            candidatos = [c for c in candidatos if c != 'SEMI']
        # Si se puede cerrar el ( [ { abierto más interno, eso va primero
        # (el parser LALR a veces "espera" ) y ] a la vez en el mismo estado).
        abierto, en_match = self._abierto_mas_interno()
        if abierto is not None and CIERRE_DE[abierto] in candidatos:
            if 'SEMI' not in candidatos or abierto != 'LBRACE':
                candidatos.remove(CIERRE_DE[abierto])
                candidatos.insert(0, CIERRE_DE[abierto])
        # Un cierre que no corresponde al delimitador abierto no se inserta
        candidatos = [c for c in candidatos
                      if c == 'SEMI' or (abierto is not None and c == CIERRE_DE[abierto])]
        # Falta una coma: dentro de ( ) [ ] o de un match, el siguiente
        # token empieza un elemento nuevo:  f(a b)   [1 2]   1 => x  2 => y
        if (tok is not None and tok.type in INICIO_ELEMENTO and 'COMMA' in esperados
                and (abierto in ('LPAREN', 'LBRACKET') or (abierto == 'LBRACE' and en_match))):
            candidatos = ['COMMA']
        cierre = candidatos[0] if candidatos else None
        if cierre is not None and previo is not None:
            clave = (tok.lexpos if tok is not None else ('fin', len(self.insertados)), cierre)
            if clave not in self.insertados and len(self.insertados) < 500:
                self.insertados.add(clave)
                linea, col = self._despues_de(previo)
                if tok is None:
                    if cierre not in self.eof_reportados:    # una vez por tipo
                        self.eof_reportados.add(cierre)
                        self._error_esperado(cierre, linea, col)
                else:
                    self._error_esperado(cierre, linea, col)
                    self.pendientes.append(tok)              # se entrega después
                self.parser.errok()
                nuevo = self._token_sintetico(cierre, previo)
                self._registrar(nuevo)
                return nuevo

        # ---- Error general: se reporta y se recupera en modo pánico ----
        if tok is None:
            linea, col = self._despues_de(previo) if previo is not None else (1, 1)
            self.errores.agregar(SINTACTICO, "Fin de archivo inesperado.", linea, col)
            return
        texto = self.codigo[tok.lexpos:getattr(tok, '_fin', tok.lexpos + 1)] or str(tok.value)
        opciones = sorted({NOMBRES_TOKEN.get(e, f"'{e.lower()}'") for e in esperados
                           if e not in ('error', '$end')})
        if {'INT', 'ID', 'LPAREN'} <= esperados:
            mensaje = f"Se esperaba una expresión, pero se encontró '{texto}'."
        elif {'T_I32', 'T_F64', 'T_STRING'} <= esperados:
            mensaje = f"Se esperaba un tipo (i32, f64, bool, char, String o [T; N]), " \
                      f"pero se encontró '{texto}'."
        elif 0 < len(opciones) <= 4:
            lista = ', '.join(opciones[:-1]) + (' o ' if len(opciones) > 1 else '') + opciones[-1]
            mensaje = f"Se esperaba {lista}, pero se encontró '{texto}'."
        else:
            mensaje = f"Token inesperado '{texto}'."
        self.errores.agregar(SINTACTICO, mensaje, tok.lineno,
                             self.lexer.find_column(tok.lexpos))

    def _error_esperado(self, cierre, linea, columna):
        self.errores.agregar(SINTACTICO, f"Se esperaba '{SIMBOLO[cierre]}'.", linea, columna)

    def _despues_de(self, tok):
        """(línea, columna) de la posición justo después de un token."""
        pos = getattr(tok, '_fin', tok.lexpos)
        return self.codigo.count('\n', 0, pos) + 1, self.lexer.find_column(pos)

    def _token_sintetico(self, tipo, previo):
        """Token insertado por la recuperación (no está en el código)."""
        t = lex.LexToken()
        t.type = tipo
        t.value = SIMBOLO[tipo]
        t.lexpos = getattr(previo, '_fin', previo.lexpos)
        t.lineno = self.codigo.count('\n', 0, t.lexpos) + 1
        t._fin = t.lexpos
        t.lexer = self.lexer.lexer
        return t
