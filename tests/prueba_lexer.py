"""
Prueba rápida del lexer. 
"""
from compiler.errors import ErrorList
from compiler.lexer import Lexer

CODIGO = r'''
fn sumar(a: i32, b: i32) -> i32 {
    return a + b;
}

fn main() {
    // Comentario de línea
    let mut x: i32 = 10;
    let pi: f64 = 3.14;
    let letra: char = 'a';
    let s = String::from("Hola\n\"Mundo\"");
    let r = String::from(r#"Él dijo: "Hola""#);
    /* comentario
       de bloque */
    x += 5;
    if x >= 10 && !false || x != 3 {
        println!("x = {}", x);
    }
    let numeros = [10, 20, 30, 40, 50];
    let parte = &numeros[1..4];
    'outer: loop {
        break 'outer;
    }
    match x {
        1 => println!("UNO"),
        _ => println!("otro"),
    }
    let total = @100;
}
'''


def main():
    errores = ErrorList()
    lx = Lexer(errores)
    lx.build()

    for tok in lx.tokenize(CODIGO):
        print(f"{tok.lineno:>3}:{tok.column:<3} {tok.type:<14} {tok.value!r}")

    print("\n--- Errores ---")
    for e in errores:
        print(e)


if __name__ == "__main__":
    main()