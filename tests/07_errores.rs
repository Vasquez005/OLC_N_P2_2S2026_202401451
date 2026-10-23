// Paso 7: errores
fn main() {
    let x = 5;
    match x {
        1 => println!("uno"),
    }
    match x {
        _ => println!("todo"),
        2 => println!("dos"),
    }
    match x {
        "cinco" => println!("?"),
        _ => println!("ok"),
    }
    let fijo = [3, 2, 1];
    fijo.reverse();
    let t = String::from("a b");
    println!(t.mayusculas());
    println!(typeof());
    println!(random(1.5, 3));
    for i in 0..2.5 {
    }
    for c in x {
    }
    for k in 0..3 {
        k = 10;
    }
    let partes = t.split(" ");
    println!("{}", partes[-1]);
    println!("sigue funcionando: {} {:?}", t.to_uppercase(), partes);
    println!("{}", partes[5]);
    println!("no se llega aquí");
}
