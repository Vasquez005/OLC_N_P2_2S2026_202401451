// Generado por OxigenNative
    .global main
    .extern printf

    .section .data
str_0: .asciz "Excelente\n"
str_1: .asciz "Nota en rango\n"
str_2: .asciz "impar: %d"
str_3: .asciz "\n"
str_4: .asciz "suma = %d"
str_5: .asciz " con n = %d"
str_6: .asciz "fila %d"
str_7: .asciz " col %d"
str_8: .asciz "sali\303\263 en fila %d"
str_9: .asciz "%d"
str_10: .asciz " x %d"
str_11: .asciz " = %d"
str_12: .asciz "local = %d"
str_13: .asciz "FizzBuzz\n"
str_14: .asciz "Fin\n"

    .section .text

main:
    stp x29, x30, [sp, #-16]!           // guardar x29 (marco) y x30 (retorno)
    mov x29, sp                         // x29 = base del nuevo marco
    sub sp, sp, #96                     // espacio para variables (96 bytes)
    // let nota: i32  (línea 4)
    mov x0, #75
    str x0, [x29, #-8]                  // nota = x0
    // if  (línea 5)
    ldr x0, [x29, #-8]                  // x0 = nota
    str x0, [sp, #-16]!                 // push x0
    mov x0, #90
    ldr x1, [sp], #16                   // pop x1
    cmp x1, x0
    cset x0, ge                         // x0 = (izq >= der) ? 1 : 0
    cbz x0, .Lif_fin_3                  // condición false -> saltar
    // println!  (línea 6)
    adrp x0, str_0
    add x0, x0, :lo12:str_0
    bl printf
.Lif_fin_3:
    // if  (línea 14)
    ldr x0, [x29, #-8]                  // x0 = nota
    str x0, [sp, #-16]!                 // push x0
    mov x0, #50
    ldr x1, [sp], #16                   // pop x1
    cmp x1, x0
    cset x0, gt                         // x0 = (izq > der) ? 1 : 0
    cbz x0, .Llogico_fin_6              // izq es false -> resultado false
    ldr x0, [x29, #-8]                  // x0 = nota
    str x0, [sp, #-16]!                 // push x0
    mov x0, #100
    ldr x1, [sp], #16                   // pop x1
    cmp x1, x0
    cset x0, lt                         // x0 = (izq < der) ? 1 : 0
.Llogico_fin_6:
    cbz x0, .Lif_fin_5                  // condición false -> saltar
    // println!  (línea 15)
    adrp x0, str_1
    add x0, x0, :lo12:str_1
    bl printf
.Lif_fin_5:
    // let mut i: i32  (línea 19)
    mov x0, #0
    str x0, [x29, #-16]                 // i = x0
    // while  (línea 20)
.Lwhile_inicio_7:
    ldr x0, [x29, #-16]                 // x0 = i
    str x0, [sp, #-16]!                 // push x0
    mov x0, #10
    ldr x1, [sp], #16                   // pop x1
    cmp x1, x0
    cset x0, lt                         // x0 = (izq < der) ? 1 : 0
    cbz x0, .Lwhile_fin_8               // condición false -> salir del while
    // i += ...  (línea 21)
    ldr x0, [x29, #-16]                 // x0 = i
    str x0, [sp, #-16]!                 // push x0
    mov x0, #1
    ldr x1, [sp], #16                   // pop x1
    add w0, w1, w0
    sxtw x0, w0                         // extender el signo a 64 bits
    str x0, [x29, #-16]                 // i = x0
    // if  (línea 22)
    ldr x0, [x29, #-16]                 // x0 = i
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
    cbz x0, .Lif_fin_10                 // condición false -> saltar
    b .Lwhile_inicio_7                  // continue  (línea 23)
.Lif_fin_10:
    // println!  (línea 25)
    ldr x0, [x29, #-16]                 // x0 = i
    mov x1, x0                          // x1 = valor a imprimir
    adrp x0, str_2
    add x0, x0, :lo12:str_2
    bl printf
    adrp x0, str_3
    add x0, x0, :lo12:str_3
    bl printf
    b .Lwhile_inicio_7                  // volver a evaluar la condición
.Lwhile_fin_8:
    // let mut suma: i32  (línea 29)
    mov x0, #0
    str x0, [x29, #-24]                 // suma = x0
    // let mut n: i32  (línea 30)
    mov x0, #0
    str x0, [x29, #-32]                 // n = x0
    // loop  (línea 31)
.Lloop_inicio_11:
    // n += ...  (línea 32)
    ldr x0, [x29, #-32]                 // x0 = n
    str x0, [sp, #-16]!                 // push x0
    mov x0, #1
    ldr x1, [sp], #16                   // pop x1
    add w0, w1, w0
    sxtw x0, w0                         // extender el signo a 64 bits
    str x0, [x29, #-32]                 // n = x0
    // suma += ...  (línea 33)
    ldr x0, [x29, #-24]                 // x0 = suma
    str x0, [sp, #-16]!                 // push x0
    ldr x0, [x29, #-32]                 // x0 = n
    ldr x1, [sp], #16                   // pop x1
    add w0, w1, w0
    sxtw x0, w0                         // extender el signo a 64 bits
    str x0, [x29, #-24]                 // suma = x0
    // if  (línea 34)
    ldr x0, [x29, #-24]                 // x0 = suma
    str x0, [sp, #-16]!                 // push x0
    mov x0, #20
    ldr x1, [sp], #16                   // pop x1
    cmp x1, x0
    cset x0, gt                         // x0 = (izq > der) ? 1 : 0
    cbz x0, .Lif_fin_14                 // condición false -> saltar
    b .Lloop_fin_12                     // break  (línea 35)
.Lif_fin_14:
    b .Lloop_inicio_11                  // repetir
.Lloop_fin_12:
    // println!  (línea 38)
    ldr x0, [x29, #-24]                 // x0 = suma
    mov x1, x0                          // x1 = valor a imprimir
    adrp x0, str_4
    add x0, x0, :lo12:str_4
    bl printf
    ldr x0, [x29, #-32]                 // x0 = n
    mov x1, x0                          // x1 = valor a imprimir
    adrp x0, str_5
    add x0, x0, :lo12:str_5
    bl printf
    adrp x0, str_3
    add x0, x0, :lo12:str_3
    bl printf
    // let mut fila: i32  (línea 41)
    mov x0, #0
    str x0, [x29, #-40]                 // fila = x0
    // loop  (línea 42)
.Lloop_inicio_15:
    // fila += ...  (línea 43)
    ldr x0, [x29, #-40]                 // x0 = fila
    str x0, [sp, #-16]!                 // push x0
    mov x0, #1
    ldr x1, [sp], #16                   // pop x1
    add w0, w1, w0
    sxtw x0, w0                         // extender el signo a 64 bits
    str x0, [x29, #-40]                 // fila = x0
    // let mut col: i32  (línea 44)
    mov x0, #0
    str x0, [x29, #-48]                 // col = x0
    // while  (línea 45)
.Lwhile_inicio_17:
    ldr x0, [x29, #-48]                 // x0 = col
    str x0, [sp, #-16]!                 // push x0
    mov x0, #5
    ldr x1, [sp], #16                   // pop x1
    cmp x1, x0
    cset x0, lt                         // x0 = (izq < der) ? 1 : 0
    cbz x0, .Lwhile_fin_18              // condición false -> salir del while
    // col += ...  (línea 46)
    ldr x0, [x29, #-48]                 // x0 = col
    str x0, [sp, #-16]!                 // push x0
    mov x0, #1
    ldr x1, [sp], #16                   // pop x1
    add w0, w1, w0
    sxtw x0, w0                         // extender el signo a 64 bits
    str x0, [x29, #-48]                 // col = x0
    // if  (línea 47)
    ldr x0, [x29, #-48]                 // x0 = col
    str x0, [sp, #-16]!                 // push x0
    mov x0, #2
    ldr x1, [sp], #16                   // pop x1
    cmp x1, x0
    cset x0, eq                         // x0 = (izq == der) ? 1 : 0
    cbz x0, .Lif_fin_20                 // condición false -> saltar
    b .Lwhile_inicio_17                 // continue 'interno  (línea 48)
.Lif_fin_20:
    // if  (línea 50)
    ldr x0, [x29, #-40]                 // x0 = fila
    str x0, [sp, #-16]!                 // push x0
    mov x0, #3
    ldr x1, [sp], #16                   // pop x1
    cmp x1, x0
    cset x0, eq                         // x0 = (izq == der) ? 1 : 0
    cbz x0, .Lif_fin_22                 // condición false -> saltar
    b .Lloop_fin_16                     // break 'externo  (línea 51)
.Lif_fin_22:
    // if  (línea 53)
    ldr x0, [x29, #-48]                 // x0 = col
    str x0, [sp, #-16]!                 // push x0
    mov x0, #4
    ldr x1, [sp], #16                   // pop x1
    cmp x1, x0
    cset x0, eq                         // x0 = (izq == der) ? 1 : 0
    cbz x0, .Lif_fin_24                 // condición false -> saltar
    b .Lloop_inicio_15                  // continue 'externo  (línea 54)
.Lif_fin_24:
    // println!  (línea 56)
    ldr x0, [x29, #-40]                 // x0 = fila
    mov x1, x0                          // x1 = valor a imprimir
    adrp x0, str_6
    add x0, x0, :lo12:str_6
    bl printf
    ldr x0, [x29, #-48]                 // x0 = col
    mov x1, x0                          // x1 = valor a imprimir
    adrp x0, str_7
    add x0, x0, :lo12:str_7
    bl printf
    adrp x0, str_3
    add x0, x0, :lo12:str_3
    bl printf
    b .Lwhile_inicio_17                 // volver a evaluar la condición
.Lwhile_fin_18:
    b .Lloop_inicio_15                  // repetir
.Lloop_fin_16:
    // println!  (línea 59)
    ldr x0, [x29, #-40]                 // x0 = fila
    mov x1, x0                          // x1 = valor a imprimir
    adrp x0, str_8
    add x0, x0, :lo12:str_8
    bl printf
    adrp x0, str_3
    add x0, x0, :lo12:str_3
    bl printf
    // let mut a: i32  (línea 62)
    mov x0, #1
    str x0, [x29, #-56]                 // a = x0
    // while  (línea 63)
.Lwhile_inicio_25:
    ldr x0, [x29, #-56]                 // x0 = a
    str x0, [sp, #-16]!                 // push x0
    mov x0, #3
    ldr x1, [sp], #16                   // pop x1
    cmp x1, x0
    cset x0, le                         // x0 = (izq <= der) ? 1 : 0
    cbz x0, .Lwhile_fin_26              // condición false -> salir del while
    // let mut b: i32  (línea 64)
    mov x0, #1
    str x0, [x29, #-64]                 // b = x0
    // while  (línea 65)
.Lwhile_inicio_27:
    ldr x0, [x29, #-64]                 // x0 = b
    str x0, [sp, #-16]!                 // push x0
    mov x0, #3
    ldr x1, [sp], #16                   // pop x1
    cmp x1, x0
    cset x0, le                         // x0 = (izq <= der) ? 1 : 0
    cbz x0, .Lwhile_fin_28              // condición false -> salir del while
    // println!  (línea 66)
    ldr x0, [x29, #-56]                 // x0 = a
    mov x1, x0                          // x1 = valor a imprimir
    adrp x0, str_9
    add x0, x0, :lo12:str_9
    bl printf
    ldr x0, [x29, #-64]                 // x0 = b
    mov x1, x0                          // x1 = valor a imprimir
    adrp x0, str_10
    add x0, x0, :lo12:str_10
    bl printf
    ldr x0, [x29, #-56]                 // x0 = a
    str x0, [sp, #-16]!                 // push x0
    ldr x0, [x29, #-64]                 // x0 = b
    ldr x1, [sp], #16                   // pop x1
    mul w0, w1, w0
    sxtw x0, w0                         // extender el signo a 64 bits
    mov x1, x0                          // x1 = valor a imprimir
    adrp x0, str_11
    add x0, x0, :lo12:str_11
    bl printf
    adrp x0, str_3
    add x0, x0, :lo12:str_3
    bl printf
    // b += ...  (línea 67)
    ldr x0, [x29, #-64]                 // x0 = b
    str x0, [sp, #-16]!                 // push x0
    mov x0, #1
    ldr x1, [sp], #16                   // pop x1
    add w0, w1, w0
    sxtw x0, w0                         // extender el signo a 64 bits
    str x0, [x29, #-64]                 // b = x0
    b .Lwhile_inicio_27                 // volver a evaluar la condición
.Lwhile_fin_28:
    // a += ...  (línea 69)
    ldr x0, [x29, #-56]                 // x0 = a
    str x0, [sp, #-16]!                 // push x0
    mov x0, #1
    ldr x1, [sp], #16                   // pop x1
    add w0, w1, w0
    sxtw x0, w0                         // extender el signo a 64 bits
    str x0, [x29, #-56]                 // a = x0
    b .Lwhile_inicio_25                 // volver a evaluar la condición
.Lwhile_fin_26:
    // let mut k: i32  (línea 73)
    mov x0, #0
    str x0, [x29, #-72]                 // k = x0
    // while  (línea 74)
.Lwhile_inicio_29:
    ldr x0, [x29, #-72]                 // x0 = k
    str x0, [sp, #-16]!                 // push x0
    mov x0, #3
    ldr x1, [sp], #16                   // pop x1
    cmp x1, x0
    cset x0, lt                         // x0 = (izq < der) ? 1 : 0
    cbz x0, .Lwhile_fin_30              // condición false -> salir del while
    // let local: i32  (línea 75)
    ldr x0, [x29, #-72]                 // x0 = k
    str x0, [sp, #-16]!                 // push x0
    mov x0, #10
    ldr x1, [sp], #16                   // pop x1
    mul w0, w1, w0
    sxtw x0, w0                         // extender el signo a 64 bits
    str x0, [x29, #-80]                 // local = x0
    // println!  (línea 76)
    ldr x0, [x29, #-80]                 // x0 = local
    mov x1, x0                          // x1 = valor a imprimir
    adrp x0, str_12
    add x0, x0, :lo12:str_12
    bl printf
    adrp x0, str_3
    add x0, x0, :lo12:str_3
    bl printf
    // k += ...  (línea 77)
    ldr x0, [x29, #-72]                 // x0 = k
    str x0, [sp, #-16]!                 // push x0
    mov x0, #1
    ldr x1, [sp], #16                   // pop x1
    add w0, w1, w0
    sxtw x0, w0                         // extender el signo a 64 bits
    str x0, [x29, #-72]                 // k = x0
    b .Lwhile_inicio_29                 // volver a evaluar la condición
.Lwhile_fin_30:
    // let mut x: i32  (línea 81)
    mov x0, #1
    str x0, [x29, #-88]                 // x = x0
    // while  (línea 82)
.Lwhile_inicio_31:
    ldr x0, [x29, #-88]                 // x0 = x
    str x0, [sp, #-16]!                 // push x0
    mov x0, #15
    ldr x1, [sp], #16                   // pop x1
    cmp x1, x0
    cset x0, le                         // x0 = (izq <= der) ? 1 : 0
    cbz x0, .Lwhile_fin_32              // condición false -> salir del while
    // if  (línea 83)
    ldr x0, [x29, #-88]                 // x0 = x
    str x0, [sp, #-16]!                 // push x0
    mov x0, #15
    ldr x1, [sp], #16                   // pop x1
    sdiv w2, w1, w0                     // w2 = a / b
    msub w0, w2, w0, w1                 // w0 = a - (a / b) * b
    sxtw x0, w0                         // extender el signo a 64 bits
    str x0, [sp, #-16]!                 // push x0
    mov x0, #0
    ldr x1, [sp], #16                   // pop x1
    cmp x1, x0
    cset x0, eq                         // x0 = (izq == der) ? 1 : 0
    cbz x0, .Lif_fin_34                 // condición false -> saltar
    // println!  (línea 84)
    adrp x0, str_13
    add x0, x0, :lo12:str_13
    bl printf
.Lif_fin_34:
    // x += ...  (línea 92)
    ldr x0, [x29, #-88]                 // x0 = x
    str x0, [sp, #-16]!                 // push x0
    mov x0, #1
    ldr x1, [sp], #16                   // pop x1
    add w0, w1, w0
    sxtw x0, w0                         // extender el signo a 64 bits
    str x0, [x29, #-88]                 // x = x0
    b .Lwhile_inicio_31                 // volver a evaluar la condición
.Lwhile_fin_32:
    // if omitido: condición inválida (línea 96)
    // println!  (línea 99)
    adrp x0, str_14
    add x0, x0, :lo12:str_14
    bl printf
.Lfin_main_1:
    mov w0, #0                          // return 0
    mov sp, x29                         // liberar las variables
    ldp x29, x30, [sp], #16             // restaurar marco y retorno
    ret
