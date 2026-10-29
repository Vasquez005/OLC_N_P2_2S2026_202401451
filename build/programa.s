// Generado por OxigenNative
    .global main
    // Funciones de la biblioteca de C que se usan
    .extern printf, snprintf, malloc, calloc, memcpy, strlen,
    .extern strcpy, strcat, strcmp, exit, strstr, strncat, rand, srand, time,
    .extern setvbuf, stdout

    .section .data
str_0: .asciz "a[1] = %d"
str_1: .asciz ", a[4] = %d"
str_2: .asciz "\n"
str_3: .asciz "["
str_4: .asciz ", "
str_5: .asciz "%d"
str_6: .asciz "]"
str_7: .asciz "suma = %d"
str_8: .asciz "slice &a[1..3] = "
str_9: .asciz "matriz sigue en 0: m[0][1] = %d"
str_10: .asciz ", m[1][0] = %d"
str_11: .asciz "uno dos tres"
str_12: .asciz " "
str_13: .asciz "split: partes[1] = %s"
str_14: .asciz ", partes[3] = %s"
    .balign 8
dbl_0: .double 1.5
    .balign 8
dbl_1: .double 2.5
str_15: .asciz "f[2] = %s"
    .balign 8
dbl_2: .double 1000000000000000.0
str_16: .asciz "%.1f"
str_17: .asciz "%.15g"
str_18: .asciz "\n[Error de ejecuci\303\263n] L\303\255nea %d, Columna %d: \303\215ndice fuera de los l\303\255mites del arreglo (\303\255ndice %d, longitud %d).\n"

    .section .bss
    .balign 8
buf_f64:  .skip 64                     // texto de un f64 al imprimir
buf_char: .skip 8                      // texto UTF-8 de un char
oxi_semilla: .skip 8                   // 1 si ya se inicializó random

    .section .text

