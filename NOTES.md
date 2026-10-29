# NOTAS

ACA SE ANOTARAN QUE ARCHIVOS Y QUE NUMEROS DE LINEAS HAY QUE MODIFICAR, SIEMPRE TOMANDO COMO BASE LOS ARCHIVOS EXISTENTES.

### Ejemplo:

# Cambio: Modificar los arreglos de una dimension para que el indice inicie en 1

### compiler/semantic.py
```bash
587  nodo.desde_uno = False  


597  # Un arreglo es de UNA dimensión si sus elementos no son arreglos
598  # ([i32; 5]) y no es la fila de una matriz (la m[i] de m[i][j]).
599  # Solo en esos arreglos el índice empieza en 1; las matrices siguen en 0.
600  nodo.desde_uno = (not es_arreglo(elemento(tipo_base))
601                    and not isinstance(nodo.base, ast.Index))


602  constante = constante_entera(nodo.indice)
603  if constante is not None:
604      if nodo.desde_uno:
605          constante -= 1          # a[1] es la posición 0 de la memoria
606      # Desde aquí `constante` es la posición real (desde 0), así que la
607      # misma revisión de límites sirve para los dos casos.
     ...
611      if constante < 0 or (maximo is not None and constante >= maximo):
612          self.error(nodo, "Índice fuera de los límites del arreglo.")
     ...
614          nodo.indice_constante = constante   # el generador usa la posición real


636  # En un arreglo de una dimensión los límites también cuentan desde 1:
637  # &a[1..3] toma a[1] y a[2], que son las posiciones reales 0..2.
638  if not es_arreglo(elemento(tipo_base)) and not isinstance(nodo.base, ast.Index):
639      desde, hasta = desde - 1, hasta - 1

```


## compiler/codegen/arm64.py
```bash
895  self.visitar(nodo.indice)                   # x0 = índice
896  if nodo.desde_uno:                          # arreglo de una dimensión:
897      self.emit("sub x0, x0, #1", "índice desde 1: a[1] es la posición 0")
898      # Desde aquí x0 es la posición real, así que la revisión de
899      # límites de abajo no cambia: a[0] queda en -1 y da error.

910  self.emit("mov x2, x0")
911  if nodo.desde_uno:                          # el mensaje muestra el índice que
912      self.emit("add x2, x2, #1", "escribió el usuario, no la posición")
```

## compiler/reports.py
```bash
912                  'desde_uno'}   # dato interno del índice desde 1, no se dibuja en el AST
```

---

# Cambio: Intercambiar precedencia de + con *, y de && con ||

Solo se toca la tabla `precedence` del parser. En PLY, mientras más ABAJO
está una fila, MÁS precedencia tiene. La tabla decide cómo se arma el AST;
el semántico y el generador ARM64 solo recorren ese árbol, así que no se
cambia nada más.

### compiler/parser.py
```bash
# ANTES (líneas 77-81)
77          ('left', 'OR'),
78          ('left', 'AND'),
79          ('nonassoc', 'EQ', 'NE', 'LT', 'GT', 'LE', 'GE'),
80          ('left', 'PLUS', 'MINUS'),
81          ('left', 'TIMES', 'DIVIDE', 'MOD'),

# DESPUÉS (mismas líneas: solo se intercambian OR<->AND y PLUS<->TIMES)
77          ('left', 'AND'),                    # && ahora es el más débil (antes era ||)
78          ('left', 'OR'),                     # || ahora pesa más que && (antes era al revés)
79          ('nonassoc', 'EQ', 'NE', 'LT', 'GT', 'LE', 'GE'),
80          ('left', 'TIMES', 'MINUS'),         # * bajó al nivel donde estaba +
81          ('left', 'PLUS', 'DIVIDE', 'MOD'),  # + subió al nivel donde estaba *
```

### Prueba: tests/09_precedencia.rs
| Expresión                  | Antes | Ahora                          |
|----------------------------|-------|--------------------------------|
| `2 + 3 * 4`                | 14    | 20 → `(2+3)*4`                 |
| `2 * 3 + 4`                | 10    | 14 → `2*(3+4)`                 |
| `10 - 2 + 3`               | 11    | 5  → `10-(2+3)`                |
| `8 / 2 * 3`                | 12    | 12 (sin cambio)                |
| `true \|\| false && false` | true  | false → `(true\|\|false)&&false` |
| `false && true \|\| true`  | true  | false → `false&&(true\|\|true)`  |

Salida esperada: `20 14 5 12 false false`

### Nota para explicarlo
- Se tomó literal: solo `+` y `*` cambian de lugar; `-`, `/` y `%` se quedan.
- Si piden intercambiar los GRUPOS completos, las líneas 80-81 serían:
  `('left', 'TIMES', 'DIVIDE', 'MOD'),` y luego `('left', 'PLUS', 'MINUS'),`
- No hay tablas guardadas que borrar: el parser usa `write_tables=False`.
