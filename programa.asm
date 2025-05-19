%include 'funciones.asm'
section .data
   x dd 0
   y dd 0
   z dd 0
   newline db 0xA
section .bss
   char resb 16
section .text
   global _start
_start:
   mov eax, 1 ; Cargar número 1 en eax
   mov [x], eax; Guardar resultado en x
   mov eax, 5 ; Cargar número 5 en eax
   mov [y], eax; Guardar resultado en y
   mov eax, 6 ; Cargar número 6 en eax
   mov [z], eax; Guardar resultado en z
etiqueta_inicio:
   mov eax, [x] ; Cargar variable x en eax
   push eax; guardar en la pila
   mov eax, 10 ; Cargar número 10 en eax
   pop ebx; recuperar el primer operando
   cmp eax, ebx; comparar eax y ebx
   mov eax, 0; cargar 0 en eax
   setl al; eax = eax < ebx
   cmp eax, 0 ; Comparar resultado con 0
   jne etiqueta_fin_while ; Saltar al final si la condición es falsa
   mov eax, [x] ; Cargar variable x en eax
   push eax; guardar en la pila
   mov eax, 1 ; Cargar número 1 en eax
   pop ebx; recuperar el primer operando
   add eax, ebx; eax = eax + ebx
   mov [x], eax; Guardar resultado en x
   jmp etiqueta_inicio ; Saltar al inicio del ciclo
etiqueta_fin_while:
   mov eax, [x] ; Cargar variable x en eax
   call printnum
   call quit