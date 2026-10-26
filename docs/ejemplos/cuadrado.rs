fn cuadrado(n: i32) -> i32 {
    return n * n;
}

fn main() {
    let x = cuadrado(4);
    if x > 10 {
        println!("x = {}", x);
    }
}
