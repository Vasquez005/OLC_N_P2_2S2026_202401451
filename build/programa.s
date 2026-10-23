// Generado por OxigenNative
    .global main
    // Funciones de la biblioteca de C que se usan
    .extern printf, snprintf, malloc, calloc, memcpy, strlen,
    .extern strcpy, strcat, strcmp, exit, strstr, strncat, rand, srand, time

    .section .data
str_0: .asciz "None\n"
str_1: .asciz "antes del error de ejecuci\303\263n: "
str_2: .asciz "["
str_3: .asciz ", "
str_4: .asciz "%d"
str_5: .asciz "]"
str_6: .asciz "\n"
str_7: .asciz "numeros[%d"
str_8: .asciz "] = %d"
str_9: .asciz "esto ya no se imprime\n"
str_10: .asciz "\n[Error de ejecuci\303\263n] L\303\255nea %d, Columna %d: \303\215ndice fuera de los l\303\255mites del arreglo (\303\255ndice %d, longitud %d).\n"

    .section .bss
    .balign 8
buf_f64:  .skip 64                     // texto de un f64 al imprimir
buf_char: .skip 8                      // texto UTF-8 de un char
oxi_semilla: .skip 8                   // 1 si ya se inicializó random

    .section .text

main:
    stp x29, x30, [sp, #-16]!           // guardar x29 (marco) y x30 (retorno)
    mov x29, sp                         // x29 = base del nuevo marco
    sub sp, sp, #64                     // espacio para variables (64 bytes)
    // let numeros: [i32; 3]  (línea 3)
    // arreglo [i32; 3]  (línea 3)
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
    // println!  (línea 4)
    adrp x0, str_0
    add x0, x0, :lo12:str_0
    bl printf
    // let x: i32  (línea 6)
    mov x0, #5
    str x0, [x29, #-24]                 // x = x0
    // println!  (línea 7)
    adrp x0, str_0
    add x0, x0, :lo12:str_0
    bl printf
    // println!  (línea 8)
    adrp x0, str_0
    add x0, x0, :lo12:str_0
    bl printf
    // let mut m: [[i32; 2]; 2]  (línea 10)
    // arreglo [[i32; 2]; 2]  (línea 10)
    mov x0, #32
    bl malloc                           // reservar 32 bytes en el heap
    str x0, [sp, #-16]!                 // push x0
    mov x0, #1
    ldr x10, [sp]                       // x10 = bloque
    str x0, [x10]                       // elemento en el byte 0
    mov x0, #2
    ldr x10, [sp]                       // x10 = bloque
    add x10, x10, #8
    str x0, [x10]                       // elemento en el byte 8
    mov x0, #3
    ldr x10, [sp]                       // x10 = bloque
    add x10, x10, #16
    str x0, [x10]                       // elemento en el byte 16
    mov x0, #4
    ldr x10, [sp]                       // x10 = bloque
    add x10, x10, #24
    str x0, [x10]                       // elemento en el byte 24
    ldr x0, [sp], #16                   // pop x0
    str x0, [x29, #-32]                 // m = x0
    // println!  (línea 14)
    ldr x0, [x29, #-32]                 // x0 = m
    str x0, [sp, #-16]!                 // push x0
    adrp x0, str_1
    add x0, x0, :lo12:str_1
    bl printf
    ldr x0, [sp], #16                   // pop x0
    mov x1, #2
    str x0, [sp, #-16]!                 // push x0
    str x1, [sp, #-16]!                 // push x1
    str xzr, [sp, #-16]!                // [sp] = i = 0
    adrp x0, str_2
    add x0, x0, :lo12:str_2
    bl printf
.Limprimir_2:
    ldr x11, [sp]
    ldr x12, [sp, #16]                  // largo
    cmp x11, x12
    b.ge .Limprimir_fin_3
    cbz x11, .Lsin_coma_4               // antes del primero no va coma
    adrp x0, str_3
    add x0, x0, :lo12:str_3
    bl printf
.Lsin_coma_4:
    ldr x11, [sp]
    ldr x10, [sp, #32]                  // datos
    mov x12, #16
    madd x0, x11, x12, x10              // x0 = dirección del elemento i
    mov x1, #2
    str x0, [sp, #-16]!                 // push x0
    str x1, [sp, #-16]!                 // push x1
    str xzr, [sp, #-16]!                // [sp] = i = 0
    adrp x0, str_2
    add x0, x0, :lo12:str_2
    bl printf
.Limprimir_5:
    ldr x11, [sp]
    ldr x12, [sp, #16]                  // largo
    cmp x11, x12
    b.ge .Limprimir_fin_6
    cbz x11, .Lsin_coma_7               // antes del primero no va coma
    adrp x0, str_3
    add x0, x0, :lo12:str_3
    bl printf
.Lsin_coma_7:
    ldr x11, [sp]
    ldr x10, [sp, #32]                  // datos
    mov x12, #8
    madd x0, x11, x12, x10              // x0 = dirección del elemento i
    ldr x0, [x0]
    mov x1, x0                          // x1 = valor a imprimir
    adrp x0, str_4
    add x0, x0, :lo12:str_4
    bl printf
    ldr x11, [sp]
    add x11, x11, #1
    str x11, [sp]                       // i += 1
    b .Limprimir_5
.Limprimir_fin_6:
    adrp x0, str_5
    add x0, x0, :lo12:str_5
    bl printf
    add sp, sp, #48                     // quitar i, largo y datos
    ldr x11, [sp]
    add x11, x11, #1
    str x11, [sp]                       // i += 1
    b .Limprimir_2
.Limprimir_fin_3:
    adrp x0, str_5
    add x0, x0, :lo12:str_5
    bl printf
    add sp, sp, #48                     // quitar i, largo y datos
    adrp x0, str_6
    add x0, x0, :lo12:str_6
    bl printf
    // let mut i: i32  (línea 15)
    mov x0, #0
    str x0, [x29, #-56]                 // i = x0
    // while  (línea 16)
.Lwhile_inicio_8:
    ldr x0, [x29, #-56]                 // x0 = i
    str x0, [sp, #-16]!                 // push x0
    mov x0, #10
    ldr x1, [sp], #16                   // pop x1
    cmp x1, x0
    cset x0, lt                         // x0 = (izq < der) ? 1 : 0
    cbz x0, .Lwhile_fin_9               // condición false -> salir del while
    // println!  (línea 17)
    ldr x0, [x29, #-56]                 // x0 = i
    mov x1, x0                          // x1 = valor a imprimir
    adrp x0, str_7
    add x0, x0, :lo12:str_7
    bl printf
    ldr x0, [x29, #-8]                  // x0 = numeros
    str x0, [sp, #-16]!                 // push x0
    ldr x0, [x29, #-56]                 // x0 = i
    mov x12, #3
    cmp x0, x12
    b.lo .Lindice_ok_10                 // 0 <= índice < largo
    mov x2, x0
    mov x3, x12
    mov x0, #17
    mov x1, #41
    bl __oxi_fuera_limites
.Lindice_ok_10:
    ldr x1, [sp], #16                   // pop x1
    mov x12, #8
    madd x0, x0, x12, x1                // x0 = base + índice * tamaño
    ldr x0, [x0]                        // leer el elemento
    mov x1, x0                          // x1 = valor a imprimir
    adrp x0, str_8
    add x0, x0, :lo12:str_8
    bl printf
    adrp x0, str_6
    add x0, x0, :lo12:str_6
    bl printf
    // i += ...  (línea 18)
    ldr x0, [x29, #-56]                 // x0 = i
    str x0, [sp, #-16]!                 // push x0
    mov x0, #1
    ldr x1, [sp], #16                   // pop x1
    add w0, w1, w0
    sxtw x0, w0                         // extender el signo a 64 bits
    str x0, [x29, #-56]                 // i = x0
    b .Lwhile_inicio_8                  // volver a evaluar la condición
.Lwhile_fin_9:
    // println!  (línea 20)
    adrp x0, str_9
    add x0, x0, :lo12:str_9
    bl printf
.Lfin_main_1:
    mov w0, #0                          // return 0
    mov sp, x29                         // liberar las variables
    ldp x29, x30, [sp], #16             // restaurar marco y retorno
    ret

// ---- __oxi_fuera_limites: x0 = línea, x1 = columna, x2 = índice, x3 = largo ----
// Imprime el error y termina el programa con código 1.
__oxi_fuera_limites:
    stp x29, x30, [sp, #-16]!
    mov x29, sp
    mov x4, x3
    mov x3, x2
    mov x2, x1
    mov x1, x0
    adrp x0, str_10
    add x0, x0, :lo12:str_10
    bl printf
    mov w0, #1
    bl exit                             // exit vacía el búfer de printf
