%include 'funciones.asm'
section .data
   a dd 0
   signo_menos db '-'
   charr db 12 dup(0)
   newline db 0xA
section .bss
   char resb 16
section .text
   global _start
_start:
   mov eax, 30 ; Cargar número 30 en eax
   mov [a], eax; Guardar resultado en a
   mov eax, [a] ; Cargar variable a en eax
   call printnum
   call quit