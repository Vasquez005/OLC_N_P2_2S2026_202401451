// Paso 4: sentencias de control de flujo y de transferencia
fn main() {
    let flag: bool = false;
    let mut n: i32 = 0;

    // if / else if / else (ejemplo del enunciado)
    if flag {
        println!("verdadero");
    } else if flag == false {
        println!("else if");
    } else {
        println!("else");
    }

    // if sin else, y paréntesis que NO envuelven toda la condición
    if (n > 5) && (n < 10) {
        println!("entre 5 y 10");
    }

    // while
    while n < 5 {
        n += 1;
        if n == 3 {
            continue;
        }
        println!("n = {}", n);
    }

    // loop simple con break
    loop {
        n -= 1;
        if n <= 0 {
            break;
        }
    }

    // loops anidados con etiquetas
    'outer: loop {
        'inner: loop {
            n += 1;
            if n > 10 {
                break 'outer;
            }
            continue 'inner;
        }
    }

    // while con etiqueta y bloque vacío
    'w: while false {
    }

    // un ';' suelto después de un bloque no es error
    if true {
    };
}