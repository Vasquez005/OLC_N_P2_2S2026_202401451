// Generado por OxigenNative
    .global main
    // Funciones de la biblioteca de C que se usan
    .extern printf, snprintf, malloc, strlen, strcpy, strcat, strcmp

    .section .data
str_0: .asciz "x = %d"
str_1: .asciz "\n"

    .section .bss
    .balign 8
buf_f64:  .skip 64                     // texto de un f64 al imprimir
buf_char: .skip 8                      // texto UTF-8 de un char

    .section .text

main:
    stp x29, x30, [sp, #-16]!           // guardar x29 (marco) y x30 (retorno)
    mov x29, sp                         // x29 = base del nuevo marco
    sub sp, sp, #16                     // espacio para variables (16 bytes)
    // let x: i32  (línea 2)
    mov x0, #5
    str x0, [x29, #-8]                  // x = x0
    // println!  (línea 3)
    ldr x0, [x29, #-8]                  // x0 = x
    str x0, [sp, #-16]!                 // push x0
    mov x0, #2
    ldr x1, [sp], #16                   // pop x1
    mul w0, w1, w0
    sxtw x0, w0                         // extender el signo a 64 bits
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
