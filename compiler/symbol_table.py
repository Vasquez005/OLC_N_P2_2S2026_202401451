"""
Tabla de símbolos de OxigenNative.

Guarda la información de cada identificador declarado (variables,
parámetros y funciones) y maneja los ámbitos (scopes) anidados.

Además decide DÓNDE vive cada variable en memoria: le asigna un
`offset` dentro del marco de pila (stack frame) de su función. El
generador de ARM64 solo lee ese número:

        let a = 10;   ->  offset -8   ->  str x0, [x29, #-8]
        let b = 20;   ->  offset -16  ->  str x0, [x29, #-16]

Organización:
    Symbol       un identificador (variable, parámetro o función)
    Scope        un ámbito: diccionario nombre -> Symbol + puntero al padre
    SymbolTable  la pila de ámbitos + lista de todos los símbolos (reporte)
"""

# Cada valor ocupa 8 bytes en la pila: i32 y bool se guardan en un
# registro de 64 bits, f64 ocupa 8 bytes, y String guarda un puntero.
TAMANO_SLOT = 8

# Categorías (columna "Categoría" del reporte)
VARIABLE = "Variable"
PARAMETRO = "Parámetro"
FUNCION = "Función"

# Valores por defecto según la tabla de tipos
VALOR_POR_DEFECTO = {
    'i32': 0,
    'f64': 0.0,
    'bool': False,
    'char': '\0',
    'String': "",
}


class Symbol:
    def __init__(self, nombre, categoria, tipo, linea, columna, ambito,
                 mutable=False, valor=None):
        self.nombre = nombre
        self.categoria = categoria  # VARIABLE, PARAMETRO o FUNCION
        self.tipo = tipo            # 'i32', 'f64', ... (en funciones: tipo de retorno)
        self.linea = linea
        self.columna = columna
        self.ambito = ambito        # nombre del ámbito, p. ej. 'main > while'
        self.mutable = mutable
        self.valor = valor          # valor inicial conocido (solo para el reporte)

        # Variables y parámetros: posición respecto a x29 (siempre negativa)
        self.offset = None

        # Funciones
        self.params = []            # list[Symbol] de los parámetros
        self.tipos_params = []      # tipos de los parámetros (para revisar llamadas)
        self.tamano_frame = 0       # bytes que reserva la función (múltiplo de 16)

    def valor_reporte(self):
        if self.categoria == FUNCION or self.valor is None:
            return '---'
        if self.tipo == 'String':
            return f'"{self.valor}"'
        if self.tipo == 'char':
            return f"'{self.valor}'" if self.valor != '\0' else "'\\0'"
        if self.tipo == 'bool':
            return 'true' if self.valor else 'false'
        return str(self.valor)

    def to_dict(self, numero):
        """Fila del reporte de tabla de símbolos"""
        return {
            "no": numero,
            "identificador": self.nombre,
            "categoria": self.categoria,
            "tipo": self.tipo if self.tipo else "()",
            "ambito": self.ambito,
            "linea": self.linea,
            "columna": self.columna,
            "valor": self.valor_reporte(),
        }

    def __repr__(self):
        extra = f" offset={self.offset}" if self.offset is not None else ""
        return f"<{self.categoria} {self.nombre}: {self.tipo}{extra}>"


class Scope:
    def __init__(self, nombre, padre=None):
        self.nombre = nombre
        self.padre = padre          # Scope que lo contiene (None = global)
        self.simbolos = {}          # nombre -> Symbol

    def buscar_local(self, nombre):
        """Solo en este ámbito (para detectar redeclaraciones)."""
        return self.simbolos.get(nombre)

    def buscar(self, nombre):
        """En este ámbito y, si no está, en los padres hacia afuera."""
        scope = self
        while scope is not None:
            if nombre in scope.simbolos:
                return scope.simbolos[nombre]
            scope = scope.padre
        return None


class SymbolTable:
    def __init__(self):
        self.global_scope = Scope("Global")
        self.actual = self.global_scope
        self.todos = []             # todos los símbolos en orden (para el reporte)

        self.funcion_actual = None  # Symbol de la función que se analiza
        self._bytes_usados = 0      # espacio ocupado en el marco de esa función

    # ------------------------------------------------------------------
    # Ámbitos
    # ------------------------------------------------------------------

    def abrir_scope(self, nombre):
        """Cada bloque { } abre un ámbito. El nombre es solo informativo
        para el reporte: 'main', 'main > if', 'main > while > if'..."""
        if self.actual is not self.global_scope:
            nombre = f"{self.actual.nombre} > {nombre}"
        self.actual = Scope(nombre, self.actual)
        return self.actual

    def cerrar_scope(self):
        self.actual = self.actual.padre

    def buscar(self, nombre):
        return self.actual.buscar(nombre)

    def buscar_local(self, nombre):
        return self.actual.buscar_local(nombre)

    # ------------------------------------------------------------------
    # Funciones
    # ------------------------------------------------------------------

    def declarar_funcion(self, nombre, tipo_retorno, linea, columna):
        """Registra una función en el ámbito global.
        Devuelve None si ya existía (el semántico reporta el error)."""
        if self.global_scope.buscar_local(nombre):
            return None
        sym = Symbol(nombre, FUNCION, tipo_retorno, linea, columna, "Global")
        self.global_scope.simbolos[nombre] = sym
        self.todos.append(sym)
        return sym

    def entrar_funcion(self, sym_funcion):
        """Empieza el cuerpo de una función: nuevo ámbito y marco vacío."""
        self.funcion_actual = sym_funcion
        self._bytes_usados = 0
        self.abrir_scope(sym_funcion.nombre)

    def salir_funcion(self):
        """Termina la función y guarda cuánto espacio necesita su marco.
        ARM64 exige que sp esté alineado a 16 bytes."""
        self.cerrar_scope()
        self.funcion_actual.tamano_frame = (self._bytes_usados + 15) // 16 * 16
        self.funcion_actual = None

    # ------------------------------------------------------------------
    # Variables y parámetros
    # ------------------------------------------------------------------

    def declarar_variable(self, nombre, tipo, mutable, linea, columna,
                          valor=None, categoria=VARIABLE, tamano=TAMANO_SLOT):
        """Declara una variable en el ámbito actual y le asigna espacio.

        Sombreado (shadowing): si ya existe una variable con ese nombre en
        el mismo ámbito, la nueva la reemplaza en el diccionario, pero
        recibe su PROPIO espacio en la pila (puede ser de otro tipo). La
        anterior sigue en `todos` para que aparezca en el reporte.

        `tamano` permitirá reservar más espacio para arreglos
        """
        sym = Symbol(nombre, categoria, tipo, linea, columna,
                     self.actual.nombre, mutable, valor)
        self._bytes_usados += tamano
        sym.offset = -self._bytes_usados
        self.actual.simbolos[nombre] = sym
        self.todos.append(sym)
        if categoria == PARAMETRO and self.funcion_actual is not None:
            self.funcion_actual.params.append(sym)
        return sym

    # ------------------------------------------------------------------
    # Reporte
    # ------------------------------------------------------------------

    def reporte(self):
        return [s.to_dict(i + 1) for i, s in enumerate(self.todos)]