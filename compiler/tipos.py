"""
Utilidades para los tipos de arreglo de OxigenNative.

Hay dos clases de arreglo, y los dos se escriben como texto:

  ESTÁTICO  "[i32; 3]", "[[f64; 2]; 4]"...
      El tamaño es parte del tipo y se conoce al compilar.
      Memoria (row-major, ver manual técnico): UN bloque contiguo en el
      heap con 8 bytes por valor básico. La matriz [[1, 2, 3], [4, 5, 6]]
      queda como  1 2 3 4 5 6  y m[i][j] está en  base + (i * 3 + j) * 8.

  DINÁMICO  "[String]"   (lo que devuelve texto.split(...); en el código
      fuente se puede escribir Vec<&str> o Vec<String>)
      El tamaño solo se conoce al ejecutar, así que el bloque guarda el
      largo al inicio:   [ largo | e0 | e1 | ... ]   (8 bytes cada uno).
      El elemento i está en  base + 8 + i * 8.
"""

TAMANO_BASICO = 8   # bytes de cada valor básico (i32, f64, bool, char, puntero)


def es_arreglo(tipo):
    """Cualquier arreglo, estático o dinámico."""
    return isinstance(tipo, str) and tipo.startswith('[')


def es_dinamico(tipo):
    """"[String]": arreglo cuyo largo se guarda en memoria."""
    return es_arreglo(tipo) and ';' not in tipo


def es_estatico(tipo):
    return es_arreglo(tipo) and not es_dinamico(tipo)


def partes(tipo):
    """"[[i32; 3]; 2]" -> ("[i32; 3]", 2)      "[String]" -> ("String", None)
    En un estático el separador de la dimensión exterior es el ÚLTIMO "; "."""
    interior = tipo[1:-1]
    if es_dinamico(tipo):
        return interior, None
    elemento, longitud = interior.rsplit('; ', 1)
    return elemento, int(longitud)


def elemento(tipo):
    return partes(tipo)[0]


def longitud(tipo):
    """Largo de un arreglo estático (None si es dinámico)."""
    return partes(tipo)[1]


def tipo_base(tipo):
    """Tipo de los valores guardados: "[[i32; 3]; 2]" -> "i32"."""
    while es_estatico(tipo):
        tipo = elemento(tipo)
    return tipo


def total_elementos(tipo):
    """Cantidad de valores básicos de un estático: "[[i32; 3]; 2]" -> 6.
    Un arreglo dinámico guardado dentro de otro ocupa 1 (su puntero)."""
    total = 1
    while es_estatico(tipo):
        tipo, n = partes(tipo)
        total *= n
    return total


def tamano(tipo):
    """Bytes que ocupa un valor de este tipo DENTRO de un arreglo
    (un estático se guarda completo; lo demás, en 8 bytes)."""
    return total_elementos(tipo) * TAMANO_BASICO


def nombre_tipo(tipo):
    """Texto que devuelve typeof(): igual al tipo, salvo los dinámicos,
    que se muestran como en Rust."""
    if es_dinamico(tipo):
        return f"Vec<{elemento(tipo)}>"
    return tipo
