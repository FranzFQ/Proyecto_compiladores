%include 'funciones.asm'
section .data
   fmt_float db 'Resultado: %f', 10, 0
   fmt_in_float db '%lf', 0
   a dq 0.0
   b dq 0.0
   c dq 0.0
   d dq 0.0
   e dq 0.0
   f dq 0.0
   const_float_10_0 dq  10.0
   const_float_3_3 dq  3.3
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
   mov [a], eax ; Guardar entero en a
   fld qword [const_float_3_3] ; Cargar float 3.3 en ST0
   mov [b], eax ; Guardar entero en b
   fld qword [a] ; Cargar float a en FPU
   fld qword [b] ; Cargar float b en FPU
   fmulp st1, st0
   sub esp, 8
   fstp qword [esp]
   pop eax
   fstp qword [c] ; Guardar float en c
   fld qword [a] ; Cargar float a en FPU
   fld qword [b] ; Cargar float b en FPU
   fdivp st1, st0
   sub esp, 8
   fstp qword [esp]
   pop eax
   fstp qword [d] ; Guardar float en d
   fld qword [a] ; Cargar float a en FPU
   fld qword [b] ; Cargar float b en FPU
   faddp st1, st0
   sub esp, 8
   fstp qword [esp]
   pop eax
   fstp qword [e] ; Guardar float en e
   fld qword [a] ; Cargar float a en FPU
   fld qword [b] ; Cargar float b en FPU
   fsubp st1, st0
   sub esp, 8
   fstp qword [esp]
   pop eax
   fstp qword [f] ; Guardar float en f
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
   mov eax, 0
   ret