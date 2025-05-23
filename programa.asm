%include 'funciones.asm'
section .data
   mensaje db 'prueba de ingreso', 0
   exito db 'prueba de ingreso exitosa', 0
   newline db 0xA
section .bss
   char resb 16
section .text
   global _start
_start:


   mov eax, mensaje ; Cargar variable mensaje en eax
   call printStr
   mov eax, exito ; Cargar variable exito en eax
   call printStr
   mov eax, 0 ; Cargar número 0 en eax
   ret ; Retornar desde la subrutina
   call quit