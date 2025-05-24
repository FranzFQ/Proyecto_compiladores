%include 'funciones.asm'
section .data
   fmt_float db 'Resultado: %f', 10, 0
   fmt_in_float db '%lf', 0
   a dq 0.0
   signo_menos db '-'
   charr db 12 dup(0)
   newline db 0xA
section .bss
   char resb 16
section .text
   extern printf
   extern scanf
   global main
main:

   push a
   push fmt_in_float
   call scanf
   add esp, 8
   fld qword [a]
   sub esp, 8
   fstp qword [esp]
   push fmt_float
   call printf
   add esp, 12
   mov eax, 0
   ret