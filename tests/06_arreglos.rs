// Paso 6: arreglos (ejemplos de la sección 3.3.10)
fn suma_arreglo(datos: [i32; 5]) -> i32 {
    let mut total = 0;
    let mut i = 0;
    while i < datos.len() {
        total += datos[i];
        i += 1;
    }
    return total;
}

fn main() {
    // Declaración explícita y por inferencia
    let numeros: [i32; 5] = [10, 20, 30, 40, 50];
    let edades = [18, 20, 22];

    // Acceso por índice y cantidad de elementos
    println!("Primer elemento: {}", numeros[0]);
    println!("Tercer elemento: {}", numeros[2]);
    println!("Longitud de numeros: {}", numeros.len());
    println!("Longitud de edades: {}", edades.len());

    // Recorrer con while
    println!("\nElementos de numeros:");
    let mut i = 0;
    while i < numeros.len() {
        println!("{}", numeros[i]);
        i = i + 1;
    }

    // Slice (porción del arreglo)
    let parte = &numeros[1..4];
    println!("\nSlice: {:?}", parte);
    println!("Primera edad: {}", edades[0]);

    // Matrices (row-major)
    let mut matrix: [[i32; 3]; 2] = [
        [1, 2, 3],
        [4, 5, 6]
    ];
    let cubo: [[[i32; 2]; 2]; 2] = [
        [[1, 2], [3, 4]],
        [[5, 6], [7, 8]]
    ];
    matrix[1][2] = 7;
    println!("Valor modificado: {}", matrix[1][2]);
    println!("matrix = {:?}", matrix);
    println!("cubo[1][0][1] = {}", cubo[1][0][1]);
    println!("cubo = {:?}", cubo);
    println!("fila 0 de matrix: {:?}", matrix[0]);

    // Índices calculados y asignación compuesta
    let mut f = 0;
    while f < 2 {
        let mut c = 0;
        while c < 3 {
            matrix[f][c] *= 10;
            c += 1;
        }
        f += 1;
    }
    println!("matrix x 10 = {:?}", matrix);

    // Otros tipos, [valor; N] y valores por defecto
    let decimales = [1.5, 2.25, 3.0];
    let nombres = [String::from("Ana"), String::from("Luis")];
    let letras = ['a', 'b'];
    let banderas = [true, false, true];
    let ceros = [0; 4];
    let tablero = [[0; 3]; 2];
    let vacio: [String; 2];
    println!("{:?} {:?} {:?} {:?}", decimales, nombres, letras, banderas);
    println!("{:?} {:?} {:?}", ceros, tablero, vacio);

    // Copia: modificar la copia no cambia el original
    let mut copia = numeros;
    copia[0] = 999;
    println!("numeros[0] = {}, copia[0] = {}", numeros[0], copia[0]);

    // Arreglo como parámetro
    println!("suma_arreglo(numeros) = {}", suma_arreglo(numeros));
}
