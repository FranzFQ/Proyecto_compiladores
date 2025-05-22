%include 'funciones.asm'
section .data
   a dd 0
   menor db 'es menor', 0
   mayor db 'Es mayor', 0
   newline db 0xA
section .bss
   char resb 16
section .text
   global _start
_start:
   mov eax, a ; Cargar dirección de la variable en eax
   call input
   mov eax, [a] ; Cargar variable a en eax
   push eax; guardar en la pila
   mov eax, 5 ; Cargar número 5 en eax
   pop ebx; recuperar el primer operando
   cmp eax, ebx; comparar eax y ebx
   mov eax, 0; cargar 0 en eax
   setl al; eax = eax < ebx
   cmp eax, 0 ; Comparar resultado con 0
   jne etiqueta_else ; Saltar a else si la condición es falsa
   mov eax, menor ; Cargar variable menor en eax
   call printStr
   jmp etiqueta_fin_if ; Saltar al final del if
etiqueta_else:
   mov eax, mayor ; Cargar variable mayor en eax
   call printStr
etiqueta_fin_if:
   call quit