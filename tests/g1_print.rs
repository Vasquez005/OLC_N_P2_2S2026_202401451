// G1: literales, declaraciones, variables y println!
fn main() {
    println!("Hola Mundo");
    println!("Entero: {}", 42);

    let edad: i32 = 20;
    let pi: f64 = 3.1416;
    let activo = true;
    let letra: char = 'A';
    let nombre = String::from("Ana");

    println!("{} tiene {} años", nombre, edad);
    println!("pi = {}, activo = {}, letra = {}", pi, activo, letra);

    // Valores por defecto
    let contador: i32;
    let promedio: f64;
    let vacio: bool;
    let mensaje: String;
    println!("Por defecto: {} {} {} [{}]", contador, promedio, vacio, mensaje);

    // Promoción i32 -> f64 y números grandes
    let r: f64 = 7;
    let grande = 2147483647;
    println!("r = {}, grande = {}", r, grande);

    // Sombreado
    let edad = 3.5;
    println!("edad ahora es {}", edad);

    // Texto con % y llaves literales
    println!("100% listo {{ok}}");
    println!();

    // Resiliencia: error semántico, el programa igual se ejecuta
    let malo = edad + nombre;
    println!("malo = {}", malo);
    println!("Fin");
}