fn_suma:
    stp x29, x30, [sp, #-16]!           // guardar x29 (marco) y x30 (retorno)
    mov x29, sp                         // x29 = base del nuevo marco
    sub sp, sp, #32                     // espacio para variables (32 bytes)
    str x0, [x29, #-8]                  // parámetro a = x0
    // let mut total: i32  (línea 2)
    mov x0, #0
    str x0, [x29, #-16]                 // total = x0
    // let mut i: i32  (línea 3)
    mov x0, #1
    str x0, [x29, #-24]                 // i = x0
    // while  (línea 4)
.Lwhile_inicio_2:
    ldr x0, [x29, #-24]                 // x0 = i
    str x0, [sp, #-16]!                 // push x0
    // .len()  (línea 4)
    mov x0, #4
    ldr x1, [sp], #16                   // pop x1
    cmp x1, x0
    cset x0, le                         // x0 = (izq <= der) ? 1 : 0
    cbz x0, .Lwhile_fin_3               // condición false -> salir del while
    // total += ...  (línea 5)
    ldr x0, [x29, #-16]                 // x0 = total
    str x0, [sp, #-16]!                 // push x0
    ldr x0, [x29, #-8]                  // x0 = a
    str x0, [sp, #-16]!                 // push x0
    ldr x0, [x29, #-24]                 // x0 = i
    sub x0, x0, #1                      // índice desde 1: a[1] es la posición 0
    mov x12, #4
    cmp x0, x12
    b.lo .Lindice_ok_4                  // 0 <= índice < largo
    mov x2, x0
    add x2, x2, #1                      // escribió el usuario, no la posición
    mov x3, x12
    mov x0, #5
    mov x1, #18
    bl __oxi_fuera_limites
.Lindice_ok_4:
    ldr x1, [sp], #16                   // pop x1
    mov x12, #8
    madd x0, x0, x12, x1                // x0 = base + índice * tamaño
    ldr x0, [x0]                        // leer el elemento
    ldr x1, [sp], #16                   // pop x1
    add w0, w1, w0
    sxtw x0, w0                         // extender el signo a 64 bits
    str x0, [x29, #-16]                 // total = x0
    // i += ...  (línea 6)
    ldr x0, [x29, #-24]                 // x0 = i
    str x0, [sp, #-16]!                 // push x0
    mov x0, #1
    ldr x1, [sp], #16                   // pop x1
    add w0, w1, w0
    sxtw x0, w0                         // extender el signo a 64 bits
    str x0, [x29, #-24]                 // i = x0
    b .Lwhile_inicio_2                  // volver a evaluar la condición
.Lwhile_fin_3:
    ldr x0, [x29, #-16]                 // x0 = total
    b .Lfin_suma_1                      // return  (línea 8)
    mov x0, #0                          // 0 / false / '\0'
.Lfin_suma_1:
    mov sp, x29                         // liberar las variables
    ldp x29, x30, [sp], #16             // restaurar marco y retorno
    ret

main:
    stp x29, x30, [sp, #-16]!           // guardar x29 (marco) y x30 (retorno)
    mov x29, sp                         // x29 = base del nuevo marco
    sub sp, sp, #48                     // espacio para variables (48 bytes)
    adrp x0, stdout
    ldr x0, [x0, :lo12:stdout]          // x0 = stdout
    mov x1, #0
    mov x2, #1                          // _IOLBF: vaciar en cada salto de línea
    mov x3, #0
    bl setvbuf
    // let mut a: [i32; 4]  (línea 11)
    // arreglo [i32; 4]  (línea 11)
    mov x0, #32
    bl malloc                           // reservar 32 bytes en el heap
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
    mov x0, #40
    ldr x10, [sp]                       // x10 = bloque
    add x10, x10, #24
    str x0, [x10]                       // elemento en el byte 24
    ldr x0, [sp], #16                   // pop x0
    str x0, [x29, #-8]                  // a = x0
    // println!  (línea 12)
    ldr x0, [x29, #-8]                  // x0 = a
    ldr x0, [x0]                        // leer el elemento
    mov x1, x0                          // x1 = valor a imprimir
    adrp x0, str_0
    add x0, x0, :lo12:str_0
    bl printf
    ldr x0, [x29, #-8]                  // x0 = a
    add x0, x0, #24
    ldr x0, [x0]                        // leer el elemento
    mov x1, x0                          // x1 = valor a imprimir
    adrp x0, str_1
    add x0, x0, :lo12:str_1
    bl printf
    adrp x0, str_2
    add x0, x0, :lo12:str_2
    bl printf
    // elemento = ...  (línea 13)
    ldr x0, [x29, #-8]                  // x0 = a
    add x0, x0, #8
    str x0, [sp, #-16]!                 // push x0
    mov x0, #99
    ldr x10, [sp], #16                  // pop x10
    str x0, [x10]                       // guardar el elemento
    // elemento += ...  (línea 14)
    ldr x0, [x29, #-8]                  // x0 = a
    add x0, x0, #16
    str x0, [sp, #-16]!                 // push x0
    ldr x0, [sp]
    ldr x0, [x0]                        // valor actual
    str x0, [sp, #-16]!                 // push x0
    mov x0, #1
    ldr x1, [sp], #16                   // pop x1
    add w0, w1, w0
    sxtw x0, w0                         // extender el signo a 64 bits
    ldr x10, [sp], #16                  // pop x10
    str x0, [x10]                       // guardar el elemento
    // println!  (línea 15)
    ldr x0, [x29, #-8]                  // x0 = a
    mov x1, #4
    str x0, [sp, #-16]!                 // push x0
    str x1, [sp, #-16]!                 // push x1
    str xzr, [sp, #-16]!                // [sp] = i = 0
    adrp x0, str_3
    add x0, x0, :lo12:str_3
    bl printf
.Limprimir_6:
    ldr x11, [sp]
    ldr x12, [sp, #16]                  // largo
    cmp x11, x12
    b.ge .Limprimir_fin_7
    cbz x11, .Lsin_coma_8               // antes del primero no va coma
    adrp x0, str_4
    add x0, x0, :lo12:str_4
    bl printf
.Lsin_coma_8:
    ldr x11, [sp]
    ldr x10, [sp, #32]                  // datos
    mov x12, #8
    madd x0, x11, x12, x10              // x0 = dirección del elemento i
    ldr x0, [x0]
    mov x1, x0                          // x1 = valor a imprimir
    adrp x0, str_5
    add x0, x0, :lo12:str_5
    bl printf
    ldr x11, [sp]
    add x11, x11, #1
    str x11, [sp]                       // i += 1
    b .Limprimir_6
.Limprimir_fin_7:
    adrp x0, str_6
    add x0, x0, :lo12:str_6
    bl printf
    add sp, sp, #48                     // quitar i, largo y datos
    adrp x0, str_2
    add x0, x0, :lo12:str_2
    bl printf
    // println!  (línea 16)
    // llamada a suma()  (línea 16)
    ldr x0, [x29, #-8]                  // x0 = a
    mov x1, #32
    bl __oxi_copiar
    str x0, [sp, #-16]!                 // push x0
    ldr x0, [sp], #16                   // pop x0
    bl fn_suma
    mov x1, x0                          // x1 = valor a imprimir
    adrp x0, str_7
    add x0, x0, :lo12:str_7
    bl printf
    adrp x0, str_2
    add x0, x0, :lo12:str_2
    bl printf
    // let s: [i32; 2]  (línea 17)
    // slice [0..2]  (línea 17)
    ldr x0, [x29, #-8]                  // x0 = a
    mov x1, #16
    bl __oxi_copiar
    str x0, [x29, #-16]                 // s = x0
    // println!  (línea 18)
    ldr x0, [x29, #-16]                 // x0 = s
    str x0, [sp, #-16]!                 // push x0
    adrp x0, str_8
    add x0, x0, :lo12:str_8
    bl printf
    ldr x0, [sp], #16                   // pop x0
    mov x1, #2
    str x0, [sp, #-16]!                 // push x0
    str x1, [sp, #-16]!                 // push x1
    str xzr, [sp, #-16]!                // [sp] = i = 0
    adrp x0, str_3
    add x0, x0, :lo12:str_3
    bl printf
.Limprimir_9:
    ldr x11, [sp]
    ldr x12, [sp, #16]                  // largo
    cmp x11, x12
    b.ge .Limprimir_fin_10
    cbz x11, .Lsin_coma_11              // antes del primero no va coma
    adrp x0, str_4
    add x0, x0, :lo12:str_4
    bl printf
.Lsin_coma_11:
    ldr x11, [sp]
    ldr x10, [sp, #32]                  // datos
    mov x12, #8
    madd x0, x11, x12, x10              // x0 = dirección del elemento i
    ldr x0, [x0]
    mov x1, x0                          // x1 = valor a imprimir
    adrp x0, str_5
    add x0, x0, :lo12:str_5
    bl printf
    ldr x11, [sp]
    add x11, x11, #1
    str x11, [sp]                       // i += 1
    b .Limprimir_9
.Limprimir_fin_10:
    adrp x0, str_6
    add x0, x0, :lo12:str_6
    bl printf
    add sp, sp, #48                     // quitar i, largo y datos
    adrp x0, str_2
    add x0, x0, :lo12:str_2
    bl printf
    // let m: [[i32; 2]; 2]  (línea 19)
    // arreglo [[i32; 2]; 2]  (línea 19)
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
    str x0, [x29, #-24]                 // m = x0
    // println!  (línea 20)
    ldr x0, [x29, #-24]                 // x0 = m
    add x0, x0, #8
    ldr x0, [x0]                        // leer el elemento
    mov x1, x0                          // x1 = valor a imprimir
    adrp x0, str_9
    add x0, x0, :lo12:str_9
    bl printf
    ldr x0, [x29, #-24]                 // x0 = m
    add x0, x0, #16
    ldr x0, [x0]                        // leer el elemento
    mov x1, x0                          // x1 = valor a imprimir
    adrp x0, str_10
    add x0, x0, :lo12:str_10
    bl printf
    adrp x0, str_2
    add x0, x0, :lo12:str_2
    bl printf
    // let partes: [String]  (línea 21)
    // .split()  (línea 21)
    adrp x0, str_11
    add x0, x0, :lo12:str_11
    str x0, [sp, #-16]!                 // push x0
    adrp x0, str_12
    add x0, x0, :lo12:str_12
    mov x1, x0
    ldr x0, [sp], #16                   // pop x0
    bl __oxi_split
    str x0, [x29, #-32]                 // partes = x0
    // println!  (línea 22)
    ldr x0, [x29, #-32]                 // x0 = partes
    str x0, [sp, #-16]!                 // push x0
    mov x0, #1
    sub x0, x0, #1                      // índice desde 1: a[1] es la posición 0
    ldr x1, [sp]
    ldr x12, [x1]                       // x12 = largo (guardado en el bloque)
    cmp x0, x12
    b.lo .Lindice_ok_12                 // 0 <= índice < largo
    mov x2, x0
    add x2, x2, #1                      // escribió el usuario, no la posición
    mov x3, x12
    mov x0, #22
    mov x1, #55
    bl __oxi_fuera_limites
.Lindice_ok_12:
    ldr x1, [sp], #16                   // pop x1
    add x1, x1, #8                      // saltar el largo
    mov x12, #8
    madd x0, x0, x12, x1                // x0 = base + índice * tamaño
    ldr x0, [x0]                        // leer el elemento
    mov x1, x0                          // x1 = valor a imprimir
    adrp x0, str_13
    add x0, x0, :lo12:str_13
    bl printf
    ldr x0, [x29, #-32]                 // x0 = partes
    str x0, [sp, #-16]!                 // push x0
    mov x0, #3
    sub x0, x0, #1                      // índice desde 1: a[1] es la posición 0
    ldr x1, [sp]
    ldr x12, [x1]                       // x12 = largo (guardado en el bloque)
    cmp x0, x12
    b.lo .Lindice_ok_13                 // 0 <= índice < largo
    mov x2, x0
    add x2, x2, #1                      // escribió el usuario, no la posición
    mov x3, x12
    mov x0, #22
    mov x1, #66
    bl __oxi_fuera_limites
.Lindice_ok_13:
    ldr x1, [sp], #16                   // pop x1
    add x1, x1, #8                      // saltar el largo
    mov x12, #8
    madd x0, x0, x12, x1                // x0 = base + índice * tamaño
    ldr x0, [x0]                        // leer el elemento
    mov x1, x0                          // x1 = valor a imprimir
    adrp x0, str_14
    add x0, x0, :lo12:str_14
    bl printf
    adrp x0, str_2
    add x0, x0, :lo12:str_2
    bl printf
    // let f: [f64; 2]  (línea 23)
    // arreglo [f64; 2]  (línea 23)
    mov x0, #16
    bl malloc                           // reservar 16 bytes en el heap
    str x0, [sp, #-16]!                 // push x0
    adrp x9, dbl_0
    ldr d0, [x9, :lo12:dbl_0]           // d0 = 1.5
    ldr x10, [sp]                       // x10 = bloque
    str d0, [x10]                       // elemento en el byte 0
    adrp x9, dbl_1
    ldr d0, [x9, :lo12:dbl_1]           // d0 = 2.5
    ldr x10, [sp]                       // x10 = bloque
    add x10, x10, #8
    str d0, [x10]                       // elemento en el byte 8
    ldr x0, [sp], #16                   // pop x0
    str x0, [x29, #-40]                 // f = x0
    // println!  (línea 24)
    ldr x0, [x29, #-40]                 // x0 = f
    add x0, x0, #8
    ldr d0, [x0]                        // leer el elemento
    bl __oxi_f64_str
    mov x1, x0                          // x1 = valor a imprimir
    adrp x0, str_15
    add x0, x0, :lo12:str_15
    bl printf
    adrp x0, str_2
    add x0, x0, :lo12:str_2
    bl printf
    // let mut k: i32  (línea 25)
    mov x0, #0
    str x0, [x29, #-48]                 // k = x0
    // println!  (línea 26)
    ldr x0, [x29, #-8]                  // x0 = a
    str x0, [sp, #-16]!                 // push x0
    ldr x0, [x29, #-48]                 // x0 = k
    sub x0, x0, #1                      // índice desde 1: a[1] es la posición 0
    mov x12, #4
    cmp x0, x12
    b.lo .Lindice_ok_14                 // 0 <= índice < largo
    mov x2, x0
    add x2, x2, #1                      // escribió el usuario, no la posición
    mov x3, x12
    mov x0, #26
    mov x1, #20
    bl __oxi_fuera_limites
.Lindice_ok_14:
    ldr x1, [sp], #16                   // pop x1
    mov x12, #8
    madd x0, x0, x12, x1                // x0 = base + índice * tamaño
    ldr x0, [x0]                        // leer el elemento
    mov x1, x0                          // x1 = valor a imprimir
    adrp x0, str_5
    add x0, x0, :lo12:str_5
    bl printf
    adrp x0, str_2
    add x0, x0, :lo12:str_2
    bl printf
.Lfin_main_5:
    mov w0, #0                          // return 0
    mov sp, x29                         // liberar las variables
    ldp x29, x30, [sp], #16             // restaurar marco y retorno
    ret

// ---- __oxi_copiar: x0 = origen, x1 = bytes -> x0 = copia nueva en el heap ----
__oxi_copiar:
    stp x29, x30, [sp, #-32]!
    mov x29, sp
    stp x19, x20, [sp, #16]
    mov x19, x0                         // x19 = origen
    mov x20, x1                         // x20 = bytes
    mov x0, x20
    bl malloc
    mov x1, x19
    mov x2, x20
    bl memcpy                           // memcpy(nuevo, origen, bytes) -> x0 = nuevo
    ldp x19, x20, [sp, #16]
    ldp x29, x30, [sp], #32
    ret

// ---- __oxi_f64_str: d0 -> x0 = texto del f64 ----
__oxi_f64_str:
    stp x29, x30, [sp, #-16]!
    mov x29, sp
    adrp x2, str_17
    add x2, x2, :lo12:str_17         // formato "%.15g" por defecto
    frintz d1, d0                       // d1 = parte entera
    fcmp d1, d0
    b.ne .Lf64_formato                  // tiene decimales -> "%.15g"
    fabs d1, d0
    adrp x9, dbl_2
    ldr d2, [x9, :lo12:dbl_2]
    fcmp d1, d2
    b.ge .Lf64_formato                  // número enorme -> "%.15g"
    adrp x2, str_16
    add x2, x2, :lo12:str_16          // entero -> "%.1f" (3.0)
.Lf64_formato:
    adrp x0, buf_f64
    add x0, x0, :lo12:buf_f64
    mov x1, #64
    bl snprintf                         // snprintf(buf, 64, formato, d0)
    adrp x0, buf_f64
    add x0, x0, :lo12:buf_f64
    ldp x29, x30, [sp], #16
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
    adrp x0, str_18
    add x0, x0, :lo12:str_18
    bl printf
    mov w0, #1
    bl exit                             // exit vacía el búfer de printf

// ---- __oxi_split: x0 = texto, x1 = separador -> x0 = arreglo dinámico ----
// Resultado en el heap:  [ largo | parte0 | parte1 | ... ]
// Primero cuenta las partes (apariciones + 1), luego copia cada una.
__oxi_split:
    stp x29, x30, [sp, #-64]!
    mov x29, sp
    stp x19, x20, [sp, #16]
    stp x21, x22, [sp, #32]
    stp x23, x24, [sp, #48]
    mov x19, x0                         // x19 = texto
    mov x20, x1                         // x20 = separador
    mov x0, x20
    bl strlen
    mov x21, x0                         // x21 = largo del separador
    cbz x21, .Lspl_uno                  // separador "": una sola parte
    mov x22, #1                         // x22 = cantidad de partes
    mov x23, x19
.Lspl_contar:
    mov x0, x23
    mov x1, x20
    bl strstr
    cbz x0, .Lspl_reservar
    add x22, x22, #1
    add x23, x0, x21
    b .Lspl_contar
.Lspl_reservar:
    lsl x0, x22, #3
    add x0, x0, #8
    bl malloc
    mov x24, x0                         // x24 = arreglo
    str x22, [x24]                      // largo
    mov x22, #0                         // x22 = índice de la parte
    mov x23, x19                        // x23 = inicio de la parte
.Lspl_parte:
    mov x0, x23
    mov x1, x20
    bl strstr                           // x0 = fin de la parte (o 0)
    cbz x0, .Lspl_ultima
    str x0, [sp, #-16]!
    sub x1, x0, x23
    mov x0, x23
    bl __oxi_subcadena
    add x9, x24, #8
    str x0, [x9, x22, lsl #3]           // arreglo[i] = parte
    add x22, x22, #1
    ldr x0, [sp], #16
    add x23, x0, x21                    // la siguiente empieza después del separador
    b .Lspl_parte
.Lspl_ultima:
    mov x0, x23
    bl strlen
    mov x1, x0
    mov x0, x23
    bl __oxi_subcadena
    add x9, x24, #8
    str x0, [x9, x22, lsl #3]
    mov x0, x24
    b .Lspl_fin
.Lspl_uno:
    mov x0, #16
    bl malloc
    mov x24, x0
    mov x1, #1
    str x1, [x24]
    mov x0, x19
    bl strlen
    mov x1, x0
    mov x0, x19
    bl __oxi_subcadena
    str x0, [x24, #8]
    mov x0, x24
.Lspl_fin:
    ldp x19, x20, [sp, #16]
    ldp x21, x22, [sp, #32]
    ldp x23, x24, [sp, #48]
    ldp x29, x30, [sp], #64
    ret

// ---- __oxi_subcadena: x0 = inicio, x1 = largo -> x0 = texto nuevo ----
__oxi_subcadena:
    stp x29, x30, [sp, #-32]!
    mov x29, sp
    stp x19, x20, [sp, #16]
    mov x19, x0
    mov x20, x1
    add x0, x20, #1
    bl malloc
    mov x1, x19
    mov x2, x20
    bl memcpy                           // x0 = nuevo
    strb wzr, [x0, x20]                 // terminar con '\0'
    ldp x19, x20, [sp, #16]
    ldp x29, x30, [sp], #32
    ret
