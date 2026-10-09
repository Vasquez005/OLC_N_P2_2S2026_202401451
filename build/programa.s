// Generado por OxigenNative
    .global main
    .extern printf

    .section .data
str_0: .asciz "%d"
str_1: .asciz " + %d"
str_2: .asciz " = %d"
str_3: .asciz "\n"
str_4: .asciz " - %d"
str_5: .asciz " * %d"
str_6: .asciz " / %d"
str_7: .asciz " %% %d"
str_8: .asciz "-7 / 2 = %d"
str_9: .asciz ", -7 %% 3 = %d"
str_10: .asciz "2 + 3 * 4 = %d"
str_11: .asciz "(2 + 3) * 4 = %d"
str_12: .asciz "10 - 3 - 2 = %d"
str_13: .asciz "-a + 5 = %d"
str_14: .asciz "x = %d"
str_15: .asciz "x += 5 -> %d"
str_16: .asciz "x -= 3 -> %d"
str_17: .asciz "x *= 2 -> %d"
str_18: .asciz "x /= 4 -> %d"
str_19: .asciz "x %%= 4 -> %d"
str_20: .asciz "x %%= 5 -> %d"
str_21: .asciz "maximo + 1 = %d"
str_22: .asciz "true"
str_23: .asciz "false"
str_24: .asciz "a > b: %s"
str_25: .asciz ", a < b: %s"
str_26: .asciz ", a == 17: %s"
str_27: .asciz "a != b: %s"
str_28: .asciz ", a >= 17: %s"
str_29: .asciz ", b <= 4: %s"
str_30: .asciz "letra > 'A': %s"
str_31: .asciz ", letra == 67: %s"
str_32: .asciz "t && f = %s"
str_33: .asciz ", t || f = %s"
str_34: .asciz ", !t = %s"
str_35: .asciz "a > 10 && b < 10 = %s"
str_36: .asciz "a < 10 || b == 5 = %s"
str_37: .asciz "bandera = %s"
str_38: .asciz "a sigue siendo %d"

    .section .text

