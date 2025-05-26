%include 'funciones.asm'
section .data
   fmt_float db 'Resultado: %f', 10, 0
   fmt_in_float db '%lf', 0
   a dd 0
   b dd 0
   c dq 0.0
   d dq 0.0
   e dq 0.0
   cadena_0 db 'El valor ingresado es', 0
   cadena_1 db 'Fin del programa', 0
   const_float_2_3 dq  2.3
   const_float_5_0 dq  5.0
   const_float_2_5 dq  2.5
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
   mov eax, 23 ; Cargar número 23 en eax
   mov [a], eax ; Guardar entero en a
   mov eax, 4 ; Cargar número 4 en eax
   mov [b], eax ; Guardar entero en b
   fld qword [const_float_2_3] ; Cargar float 2.3 en ST0
   mov eax, [b] ; Cargar variable b en eax
sub esp, 4
   mov [esp], eax
   fild dword [esp]
   add esp, 4
   faddp st1, st0
   fstp qword [c] ; Guardar float en c
   fld qword [const_float_5_0] ; Cargar float 5.0 en ST0
   fstp qword [d] ; Guardar float en d

   push e
   push fmt_in_float
   call scanf
   add esp, 8
   mov eax, cadena_0 ; Cargar variable cadena_0 en eax
   call printStr
   fld qword [e]
   sub esp, 8
   fstp qword [esp]
   push fmt_float
   call printf
   add esp, 12
etiqueta_inicio_140050219166176:
   mov eax, [b] ; Cargar variable b en eax
   push eax; guardar en la pila
   mov eax, [a] ; Cargar variable a en eax
   pop ebx; recuperar el primer operando
   cmp eax, ebx; comparar eax y ebx
   mov eax, 0; cargar 0 en eax
   setl al; eax = eax < ebx
   cmp eax, 0 ; Comparar resultado con 0
   jne etiqueta_fin_while_140050219166176 ; Saltar al final si la condición es falsa
   mov eax, [b] ; Cargar variable b en eax
   push eax; guardar en la pila
   mov eax, 1 ; Cargar número 1 en eax
   pop ebx; recuperar el primer operando
   add eax, ebx; eax = eax + ebx
   mov [b], eax ; Guardar entero en b
   fld qword [d] ; Cargar float d en FPU
   fld qword [const_float_2_5] ; Cargar float 2.5 en ST0
   faddp st1, st0
   fstp qword [d] ; Guardar float en d
   fld qword [d]
   sub esp, 8
   fstp qword [esp]
   push fmt_float
   call printf
   add esp, 12
   jmp etiqueta_inicio_140050219166176 ; Saltar al inicio del ciclo
etiqueta_fin_while_140050219166176:
   mov eax, cadena_1 ; Cargar variable cadena_1 en eax
   call printStr
   mov eax, [b] ; Cargar variable b en eax
   call printnum
   mov eax, 0
   ret