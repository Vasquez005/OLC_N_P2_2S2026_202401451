// Semántico: programa SIN errores
fn main() {
    let a: i32 = 10;
    let b: f64 = 2.5;
    let nombre = String::from("Ana");

    let r1 = a + b;             // f64 (promoción)
    let r2 = a * 5;             // i32
    let r3 = nombre + String::from(" Pérez");   // String
    let r4: f64 = 7;            // i32 -> f64 permitido
    let mayor = a > 5 && b <= 3.0;
    let letra: char = 'z';
    let cmp = letra == 'z';

    // Sin valor inicial: usan el valor por defecto
    let contador: i32;
    let activo: bool;

    let mut x = 0;
    x += 5;
    x = x * 2;

    // Sombreado: la x de la derecha es la anterior (i32)
    let x = x + 0.5;

    if mayor {
        let interna = 1;
        println!("interna = {}", interna);
    } else if a == 10 {
        println!("diez");
    }

    let mut n = 0;
    'outer: loop {
        while n < 3 {
            n += 1;
            if n == 2 {
                continue;
            }
            break 'outer;
        }
    }
    println!("{} {} {} {}", r1, r2, r3, x);
}