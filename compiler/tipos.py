"""
Utilidades para los tipos de arreglo de OxigenNative.

Un tipo de arreglo se guarda como texto, igual que en el código fuente:
    "[i32; 3]"            arreglo de 3 i32
    "[[i32; 3]; 2]"       matriz de 2 filas x 3 columnas
    "[[[f64; 2]; 2]; 2]"  cubo de 2 x 2 x 2

Memoria (row-major, ver manual técnico):
    Todo arreglo, tenga las dimensiones que tenga, ocupa UN bloque
    contiguo en el heap con 8 bytes por elemento básico. La matriz
    [[1, 2, 3], [4, 5, 6]] queda como  1 2 3 4 5 6  y el elemento
    m[i][j] está en  base + (i * 3 + j) * 8.
"""

TAMANO_BASICO = 8   # bytes de cada valor básico (i32, f64, bool, char, puntero)


def es_arreglo(tipo):
    return isinstance(tipo, str) and tipo.startswith('[')


def partes(tipo):
    """"[[i32; 3]; 2]" -> ("[i32; 3]", 2).
    El separador de la dimensión exterior es siempre el ÚLTIMO "; "."""
    interior = tipo[1:-1]
    elemento, longitud = interior.rsplit('; ', 1)
    return elemento, int(longitud)


def elemento(tipo):
    return partes(tipo)[0]


def longitud(tipo):
    return partes(tipo)[1]


def tipo_base(tipo):
    """Tipo de los valores guardados: "[[i32; 3]; 2]" -> "i32"."""
    while es_arreglo(tipo):
        tipo = elemento(tipo)
    return tipo


def total_elementos(tipo):
    """Cantidad de valores básicos: "[[i32; 3]; 2]" -> 6."""
    total = 1
    while es_arreglo(tipo):
        tipo, n = partes(tipo)
        total *= n
    return total


def tamano(tipo):
    """Bytes que ocupa un valor de este tipo dentro de un arreglo."""
    return total_elementos(tipo) * TAMANO_BASICO
