// Paso 2: expresiones con precedencia
fn main() {
    let a: i32 = 10;
    let b: f64 = 2.5;

    // Aritméticas
    let suma = a + b;
    let prec1 = 2 + 3 * 4;          // 2 + (3 * 4)
    let prec2 = (2 + 3) * 4;        // paréntesis
    let resta = 10 - 3 - 2;         // (10 - 3) - 2
    let mezcla = a * 2 + b / 4 % 3;
    let neg = -a + 5;               // (-a) + 5
    let neg2 = -(a + 5);

    // Relacionales
    let mayor = a > 5;
    let igual = a + 1 == 11;        // (a + 1) == 11

    // Lógicos
    let l1 = true || false && false;     // true || (false && false)
    let l2 = !true && a >= 3;            // (!true) && (a >= 3)
    let l3 = a < 5 || a != 10 && !(b <= 1.0);
}