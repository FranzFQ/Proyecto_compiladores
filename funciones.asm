
;---------------------- Imprimir cadena ----------- 
printStr:
    ; Guardar registros en pila
    push edx
    push ecx
    push ebx
    push eax ; Acá apunta a la cadena

    call strlen   ; llamada a la funcion de conteo de caracter
    
    mov edx, eax ; longitud de cadena
    pop eax
    mov ecx, eax  ; Cadena a imprimir

    mov ebx, 1    ; tipo de salida (1 implica salida por pantalla) (STDOUT file)
    mov eax, 4    ; SYS_WRITE (Kernel opcode 4)
    int 80h       ; Se imprime en pantalla

    ; ----- salto de línea -----
    push eax      ; Preservar eax
    mov eax, 4    ; SYS_WRITE
    mov ebx, 1    ; STDOUT
    mov ecx, newline ; Dirección del salto de línea
    mov edx, 1    ; Longitud 1 byte
    int 80h
    pop eax       ; Restaurar eax
    ; ----------------------------------



    pop ebx
    pop ecx
    pop edx
    ret
; ----------------------- funcion input --------------------
inputStr:
    push    edx
    push    ecx
    push    ebx
    push    eax

    mov     ebx, 45 ; suponiendo un tamaño para la cadena de 30

    mov     edx, ebx        ; edx = espacio total para lectura
    mov     ecx, eax        ; ecx = dir. de memoria para almacenar el dato
    mov     ebx, 0          ; lee desde STDIN
    mov     eax, 3          ; servicio de sistema SYS_READ
    int     80h             ; llamada al sistema

    pop     eax
    pop     ebx
    pop     ecx
    pop     edx
    ret


; --------------------- Funcion de ingreso de numeros ----------
inputNum:
    push eax
    push ecx
    push edx
    push esi
    push ebx

    ; Leer cadena con inputStr (resultado va en [eax])
    call inputStr

    mov esi, eax        ; ESI apunta al inicio de la cadena
    xor ecx, ecx        ; ECX = acumulador numérico
    xor edx, edx        ; EDX = dígito temporal
    xor ebx, ebx        ; EBX = flag de signo negativo (0=positivo, 1=negativo)

    ; Verificar si es negativo
    mov dl, [esi]
    cmp dl, '-'
    jne .convertir

    ; Es negativo
    mov ebx, 1          ; Marcar como negativo
    inc esi             ; Avanzar al siguiente carácter

.convertir:
    mov dl, [esi]
    cmp dl, 10          ; Enter (salto de línea)
    je .fin_convertir
    cmp dl, 0
    je .fin_convertir

    sub dl, '0'         ; ASCII -> número
    imul ecx, ecx, 10
    add ecx, edx
    inc esi
    jmp .convertir

.fin_convertir:
    cmp ebx, 1
    jne .almacenar

    ; Aplicar signo negativo
    neg ecx

.almacenar:
    mov [eax], ecx      ; Guardar número en memoria

    pop ebx
    pop esi
    pop edx
    pop ecx
    pop eax
    ret




; --------------------- funcion de salida --------------------
quit:
    mov ebx, 0    ; return 0 status on exit
    mov eax, 1    ; SYS_EXIT (kernel opcode 1)
    int 80h       ; Fin del programa


;--------------------- calculo de longitud de cadena -------------
strlen:
    push ebx
    mov ebx, eax

nextChar:
    cmp byte [eax], 0
    jz finLen
    inc eax
    jmp nextChar

finLen:
    sub eax, ebx
    pop ebx
    ret


;--------------------- Imprimir variables que contengan número --------------

printnum: 
    push edx
    push ecx
    push ebx
    push eax            ; Guardar número original (negativo o no)

    mov ebx, eax        ; Copiar eax a ebx para análisis
    cmp ebx, 0
    jge .positivo       ; Si es positivo, saltar

    ; Manejo de número negativo
    ; Imprimir signo '-'
    mov eax, 4
    mov ebx, 1
    mov ecx, signo_menos
    mov edx, 1
    int 0x80

    ; Convertir a positivo para impresión
    pop eax             ; Recuperar original
    neg eax             ; eax = -eax
    push eax            ; Guardar valor positivo nuevamente
.positivo:

    ; Conversión a cadena decimal
    pop eax             ; eax tiene el número positivo
    mov ecx, 10         ; Divisor
    mov edi, charr+11
    mov byte [edi], 0   ; Null terminator
    dec edi
    mov byte [edi], 0xA ; Newline
    dec edi
    mov esi, 2          ; Contador de caracteres (newline + null)

convert_loop:
    xor edx, edx
    div ecx             ; eax / 10, resto en edx
    add dl, '0'
    mov [edi], dl
    dec edi
    inc esi
    test eax, eax
    jnz convert_loop

    inc edi             ; Ajustar puntero al inicio del número

    ; Imprimir el número
    mov eax, 4
    mov ebx, 1
    mov ecx, edi
    mov edx, esi
    int 0x80

    pop ebx
    pop ecx
    pop edx
    ret

