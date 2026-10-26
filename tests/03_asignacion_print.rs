// Paso 3: asignaciones y println!
fn main() {
    let mut x: i32 = 10;
    let nombre = String::from("Ana");
    let pi: f64 = 3.1416;

    // Asignaciones simples y compuestas
    x = 20;
    x += 5;
    x -= 3;
    x *= 2;
    x /= 4;
    x %= 3;
    x = x * 2 + 1;

    // println!
    println!();
    println!("Hola Mundo");
    println!("x = {}", x);
    println!("Nombre: {}, pi: {}", nombre, pi);
    println!("Suma: {}", x + 10 * 2);
    println!("Debug: {:?}", x);
    println!("Llaves literales: {{}} y {}", x > 5);
    println!("Escapes:\tTab y \"comillas\"");
}
