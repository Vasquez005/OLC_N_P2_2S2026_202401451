"""
Analizador semántico
 
Recorre el AST y se hace tres cosas:
 
  1. Llena la tabla de símbolos (ámbitos, tipos y offsets en la pila).
  2. Se calcula el tipo de cada expresión y lo ANOTA en el nodo:
         nodo.tipo_resultado = 'i32' | 'f64' | 'bool' | 'char' | 'String' | 'None'
     Los usos de variables quedan enlazados a su símbolo:
         Identifier.simbolo, VarDecl.simbolo, Assignment.simbolo
  3. Registra los errores semánticos con línea y columna.
 
El generador de ARM64 recorrerá este mismo AST ya anotado.
 
Resiliencia: un error no detiene el análisis. Una
expresión inválida recibe el tipo 'None' (así lo muestra el enunciado:
`println!(resultado3)` imprime None) y las instrucciones inválidas se
marcan con `nodo.omitir = True` para que el generador las salte.
 
Uso:
    tabla = Semantic(errores).analizar(arbol)
"""

from compiler import ast_nodes as ast
from compiler.errors import ErrorList, SEMANTICO
from compiler.symbol_table import SymbolTable, VALOR_POR_DEFECTO

# ----------------------------------------------------------------------
# Tipos
# ----------------------------------------------------------------------
I32, F64, BOOL, CHAR, STRING = 'i32', 'f64', 'bool', 'char', 'String'
 
# Tipo de una expresión con error. Se propaga sin generar más errores
# (si `a + nombre` ya falló, `(a + nombre) * 2` no vuelve a reportar).
ERROR = 'None'
 
I32_MIN, I32_MAX = -2**31, 2**31 - 1 # multiplicamos por 2**31 para que el resultado sea un entero de Python, no un long

# ----------------------------------------------------------------------
# Tablas de tipos resultantes
# Clave: (tipo_izq, tipo_der) -> tipo resultante.
# Si la combinación no está en la tabla, la operación no es válida.
# ----------------------------------------------------------------------
_NUMERICAS = {
    (I32, I32): I32,
    (I32, F64): F64,     # promoción: el i32 se convierte a f64
    (F64, I32): F64,
    (F64, F64): F64,
}
 
ARITMETICAS = {
    '+': {**_NUMERICAS, (STRING, STRING): STRING},       # ** dict(_NUMERICAS) para que no se modifique el original y agregar la concatenación de strings
    '-': dict(_NUMERICAS), # dict de _NUMERICAS para que no se modifique el original
    '*': {**_NUMERICAS, (I32, STRING): STRING, (STRING, I32): STRING}, # **dict de _NUMERICAS para que no se modifique el original y agregar la multiplicación de strings
    '/': dict(_NUMERICAS), 
    '%': dict(_NUMERICAS),
}
 
# Igualdad (== !=) y orden (< > <= >=) aceptan las mismas combinaciones
_COMPARABLES = {
    (I32, I32), (I32, F64), (F64, I32), (F64, F64),
    (I32, CHAR), (CHAR, I32), (CHAR, CHAR),
    (BOOL, BOOL),
    (STRING, STRING),
}
RELACIONALES = {'==', '!=', '<', '>', '<=', '>='}
LOGICOS = {'&&', '||'}
 
# Operador compuesto -> operador aritmético que aplica
COMPUESTOS = {'+=': '+', '-=': '-', '*=': '*', '/=': '/', '%=': '%'}

def asignable(destino, origen):
    """¿Se puede guardar un valor de tipo `origen` en una variable `destino`?
    Se permite la conversión i32 -> f64 (el generador hará la conversión)."""

    return destino == origen or (destino == F64 and origen == I32)

