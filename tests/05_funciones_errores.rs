// Paso 5: errores con funciones (uno por línea)
fn suma(a: i32, b: i32) {
}

fn doble(x: i32) -> i32 {
    return x * 2;
}

fn sin_return(x: i32) -> i32 {
    println!("{}", x);
}

fn mal_tipo() -> i32 {
    return String::from("hola");
}

fn nada() {
    return 5;
}

fn main() {
    saludar();
    suma(10);
    doble(String::from("a"));
    let v = suma(1, 2);
    println!("{}", suma(1, 2));
    let bien = doble(4);
    println!("bien = {}", bien);
    println!("doble(21) = {}", doble(21));
}
