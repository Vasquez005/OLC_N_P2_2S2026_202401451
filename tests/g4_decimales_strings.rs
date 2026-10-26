// G4: f64, String y char
fn main() {
    // ---- f64 ----
    let a: i32 = 10;
    let b: f64 = 2.5;
    println!("a + b = {}", a + b);          // 12.5 (promoción)
    println!("b * 4 = {}", b * 4);           // 10.0
    println!("7.5 - 2 = {}", 7.5 - 2);
    println!("1 / 3.0 = {}", 1 / 3.0);
    println!("7.5 % 2 = {}", 7.5 % 2);
    println!("-b = {}", -b);
    println!("0.1 + 0.2 = {}", 0.1 + 0.2);

    let mut total: f64 = 0;                  // i32 -> f64
    total += 1.5;
    total += 2;                              // f64 += i32
    total *= 3;
    total -= 0.5;
    total /= 2;
    println!("total = {}", total);

    let promedio: f64;                       // valor por defecto
    println!("promedio = {}", promedio);

    // Comparaciones de f64 (y mezcladas con i32)
    println!("b > 2: {}, b == 2.5: {}, a < b: {}, b <= 2.4: {}", b > 2, b == 2.5, a < b, b <= 2.4);

    // ---- String ----
    let nombre = String::from("Ana");
    let apellido = String::from("López");
    let completo = nombre + String::from(" ") + apellido;
    println!("completo = {}", completo);

    let mut saludo = String::from("Hola");
    saludo += String::from(", mundo");
    println!("saludo = {}", saludo);

    println!("repetir: {} | {}", 3 * String::from("ab"), String::from("-") * 5);

    let vacio: String;
    println!("vacío = [{}]", vacio);

    // Comparaciones de String (orden alfabético)
    let x = String::from("manzana");
    let y = String::from("pera");
    println!("x == y: {}, x != y: {}, x < y: {}, x >= y: {}", x == y, x != y, x < y, x >= y);
    println!("igual: {}", x == String::from("manzana"));

    // ---- char ----
    let letra: char = 'ñ';
    let otra: char = 'Z';
    println!("letras: {} {} {}", letra, otra, 'é');
    println!("'a' < 'b': {}", 'a' < 'b');

    // ---- Ejemplo del enunciado (sección 3.3.5) ----
    let resultado1 = a + b;
    let resultado2 = a * 5;
    let resultado3 = a + nombre;
    println!("{}", resultado1);
    println!("{}", resultado2);
    println!("{}", resultado3);

    // Ciclo con f64
    let mut t: f64 = 0.0;
    while t < 1.0 {
        t += 0.25;
    }
    println!("t = {}", t);
}