class Semantic:

    def __init__(self, errores: None): #inicializamos con errores vacios, para que se pueda usar el analizador sin errores
        self.errores = errores if errores is not None else ErrorList()
        self.tabla = SymbolTable()
        self.ciclos = []  # pila de nodos While y For para validar break/continue

    # ------------------------------------------------------------------
    # Punto de entrada
    # ------------------------------------------------------------------
 
    def analizar(self, programa):
        if programa is not None:
            self.visitar(programa)
        return self.tabla

    def visitar(self, nodo):
        """Despacha a visit_<NombreDeClase>. Ej: un While -> visit_While."""
        metodo = getattr(self, f"visit_{type(nodo).__name__}", None)
        if metodo is None:
            raise NotImplementedError(
                f"El semántico aún no maneja nodos {type(nodo).__name__}")
        return metodo(nodo)
 
    def error(self, nodo, mensaje):
        self.errores.agregar(SEMANTICO, mensaje, nodo.linea, nodo.columna)


    # ==================================================================
    # Programa y funciones
    # ==================================================================
 
    def visit_Program(self, nodo):
        # Primera pasada: registrar TODAS las funciones antes de analizar
        # los cuerpos
        for fn in nodo.funciones:
            sym = self.tabla.declarar_funcion(fn.nombre, fn.tipo_retorno,
                                              fn.linea, fn.columna)
            if sym is None:
                self.error(fn, f"La función '{fn.nombre}' ya fue declarada.")
                fn.omitir = True
            else:
                fn.simbolo = sym
 
        main = self.tabla.global_scope.buscar_local('main')
        if main is None:
            self.errores.agregar(SEMANTICO,
                                 "No se encontró la función 'main'.", 1, 1)

        # Segunda pasada: analizar cada cuerpo
        for fn in nodo.funciones:
            if not getattr(fn, 'omitir', False):
                self.visitar(fn)

    def visit_Function(self, nodo):
        self.tabla.entrar_funcion(nodo.simbolo)
        # Los parámetros se declaran aquí en el paso 5.
        # El cuerpo usa el ámbito de la función (no abre otro).
        self.visitar_instrucciones(nodo.cuerpo)
        self.tabla.salir_funcion()

    # ==================================================================
    # Bloques
    # ==================================================================
 
    def visitar_instrucciones(self, bloque):
        for ins in bloque.instrucciones:
            self.visitar(ins)
 
    def visitar_bloque(self, bloque, nombre_ambito):
        """Bloque de un if/while/loop: abre su propio ámbito."""
        self.tabla.abrir_scope(nombre_ambito)
        self.visitar_instrucciones(bloque)
        self.tabla.cerrar_scope()
 
    def visit_Block(self, nodo):
        self.visitar_bloque(nodo, 'bloque')


    # ==================================================================
    # Declaraciones y asignaciones
    # ==================================================================
 
    def visit_VarDecl(self, nodo):
        # 1) Primero se analiza el valor, ANTES de declarar la variable.
        #    Así en `let x = x + 1;` (sombreado) la `x` de la derecha es la anterior y no la nueva
        tipo_valor = self.visitar(nodo.valor) if nodo.valor is not None else None
 
        # 2) Decidir el tipo de la variable
        nodo.usar_defecto = False
        if nodo.tipo is not None:
            tipo = nodo.tipo
            if tipo_valor is None:
                nodo.usar_defecto = True          # let x: i32;  -> 0
            elif tipo_valor != ERROR and not asignable(tipo, tipo_valor):
                self.error(nodo.valor,
                           f"No es posible asignar un valor de tipo {tipo_valor} "
                           f"a una variable de tipo {tipo}.")
                nodo.usar_defecto = True          # se guarda el valor por defecto
            elif tipo_valor == ERROR:
                nodo.usar_defecto = True
        else:
            if tipo_valor is None:
                self.error(nodo, f"No es posible inferir el tipo de la variable "
                                 f"'{nodo.nombre}': indique un tipo o un valor inicial.")
                tipo = ERROR
            else:
                tipo = tipo_valor                 # inferido (puede ser 'None')
 
        # 3) Valor que se muestra en el reporte de la tabla de símbolos
        if nodo.usar_defecto:
            valor = VALOR_POR_DEFECTO.get(tipo)
        elif isinstance(nodo.valor, ast.Literal):
            valor = nodo.valor.valor
        else:
            valor = None                          # se calcula al ejecutar: '---'
 
        # 4) Declarar (permite sombreado, ver symbol_table.py)
        nodo.simbolo = self.tabla.declarar_variable(
            nodo.nombre, tipo, nodo.mutable, nodo.linea, nodo.columna, valor)
 
    def visit_Assignment(self, nodo):
        nodo.omitir = False
        tipo_valor = self.visitar(nodo.valor)
 
        # Por ahora el objetivo siempre es un Identifier (arreglos: paso 6)
        objetivo = nodo.objetivo
        sym = self.tabla.buscar(objetivo.nombre)
        if sym is None:
            self.error(objetivo, f"La variable '{objetivo.nombre}' no ha sido declarada.")
            nodo.omitir = True
            return
        objetivo.simbolo = sym
        objetivo.tipo_resultado = sym.tipo
        nodo.simbolo = sym
 
        if not sym.mutable:
            self.error(nodo, f"No es posible modificar la variable '{sym.nombre}' "
                             f"porque fue declarada como inmutable.")
            nodo.omitir = True
            return
 
        if sym.tipo == ERROR or tipo_valor == ERROR:
            nodo.omitir = True
            return
 
        # x += v  se valida como  x = x + v
        if nodo.op in COMPUESTOS:
            op = COMPUESTOS[nodo.op]
            resultado = ARITMETICAS[op].get((sym.tipo, tipo_valor))
            if resultado is None:
                self.error(nodo, f"No es posible aplicar el operador '{nodo.op}' "
                                 f"entre los tipos {sym.tipo} y {tipo_valor}.")
                nodo.omitir = True
                return
            tipo_valor = resultado
 
        if not asignable(sym.tipo, tipo_valor):
            self.error(nodo.valor,
                       f"Tipos incompatibles. No es posible utilizar un valor de tipo "
                       f"{tipo_valor} donde se esperaba un valor de tipo {sym.tipo}.")
            nodo.omitir = True

    # ==================================================================
    # println!
    # ==================================================================
 
    def visit_Print(self, nodo):
        for arg in nodo.args:
            self.visitar(arg)       # anota tipos; un 'None' se imprime como None
        esperados = nodo.num_marcadores()
        if esperados != len(nodo.args):
            self.error(nodo, f"println! esperaba {esperados} argumento(s) según "
                             f"el formato, pero recibió {len(nodo.args)}.")


    # ==================================================================
    # Control de flujo
    # ==================================================================
 
    def revisar_condicion(self, cond, sentencia):
        tipo = self.visitar(cond)
        if tipo not in (BOOL, ERROR):
            self.error(cond, f"La condición del '{sentencia}' debe ser de tipo bool, "
                             f"pero es de tipo {tipo}.")
 
    def visit_If(self, nodo):
        self.revisar_condicion(nodo.condicion, 'if')
        self.visitar_bloque(nodo.entonces, 'if')
        if isinstance(nodo.sino, ast.If):
            self.visitar(nodo.sino)               # else if
        elif nodo.sino is not None:
            self.visitar_bloque(nodo.sino, 'else')
 
    def visit_While(self, nodo):
        self.revisar_etiqueta_nueva(nodo)
        self.revisar_condicion(nodo.condicion, 'while')
        self.ciclos.append(nodo.etiqueta)
        self.visitar_bloque(nodo.cuerpo, 'while')
        self.ciclos.pop()
 
    def visit_Loop(self, nodo):
        self.revisar_etiqueta_nueva(nodo)
        self.ciclos.append(nodo.etiqueta)
        self.visitar_bloque(nodo.cuerpo, 'loop')
        self.ciclos.pop()
 
    def revisar_etiqueta_nueva(self, nodo):
        if nodo.etiqueta is not None and nodo.etiqueta in self.ciclos:
            self.error(nodo, f"La etiqueta '{nodo.etiqueta} ya está en uso "
                             f"por un ciclo que contiene a este.")
 
    def revisar_salto(self, nodo, palabra):
        nodo.omitir = False
        if not self.ciclos:
            self.error(nodo, f"'{palabra}' solo puede usarse dentro de un ciclo.")
            nodo.omitir = True
        elif nodo.etiqueta is not None and nodo.etiqueta not in self.ciclos:
            self.error(nodo, f"La etiqueta '{nodo.etiqueta} no ha sido declarada.")
            nodo.omitir = True
 
    def visit_Break(self, nodo):
        self.revisar_salto(nodo, 'break')
 
    def visit_Continue(self, nodo):
        self.revisar_salto(nodo, 'continue')


    # ==================================================================
    # Expresiones: cada visit_ devuelve el tipo y lo anota en el nodo
    # ==================================================================
 
    def visit_Literal(self, nodo):
        tipo = nodo.tipo
        if tipo == I32 and not (I32_MIN <= nodo.valor <= I32_MAX):
            self.error(nodo, f"El valor {nodo.valor} está fuera del rango de i32.")
            tipo = ERROR
        nodo.tipo_resultado = tipo
        return tipo
 
    def visit_Identifier(self, nodo):
        sym = self.tabla.buscar(nodo.nombre)
        if sym is None:
            self.error(nodo, f"La variable '{nodo.nombre}' no ha sido declarada.")
            nodo.simbolo = None
            nodo.tipo_resultado = ERROR
        else:
            nodo.simbolo = sym      # el generador lee sym.offset de aquí
            nodo.tipo_resultado = sym.tipo
        return nodo.tipo_resultado
 
    def visit_UnaryOp(self, nodo):
        tipo = self.visitar(nodo.expr)
        if tipo == ERROR:
            resultado = ERROR
        elif nodo.op == '-' and tipo in (I32, F64):
            resultado = tipo
        elif nodo.op == '!' and tipo == BOOL:
            resultado = BOOL
        else:
            self.error(nodo, f"No es posible aplicar el operador '{nodo.op}' "
                             f"al tipo {tipo}.")
            resultado = ERROR
        nodo.tipo_resultado = resultado
        return resultado
 
    def visit_BinaryOp(self, nodo):
        izq = self.visitar(nodo.izq)
        der = self.visitar(nodo.der)
        op = nodo.op
 
        if izq == ERROR or der == ERROR:
            resultado = ERROR                     # ya se reportó antes
        elif op in ARITMETICAS:
            resultado = ARITMETICAS[op].get((izq, der), ERROR)
        elif op in RELACIONALES:
            resultado = BOOL if (izq, der) in _COMPARABLES else ERROR
        elif op in LOGICOS:
            resultado = BOOL if (izq, der) == (BOOL, BOOL) else ERROR
        else:
            resultado = ERROR
 
        if resultado == ERROR and izq != ERROR and der != ERROR:
            self.error(nodo, f"No es posible aplicar el operador '{op}' "
                             f"entre los tipos {izq} y {der}.")
 
        # División o módulo entre la constante 0
        if (op in ('/', '%') and isinstance(nodo.der, ast.Literal)
                and nodo.der.valor == 0 and resultado == I32):
            self.error(nodo, "División entre cero.")
 
        nodo.tipo_resultado = resultado
        return resultado
 

