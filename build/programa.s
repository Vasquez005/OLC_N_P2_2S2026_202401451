// Generado por OxigenNative
    .global main
    // Funciones de la biblioteca de C que se usan
    .extern printf, snprintf, malloc, calloc, memcpy, strlen,
    .extern strcpy, strcat, strcmp, exit, strstr, strncat, rand, srand, time,
    .extern setvbuf, stdout

    .section .data
str_0: .asciz "Primer n\303\272mero: %d"
str_1: .asciz "\n"

    .section .bss
    .balign 8
buf_f64:  .skip 64                     // texto de un f64 al imprimir
buf_char: .skip 8                      // texto UTF-8 de un char
oxi_semilla: .skip 8                   // 1 si ya se inicializó random

    .section .text

main:
    stp x29, x30, [sp, #-16]!           // guardar x29 (marco) y x30 (retorno)
    mov x29, sp                         // x29 = base del nuevo marco
    sub sp, sp, #16                     // espacio para variables (16 bytes)
    adrp x0, stdout
    ldr x0, [x0, :lo12:stdout]          // x0 = stdout
    mov x1, #0
    mov x2, #1                          // _IOLBF: vaciar en cada salto de línea
    mov x3, #0
    bl setvbuf
    // let numeros: [i32; 3]  (línea 9)
    // arreglo [i32; 3]  (línea 9)
    mov x0, #24
    bl malloc                           // reservar 24 bytes en el heap
    str x0, [sp, #-16]!                 // push x0
    mov x0, #10
    ldr x10, [sp]                       // x10 = bloque
    str x0, [x10]                       // elemento en el byte 0
    mov x0, #20
    ldr x10, [sp]                       // x10 = bloque
    add x10, x10, #8
    str x0, [x10]                       // elemento en el byte 8
    mov x0, #30
    ldr x10, [sp]                       // x10 = bloque
    add x10, x10, #16
    str x0, [x10]                       // elemento en el byte 16
    ldr x0, [sp], #16                   // pop x0
    str x0, [x29, #-8]                  // numeros = x0
    // println!  (línea 10)
    ldr x0, [x29, #-8]                  // x0 = numeros
    add x0, x0, #16
    ldr x0, [x0]                        // leer el elemento
    mov x1, x0                          // x1 = valor a imprimir
    adrp x0, str_0
    add x0, x0, :lo12:str_0
    bl printf
    adrp x0, str_1
    add x0, x0, :lo12:str_1
    bl printf
.Lfin_main_1:
    mov w0, #0                          // return 0
    mov sp, x29                         // liberar las variables
    ldp x29, x30, [sp], #16             // restaurar marco y retorno
    ret
