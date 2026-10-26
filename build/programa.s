// Generado por OxigenNative
    .global main
    // Funciones de la biblioteca de C que se usan
    .extern printf, snprintf, malloc, calloc, memcpy, strlen,
    .extern strcpy, strcat, strcmp, exit, strstr, strncat, rand, srand, time,
    .extern setvbuf, stdout

    .section .data
str_0: .asciz "Ana"
str_1: .asciz "None\n"
str_2: .asciz "%d"
str_3: .asciz " None\n"

    .section .bss
    .balign 8
buf_f64:  .skip 64                     // texto de un f64 al imprimir
buf_char: .skip 8                      // texto UTF-8 de un char
oxi_semilla: .skip 8                   // 1 si ya se inicializó random

    .section .text

main:
    stp x29, x30, [sp, #-16]!           // guardar x29 (marco) y x30 (retorno)
    mov x29, sp                         // x29 = base del nuevo marco
    sub sp, sp, #96                     // espacio para variables (96 bytes)
    adrp x0, stdout
    ldr x0, [x0, :lo12:stdout]          // x0 = stdout
    mov x1, #0
    mov x2, #1                          // _IOLBF: vaciar en cada salto de línea
    mov x3, #0
    bl setvbuf
    // let a: i32  (línea 3)
    mov x0, #10
    str x0, [x29, #-8]                  // a = x0
    // let nombre: String  (línea 4)
    adrp x0, str_0
    add x0, x0, :lo12:str_0
    str x0, [x29, #-16]                 // nombre = x0
    // let edad: i32  (línea 6)
    mov x0, #0                          // 0 / false / '\0'
    str x0, [x29, #-32]                 // edad = x0
    // let contador: i32  (línea 7)
    mov x0, #10
    str x0, [x29, #-40]                 // contador = x0
    // println!  (línea 9)
    adrp x0, str_1
    add x0, x0, :lo12:str_1
    bl printf
    // let mut y: i32  (línea 10)
    mov x0, #0
    str x0, [x29, #-48]                 // y = x0
    // if omitido: condición inválida (línea 13)
    // loop  (línea 18)
.Lloop_inicio_2:
    b .Lloop_fin_3                      // break  (línea 20)
    b .Lloop_inicio_2                   // repetir
.Lloop_fin_3:
    // println!  (línea 22)
    ldr x0, [x29, #-8]                  // x0 = a
    mov x1, x0                          // x1 = valor a imprimir
    adrp x0, str_2
    add x0, x0, :lo12:str_2
    bl printf
    adrp x0, str_3
    add x0, x0, :lo12:str_3
    bl printf
    // let div: i32  (línea 24)
    ldr x0, [x29, #-8]                  // x0 = a
    str x0, [sp, #-16]!                 // push x0
    mov x0, #0
    ldr x1, [sp], #16                   // pop x1
    sdiv w0, w1, w0                     // división entera con signo
    sxtw x0, w0                         // extender el signo a 64 bits
    str x0, [x29, #-72]                 // div = x0
    // println!  (línea 27)
    adrp x0, str_1
    add x0, x0, :lo12:str_1
    bl printf
.Lfin_main_1:
    mov w0, #0                          // return 0
    mov sp, x29                         // liberar las variables
    ldp x29, x30, [sp], #16             // restaurar marco y retorno
    ret
