// Paso 7: funciones embebidas, split, match y for (secciones 3.3.8, 3.3.11 y 3.3.13)
fn nombre_dia(n: i32) -> String {
    match n {
        1 => return String::from("lunes"),
        2 => return String::from("martes"),
        3 => { return String::from("miércoles"); }
        _ => return String::from("otro día"),
    }
}

fn contar_palabras(palabras: Vec<&str>) -> i32 {
    return palabras.len();
}

fn main() {
    // ---- Ejemplo completo de la sección 3.3.13 ----
    let texto = String::from("Hola Mundo");
    let mut numeros = [10, 20, 30];
    println!("Hola Mundo");
    println!(texto);
    println!("Texto: {}", texto);
    println!("Longitud: {}", texto.len());
    println!(typeof(texto));
    println!(texto.len());
    println!(texto.contains("Mundo"));
    println!(texto.replace("Mundo", "Rust"));
    println!(texto.to_uppercase());
    println!(texto.to_lowercase());
    println!(texto.split(" "));
    numeros.reverse();
    println!(numeros);
    let r = random(1, 10);
    println!("random entre 1 y 10: {}", r >= 1 && r <= 10);

    // ---- Ejemplo completo de la sección 3.3.11 ----
    let saludo = String::from("Hola Mundo desde Rust");
    println!("Cadena: {}", saludo);
    println!("Longitud: {}", saludo.len());
    let nuevo_saludo = saludo.replace("Rust", "Compiladores");
    println!("Nueva cadena: {}", nuevo_saludo);
    println!("\nPalabras:");
    let palabras: Vec<&str> = saludo.split_whitespace().collect();
    let mut i = 0;
    while i < palabras.len() {
        println!("{}", palabras[i]);
        i = i + 1;
    }

    // ---- split y arreglos dinámicos ----
    let csv = String::from("ana,luis,,marta");
    let campos = csv.split(",");
    println!("campos: {:?} (largo {})", campos, campos.len());
    println!("primero: {}, último: {}", campos[0], campos[3]);
    println!("contains luis: {}, contains pedro: {}", campos.contains(String::from("luis")), campos.contains(String::from("pedro")));
    let mut copia = campos;
    copia[2] = String::from("(vacío)");
    copia.reverse();
    println!("copia invertida: {:?}, original: {:?}", copia, campos);
    println!("slice: {:?}", &campos[1..3]);
    println!("espacios: {:?}", String::from("  uno   dos\ttres  ").split_whitespace());
    println!("contar_palabras: {}", contar_palabras(palabras));
    println!("typeof(palabras): {}", typeof(palabras));
    let vacio: Vec<String>;
    println!("vacío: {:?} largo {}", vacio, vacio.len());

    // ---- mayúsculas y minúsculas con tildes ----
    let frase = String::from("Árbol, camión, ñandú y pingüino");
    println!(frase.to_uppercase());
    println!(frase.to_uppercase().to_lowercase());

    // ---- for ----
    for k in 0..5 {
        print_par(k);
    }
    let mut suma = 0;
    for k in 1..=10 {
        suma += k;
    }
    println!("suma 1..=10 = {}", suma);
    for p in palabras {
        println!("palabra: {}", p);
    }
    let matriz = [[1, 2], [3, 4]];
    for fila in matriz {
        for valor in fila {
            if valor == 3 {
                continue;
            }
            println!("valor {}", valor);
        }
    }
    'externo: for a in 0..3 {
        for b in 0..3 {
            if a + b == 3 {
                break 'externo;
            }
            println!("a={}, b={}", a, b);
        }
    }
    let decimales = [1.5, 2.5];
    let mut total: f64 = 0;
    for d in decimales {
        total += d;
    }
    println!("total decimales = {}", total);

    // ---- match (ejemplo de la sección 3.3.8, con las comillas del PDF) ----
    let number: i32 = 32;
    match number {
        1 => println!(“UNO!”),
        2 => println!(“DOS!”),
        _ => println!(“nada más!”),
    }
    for j in 0..6 {
        match j {
            0 => println!("cero"),
            2 => {
                println!("dos");
            }
            4 => break,
            _ => println!("otro: {}", j),
        }
    }
    let letra = 'b';
    match letra {
        'a' => println!("es a"),
        'b' => println!("es b"),
        _ => println!("otra letra")
    }
    let palabra = String::from("hola");
    match palabra {
        "adios" => println!("adiós"),
        "hola" => println!("saludo encontrado"),
        _ => println!("?"),
    }
    println!("día 2: {}, día 3: {}, día 9: {}", nombre_dia(2), nombre_dia(3), nombre_dia(9));
    println!("typeof: {} {} {} {} {}", typeof(1), typeof(2.5), typeof(true), typeof('c'), typeof(numeros));
}

fn print_par(n: i32) {
    if n % 2 == 0 {
        println!("{} es par", n);
    }
}
