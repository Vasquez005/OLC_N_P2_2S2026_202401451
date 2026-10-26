// G3: control de flujo
fn main() {
    // if / else if / else
    let nota = 75;
    if nota >= 90 {
        println!("Excelente");
    } else if nota >= 70 {
        println!("Aprobado con {}", nota);
    } else {
        println!("Reprobado");
    }

    // if sin else
    if nota > 50 && nota < 100 {
        println!("Nota en rango");
    }

    // while con continue: imprime los impares del 1 al 9
    let mut i = 0;
    while i < 10 {
        i += 1;
        if i % 2 == 0 {
            continue;
        }
        println!("impar: {}", i);
    }

    // loop con break: suma hasta pasar 20
    let mut suma = 0;
    let mut n = 0;
    loop {
        n += 1;
        suma += n;
        if suma > 20 {
            break;
        }
    }
    println!("suma = {} con n = {}", suma, n);

    // Ciclos anidados con etiquetas
    let mut fila = 0;
    'externo: loop {
        fila += 1;
        let mut col = 0;
        'interno: while col < 5 {
            col += 1;
            if col == 2 {
                continue 'interno;
            }
            if fila == 3 {
                break 'externo;     // termina los dos ciclos
            }
            if col == 4 {
                continue 'externo;  // siguiente fila
            }
            println!("fila {} col {}", fila, col);
        }
    }
    println!("salió en fila {}", fila);

    // Tabla de multiplicar (while anidados)
    let mut a = 1;
    while a <= 3 {
        let mut b = 1;
        while b <= 3 {
            println!("{} x {} = {}", a, b, a * b);
            b += 1;
        }
        a += 1;
    }

    // Variable declarada dentro de un ciclo se reinicia en cada vuelta
    let mut k = 0;
    while k < 3 {
        let local = k * 10;
        println!("local = {}", local);
        k += 1;
    }

    // FizzBuzz del 1 al 15
    let mut x = 1;
    while x <= 15 {
        if x % 15 == 0 {
            println!("FizzBuzz");
        } else if x % 3 == 0 {
            println!("Fizz");
        } else if x % 5 == 0 {
            println!("Buzz");
        } else {
            println!("{}", x);
        }
        x += 1;
    }

    // Resiliencia: condición inválida se reporta y el if se salta
    if nota {
        println!("esto no se imprime");
    }
    println!("Fin");
}
