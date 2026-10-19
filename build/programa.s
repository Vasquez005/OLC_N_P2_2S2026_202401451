// Generado por OxigenNative
    .global main
    // Funciones de la biblioteca de C que se usan
    .extern printf, snprintf, malloc, strlen, strcpy, strcat, strcmp

    .section .data
str_0: .asciz "OxigenNative"
    .balign 8
dbl_0: .double 5.0
str_1: .asciz "Hola desde %s"
str_2: .asciz "\n"
str_3: .asciz "Suma: %d"
str_4: .asciz ", promedio: %s"
    .balign 8
dbl_1: .double 3.0
str_5: .asciz "Mayor que 10\n"
str_6: .asciz "Menor o igual a 10\n"

    .section .bss
    .balign 8
buf_f64:  .skip 64                     // texto de un f64 al imprimir
buf_char: .skip 8                      // texto UTF-8 de un char

    .section .text

main:
    stp x29, x30, [sp, #-16]!           // guardar x29 (marco) y x30 (retorno)
    mov x29, sp                         // x29 = base del nuevo marco
    sub sp, sp, #32                     // espacio para variables (32 bytes)
    // let nombre: String  (línea 2)
    adrp x0, str_0
    add x0, x0, :lo12:str_0
    str x0, [x29, #-8]                  // nombre = x0
    // let mut total: i32  (línea 3)
    mov x0, #0
    str x0, [x29, #-16]                 // total = x0
    // let mut i: i32  (línea 4)
    mov x0, #1
    str x0, [x29, #-24]                 // i = x0
    // while  (línea 6)
.Lwhile_inicio_2:
    ldr x0, [x29, #-24]                 // x0 = i
    str x0, [sp, #-16]!                 // push x0
    mov x0, #5
    ldr x1, [sp], #16                   // pop x1
    cmp x1, x0
    cset x0, le                         // x0 = (izq <= der) ? 1 : 0
    cbz x0, .Lwhile_fin_3               // condición false -> salir del while
    // total += ...  (línea 7)
    ldr x0, [x29, #-16]                 // x0 = total
    str x0, [sp, #-16]!                 // push x0
    ldr x0, [x29, #-24]                 // x0 = i
    ldr x1, [sp], #16                   // pop x1
    add w0, w1, w0
    sxtw x0, w0                         // extender el signo a 64 bits
    str x0, [x29, #-16]                 // total = x0
    // i += ...  (línea 8)
    ldr x0, [x29, #-24]                 // x0 = i
    str x0, [sp, #-16]!                 // push x0
    mov x0, #1
    ldr x1, [sp], #16                   // pop x1
    add w0, w1, w0
    sxtw x0, w0                         // extender el signo a 64 bits
    str x0, [x29, #-24]                 // i = x0
    b .Lwhile_inicio_2                  // volver a evaluar la condición
.Lwhile_fin_3:
    // let promedio: f64  (línea 11)
    ldr x0, [x29, #-16]                 // x0 = total
    str x0, [sp, #-16]!                 // push x0
    adrp x9, dbl_0
    ldr d0, [x9, :lo12:dbl_0]           // d0 = 5.0
    ldr x1, [sp], #16                   // pop x1
    scvtf d1, x1                        // promoción izq i32 -> f64
    fdiv d0, d1, d0                     // d0 = izq / der
    str d0, [x29, #-32]                 // promedio = d0
    // println!  (línea 12)
    ldr x0, [x29, #-8]                  // x0 = nombre
    mov x1, x0                          // x1 = valor a imprimir
    adrp x0, str_1
    add x0, x0, :lo12:str_1
    bl printf
    adrp x0, str_2
    add x0, x0, :lo12:str_2
    bl printf
    // println!  (línea 13)
    ldr x0, [x29, #-16]                 // x0 = total
    mov x1, x0                          // x1 = valor a imprimir
    adrp x0, str_3
    add x0, x0, :lo12:str_3
    bl printf
    ldr d0, [x29, #-32]                 // d0 = promedio
    adrp x0, str_4
    add x0, x0, :lo12:str_4
    bl printf
    adrp x0, str_2
    add x0, x0, :lo12:str_2
    bl printf
    // if  (línea 15)
    ldr x0, [x29, #-16]                 // x0 = total
    str x0, [sp, #-16]!                 // push x0
    mov x0, #10
    ldr x1, [sp], #16                   // pop x1
    cmp x1, x0
    cset x0, gt                         // x0 = (izq > der) ? 1 : 0
    cbz x0, .Llogico_fin_6              // izq es false -> resultado false
    ldr d0, [x29, #-32]                 // d0 = promedio
    str d0, [sp, #-16]!                 // push d0
    adrp x9, dbl_1
    ldr d0, [x9, :lo12:dbl_1]           // d0 = 3.0
    ldr d1, [sp], #16                   // pop d1
    fcmp d1, d0
    cset x0, ge                         // x0 = (izq >= der) ? 1 : 0
.Llogico_fin_6:
    cbz x0, .Lif_sino_4                 // condición false -> saltar
    // println!  (línea 16)
    adrp x0, str_5
    add x0, x0, :lo12:str_5
    bl printf
    b .Lif_fin_5                        // terminar el if
.Lif_sino_4:
    // println!  (línea 18)
    adrp x0, str_6
    add x0, x0, :lo12:str_6
    bl printf
.Lif_fin_5:
.Lfin_main_1:
    mov w0, #0                          // return 0
    mov sp, x29                         // liberar las variables
    ldp x29, x30, [sp], #16             // restaurar marco y retorno
    ret
