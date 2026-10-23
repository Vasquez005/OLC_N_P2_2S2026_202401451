// Paso 6: errores con arreglos
fn main() {
    let numeros = [10, 20, 30];
    println!(numeros[5]);
    let mezcla = [1, 2.5, 3];
    let x = 5;
    println!("{}", x[0]);
    println!("{}", numeros[true]);
    numeros[0] = 1;
    let mut m = [[1, 2], [3, 4]];
    m[0][1] = String::from("no");
    let s = &numeros[2..9];
    let tam = x.len();
    println!("antes del error de ejecución: {:?}", m);
    let mut i = 0;
    while i < 10 {
        println!("numeros[{}] = {}", i, numeros[i]);
        i += 1;
    }
    println!("esto ya no se imprime");
}
