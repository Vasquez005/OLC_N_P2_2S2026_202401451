// Paso 5: funciones
fn saludar(nombre: String) {
    println!("Hola, {}", nombre);
}

fn sumar(a: i32, b: i32) -> i32 {
    return a + b;
}

// Mezcla de enteros y decimales: a -> x0, x -> d0, b -> x1, y -> d1
fn mezcla(a: i32, x: f64, b: i32, y: f64) -> f64 {
    return a * x + b * y;
}

// Recursión
fn factorial(n: i32) -> i32 {
    if n <= 1 {
        return 1;
    }
    return n * factorial(n - 1);
}

fn fibonacci(n: i32) -> i32 {
    if n < 2 {
        return n;
    }
    return fibonacci(n - 1) + fibonacci(n - 2);
}

// Se puede llamar antes de definirla (está más abajo)
fn es_par(n: i32) -> bool {
    return n % 2 == 0;
}

// Parámetro mutable y return dentro de un ciclo
fn primer_multiplo(mut desde: i32, de: i32) -> i32 {
    loop {
        if desde % de == 0 {
            return desde;
        }
        desde += 1;
    }
}

fn promedio(total: f64, cantidad: i32) -> f64 {
    return total / cantidad;
}

fn mayusculas(texto: String, veces: i32) -> String {
    return texto * veces;
}

fn evaluar(valor: i32) -> bool {
    println!("  (evaluando {})", valor);
    return valor > 0;
}

fn main() {
    // Ejemplo de la sección 3.3.12
    saludar(String::from("Ana"));
    let resultado = sumar(10, 5);
    println!("Resultado: {}", resultado);

    println!("sumar anidado: {}", sumar(sumar(1, 2), sumar(3, 4)));
    println!("mezcla: {}", mezcla(2, 1.5, 3, 0.5));
    println!("factorial(5) = {}", factorial(5));
    println!("factorial(10) = {}", factorial(10));
    println!("fibonacci(15) = {}", fibonacci(15));
    println!("es_par(10): {}, es_par(7): {}", es_par(10), es_par(7));
    println!("primer múltiplo de 7 desde 30: {}", primer_multiplo(30, 7));
    println!("promedio: {}", promedio(10, 4));
    println!("repetir: {}", mayusculas(String::from("ja"), 3));

    // Cortocircuito con funciones (sección 3.3.7)
    let flag = false;
    flag && evaluar(10);
    println!("con true:");
    true && evaluar(10);

    // Llamada dentro de una condición y de un ciclo
    let mut i = 0;
    while i < 5 {
        if es_par(i) {
            println!("{} es par", i);
        }
        i += 1;
    }
}
