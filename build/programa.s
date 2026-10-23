// Generado por OxigenNative
    .global main
    // Funciones de la biblioteca de C que se usan
    .extern printf, snprintf, malloc, strlen, strcpy, strcat, strcmp

    .section .data
str_0: .asciz "Hola, %s"
str_1: .asciz "\n"
str_2: .asciz ""
str_3: .asciz "  (evaluando %d"
str_4: .asciz ")\n"
str_5: .asciz "Ana"
str_6: .asciz "Resultado: %d"
str_7: .asciz "sumar anidado: %d"
    .balign 8
dbl_0: .double 1.5
    .balign 8
dbl_1: .double 0.5
str_8: .asciz "mezcla: %s"
str_9: .asciz "factorial(5) = %d"
str_10: .asciz "factorial(10) = %d"
str_11: .asciz "fibonacci(15) = %d"
str_12: .asciz "true"
str_13: .asciz "false"
str_14: .asciz "es_par(10): %s"
str_15: .asciz ", es_par(7): %s"
str_16: .asciz "primer m\303\272ltiplo de 7 desde 30: %d"
str_17: .asciz "promedio: %s"
str_18: .asciz "ja"
str_19: .asciz "repetir: %s"
str_20: .asciz "con true:\n"
str_21: .asciz "%d"
str_22: .asciz " es par\n"
    .balign 8
dbl_2: .double 1000000000000000.0
str_23: .asciz "%.1f"
str_24: .asciz "%.15g"

    .section .bss
    .balign 8
buf_f64:  .skip 64                     // texto de un f64 al imprimir
buf_char: .skip 8                      // texto UTF-8 de un char

    .section .text

