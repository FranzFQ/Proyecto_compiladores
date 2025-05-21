%include 'funciones.asm'
section .data
   a dd 0
   b dd 0
   mensaje db 'Es menor', 0
   mensaje2 db 'Es mayor', 0
   newline db 0xA
section .bss
   char resb 16
section .text
   global _start
_start:
   mov eax, 1 ; Cargar número 1 en eax
   mov [a], eax; Guardar resultado en a
   mov eax, 15 ; Cargar número 15 en eax
   mov [b], eax; Guardar resultado en b


etiqueta_inicio:
   mov eax, [a] ; Cargar variable a en eax
   push eax; guardar en la pila
   mov eax, [b] ; Cargar variable b en eax
   pop ebx; recuperar el primer operando
   cmp eax, ebx; comparar eax y ebx
   mov eax, 0; cargar 0 en eax
   setl al; eax = eax < ebx
   cmp eax, 0 ; Comparar resultado con 0
   jne etiqueta_fin_while ; Saltar al final si la condición es falsa
   mov eax, [a] ; Cargar variable a en eax
   push eax; guardar en la pila
   mov eax, 1 ; Cargar número 1 en eax
   pop ebx; recuperar el primer operando
   add eax, ebx; eax = eax + ebx
   mov [a], eax; Guardar resultado en a
   mov eax, [a] ; Cargar variable a en eax
   call printnum
   jmp etiqueta_inicio ; Saltar al inicio del ciclo
etiqueta_fin_while:
   mov eax, mensaje2 ; Cargar variable mensaje2 en eax
   call printStr
   call quit