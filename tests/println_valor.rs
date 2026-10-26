// println! con un solo valor (como en los ejemplos del enunciado)
fn main() {
    let edad = 20;
    let nombre = String::from("Ana");
    let pi: f64 = 3.14;
    println!(edad);
    println!(nombre);
    println!(pi * 2);
    println!(edad > 18);
    println!("Hola " + nombre);
    println!("texto {{literal}}");
    println!(String::from("con {} adentro"));
    println!("{} y {}", edad, nombre);
    println!(("entre paréntesis"));

    // Ejemplo de la sección 3.3.5
    let a: i32 = 10;
    let b: f64 = 2.5;
    let resultado1 = a + b;
    let resultado2 = a * 5;
    let resultado3 = a + nombre;
    println!(resultado1);
    println!(resultado2);
    println!(resultado3);
}
