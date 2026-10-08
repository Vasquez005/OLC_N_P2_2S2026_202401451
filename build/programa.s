// Generado por OxigenNative
    .global main
    .extern printf

    .section .data
str_0: .asciz "Hola Mundo\n"
str_1: .asciz "Entero: %d"
str_2: .asciz "\n"
    .balign 8
dbl_0: .double 3.1416
str_3: .asciz "Ana"
str_4: .asciz "%s"
str_5: .asciz " tiene %d"
str_6: .asciz " a\303\261os\n"
str_7: .asciz "pi = %.15g"
str_8: .asciz "true"
str_9: .asciz "false"
str_10: .asciz ", activo = %s"
str_11: .asciz ", letra = %c"
str_12: .asciz ""
str_13: .asciz "Por defecto: %d"
str_14: .asciz " %.15g"
str_15: .asciz " %s"
str_16: .asciz " [%s"
str_17: .asciz "]\n"
str_18: .asciz "r = %.15g"
str_19: .asciz ", grande = %d"
    .balign 8
dbl_1: .double 3.5
str_20: .asciz "edad ahora es %.15g"
str_21: .asciz "100%% listo {ok}\n"
str_22: .asciz "malo = None\n"
str_23: .asciz "Fin\n"

    .section .text

main:
    stp x29, x30, [sp, #-16]!           // guardar x29 (marco) y x30 (retorno)
    mov x29, sp                         // x29 = base del nuevo marco
    sub sp, sp, #112                    // espacio para variables (112 bytes)
    // println!  (línea 3)
    adrp x0, str_0
    add x0, x0, :lo12:str_0
    bl printf
    // println!  (línea 4)
    mov x0, #42
    mov x1, x0                          // x1 = valor a imprimir
    adrp x0, str_1
    add x0, x0, :lo12:str_1
    bl printf
    adrp x0, str_2
    add x0, x0, :lo12:str_2
    bl printf
    // let edad: i32  (línea 6)
    mov x0, #20
    str x0, [x29, #-8]                  // edad = x0
    // let pi: f64  (línea 7)
    adrp x9, dbl_0
    ldr d0, [x9, :lo12:dbl_0]           // d0 = 3.1416
    str d0, [x29, #-16]                 // pi = d0
    // let activo: bool  (línea 8)
    mov x0, #1                          // true
    str x0, [x29, #-24]                 // activo = x0
    // let letra: char  (línea 9)
    mov x0, #65
    str x0, [x29, #-32]                 // letra = x0
    // let nombre: String  (línea 10)
    adrp x0, str_3
    add x0, x0, :lo12:str_3
    str x0, [x29, #-40]                 // nombre = x0
    // println!  (línea 12)
    ldr x0, [x29, #-40]                 // x0 = nombre
    mov x1, x0                          // x1 = valor a imprimir
    adrp x0, str_4
    add x0, x0, :lo12:str_4
    bl printf
    ldr x0, [x29, #-8]                  // x0 = edad
    mov x1, x0                          // x1 = valor a imprimir
    adrp x0, str_5
    add x0, x0, :lo12:str_5
    bl printf
    adrp x0, str_6
    add x0, x0, :lo12:str_6
    bl printf
    // println!  (línea 13)
    ldr d0, [x29, #-16]                 // d0 = pi
    adrp x0, str_7
    add x0, x0, :lo12:str_7
    bl printf
    ldr x0, [x29, #-24]                 // x0 = activo
    adrp x1, str_8
    add x1, x1, :lo12:str_8
    adrp x2, str_9
    add x2, x2, :lo12:str_9
    cmp x0, #0
    csel x1, x1, x2, ne                 // x1 = texto del bool
    adrp x0, str_10
    add x0, x0, :lo12:str_10
    bl printf
    ldr x0, [x29, #-32]                 // x0 = letra
    mov x1, x0                          // x1 = valor a imprimir
    adrp x0, str_11
    add x0, x0, :lo12:str_11
    bl printf
    adrp x0, str_2
    add x0, x0, :lo12:str_2
    bl printf
    // let contador: i32  (línea 16)
    mov x0, #0                          // 0 / false / '\0'
    str x0, [x29, #-48]                 // contador = x0
    // let promedio: f64  (línea 17)
    fmov d0, xzr                        // 0.0
    str d0, [x29, #-56]                 // promedio = d0
    // let vacio: bool  (línea 18)
    mov x0, #0                          // 0 / false / '\0'
    str x0, [x29, #-64]                 // vacio = x0
    // let mensaje: String  (línea 19)
    adrp x0, str_12
    add x0, x0, :lo12:str_12
    str x0, [x29, #-72]                 // mensaje = x0
    // println!  (línea 20)
    ldr x0, [x29, #-48]                 // x0 = contador
    mov x1, x0                          // x1 = valor a imprimir
    adrp x0, str_13
    add x0, x0, :lo12:str_13
    bl printf
    ldr d0, [x29, #-56]                 // d0 = promedio
    adrp x0, str_14
    add x0, x0, :lo12:str_14
    bl printf
    ldr x0, [x29, #-64]                 // x0 = vacio
    adrp x1, str_8
    add x1, x1, :lo12:str_8
    adrp x2, str_9
    add x2, x2, :lo12:str_9
    cmp x0, #0
    csel x1, x1, x2, ne                 // x1 = texto del bool
    adrp x0, str_15
    add x0, x0, :lo12:str_15
    bl printf
    ldr x0, [x29, #-72]                 // x0 = mensaje
    mov x1, x0                          // x1 = valor a imprimir
    adrp x0, str_16
    add x0, x0, :lo12:str_16
    bl printf
    adrp x0, str_17
    add x0, x0, :lo12:str_17
    bl printf
    // let r: f64  (línea 23)
    mov x0, #7
    scvtf d0, x0                        // promoción i32 -> f64
    str d0, [x29, #-80]                 // r = d0
    // let grande: i32  (línea 24)
    movz w0, #65535
    movk w0, #32767, lsl #16
    sxtw x0, w0                         // extender el signo a 64 bits
    str x0, [x29, #-88]                 // grande = x0
    // println!  (línea 25)
    ldr d0, [x29, #-80]                 // d0 = r
    adrp x0, str_18
    add x0, x0, :lo12:str_18
    bl printf
    ldr x0, [x29, #-88]                 // x0 = grande
    mov x1, x0                          // x1 = valor a imprimir
    adrp x0, str_19
    add x0, x0, :lo12:str_19
    bl printf
    adrp x0, str_2
    add x0, x0, :lo12:str_2
    bl printf
    // let edad: f64  (línea 28)
    adrp x9, dbl_1
    ldr d0, [x9, :lo12:dbl_1]           // d0 = 3.5
    str d0, [x29, #-96]                 // edad = d0
    // println!  (línea 29)
    ldr d0, [x29, #-96]                 // d0 = edad
    adrp x0, str_20
    add x0, x0, :lo12:str_20
    bl printf
    adrp x0, str_2
    add x0, x0, :lo12:str_2
    bl printf
    // println!  (línea 32)
    adrp x0, str_21
    add x0, x0, :lo12:str_21
    bl printf
    // println!  (línea 33)
    adrp x0, str_2
    add x0, x0, :lo12:str_2
    bl printf
    // println!  (línea 37)
    adrp x0, str_22
    add x0, x0, :lo12:str_22
    bl printf
    // println!  (línea 38)
    adrp x0, str_23
    add x0, x0, :lo12:str_23
    bl printf
.Lfin_main_1:
    mov w0, #0                          // return 0
    mov sp, x29                         // liberar las variables
    ldp x29, x30, [sp], #16             // restaurar marco y retorno
    ret
