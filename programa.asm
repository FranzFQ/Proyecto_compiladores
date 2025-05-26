%include 'funciones.asm'
section .data
   fmt_float db 'Resultado: %f', 10, 0
   fmt_in_float db '%lf', 0
   a dd 0
   b dd 0
   cadena_0 db 'a es menor que b', 0
   cadena_1 db 'a es mayor que b', 0
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
   mov eax, 6 ; Cargar número 6 en eax
   mov [a], eax ; Guardar entero en a
   mov eax, 5 ; Cargar número 5 en eax
   mov [b], eax ; Guardar entero en b
   mov eax, [a] ; Cargar variable a en eax
   push eax; guardar en la pila
   mov eax, [b] ; Cargar variable b en eax
   pop ebx; recuperar el primer operando
   cmp eax, ebx; comparar eax y ebx
   mov eax, 0; cargar 0 en eax
   setl al; eax = eax < ebx
   cmp eax, 0 ; Comparar resultado con 0
   jne etiqueta_else_140709786729776 ; Saltar a else si la condición es falsa
   mov eax, cadena_0 ; Cargar variable cadena_0 en eax
   call printStr
   jmp etiqueta_fin_if_140709786729776 ; Saltar al final del if
etiqueta_else_140709786729776:
   mov eax, cadena_1 ; Cargar variable cadena_1 en eax
   call printStr
etiqueta_fin_if_140709786729776:
   mov eax, 0
   ret