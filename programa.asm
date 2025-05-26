%include 'funciones.asm'
section .data
   fmt_float db 'Resultado: %f', 10, 0
   fmt_in_float db '%lf', 0
   a dq 0.0
   b dq 0.0
   m dd 0
   c dq 0.0
   d dq 0.0
   e dq 0.0
   f dq 0.0
   g dq 0.0
   const_float_10_0 dq  10.0
   const_float_3_3 dq  3.3
   const_float_3_6 dq  3.6
   const_float_1_2 dq  1.2
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
   fld qword [const_float_10_0] ; Cargar float 10.0 en ST0
   fstp qword [a] ; Guardar float en a
   fld qword [const_float_3_3] ; Cargar float 3.3 en ST0
   fstp qword [b] ; Guardar float en b
   mov eax, 3 ; Cargar número 3 en eax
   mov [m], eax ; Guardar entero en m
   fld qword [const_float_3_6] ; Cargar float 3.6 en ST0
   fld qword [b] ; Cargar float b en FPU
   fdivp st1, st0
   fstp qword [c] ; Guardar float en c
   fld qword [a] ; Cargar float a en FPU
   fld qword [b] ; Cargar float b en FPU
   fdivp st1, st0
   fstp qword [d] ; Guardar float en d
   fld qword [a] ; Cargar float a en FPU
   fld qword [b] ; Cargar float b en FPU
   faddp st1, st0
   fstp qword [e] ; Guardar float en e
   fld qword [a] ; Cargar float a en FPU
   fld qword [b] ; Cargar float b en FPU
   fsubp st1, st0
   fstp qword [f] ; Guardar float en f
   fld qword [m] ; Cargar float m en FPU
sub esp, 4
   mov [esp], eax
   fild dword [esp]
   add esp, 4
   fld qword [const_float_1_2] ; Cargar float 1.2 en ST0
   faddp st1, st0
   fstp qword [g] ; Guardar float en g
   fld qword [c]
   sub esp, 8
   fstp qword [esp]
   push fmt_float
   call printf
   add esp, 12
   fld qword [d]
   sub esp, 8
   fstp qword [esp]
   push fmt_float
   call printf
   add esp, 12
   fld qword [e]
   sub esp, 8
   fstp qword [esp]
   push fmt_float
   call printf
   add esp, 12
   fld qword [f]
   sub esp, 8
   fstp qword [esp]
   push fmt_float
   call printf
   add esp, 12
   fld qword [g]
   sub esp, 8
   fstp qword [esp]
   push fmt_float
   call printf
   add esp, 12
   mov eax, 0
   ret