"""
Prueba de la tabla de símbolos SIN parser: simula a mano lo que hará
el semántico al recorrer este programa.

    fn sumar(a: i32, b: i32) -> i32 {
        let r: i32 = a + b;
    }
    fn main() {
        let x: i32 = 10;
        let mut nombre = String::from("Ana");
        if x > 5 {
            let y: f64 = 2.5;      // solo existe dentro del if
        }
        let x: f64 = 3.14;          // sombreado de x
        let activo: bool;           // sin valor -> por defecto false
    }

Ejecutar desde la raíz del proyecto:
    python -m tests.prueba_tabla
"""
from compiler.symbol_table import SymbolTable, PARAMETRO, VALOR_POR_DEFECTO

t = SymbolTable()

# Primera pasada: registrar todas las funciones (se pueden llamar
# antes de estar definidas, como en Rust)
f_sumar = t.declarar_funcion('sumar', 'i32', 1, 1)
f_main = t.declarar_funcion('main', None, 4, 1)
print("¿main duplicada?:", t.declarar_funcion('main', None, 20, 1))  # None = ya existe

# --- fn sumar ---
t.entrar_funcion(f_sumar)
t.declarar_variable('a', 'i32', False, 1, 10, categoria=PARAMETRO)
t.declarar_variable('b', 'i32', False, 1, 18, categoria=PARAMETRO)
t.declarar_variable('r', 'i32', False, 2, 5)
t.salir_funcion()

# --- fn main ---
t.entrar_funcion(f_main)
x1 = t.declarar_variable('x', 'i32', False, 5, 5, valor=10)
t.declarar_variable('nombre', 'String', True, 6, 5, valor="Ana")

t.abrir_scope('if')
t.declarar_variable('y', 'f64', False, 8, 9, valor=2.5)
print("Dentro del if, buscar('x') ->", t.buscar('x'))
print("Dentro del if, buscar('y') ->", t.buscar('y'))
t.cerrar_scope()

print("Fuera del if, buscar('y') ->", t.buscar('y'), " (ya no es visible)")

x2 = t.declarar_variable('x', 'f64', False, 10, 5, valor=3.14)
print("Después del sombreado, buscar('x') ->", t.buscar('x'))
print("¿Son símbolos distintos?", x1 is not x2, "| offsets:", x1.offset, x2.offset)

t.declarar_variable('activo', 'bool', False, 11, 5, valor=VALOR_POR_DEFECTO['bool'])
t.salir_funcion()

print("\nParámetros de sumar:", f_sumar.params)
print("Marco de sumar:", f_sumar.tamano_frame, "bytes | Marco de main:", f_main.tamano_frame, "bytes")

print(f"\n{'No':<4}{'Identificador':<15}{'Categoría':<12}{'Tipo':<8}{'Ámbito':<12}{'Lín':<5}{'Valor'}")
for fila in t.reporte():
    print(f"{fila['no']:<4}{fila['identificador']:<15}{fila['categoria']:<12}"
          f"{fila['tipo']:<8}{fila['ambito']:<12}{fila['linea']:<5}{fila['valor']}")