main:
    stp x29, x30, [sp, #-16]!           // guardar x29 (marco) y x30 (retorno)
    mov x29, sp                         // x29 = base del nuevo marco
    sub sp, sp, #64                     // espacio para variables (64 bytes)
    // let a: i32  (línea 3)
    mov x0, #17
    str x0, [x29, #-8]                  // a = x0
    // let b: i32  (línea 4)
    mov x0, #5
    str x0, [x29, #-16]                 // b = x0
    // println!  (línea 7)
    ldr x0, [x29, #-8]                  // x0 = a
    mov x1, x0                          // x1 = valor a imprimir
    adrp x0, str_0
    add x0, x0, :lo12:str_0
    bl printf
    ldr x0, [x29, #-16]                 // x0 = b
    mov x1, x0                          // x1 = valor a imprimir
    adrp x0, str_1
    add x0, x0, :lo12:str_1
    bl printf
    ldr x0, [x29, #-8]                  // x0 = a
    str x0, [sp, #-16]!                 // push x0
    ldr x0, [x29, #-16]                 // x0 = b
    ldr x1, [sp], #16                   // pop x1
    add w0, w1, w0
    sxtw x0, w0                         // extender el signo a 64 bits
    mov x1, x0                          // x1 = valor a imprimir
    adrp x0, str_2
    add x0, x0, :lo12:str_2
    bl printf
    adrp x0, str_3
    add x0, x0, :lo12:str_3
    bl printf
    // println!  (línea 8)
    ldr x0, [x29, #-8]                  // x0 = a
    mov x1, x0                          // x1 = valor a imprimir
    adrp x0, str_0
    add x0, x0, :lo12:str_0
    bl printf
    ldr x0, [x29, #-16]                 // x0 = b
    mov x1, x0                          // x1 = valor a imprimir
    adrp x0, str_4
    add x0, x0, :lo12:str_4
    bl printf
    ldr x0, [x29, #-8]                  // x0 = a
    str x0, [sp, #-16]!                 // push x0
    ldr x0, [x29, #-16]                 // x0 = b
    ldr x1, [sp], #16                   // pop x1
    sub w0, w1, w0
    sxtw x0, w0                         // extender el signo a 64 bits
    mov x1, x0                          // x1 = valor a imprimir
    adrp x0, str_2
    add x0, x0, :lo12:str_2
    bl printf
    adrp x0, str_3
    add x0, x0, :lo12:str_3
    bl printf
    // println!  (línea 9)
    ldr x0, [x29, #-8]                  // x0 = a
    mov x1, x0                          // x1 = valor a imprimir
    adrp x0, str_0
    add x0, x0, :lo12:str_0
    bl printf
    ldr x0, [x29, #-16]                 // x0 = b
    mov x1, x0                          // x1 = valor a imprimir
    adrp x0, str_5
    add x0, x0, :lo12:str_5
    bl printf
    ldr x0, [x29, #-8]                  // x0 = a
    str x0, [sp, #-16]!                 // push x0
    ldr x0, [x29, #-16]                 // x0 = b
    ldr x1, [sp], #16                   // pop x1
    mul w0, w1, w0
    sxtw x0, w0                         // extender el signo a 64 bits
    mov x1, x0                          // x1 = valor a imprimir
    adrp x0, str_2
    add x0, x0, :lo12:str_2
    bl printf
    adrp x0, str_3
    add x0, x0, :lo12:str_3
    bl printf
    // println!  (línea 10)
    ldr x0, [x29, #-8]                  // x0 = a
    mov x1, x0                          // x1 = valor a imprimir
    adrp x0, str_0
    add x0, x0, :lo12:str_0
    bl printf
    ldr x0, [x29, #-16]                 // x0 = b
    mov x1, x0                          // x1 = valor a imprimir
    adrp x0, str_6
    add x0, x0, :lo12:str_6
    bl printf
    ldr x0, [x29, #-8]                  // x0 = a
    str x0, [sp, #-16]!                 // push x0
    ldr x0, [x29, #-16]                 // x0 = b
    ldr x1, [sp], #16                   // pop x1
    sdiv w0, w1, w0                     // división entera con signo
    sxtw x0, w0                         // extender el signo a 64 bits
    mov x1, x0                          // x1 = valor a imprimir
    adrp x0, str_2
    add x0, x0, :lo12:str_2
    bl printf
    adrp x0, str_3
    add x0, x0, :lo12:str_3
    bl printf
    // println!  (línea 11)
    ldr x0, [x29, #-8]                  // x0 = a
    mov x1, x0                          // x1 = valor a imprimir
    adrp x0, str_0
    add x0, x0, :lo12:str_0
    bl printf
    ldr x0, [x29, #-16]                 // x0 = b
    mov x1, x0                          // x1 = valor a imprimir
    adrp x0, str_7
    add x0, x0, :lo12:str_7
    bl printf
    ldr x0, [x29, #-8]                  // x0 = a
    str x0, [sp, #-16]!                 // push x0
    ldr x0, [x29, #-16]                 // x0 = b
    ldr x1, [sp], #16                   // pop x1
    sdiv w2, w1, w0                     // w2 = a / b
    msub w0, w2, w0, w1                 // w0 = a - (a / b) * b
    sxtw x0, w0                         // extender el signo a 64 bits
    mov x1, x0                          // x1 = valor a imprimir
    adrp x0, str_2
    add x0, x0, :lo12:str_2
    bl printf
    adrp x0, str_3
    add x0, x0, :lo12:str_3
    bl printf
    // println!  (línea 12)
    mov x0, #7
    neg w0, w0                          // -x
    sxtw x0, w0                         // extender el signo a 64 bits
    str x0, [sp, #-16]!                 // push x0
    mov x0, #2
    ldr x1, [sp], #16                   // pop x1
    sdiv w0, w1, w0                     // división entera con signo
    sxtw x0, w0                         // extender el signo a 64 bits
    mov x1, x0                          // x1 = valor a imprimir
    adrp x0, str_8
    add x0, x0, :lo12:str_8
    bl printf
    mov x0, #7
    neg w0, w0                          // -x
    sxtw x0, w0                         // extender el signo a 64 bits
    str x0, [sp, #-16]!                 // push x0
    mov x0, #3
    ldr x1, [sp], #16                   // pop x1
    sdiv w2, w1, w0                     // w2 = a / b
    msub w0, w2, w0, w1                 // w0 = a - (a / b) * b
    sxtw x0, w0                         // extender el signo a 64 bits
    mov x1, x0                          // x1 = valor a imprimir
    adrp x0, str_9
    add x0, x0, :lo12:str_9
    bl printf
    adrp x0, str_3
    add x0, x0, :lo12:str_3
    bl printf
    // println!  (línea 15)
    mov x0, #2
    str x0, [sp, #-16]!                 // push x0
    mov x0, #3
    str x0, [sp, #-16]!                 // push x0
    mov x0, #4
    ldr x1, [sp], #16                   // pop x1
    mul w0, w1, w0
    sxtw x0, w0                         // extender el signo a 64 bits
    ldr x1, [sp], #16                   // pop x1
    add w0, w1, w0
    sxtw x0, w0                         // extender el signo a 64 bits
    mov x1, x0                          // x1 = valor a imprimir
    adrp x0, str_10
    add x0, x0, :lo12:str_10
    bl printf
    adrp x0, str_3
    add x0, x0, :lo12:str_3
    bl printf
    // println!  (línea 16)
    mov x0, #2
    str x0, [sp, #-16]!                 // push x0
    mov x0, #3
    ldr x1, [sp], #16                   // pop x1
    add w0, w1, w0
    sxtw x0, w0                         // extender el signo a 64 bits
    str x0, [sp, #-16]!                 // push x0
    mov x0, #4
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
    // println!  (línea 17)
    mov x0, #10
    str x0, [sp, #-16]!                 // push x0
    mov x0, #3
    ldr x1, [sp], #16                   // pop x1
    sub w0, w1, w0
    sxtw x0, w0                         // extender el signo a 64 bits
    str x0, [sp, #-16]!                 // push x0
    mov x0, #2
    ldr x1, [sp], #16                   // pop x1
    sub w0, w1, w0
    sxtw x0, w0                         // extender el signo a 64 bits
    mov x1, x0                          // x1 = valor a imprimir
    adrp x0, str_12
    add x0, x0, :lo12:str_12
    bl printf
    adrp x0, str_3
    add x0, x0, :lo12:str_3
    bl printf
    // println!  (línea 18)
    ldr x0, [x29, #-8]                  // x0 = a
    neg w0, w0                          // -x
    sxtw x0, w0                         // extender el signo a 64 bits
    str x0, [sp, #-16]!                 // push x0
    mov x0, #5
    ldr x1, [sp], #16                   // pop x1
    add w0, w1, w0
    sxtw x0, w0                         // extender el signo a 64 bits
    mov x1, x0                          // x1 = valor a imprimir
    adrp x0, str_13
    add x0, x0, :lo12:str_13
    bl printf
    adrp x0, str_3
    add x0, x0, :lo12:str_3
    bl printf
    // let mut x: i32  (línea 21)
    mov x0, #10
    str x0, [x29, #-24]                 // x = x0
    // x = ...  (línea 22)
    ldr x0, [x29, #-24]                 // x0 = x
    str x0, [sp, #-16]!                 // push x0
    mov x0, #2
    ldr x1, [sp], #16                   // pop x1
    mul w0, w1, w0
    sxtw x0, w0                         // extender el signo a 64 bits
    str x0, [sp, #-16]!                 // push x0
    mov x0, #1
    ldr x1, [sp], #16                   // pop x1
    add w0, w1, w0
    sxtw x0, w0                         // extender el signo a 64 bits
    str x0, [x29, #-24]                 // x = x0
    // println!  (línea 23)
    ldr x0, [x29, #-24]                 // x0 = x
    mov x1, x0                          // x1 = valor a imprimir
    adrp x0, str_14
    add x0, x0, :lo12:str_14
    bl printf
    adrp x0, str_3
    add x0, x0, :lo12:str_3
    bl printf
    // x += ...  (línea 24)
    ldr x0, [x29, #-24]                 // x0 = x
    str x0, [sp, #-16]!                 // push x0
    mov x0, #5
    ldr x1, [sp], #16                   // pop x1
    add w0, w1, w0
    sxtw x0, w0                         // extender el signo a 64 bits
    str x0, [x29, #-24]                 // x = x0
    // println!  (línea 25)
    ldr x0, [x29, #-24]                 // x0 = x
    mov x1, x0                          // x1 = valor a imprimir
    adrp x0, str_15
    add x0, x0, :lo12:str_15
    bl printf
    adrp x0, str_3
    add x0, x0, :lo12:str_3
    bl printf
    // x -= ...  (línea 26)
    ldr x0, [x29, #-24]                 // x0 = x
    str x0, [sp, #-16]!                 // push x0
    mov x0, #3
    ldr x1, [sp], #16                   // pop x1
    sub w0, w1, w0
    sxtw x0, w0                         // extender el signo a 64 bits
    str x0, [x29, #-24]                 // x = x0
    // println!  (línea 27)
    ldr x0, [x29, #-24]                 // x0 = x
    mov x1, x0                          // x1 = valor a imprimir
    adrp x0, str_16
    add x0, x0, :lo12:str_16
    bl printf
    adrp x0, str_3
    add x0, x0, :lo12:str_3
    bl printf
    // x *= ...  (línea 28)
    ldr x0, [x29, #-24]                 // x0 = x
    str x0, [sp, #-16]!                 // push x0
    mov x0, #2
    ldr x1, [sp], #16                   // pop x1
    mul w0, w1, w0
    sxtw x0, w0                         // extender el signo a 64 bits
    str x0, [x29, #-24]                 // x = x0
    // println!  (línea 29)
    ldr x0, [x29, #-24]                 // x0 = x
    mov x1, x0                          // x1 = valor a imprimir
    adrp x0, str_17
    add x0, x0, :lo12:str_17
    bl printf
    adrp x0, str_3
    add x0, x0, :lo12:str_3
    bl printf
    // x /= ...  (línea 30)
    ldr x0, [x29, #-24]                 // x0 = x
    str x0, [sp, #-16]!                 // push x0
    mov x0, #4
    ldr x1, [sp], #16                   // pop x1
    sdiv w0, w1, w0                     // división entera con signo
    sxtw x0, w0                         // extender el signo a 64 bits
    str x0, [x29, #-24]                 // x = x0
    // println!  (línea 31)
    ldr x0, [x29, #-24]                 // x0 = x
    mov x1, x0                          // x1 = valor a imprimir
    adrp x0, str_18
    add x0, x0, :lo12:str_18
    bl printf
    adrp x0, str_3
    add x0, x0, :lo12:str_3
    bl printf
    // x %= ...  (línea 32)
    ldr x0, [x29, #-24]                 // x0 = x
    str x0, [sp, #-16]!                 // push x0
    mov x0, #4
    ldr x1, [sp], #16                   // pop x1
    sdiv w2, w1, w0                     // w2 = a / b
    msub w0, w2, w0, w1                 // w0 = a - (a / b) * b
    sxtw x0, w0                         // extender el signo a 64 bits
    str x0, [x29, #-24]                 // x = x0
    // println!  (línea 33)
    ldr x0, [x29, #-24]                 // x0 = x
    mov x1, x0                          // x1 = valor a imprimir
    adrp x0, str_19
    add x0, x0, :lo12:str_19
    bl printf
    adrp x0, str_3
    add x0, x0, :lo12:str_3
    bl printf
    // x %= ...  (línea 34)
    ldr x0, [x29, #-24]                 // x0 = x
    str x0, [sp, #-16]!                 // push x0
    mov x0, #5
    ldr x1, [sp], #16                   // pop x1
    sdiv w2, w1, w0                     // w2 = a / b
    msub w0, w2, w0, w1                 // w0 = a - (a / b) * b
    sxtw x0, w0                         // extender el signo a 64 bits
    str x0, [x29, #-24]                 // x = x0
    // println!  (línea 35)
    ldr x0, [x29, #-24]                 // x0 = x
    mov x1, x0                          // x1 = valor a imprimir
    adrp x0, str_20
    add x0, x0, :lo12:str_20
    bl printf
    adrp x0, str_3
    add x0, x0, :lo12:str_3
    bl printf
    // let maximo: i32  (línea 39)
    movz w0, #65535
    movk w0, #32767, lsl #16
    sxtw x0, w0                         // extender el signo a 64 bits
    str x0, [x29, #-32]                 // maximo = x0
    // println!  (línea 40)
    ldr x0, [x29, #-32]                 // x0 = maximo
    str x0, [sp, #-16]!                 // push x0
    mov x0, #1
    ldr x1, [sp], #16                   // pop x1
    add w0, w1, w0
    sxtw x0, w0                         // extender el signo a 64 bits
    mov x1, x0                          // x1 = valor a imprimir
    adrp x0, str_21
    add x0, x0, :lo12:str_21
    bl printf
    adrp x0, str_3
    add x0, x0, :lo12:str_3
    bl printf
    // println!  (línea 43)
    ldr x0, [x29, #-8]                  // x0 = a
    str x0, [sp, #-16]!                 // push x0
    ldr x0, [x29, #-16]                 // x0 = b
    ldr x1, [sp], #16                   // pop x1
    cmp x1, x0
    cset x0, gt                         // x0 = (izq > der) ? 1 : 0
    adrp x1, str_22
    add x1, x1, :lo12:str_22
    adrp x2, str_23
    add x2, x2, :lo12:str_23
    cmp x0, #0
    csel x1, x1, x2, ne                 // x1 = texto del bool
    adrp x0, str_24
    add x0, x0, :lo12:str_24
    bl printf
    ldr x0, [x29, #-8]                  // x0 = a
    str x0, [sp, #-16]!                 // push x0
    ldr x0, [x29, #-16]                 // x0 = b
    ldr x1, [sp], #16                   // pop x1
    cmp x1, x0
    cset x0, lt                         // x0 = (izq < der) ? 1 : 0
    adrp x1, str_22
    add x1, x1, :lo12:str_22
    adrp x2, str_23
    add x2, x2, :lo12:str_23
    cmp x0, #0
    csel x1, x1, x2, ne                 // x1 = texto del bool
    adrp x0, str_25
    add x0, x0, :lo12:str_25
    bl printf
    ldr x0, [x29, #-8]                  // x0 = a
    str x0, [sp, #-16]!                 // push x0
    mov x0, #17
    ldr x1, [sp], #16                   // pop x1
    cmp x1, x0
    cset x0, eq                         // x0 = (izq == der) ? 1 : 0
    adrp x1, str_22
    add x1, x1, :lo12:str_22
    adrp x2, str_23
    add x2, x2, :lo12:str_23
    cmp x0, #0
    csel x1, x1, x2, ne                 // x1 = texto del bool
    adrp x0, str_26
    add x0, x0, :lo12:str_26
    bl printf
    adrp x0, str_3
    add x0, x0, :lo12:str_3
    bl printf
    // println!  (línea 44)
    ldr x0, [x29, #-8]                  // x0 = a
    str x0, [sp, #-16]!                 // push x0
    ldr x0, [x29, #-16]                 // x0 = b
    ldr x1, [sp], #16                   // pop x1
    cmp x1, x0
    cset x0, ne                         // x0 = (izq != der) ? 1 : 0
    adrp x1, str_22
    add x1, x1, :lo12:str_22
    adrp x2, str_23
    add x2, x2, :lo12:str_23
    cmp x0, #0
    csel x1, x1, x2, ne                 // x1 = texto del bool
    adrp x0, str_27
    add x0, x0, :lo12:str_27
    bl printf
    ldr x0, [x29, #-8]                  // x0 = a
    str x0, [sp, #-16]!                 // push x0
    mov x0, #17
    ldr x1, [sp], #16                   // pop x1
    cmp x1, x0
    cset x0, ge                         // x0 = (izq >= der) ? 1 : 0
    adrp x1, str_22
    add x1, x1, :lo12:str_22
    adrp x2, str_23
    add x2, x2, :lo12:str_23
    cmp x0, #0
    csel x1, x1, x2, ne                 // x1 = texto del bool
    adrp x0, str_28
    add x0, x0, :lo12:str_28
    bl printf
    ldr x0, [x29, #-16]                 // x0 = b
    str x0, [sp, #-16]!                 // push x0
    mov x0, #4
    ldr x1, [sp], #16                   // pop x1
    cmp x1, x0
    cset x0, le                         // x0 = (izq <= der) ? 1 : 0
    adrp x1, str_22
    add x1, x1, :lo12:str_22
    adrp x2, str_23
    add x2, x2, :lo12:str_23
    cmp x0, #0
    csel x1, x1, x2, ne                 // x1 = texto del bool
    adrp x0, str_29
    add x0, x0, :lo12:str_29
    bl printf
    adrp x0, str_3
    add x0, x0, :lo12:str_3
    bl printf
    // let letra: char  (línea 45)
    mov x0, #67
    str x0, [x29, #-40]                 // letra = x0
    // println!  (línea 46)
    ldr x0, [x29, #-40]                 // x0 = letra
    str x0, [sp, #-16]!                 // push x0
    mov x0, #65
    ldr x1, [sp], #16                   // pop x1
    cmp x1, x0
    cset x0, gt                         // x0 = (izq > der) ? 1 : 0
    adrp x1, str_22
    add x1, x1, :lo12:str_22
    adrp x2, str_23
    add x2, x2, :lo12:str_23
    cmp x0, #0
    csel x1, x1, x2, ne                 // x1 = texto del bool
    adrp x0, str_30
    add x0, x0, :lo12:str_30
    bl printf
    ldr x0, [x29, #-40]                 // x0 = letra
    str x0, [sp, #-16]!                 // push x0
    mov x0, #67
    ldr x1, [sp], #16                   // pop x1
    cmp x1, x0
    cset x0, eq                         // x0 = (izq == der) ? 1 : 0
    adrp x1, str_22
    add x1, x1, :lo12:str_22
    adrp x2, str_23
    add x2, x2, :lo12:str_23
    cmp x0, #0
    csel x1, x1, x2, ne                 // x1 = texto del bool
    adrp x0, str_31
    add x0, x0, :lo12:str_31
    bl printf
    adrp x0, str_3
    add x0, x0, :lo12:str_3
    bl printf
    // let t: bool  (línea 49)
    mov x0, #1                          // true
    str x0, [x29, #-48]                 // t = x0
    // let f: bool  (línea 50)
    mov x0, #0                          // false
    str x0, [x29, #-56]                 // f = x0
    // println!  (línea 51)
    ldr x0, [x29, #-48]                 // x0 = t
    cbz x0, .Llogico_fin_2              // izq es false -> resultado false
    ldr x0, [x29, #-56]                 // x0 = f
.Llogico_fin_2:
    adrp x1, str_22
    add x1, x1, :lo12:str_22
    adrp x2, str_23
    add x2, x2, :lo12:str_23
    cmp x0, #0
    csel x1, x1, x2, ne                 // x1 = texto del bool
    adrp x0, str_32
    add x0, x0, :lo12:str_32
    bl printf
    ldr x0, [x29, #-48]                 // x0 = t
    cbnz x0, .Llogico_fin_3             // izq es true -> resultado true
    ldr x0, [x29, #-56]                 // x0 = f
.Llogico_fin_3:
    adrp x1, str_22
    add x1, x1, :lo12:str_22
    adrp x2, str_23
    add x2, x2, :lo12:str_23
    cmp x0, #0
    csel x1, x1, x2, ne                 // x1 = texto del bool
    adrp x0, str_33
    add x0, x0, :lo12:str_33
    bl printf
    ldr x0, [x29, #-48]                 // x0 = t
    eor x0, x0, #1                      // !x  (1 -> 0, 0 -> 1)
    adrp x1, str_22
    add x1, x1, :lo12:str_22
    adrp x2, str_23
    add x2, x2, :lo12:str_23
    cmp x0, #0
    csel x1, x1, x2, ne                 // x1 = texto del bool
    adrp x0, str_34
    add x0, x0, :lo12:str_34
    bl printf
    adrp x0, str_3
    add x0, x0, :lo12:str_3
    bl printf
    // println!  (línea 52)
    ldr x0, [x29, #-8]                  // x0 = a
    str x0, [sp, #-16]!                 // push x0
    mov x0, #10
    ldr x1, [sp], #16                   // pop x1
    cmp x1, x0
    cset x0, gt                         // x0 = (izq > der) ? 1 : 0
    cbz x0, .Llogico_fin_4              // izq es false -> resultado false
    ldr x0, [x29, #-16]                 // x0 = b
    str x0, [sp, #-16]!                 // push x0
    mov x0, #10
    ldr x1, [sp], #16                   // pop x1
    cmp x1, x0
    cset x0, lt                         // x0 = (izq < der) ? 1 : 0
.Llogico_fin_4:
    adrp x1, str_22
    add x1, x1, :lo12:str_22
    adrp x2, str_23
    add x2, x2, :lo12:str_23
    cmp x0, #0
    csel x1, x1, x2, ne                 // x1 = texto del bool
    adrp x0, str_35
    add x0, x0, :lo12:str_35
    bl printf
    adrp x0, str_3
    add x0, x0, :lo12:str_3
    bl printf
    // println!  (línea 53)
    ldr x0, [x29, #-8]                  // x0 = a
    str x0, [sp, #-16]!                 // push x0
    mov x0, #10
    ldr x1, [sp], #16                   // pop x1
    cmp x1, x0
    cset x0, lt                         // x0 = (izq < der) ? 1 : 0
    cbnz x0, .Llogico_fin_5             // izq es true -> resultado true
    ldr x0, [x29, #-16]                 // x0 = b
    str x0, [sp, #-16]!                 // push x0
    mov x0, #5
    ldr x1, [sp], #16                   // pop x1
    cmp x1, x0
    cset x0, eq                         // x0 = (izq == der) ? 1 : 0
.Llogico_fin_5:
    adrp x1, str_22
    add x1, x1, :lo12:str_22
    adrp x2, str_23
    add x2, x2, :lo12:str_23
    cmp x0, #0
    csel x1, x1, x2, ne                 // x1 = texto del bool
    adrp x0, str_36
    add x0, x0, :lo12:str_36
    bl printf
    adrp x0, str_3
    add x0, x0, :lo12:str_3
    bl printf
    // let mut bandera: bool  (línea 54)
    mov x0, #0                          // false
    str x0, [x29, #-64]                 // bandera = x0
    // bandera = ...  (línea 55)
    ldr x0, [x29, #-64]                 // x0 = bandera
    eor x0, x0, #1                      // !x  (1 -> 0, 0 -> 1)
    cbz x0, .Llogico_fin_6              // izq es false -> resultado false
    ldr x0, [x29, #-8]                  // x0 = a
    str x0, [sp, #-16]!                 // push x0
    ldr x0, [x29, #-16]                 // x0 = b
    ldr x1, [sp], #16                   // pop x1
    cmp x1, x0
    cset x0, gt                         // x0 = (izq > der) ? 1 : 0
.Llogico_fin_6:
    str x0, [x29, #-64]                 // bandera = x0
    // println!  (línea 56)
    ldr x0, [x29, #-64]                 // x0 = bandera
    adrp x1, str_22
    add x1, x1, :lo12:str_22
    adrp x2, str_23
    add x2, x2, :lo12:str_23
    cmp x0, #0
    csel x1, x1, x2, ne                 // x1 = texto del bool
    adrp x0, str_37
    add x0, x0, :lo12:str_37
    bl printf
    adrp x0, str_3
    add x0, x0, :lo12:str_3
    bl printf
    // println!  (línea 60)
    ldr x0, [x29, #-8]                  // x0 = a
    mov x1, x0                          // x1 = valor a imprimir
    adrp x0, str_38
    add x0, x0, :lo12:str_38
    bl printf
    adrp x0, str_3
    add x0, x0, :lo12:str_3
    bl printf
.Lfin_main_1:
    mov w0, #0                          // return 0
    mov sp, x29                         // liberar las variables
    ldp x29, x30, [sp], #16             // restaurar marco y retorno
    ret
