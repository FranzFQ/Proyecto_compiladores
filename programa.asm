%include 'funciones.asm'
section .data
   a dd 0
   b dd 0
   c dd 0
   x dd 0
   y dd 0
   z dd 0
   cadena_0 db 'z es mayor que veinte', 0
   newline db 0xA
section .bss
   char resb 16
section .text
   global _start
suma:
   mov eax, [esp + 4]
   mov [a], eax
   mov eax, [esp + 8]
   mov [b], eax
   mov eax, [a] ; Cargar variable a en eax
   push eax; guardar en la pila
   mov eax, [b] ; Cargar variable b en eax
   pop ebx; recuperar el primer operando
   add eax, ebx; eax = eax + ebx
   mov [c], eax; Guardar resultado en c
   mov eax, [c] ; Cargar variable c en eax
   call printnum
   mov eax, [c] ; Cargar variable c en eax
   ret ; Retornar desde la subrutina
   mov eax, 0 ; Cargar número 0 en eax
   ret ; Retornar desde la subrutina
_start:
   mov eax, 1 ; Cargar número 1 en eax
   mov [x], eax; Guardar resultado en x
   mov eax, 5 ; Cargar número 5 en eax
   mov [y], eax; Guardar resultado en y
   mov eax, [y] ; Cargar variable y en eax
   push eax
   mov eax, [x] ; Cargar variable x en eax
   push eax
   call suma
   add esp, 8
   mov [z], eax; Guardar resultado en z
   mov eax, [z] ; Cargar variable z en eax
   call printnum
etiqueta_inicio:
   mov eax, [z] ; Cargar variable z en eax
   push eax; guardar en la pila
   mov eax, 20 ; Cargar número 20 en eax
   pop ebx; recuperar el primer operando
   cmp eax, ebx; comparar eax y ebx
   mov eax, 0; cargar 0 en eax
   setl al; eax = eax < ebx
   cmp eax, 0 ; Comparar resultado con 0
   jne etiqueta_fin_while ; Saltar al final si la condición es falsa
   mov eax, [z] ; Cargar variable z en eax
   push eax; guardar en la pila
   mov eax, 1 ; Cargar número 1 en eax
   pop ebx; recuperar el primer operando
   add eax, ebx; eax = eax + ebx
   mov [z], eax; Guardar resultado en z
   mov eax, [z] ; Cargar variable z en eax
   call printnum
   jmp etiqueta_inicio ; Saltar al inicio del ciclo
etiqueta_fin_while:
   mov eax, cadena_0 ; Cargar variable cadena_0 en eax
   call printStr
   mov eax, 0 ; Cargar número 0 en eax
   ret ; Retornar desde la subrutina
   call quit