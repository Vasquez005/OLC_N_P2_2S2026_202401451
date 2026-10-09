// G2: operaciones con i32, bool y char
fn main() {
    let a: i32 = 17;
    let b: i32 = 5;

    // Aritméticas
    println!("{} + {} = {}", a, b, a + b);
    println!("{} - {} = {}", a, b, a - b);
    println!("{} * {} = {}", a, b, a * b);
    println!("{} / {} = {}", a, b, a / b);
    println!("{} % {} = {}", a, b, a % b);
    println!("-7 / 2 = {}, -7 % 3 = {}", -7 / 2, -7 % 3);

    // Precedencia y paréntesis
    println!("2 + 3 * 4 = {}", 2 + 3 * 4);
    println!("(2 + 3) * 4 = {}", (2 + 3) * 4);
    println!("10 - 3 - 2 = {}", 10 - 3 - 2);
    println!("-a + 5 = {}", -a + 5);

    // Asignaciones simples y compuestas
    let mut x = 10;
    x = x * 2 + 1;
    println!("x = {}", x);
    x += 5;
    println!("x += 5 -> {}", x);
    x -= 3;
    println!("x -= 3 -> {}", x);
    x *= 2;
    println!("x *= 2 -> {}", x);
    x /= 4;
    println!("x /= 4 -> {}", x);
    x %= 4;
    println!("x %= 4 -> {}", x);
    x %= 5;
    println!("x %= 5 -> {}", x);
    x %= 6;
    println!("x %= 6 -> {}", x);
    x %= 7;
    println!("x %= 7 -> {}", x);
    x %= 8;
    println!("x %= 8 -> {}", x);


    // Desbordamiento de i32 (da la vuelta)
    let maximo = 2147483647;
    println!("maximo + 1 = {}", maximo + 1);

    // Relacionales
    println!("a > b: {}, a < b: {}, a == 17: {}", a > b, a < b, a == 17);
    println!("a != b: {}, a >= 17: {}, b <= 4: {}", a != b, a >= 17, b <= 4);
    let letra: char = 'C';
    println!("letra > 'A': {}, letra == 67: {}", letra > 'A', letra == 67);

    // Lógicas
    let t = true;
    let f = false;
    println!("t && f = {}, t || f = {}, !t = {}", t && f, t || f, !t);
    println!("a > 10 && b < 10 = {}", a > 10 && b < 10);
    println!("a < 10 || b == 5 = {}", a < 10 || b == 5);
    let mut bandera = false;
    bandera = !bandera && a > b;
    println!("bandera = {}", bandera);

    // Resiliencia: asignar a una inmutable se reporta y se salta
    a = 100;
    println!("a sigue siendo {}", a);
}