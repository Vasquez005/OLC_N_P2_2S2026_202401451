// Paso 1: declaraciones de variables y literales
fn main() {
    // Tipo explícito con valor
    let entero: i32 = 10;
    let decimal: f64 = 3.14;
    let activo: bool = true;
    let letra: char = 'a';
    let nombre: String = String::from("Ana");

    // Tipo inferido
    let edad = 20;
    let saludo = String::from("Hola\nMundo");
    let ruta = String::from(r"C:\Users\Diego");
    let vacia = String::new();

    // Sin valor inicial (valor por defecto)
    let contador: i32;
    let promedio: f64;

    // Mutables
    let mut impar: i32 = 3;
    let mut termometro: i32;

    // Usando otra variable
    let copia = entero;

    // Sombreado (shadowing)
    let var_sombreada: i32 = 10;
    let var_sombreada: f64 = 3.14;
}