fn_saludar:
    stp x29, x30, [sp, #-16]!           // guardar x29 (marco) y x30 (retorno)
    mov x29, sp                         // x29 = base del nuevo marco
    sub sp, sp, #16                     // espacio para variables (16 bytes)
    str x0, [x29, #-8]                  // parámetro nombre = x0
    // println!  (línea 3)
    ldr x0, [x29, #-8]                  // x0 = nombre
    mov x1, x0                          // x1 = valor a imprimir
    adrp x0, str_0
    add x0, x0, :lo12:str_0
    bl printf
    adrp x0, str_1
    add x0, x0, :lo12:str_1
    bl printf
.Lfin_saludar_1:
    mov sp, x29                         // liberar las variables
    ldp x29, x30, [sp], #16             // restaurar marco y retorno
    ret

fn_sumar:
    stp x29, x30, [sp, #-16]!           // guardar x29 (marco) y x30 (retorno)
    mov x29, sp                         // x29 = base del nuevo marco
    sub sp, sp, #16                     // espacio para variables (16 bytes)
    str x0, [x29, #-8]                  // parámetro a = x0
    str x1, [x29, #-16]                 // parámetro b = x1
    ldr x0, [x29, #-8]                  // x0 = a
    str x0, [sp, #-16]!                 // push x0
    ldr x0, [x29, #-16]                 // x0 = b
    ldr x1, [sp], #16                   // pop x1
    add w0, w1, w0
    sxtw x0, w0                         // extender el signo a 64 bits
    b .Lfin_sumar_2                     // return  (línea 7)
    mov x0, #0                          // 0 / false / '\0'
.Lfin_sumar_2:
    mov sp, x29                         // liberar las variables
    ldp x29, x30, [sp], #16             // restaurar marco y retorno
    ret

fn_mezcla:
    stp x29, x30, [sp, #-16]!           // guardar x29 (marco) y x30 (retorno)
    mov x29, sp                         // x29 = base del nuevo marco
    sub sp, sp, #32                     // espacio para variables (32 bytes)
    str x0, [x29, #-8]                  // parámetro a = x0
    str d0, [x29, #-16]                 // parámetro x = d0
    str x1, [x29, #-24]                 // parámetro b = x1
    str d1, [x29, #-32]                 // parámetro y = d1
    ldr x0, [x29, #-8]                  // x0 = a
    str x0, [sp, #-16]!                 // push x0
    ldr d0, [x29, #-16]                 // d0 = x
    ldr x1, [sp], #16                   // pop x1
    scvtf d1, x1                        // promoción izq i32 -> f64
    fmul d0, d1, d0                     // d0 = izq * der
    str d0, [sp, #-16]!                 // push d0
    ldr x0, [x29, #-24]                 // x0 = b
    str x0, [sp, #-16]!                 // push x0
    ldr d0, [x29, #-32]                 // d0 = y
    ldr x1, [sp], #16                   // pop x1
    scvtf d1, x1                        // promoción izq i32 -> f64
    fmul d0, d1, d0                     // d0 = izq * der
    ldr d1, [sp], #16                   // pop d1
    fadd d0, d1, d0                     // d0 = izq + der
    b .Lfin_mezcla_3                    // return  (línea 12)
    fmov d0, xzr                        // 0.0
.Lfin_mezcla_3:
    mov sp, x29                         // liberar las variables
    ldp x29, x30, [sp], #16             // restaurar marco y retorno
    ret

fn_factorial:
    stp x29, x30, [sp, #-16]!           // guardar x29 (marco) y x30 (retorno)
    mov x29, sp                         // x29 = base del nuevo marco
    sub sp, sp, #16                     // espacio para variables (16 bytes)
    str x0, [x29, #-8]                  // parámetro n = x0
    // if  (línea 17)
    ldr x0, [x29, #-8]                  // x0 = n
    str x0, [sp, #-16]!                 // push x0
    mov x0, #1
    ldr x1, [sp], #16                   // pop x1
    cmp x1, x0
    cset x0, le                         // x0 = (izq <= der) ? 1 : 0
    cbz x0, .Lif_fin_6                  // condición false -> saltar
    mov x0, #1
    b .Lfin_factorial_4                 // return  (línea 18)
.Lif_fin_6:
    ldr x0, [x29, #-8]                  // x0 = n
    str x0, [sp, #-16]!                 // push x0
    // llamada a factorial()  (línea 20)
    ldr x0, [x29, #-8]                  // x0 = n
    str x0, [sp, #-16]!                 // push x0
    mov x0, #1
    ldr x1, [sp], #16                   // pop x1
    sub w0, w1, w0
    sxtw x0, w0                         // extender el signo a 64 bits
    str x0, [sp, #-16]!                 // push x0
    ldr x0, [sp], #16                   // pop x0
    bl fn_factorial
    ldr x1, [sp], #16                   // pop x1
    mul w0, w1, w0
    sxtw x0, w0                         // extender el signo a 64 bits
    b .Lfin_factorial_4                 // return  (línea 20)
    mov x0, #0                          // 0 / false / '\0'
.Lfin_factorial_4:
    mov sp, x29                         // liberar las variables
    ldp x29, x30, [sp], #16             // restaurar marco y retorno
    ret

fn_fibonacci:
    stp x29, x30, [sp, #-16]!           // guardar x29 (marco) y x30 (retorno)
    mov x29, sp                         // x29 = base del nuevo marco
    sub sp, sp, #16                     // espacio para variables (16 bytes)
    str x0, [x29, #-8]                  // parámetro n = x0
    // if  (línea 24)
    ldr x0, [x29, #-8]                  // x0 = n
    str x0, [sp, #-16]!                 // push x0
    mov x0, #2
    ldr x1, [sp], #16                   // pop x1
    cmp x1, x0
    cset x0, lt                         // x0 = (izq < der) ? 1 : 0
    cbz x0, .Lif_fin_9                  // condición false -> saltar
    ldr x0, [x29, #-8]                  // x0 = n
    b .Lfin_fibonacci_7                 // return  (línea 25)
.Lif_fin_9:
    // llamada a fibonacci()  (línea 27)
    ldr x0, [x29, #-8]                  // x0 = n
    str x0, [sp, #-16]!                 // push x0
    mov x0, #1
    ldr x1, [sp], #16                   // pop x1
    sub w0, w1, w0
    sxtw x0, w0                         // extender el signo a 64 bits
    str x0, [sp, #-16]!                 // push x0
    ldr x0, [sp], #16                   // pop x0
    bl fn_fibonacci
    str x0, [sp, #-16]!                 // push x0
    // llamada a fibonacci()  (línea 27)
    ldr x0, [x29, #-8]                  // x0 = n
    str x0, [sp, #-16]!                 // push x0
    mov x0, #2
    ldr x1, [sp], #16                   // pop x1
    sub w0, w1, w0
    sxtw x0, w0                         // extender el signo a 64 bits
    str x0, [sp, #-16]!                 // push x0
    ldr x0, [sp], #16                   // pop x0
    bl fn_fibonacci
    ldr x1, [sp], #16                   // pop x1
    add w0, w1, w0
    sxtw x0, w0                         // extender el signo a 64 bits
    b .Lfin_fibonacci_7                 // return  (línea 27)
    mov x0, #0                          // 0 / false / '\0'
.Lfin_fibonacci_7:
    mov sp, x29                         // liberar las variables
    ldp x29, x30, [sp], #16             // restaurar marco y retorno
    ret

fn_es_par:
    stp x29, x30, [sp, #-16]!           // guardar x29 (marco) y x30 (retorno)
    mov x29, sp                         // x29 = base del nuevo marco
    sub sp, sp, #16                     // espacio para variables (16 bytes)
    str x0, [x29, #-8]                  // parámetro n = x0
    ldr x0, [x29, #-8]                  // x0 = n
    str x0, [sp, #-16]!                 // push x0
    mov x0, #2
    ldr x1, [sp], #16                   // pop x1
    sdiv w2, w1, w0                     // w2 = a / b
    msub w0, w2, w0, w1                 // w0 = a - (a / b) * b
    sxtw x0, w0                         // extender el signo a 64 bits
    str x0, [sp, #-16]!                 // push x0
    mov x0, #0
    ldr x1, [sp], #16                   // pop x1
    cmp x1, x0
    cset x0, eq                         // x0 = (izq == der) ? 1 : 0
    b .Lfin_es_par_10                   // return  (línea 32)
    mov x0, #0                          // 0 / false / '\0'
.Lfin_es_par_10:
    mov sp, x29                         // liberar las variables
    ldp x29, x30, [sp], #16             // restaurar marco y retorno
    ret

fn_primer_multiplo:
    stp x29, x30, [sp, #-16]!           // guardar x29 (marco) y x30 (retorno)
    mov x29, sp                         // x29 = base del nuevo marco
    sub sp, sp, #16                     // espacio para variables (16 bytes)
    str x0, [x29, #-8]                  // parámetro desde = x0
    str x1, [x29, #-16]                 // parámetro de = x1
    // loop  (línea 37)
.Lloop_inicio_12:
    // if  (línea 38)
    ldr x0, [x29, #-8]                  // x0 = desde
    str x0, [sp, #-16]!                 // push x0
    ldr x0, [x29, #-16]                 // x0 = de
    ldr x1, [sp], #16                   // pop x1
    sdiv w2, w1, w0                     // w2 = a / b
    msub w0, w2, w0, w1                 // w0 = a - (a / b) * b
    sxtw x0, w0                         // extender el signo a 64 bits
    str x0, [sp, #-16]!                 // push x0
    mov x0, #0
    ldr x1, [sp], #16                   // pop x1
    cmp x1, x0
    cset x0, eq                         // x0 = (izq == der) ? 1 : 0
    cbz x0, .Lif_fin_15                 // condición false -> saltar
    ldr x0, [x29, #-8]                  // x0 = desde
    b .Lfin_primer_multiplo_11          // return  (línea 39)
.Lif_fin_15:
    // desde += ...  (línea 41)
    ldr x0, [x29, #-8]                  // x0 = desde
    str x0, [sp, #-16]!                 // push x0
    mov x0, #1
    ldr x1, [sp], #16                   // pop x1
    add w0, w1, w0
    sxtw x0, w0                         // extender el signo a 64 bits
    str x0, [x29, #-8]                  // desde = x0
    b .Lloop_inicio_12                  // repetir
.Lloop_fin_13:
    mov x0, #0                          // 0 / false / '\0'
.Lfin_primer_multiplo_11:
    mov sp, x29                         // liberar las variables
    ldp x29, x30, [sp], #16             // restaurar marco y retorno
    ret

fn_promedio:
    stp x29, x30, [sp, #-16]!           // guardar x29 (marco) y x30 (retorno)
    mov x29, sp                         // x29 = base del nuevo marco
    sub sp, sp, #16                     // espacio para variables (16 bytes)
    str d0, [x29, #-8]                  // parámetro total = d0
    str x0, [x29, #-16]                 // parámetro cantidad = x0
    ldr d0, [x29, #-8]                  // d0 = total
    str d0, [sp, #-16]!                 // push d0
    ldr x0, [x29, #-16]                 // x0 = cantidad
    scvtf d0, x0                        // promoción der i32 -> f64
    ldr d1, [sp], #16                   // pop d1
    fdiv d0, d1, d0                     // d0 = izq / der
    b .Lfin_promedio_16                 // return  (línea 46)
    fmov d0, xzr                        // 0.0
.Lfin_promedio_16:
    mov sp, x29                         // liberar las variables
    ldp x29, x30, [sp], #16             // restaurar marco y retorno
    ret

fn_mayusculas:
    stp x29, x30, [sp, #-16]!           // guardar x29 (marco) y x30 (retorno)
    mov x29, sp                         // x29 = base del nuevo marco
    sub sp, sp, #16                     // espacio para variables (16 bytes)
    str x0, [x29, #-8]                  // parámetro texto = x0
    str x1, [x29, #-16]                 // parámetro veces = x1
    ldr x0, [x29, #-8]                  // x0 = texto
    str x0, [sp, #-16]!                 // push x0
    ldr x0, [x29, #-16]                 // x0 = veces
    ldr x1, [sp], #16                   // pop x1
    mov x2, x0
    mov x0, x1                          // x0 = izq
    mov x1, x2                          // x1 = der
    bl __oxi_repetir
    b .Lfin_mayusculas_17               // return  (línea 50)
    adrp x0, str_2
    add x0, x0, :lo12:str_2
.Lfin_mayusculas_17:
    mov sp, x29                         // liberar las variables
    ldp x29, x30, [sp], #16             // restaurar marco y retorno
    ret

fn_evaluar:
    stp x29, x30, [sp, #-16]!           // guardar x29 (marco) y x30 (retorno)
    mov x29, sp                         // x29 = base del nuevo marco
    sub sp, sp, #16                     // espacio para variables (16 bytes)
    str x0, [x29, #-8]                  // parámetro valor = x0
    // println!  (línea 54)
    ldr x0, [x29, #-8]                  // x0 = valor
    mov x1, x0                          // x1 = valor a imprimir
    adrp x0, str_3
    add x0, x0, :lo12:str_3
    bl printf
    adrp x0, str_4
    add x0, x0, :lo12:str_4
    bl printf
    ldr x0, [x29, #-8]                  // x0 = valor
    str x0, [sp, #-16]!                 // push x0
    mov x0, #0
    ldr x1, [sp], #16                   // pop x1
    cmp x1, x0
    cset x0, gt                         // x0 = (izq > der) ? 1 : 0
    b .Lfin_evaluar_18                  // return  (línea 55)
    mov x0, #0                          // 0 / false / '\0'
.Lfin_evaluar_18:
    mov sp, x29                         // liberar las variables
    ldp x29, x30, [sp], #16             // restaurar marco y retorno
    ret

main:
    stp x29, x30, [sp, #-16]!           // guardar x29 (marco) y x30 (retorno)
    mov x29, sp                         // x29 = base del nuevo marco
    sub sp, sp, #32                     // espacio para variables (32 bytes)
    // llamada a saludar()  (línea 60)
    adrp x0, str_5
    add x0, x0, :lo12:str_5
    str x0, [sp, #-16]!                 // push x0
    ldr x0, [sp], #16                   // pop x0
    bl fn_saludar
    // let resultado: i32  (línea 61)
    // llamada a sumar()  (línea 61)
    mov x0, #10
    str x0, [sp, #-16]!                 // push x0
    mov x0, #5
    str x0, [sp, #-16]!                 // push x0
    ldr x1, [sp], #16                   // pop x1
    ldr x0, [sp], #16                   // pop x0
    bl fn_sumar
    str x0, [x29, #-8]                  // resultado = x0
    // println!  (línea 62)
    ldr x0, [x29, #-8]                  // x0 = resultado
    mov x1, x0                          // x1 = valor a imprimir
    adrp x0, str_6
    add x0, x0, :lo12:str_6
    bl printf
    adrp x0, str_1
    add x0, x0, :lo12:str_1
    bl printf
    // println!  (línea 64)
    // llamada a sumar()  (línea 64)
    // llamada a sumar()  (línea 64)
    mov x0, #1
    str x0, [sp, #-16]!                 // push x0
    mov x0, #2
    str x0, [sp, #-16]!                 // push x0
    ldr x1, [sp], #16                   // pop x1
    ldr x0, [sp], #16                   // pop x0
    bl fn_sumar
    str x0, [sp, #-16]!                 // push x0
    // llamada a sumar()  (línea 64)
    mov x0, #3
    str x0, [sp, #-16]!                 // push x0
    mov x0, #4
    str x0, [sp, #-16]!                 // push x0
    ldr x1, [sp], #16                   // pop x1
    ldr x0, [sp], #16                   // pop x0
    bl fn_sumar
    str x0, [sp, #-16]!                 // push x0
    ldr x1, [sp], #16                   // pop x1
    ldr x0, [sp], #16                   // pop x0
    bl fn_sumar
    mov x1, x0                          // x1 = valor a imprimir
    adrp x0, str_7
    add x0, x0, :lo12:str_7
    bl printf
    adrp x0, str_1
    add x0, x0, :lo12:str_1
    bl printf
    // println!  (línea 65)
    // llamada a mezcla()  (línea 65)
    mov x0, #2
    str x0, [sp, #-16]!                 // push x0
    adrp x9, dbl_0
    ldr d0, [x9, :lo12:dbl_0]           // d0 = 1.5
    str d0, [sp, #-16]!                 // push d0
    mov x0, #3
    str x0, [sp, #-16]!                 // push x0
    adrp x9, dbl_1
    ldr d0, [x9, :lo12:dbl_1]           // d0 = 0.5
    str d0, [sp, #-16]!                 // push d0
    ldr d1, [sp], #16                   // pop d1
    ldr x1, [sp], #16                   // pop x1
    ldr d0, [sp], #16                   // pop d0
    ldr x0, [sp], #16                   // pop x0
    bl fn_mezcla
    bl __oxi_f64_str
    mov x1, x0                          // x1 = valor a imprimir
    adrp x0, str_8
    add x0, x0, :lo12:str_8
    bl printf
    adrp x0, str_1
    add x0, x0, :lo12:str_1
    bl printf
    // println!  (línea 66)
    // llamada a factorial()  (línea 66)
    mov x0, #5
    str x0, [sp, #-16]!                 // push x0
    ldr x0, [sp], #16                   // pop x0
    bl fn_factorial
    mov x1, x0                          // x1 = valor a imprimir
    adrp x0, str_9
    add x0, x0, :lo12:str_9
    bl printf
    adrp x0, str_1
    add x0, x0, :lo12:str_1
    bl printf
    // println!  (línea 67)
    // llamada a factorial()  (línea 67)
    mov x0, #10
    str x0, [sp, #-16]!                 // push x0
    ldr x0, [sp], #16                   // pop x0
    bl fn_factorial
    mov x1, x0                          // x1 = valor a imprimir
    adrp x0, str_10
    add x0, x0, :lo12:str_10
    bl printf
    adrp x0, str_1
    add x0, x0, :lo12:str_1
    bl printf
    // println!  (línea 68)
    // llamada a fibonacci()  (línea 68)
    mov x0, #15
    str x0, [sp, #-16]!                 // push x0
    ldr x0, [sp], #16                   // pop x0
    bl fn_fibonacci
    mov x1, x0                          // x1 = valor a imprimir
    adrp x0, str_11
    add x0, x0, :lo12:str_11
    bl printf
    adrp x0, str_1
    add x0, x0, :lo12:str_1
    bl printf
    // println!  (línea 69)
    // llamada a es_par()  (línea 69)
    mov x0, #10
    str x0, [sp, #-16]!                 // push x0
    ldr x0, [sp], #16                   // pop x0
    bl fn_es_par
    adrp x1, str_12
    add x1, x1, :lo12:str_12
    adrp x2, str_13
    add x2, x2, :lo12:str_13
    cmp x0, #0
    csel x1, x1, x2, ne                 // x1 = texto del bool
    adrp x0, str_14
    add x0, x0, :lo12:str_14
    bl printf
    // llamada a es_par()  (línea 69)
    mov x0, #7
    str x0, [sp, #-16]!                 // push x0
    ldr x0, [sp], #16                   // pop x0
    bl fn_es_par
    adrp x1, str_12
    add x1, x1, :lo12:str_12
    adrp x2, str_13
    add x2, x2, :lo12:str_13
    cmp x0, #0
    csel x1, x1, x2, ne                 // x1 = texto del bool
    adrp x0, str_15
    add x0, x0, :lo12:str_15
    bl printf
    adrp x0, str_1
    add x0, x0, :lo12:str_1
    bl printf
    // println!  (línea 70)
    // llamada a primer_multiplo()  (línea 70)
    mov x0, #30
    str x0, [sp, #-16]!                 // push x0
    mov x0, #7
    str x0, [sp, #-16]!                 // push x0
    ldr x1, [sp], #16                   // pop x1
    ldr x0, [sp], #16                   // pop x0
    bl fn_primer_multiplo
    mov x1, x0                          // x1 = valor a imprimir
    adrp x0, str_16
    add x0, x0, :lo12:str_16
    bl printf
    adrp x0, str_1
    add x0, x0, :lo12:str_1
    bl printf
    // println!  (línea 71)
    // llamada a promedio()  (línea 71)
    mov x0, #10
    scvtf d0, x0                        // promoción del argumento i32 -> f64
    str d0, [sp, #-16]!                 // push d0
    mov x0, #4
    str x0, [sp, #-16]!                 // push x0
    ldr x0, [sp], #16                   // pop x0
    ldr d0, [sp], #16                   // pop d0
    bl fn_promedio
    bl __oxi_f64_str
    mov x1, x0                          // x1 = valor a imprimir
    adrp x0, str_17
    add x0, x0, :lo12:str_17
    bl printf
    adrp x0, str_1
    add x0, x0, :lo12:str_1
    bl printf
    // println!  (línea 72)
    // llamada a mayusculas()  (línea 72)
    adrp x0, str_18
    add x0, x0, :lo12:str_18
    str x0, [sp, #-16]!                 // push x0
    mov x0, #3
    str x0, [sp, #-16]!                 // push x0
    ldr x1, [sp], #16                   // pop x1
    ldr x0, [sp], #16                   // pop x0
    bl fn_mayusculas
    mov x1, x0                          // x1 = valor a imprimir
    adrp x0, str_19
    add x0, x0, :lo12:str_19
    bl printf
    adrp x0, str_1
    add x0, x0, :lo12:str_1
    bl printf
    // let flag: bool  (línea 75)
    mov x0, #0                          // false
    str x0, [x29, #-16]                 // flag = x0
    ldr x0, [x29, #-16]                 // x0 = flag
    cbz x0, .Llogico_fin_20             // izq es false -> resultado false
    // llamada a evaluar()  (línea 76)
    mov x0, #10
    str x0, [sp, #-16]!                 // push x0
    ldr x0, [sp], #16                   // pop x0
    bl fn_evaluar
.Llogico_fin_20:
    // println!  (línea 77)
    adrp x0, str_20
    add x0, x0, :lo12:str_20
    bl printf
    mov x0, #1                          // true
    cbz x0, .Llogico_fin_21             // izq es false -> resultado false
    // llamada a evaluar()  (línea 78)
    mov x0, #10
    str x0, [sp, #-16]!                 // push x0
    ldr x0, [sp], #16                   // pop x0
    bl fn_evaluar
.Llogico_fin_21:
    // let mut i: i32  (línea 81)
    mov x0, #0
    str x0, [x29, #-24]                 // i = x0
    // while  (línea 82)
.Lwhile_inicio_22:
    ldr x0, [x29, #-24]                 // x0 = i
    str x0, [sp, #-16]!                 // push x0
    mov x0, #5
    ldr x1, [sp], #16                   // pop x1
    cmp x1, x0
    cset x0, lt                         // x0 = (izq < der) ? 1 : 0
    cbz x0, .Lwhile_fin_23              // condición false -> salir del while
    // if  (línea 83)
    // llamada a es_par()  (línea 83)
    ldr x0, [x29, #-24]                 // x0 = i
    str x0, [sp, #-16]!                 // push x0
    ldr x0, [sp], #16                   // pop x0
    bl fn_es_par
    cbz x0, .Lif_fin_25                 // condición false -> saltar
    // println!  (línea 84)
    ldr x0, [x29, #-24]                 // x0 = i
    mov x1, x0                          // x1 = valor a imprimir
    adrp x0, str_21
    add x0, x0, :lo12:str_21
    bl printf
    adrp x0, str_22
    add x0, x0, :lo12:str_22
    bl printf
.Lif_fin_25:
    // i += ...  (línea 86)
    ldr x0, [x29, #-24]                 // x0 = i
    str x0, [sp, #-16]!                 // push x0
    mov x0, #1
    ldr x1, [sp], #16                   // pop x1
    add w0, w1, w0
    sxtw x0, w0                         // extender el signo a 64 bits
    str x0, [x29, #-24]                 // i = x0
    b .Lwhile_inicio_22                 // volver a evaluar la condición
.Lwhile_fin_23:
.Lfin_main_19:
    mov w0, #0                          // return 0
    mov sp, x29                         // liberar las variables
    ldp x29, x30, [sp], #16             // restaurar marco y retorno
    ret

// ---- __oxi_f64_str: d0 -> x0 = texto del f64 ----
__oxi_f64_str:
    stp x29, x30, [sp, #-16]!
    mov x29, sp
    adrp x2, str_24
    add x2, x2, :lo12:str_24         // formato "%.15g" por defecto
    frintz d1, d0                       // d1 = parte entera
    fcmp d1, d0
    b.ne .Lf64_formato                  // tiene decimales -> "%.15g"
    fabs d1, d0
    adrp x9, dbl_2
    ldr d2, [x9, :lo12:dbl_2]
    fcmp d1, d2
    b.ge .Lf64_formato                  // número enorme -> "%.15g"
    adrp x2, str_23
    add x2, x2, :lo12:str_23          // entero -> "%.1f" (3.0)
.Lf64_formato:
    adrp x0, buf_f64
    add x0, x0, :lo12:buf_f64
    mov x1, #64
    bl snprintf                         // snprintf(buf, 64, formato, d0)
    adrp x0, buf_f64
    add x0, x0, :lo12:buf_f64
    ldp x29, x30, [sp], #16
    ret

// ---- __oxi_repetir: x0 = texto, x1 = n -> x0 = texto repetido n veces ----
__oxi_repetir:
    stp x29, x30, [sp, #-48]!
    mov x29, sp
    stp x19, x20, [sp, #16]
    stp x21, x22, [sp, #32]
    mov x19, x0                         // x19 = texto
    cmp x1, #0
    csel x20, x1, xzr, gt               // x20 = n (si es negativo, 0)
    bl strlen
    mul x0, x0, x20
    add x0, x0, #1
    bl malloc                           // espacio para largo * n + 1
    mov x21, x0                         // x21 = resultado
    strb wzr, [x21]                     // empieza como cadena vacía
    mov x22, #0                         // x22 = contador
.Lrepetir_ciclo:
    cmp x22, x20
    b.ge .Lrepetir_fin
    mov x0, x21
    mov x1, x19
    bl strcat                           // resultado += texto
    add x22, x22, #1
    b .Lrepetir_ciclo
.Lrepetir_fin:
    mov x0, x21
    ldp x19, x20, [sp, #16]
    ldp x21, x22, [sp, #32]
    ldp x29, x30, [sp], #48
    ret
