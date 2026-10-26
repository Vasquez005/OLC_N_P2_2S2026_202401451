// Generado por OxigenNative
    .global main
    // Funciones de la biblioteca de C que se usan
    .extern printf, snprintf, malloc, calloc, memcpy, strlen,
    .extern strcpy, strcat, strcmp, exit, strstr, strncat, rand, srand, time,
    .extern setvbuf, stdout

    .section .data
str_0: .asciz "x = %d"
str_1: .asciz "\n"

    .section .bss
    .balign 8
buf_f64:  .skip 64                     // texto de un f64 al imprimir
buf_char: .skip 8                      // texto UTF-8 de un char
oxi_semilla: .skip 8                   // 1 si ya se inicializó random

    .section .text

fn_cuadrado:
    stp x29, x30, [sp, #-16]!           // guardar x29 (marco) y x30 (retorno)
    mov x29, sp                         // x29 = base del nuevo marco
    sub sp, sp, #16                     // espacio para variables (16 bytes)
    str x0, [x29, #-8]                  // parámetro n = x0
    ldr x0, [x29, #-8]                  // x0 = n
    str x0, [sp, #-16]!                 // push x0
    ldr x0, [x29, #-8]                  // x0 = n
    ldr x1, [sp], #16                   // pop x1
    mul w0, w1, w0
    sxtw x0, w0                         // extender el signo a 64 bits
    b .Lfin_cuadrado_1                  // return  (línea 2)
    mov x0, #0                          // 0 / false / '\0'
.Lfin_cuadrado_1:
    mov sp, x29                         // liberar las variables
    ldp x29, x30, [sp], #16             // restaurar marco y retorno
    ret

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
    // let x: i32  (línea 6)
    // llamada a cuadrado()  (línea 6)
    mov x0, #4
    str x0, [sp, #-16]!                 // push x0
    ldr x0, [sp], #16                   // pop x0
    bl fn_cuadrado
    str x0, [x29, #-8]                  // x = x0
    // if  (línea 7)
    ldr x0, [x29, #-8]                  // x0 = x
    str x0, [sp, #-16]!                 // push x0
    mov x0, #10
    ldr x1, [sp], #16                   // pop x1
    cmp x1, x0
    cset x0, gt                         // x0 = (izq > der) ? 1 : 0
    cbz x0, .Lif_fin_4                  // condición false -> saltar
    // println!  (línea 8)
    ldr x0, [x29, #-8]                  // x0 = x
    mov x1, x0                          // x1 = valor a imprimir
    adrp x0, str_0
    add x0, x0, :lo12:str_0
    bl printf
    adrp x0, str_1
    add x0, x0, :lo12:str_1
    bl printf
.Lif_fin_4:
.Lfin_main_2:
    mov w0, #0                          // return 0
    mov sp, x29                         // liberar las variables
    ldp x29, x30, [sp], #16             // restaurar marco y retorno
    ret

