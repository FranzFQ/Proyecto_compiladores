%include 'funciones.asm'
section .data
   a dd 0
   b dd 0
   signo_menos db '-'
   charr db 12 dup(0)
   newline db 0xA
section .bss
   char resb 16
section .text
   global _start
_start:


   mov eax, a ; Cargar dirección de la variable en eax
   call inputNum
   mov eax, [a] ; Cargar variable a en eax
   push eax; guardar en la pila
   mov eax, 10 ; Cargar número 10 en eax
   pop ebx; recuperar el primer operando
   sub ebx, eax; ebx = ebx - eax
   mov eax, ebx; eax = ebx
   mov [b], eax; Guardar resultado en b
   mov eax, [b] ; Cargar variable b en eax
   call printnum
   call quit