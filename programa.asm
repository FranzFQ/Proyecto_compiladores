%include 'funciones.asm'
section .data
   n dd 0
   m dd 0
   mayor dd 0
   menor dd 0
   cadena_0 db 'El mayor es m con un valor de', 0
   cadena_1 db 'El mayor es n con un valor de', 0
   signo_menos db '-'
   charr db 12 dup(0)
   newline db 0xA
section .bss
   char resb 16
section .text
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