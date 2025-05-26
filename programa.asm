%include 'funciones.asm'
section .data
<<<<<<< HEAD
   n dd 0
   m dd 0
   mayor dd 0
   menor dd 0
   cadena_0 db 'El mayor es m con un valor de', 0
   cadena_1 db 'El mayor es n con un valor de', 0
=======
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
>>>>>>> assembler
   signo_menos db '-'
   charr db 12 dup(0)
   newline db 0xA
section .bss
   char resb 16
section .text
<<<<<<< HEAD
   global _start
_start:




   mov eax, n ; Cargar dirección de la variable en eax
   call inputNum
   mov eax, m ; Cargar dirección de la variable en eax
   call inputNum
   mov eax, [m] ; Cargar variable m en eax
   push eax; guardar en la pila
   mov eax, [n] ; Cargar variable n en eax
   pop ebx; recuperar el primer operando
   cmp eax, ebx; comparar eax y ebx
   mov eax, 0; cargar 0 en eax
   setg al; eax = eax > ebx
   cmp eax, 0 ; Comparar resultado con 0
   jne etiqueta_else ; Saltar a else si la condición es falsa
   mov eax, [m] ; Cargar variable m en eax
   mov [mayor], eax; Guardar resultado en mayor
   mov eax, [n] ; Cargar variable n en eax
   mov [menor], eax; Guardar resultado en menor
   mov eax, cadena_0 ; Cargar variable cadena_0 en eax
   call printStr
   mov eax, [m] ; Cargar variable m en eax
   call printnum
   jmp etiqueta_fin_if ; Saltar al final del if
etiqueta_else:
   mov eax, [n] ; Cargar variable n en eax
   mov [mayor], eax; Guardar resultado en mayor
   mov eax, [m] ; Cargar variable m en eax
   mov [menor], eax; Guardar resultado en menor
   mov eax, cadena_1 ; Cargar variable cadena_1 en eax
   call printStr
   mov eax, [mayor] ; Cargar variable mayor en eax
   call printnum
etiqueta_fin_if:
   call quit
=======
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
>>>>>>> assembler
