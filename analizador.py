import re
# from analisis_semantico import AnalizadorSemantico, TablaSimbolos

# Op relacional = <, >, =, !, <=, >=, ==, !=,
# Op lógicos = &, &&, |, ||, !
# Definir patrones de tokens

token_patron = {
    "KEYWORD": r'\b(if|else|while|for|return|int|str|float|void|class|def|print|inputStr|inputNum)\b',
    "IDENTIFIER": r'\b[a-zA-Z_][a-zA-Z0-9_]*\b',
    "NUMBER": r'\b\d+(\.\d+)?\b',
    "OPERATOR": r'<=|>=|==|!=|&&|"|[\+\-\*/=<>\!\||\|\']',
    "DELIMITER": r'[(),;{}]',  # Paréntesis, llaves, punto y coma
    "WHITESPACE": r'\s+'  # Espacios en blanco
}


def tokenize(text):
    patron_general = "|".join(f"(?P<{token}>{patron})" for token, patron in token_patron.items())
    patron_regex = re.compile(patron_general)

    tokens_encontrados = []

    for match in patron_regex.finditer(text):
        for token, valor in match.groupdict().items():
            if valor is not None and token != "WHITESPACE":
                tokens_encontrados.append((token, valor))
    return tokens_encontrados


class NodoAST:
    # Clase base para todos los nodos del AST
    def traducir(self):
        raise NotImplementedError("Método traducir no implementado en este nodo")
    
    def generar_codigo(self):
        raise NotImplementedError("Método generar_codigo no implementado en este nodo")


class NodoPrograma(NodoAST):
    def __init__(self, funciones):
        self.funciones = funciones
        self.analizador_semantico = AnalizadorSemantico()
        self.analisis = None

    def generar_codigo(self):
        # Genera el código ensamblador incluyendo las variables en .data automáticamente
        self.analisis = self.analizador_semantico.analizar(self)

        # Ahora self.analizador_semantico contiene las tablas de variables y funciones

        self.variables = self.analizador_semantico.tabla_simbolos.variables  # Resetear variables
        self.cadenas = self.analizador_semantico.tabla_simbolos.cadenas  # Resetear cadenas
        self.flotantes = self.analizador_semantico.tabla_simbolos.flotantes

        codigo = []
        # Para agregar las funciones de imprimir = %include 'funciones.asm'
        codigo.append(f"%include 'funciones.asm'")

        # Sección de datos (incluye variables detectadas)
        codigo.append("section .data")
        codigo.append("   fmt_float db 'Resultado: %f', 10, 0")
        codigo.append("   fmt_in_float db '%lf', 0")
        for var, tipo in self.variables.items():
            # Se debe implementar que dependiendo del tipo de variable se reserve el espacio necesario
            
            if tipo == 'int':
                codigo.append(f"   {var} dd 0")
            elif tipo == 'float':
                if var not in self.flotantes:
                    codigo.append(f"   {var} dq 0.0")
            elif tipo == 'str':
                # Reservar espacio para una cadena de caracteres
                # Verificar que la cadena no exista en la tabla de cadenas
                if var not in self.cadenas:
                    codigo.append(f"   {var} times 128 db 0")
            elif tipo == 'char':
                # Reservar espacio para un carácter
                codigo.append(f"   {var} db 0x00")
        # Agregar cadenas a la sección de datos
        for nombre, valor in self.cadenas.items():
            # Reservar espacio para la cadena
            codigo.append(f"   {nombre} db '{valor}', 0")
        for nombre, valor in self.flotantes.items():
            codigo.append(f"   {nombre} dq  {valor}")
        codigo.append("   signo_menos db '-'")
        codigo.append("   charr db 12 dup(0)")  # Buffer para número convertido
          
        # Agregar variable salto de línea
        codigo.append("   newline db 0xA")  # Salto de línea
        codigo.append("section .bss")
        codigo.append("   char resb 16") # Reservar espacio para un carácter
        
        # Sección de código
        codigo.append("section .text")
        codigo.append("   extern printf")
        codigo.append("   extern scanf")
        codigo.append("   global main")
        
        for funcion in self.funciones:
            if funcion.nombre[1] == 'main':
                # Convertimos main en _start
                codigo.append("main:")
                for instruccion in funcion.cuerpo:
                    codigo.append(instruccion.generar_codigo(self.variables))
                codigo.append("   mov eax, 0")  # sys_exit
                codigo.append("   ret")
            else:
                codigo.append(funcion.generar_codigo(self.variables))    
        # Función para imprimir un numero
        return "\n".join(codigo)
    
    def traducir(self):
        return "\n\n".join(f.traducir() for f in self.funciones)


class NodoFuncion(NodoAST):
    # Nodo que representa una función
    def __init__(self, nombre, parametros, cuerpo, tipo_retorno):
        self.nombre = nombre
        self.parametros = parametros
        self.cuerpo = cuerpo
        self.tipo_retorno = tipo_retorno


    def traducir(self):
        params = ", ".join(p.traducir() for p in self.parametros)
        cuerpo = "\n   ".join(c.traducir() for c in self.cuerpo)
        return f"def {self.nombre[1]}({params}):\n   {cuerpo}"
    
    def generar_codigo(self, vars):
        codigo = []
        if self.nombre[1] != 'main':  # Solo generar etiqueta si no es main
            codigo.append(f'{self.nombre[1]}:')
            for i, param in enumerate(self.parametros):
                codigo.append(f'   mov eax, [esp + {4*(i+1)}]')
                codigo.append(f'   mov [{param.nombre[1]}], eax')
        
        # Generar código para el cuerpo
        for instruccion in self.cuerpo:
            codigo.append(instruccion.generar_codigo(vars))
        
        
        return '\n'.join(codigo)

class NodoParametro(NodoAST):
    # Nodo que representa un parámetro de función
    def __init__(self, tipo, nombre):
        self.tipo = tipo
        self.nombre = nombre

    def traducir(self):
        return f"{self.nombre[1]}"


class NodoAsignacion(NodoAST):
    # Nodo que representa una asignación de variable
    def __init__(self, nombre, expresion):
        self.nombre = nombre
        self.expresion = expresion

    def traducir(self):
        return f"{self.nombre[1]} = {self.expresion.traducir()}"

    def generar_codigo(self, vars):
        codigo = self.expresion.generar_codigo(vars)
        if isinstance(self.expresion, NodoOperacion) and self.expresion.tipo == 'float':
            codigo += f'\n   fstp qword [{self.nombre[1]}] ; Guardar float en {self.nombre[1]}'
        elif isinstance(self.expresion, NodoNumero) and isinstance(self.expresion.valor, float):
            codigo += f'\n   fstp qword [{self.nombre[1]}] ; Guardar float en {self.nombre[1]}'
        else:
            codigo += f'\n   mov [{self.nombre[1]}], eax ; Guardar entero en {self.nombre[1]}'
        return codigo
    
class NodoAsignacionCadena(NodoAST):
    # Nodo que representa una asignación de cadena
    def __init__(self, nombre, expresion):
        self.nombre = nombre
        self.expresion = expresion

    def generar_codigo(self, vars):
        # No se necesita código, ya que se declara en la sección de datos
        return ""


class NodoOperacion(NodoAST):
    # Nodo que representa una operación aritmética
    def __init__(self, izquierda, operador, derecha):
        self.izquierda = izquierda
        self.operador = operador
        self.derecha = derecha
        self.tipo = None

    def simplificar(self):
        if isinstance(self.izquierda, NodoOperacion):
            izquierda_sim = self.izquierda.simplificar()
        else:
            izquierda_sim = self.izquierda

        if (isinstance(izquierda_sim, NodoOperacion) and
            isinstance(izquierda_sim.izquierda, NodoNumero) and
            isinstance(izquierda_sim.derecha, NodoNumero)):
            
            resultado = 0

            if izquierda_sim.operador[1] == "+":
                resultado = izquierda_sim.izquierda.valor + izquierda_sim.derecha.valor
            elif izquierda_sim.operador[1] == "-":
                resultado = izquierda_sim.izquierda.valor - izquierda_sim.derecha.valor
            elif izquierda_sim.operador[1] == "*":
                resultado = izquierda_sim.izquierda.valor * izquierda_sim.derecha.valor
            elif izquierda_sim.operador[1] == "/" and izquierda_sim.derecha.valor != 0:
                resultado = izquierda_sim.izquierda.valor / izquierda_sim.derecha.valor
            print(resultado)
            izquierda_sim = NodoNumero(resultado)

        return NodoOperacion(izquierda_sim, self.operador, self.derecha)
    


        
    def traducir(self):
        return f"{self.izquierda.traducir()} {self.operador[1]} {self.derecha.traducir()}"
    
    def codigo_flotantes(self, izq, der, vars):
        codigo = []

        codigo.append(izq.generar_codigo(vars))
        if isinstance(izq.valor, int):
            codigo.append("sub esp, 4\n   mov [esp], eax\n   fild dword [esp]\n   add esp, 4") # sirve para convertir el (identificador / numero) entero a flotante y dejarlo en pila

        codigo.append(der.generar_codigo(vars))
        if isinstance(der.valor, int):
            codigo.append("sub esp, 4\n   mov [esp], eax\n   fild dword [esp]\n   add esp, 4") # sirve para convertir el (identificador / numero) entero a flotante y dejarlo en pila


        if self.operador[1] == '+':
            codigo.append('   faddp st1, st0')  # st1 = st1 + st0, pop st0
        elif self.operador[1] == '-':
            codigo.append('   fsubp st1, st0')
        elif self.operador[1] == '*':
            codigo.append('   fmulp st1, st0')
        elif self.operador[1] == '/':
            codigo.append('   fdivp st1, st0')

        # Guardar resultado en memoria (puedes usar una temp o pasar por eax si deseas imprimir)
        return '\n'.join(codigo)

    def codigo_enteros(self, izq, der, vars):
        codigo = []
        codigo.append(izq.generar_codigo(vars)) # Cargar el operando izquierdo
        codigo.append('   push eax; guardar en la pila') # Guardar en la pila
        codigo.append(der.generar_codigo(vars)) # Cargar el operando derecho
        codigo.append('   pop ebx; recuperar el primer operando') # Sacar de la pila
        # ebx = op1 y eax = op2
        if self.operador[1] == '+':
            codigo.append('   add eax, ebx; eax = eax + ebx')
        elif self.operador[1] == '-':
            codigo.append('   sub ebx, eax; ebx = ebx - eax')
            codigo.append('   mov eax, ebx; eax = ebx')
        elif self.operador[1] == '*':
            codigo.append('   imul ebx; eax = eax * ebx')
        elif self.operador[1] == '/':
            codigo.append('   mov edx, 0; limpiar edx')
            codigo.append('   idiv ebx; eax = eax / ebx')
        elif self.operador[1] == '<':
            codigo.append('   cmp eax, ebx; comparar eax y ebx')
            codigo.append('   mov eax, 0; cargar 0 en eax')
            codigo.append('   setl al; eax = eax < ebx')
        elif self.operador[1] == '>':
            codigo.append('   cmp eax, ebx; comparar eax y ebx')
            codigo.append('   mov eax, 0; cargar 0 en eax')
            codigo.append('   setg al; eax = eax > ebx')
        return '\n'.join(codigo)

    def generar_codigo(self, vars):

        simplified = None
        if isinstance(self.izquierda, NodoOperacion) or isinstance(self.derecha, NodoOperacion):
            simplified = self.simplificar()
        
        izq = None
        der = None

        if simplified:
            izq = simplified.izquierda
            der = simplified.derecha
        else:
            izq = self.izquierda
            der = self.derecha

        if isinstance(izq, NodoNumero) and isinstance(der, NodoNumero):
            if isinstance(izq.valor, int) and isinstance(der.valor, int):
                self.tipo = 'int'
                return self.codigo_enteros(izq, der, vars)
            else:
                self.tipo = 'float'
                return self.codigo_flotantes(izq, der, vars)
            
        elif isinstance(izq, NodoIdentificador) and isinstance(der, NodoIdentificador):
            if vars[izq.nombre[1]] == 'int' and vars[der.nombre[1]] == 'int':
                self.tipo = 'int'
                return self.codigo_enteros(izq, der, vars)
            elif vars[izq.nombre[1]] == 'float' and vars[der.nombre[1]]== 'int':
                self.tipo = 'float'
                codigo = []
                codigo.append(izq.generar_codigo(vars))
                codigo.append(der.generar_codigo(vars))
                codigo.append("sub esp, 4\n   mov [esp], eax\n   fild dword [esp]\n   add esp, 4") # sirve para convertir el (identificador / numero) entero a flotante y dejarlo en pila
                if self.operador[1] == '+':
                    codigo.append('   faddp st1, st0')  # st1 = st1 + st0, pop st0
                elif self.operador[1] == '-':
                    codigo.append('   fsubp st1, st0')
                elif self.operador[1] == '*':
                    codigo.append('   fmulp st1, st0')
                elif self.operador[1] == '/':
                    codigo.append('   fdivp st1, st0')

                # Guardar resultado en memoria (puedes usar una temp o pasar por eax si deseas imprimir)
                return '\n'.join(codigo)
            elif vars[izq.nombre[1]] == 'int' and vars[der.nombre[1]] == 'float':
                self.tipo = 'float'
                codigo = []
                codigo.append(izq.generar_codigo(vars))
                codigo.append("sub esp, 4\n   mov [esp], eax\n   fild dword [esp]\n   add esp, 4") # sirve para convertir el (identificador / numero) entero a flotante y dejarlo en pila
                codigo.append(der.generar_codigo(vars))
                if self.operador[1] == '+':
                    codigo.append('   faddp st1, st0')  # st1 = st1 + st0, pop st0
                elif self.operador[1] == '-':
                    codigo.append('   fsubp st1, st0')
                elif self.operador[1] == '*':
                    codigo.append('   fmulp st1, st0')
                elif self.operador[1] == '/':
                    codigo.append('   fdivp st1, st0')

                # Guardar resultado en memoria (puedes usar una temp o pasar por eax si deseas imprimir)
                return '\n'.join(codigo)
            else:
                self.tipo = 'float'
                codigo = []
                codigo.append(izq.generar_codigo(vars))
                codigo.append(der.generar_codigo(vars))
                if self.operador[1] == '+':
                    codigo.append('   faddp st1, st0')  # st1 = st1 + st0, pop st0
                elif self.operador[1] == '-':
                    codigo.append('   fsubp st1, st0')
                elif self.operador[1] == '*':
                    codigo.append('   fmulp st1, st0')
                elif self.operador[1] == '/':
                    codigo.append('   fdivp st1, st0')

                # Guardar resultado en memoria (puedes usar una temp o pasar por eax si deseas imprimir)
                return '\n'.join(codigo)
        

        elif isinstance(izq, NodoIdentificador) and isinstance(der, NodoNumero):
            if vars[izq.nombre[1]] == 'int' and isinstance(der.valor, int):
                self.tipo = 'int'
                return self.codigo_enteros(izq, der, vars)
            elif vars[izq.nombre[1]] == 'float' and isinstance(der.valor, int):
                self.tipo = 'float'
                codigo = []
                codigo.append(izq.generar_codigo(vars))
                codigo.append(der.generar_codigo(vars))
                codigo.append("sub esp, 4\n   mov [esp], eax\n   fild dword [esp]\n   add esp, 4") # sirve para convertir el (identificador / numero) entero a flotante y dejarlo en pila

                if self.operador[1] == '+':
                    codigo.append('   faddp st1, st0')  # st1 = st1 + st0, pop st0
                elif self.operador[1] == '-':
                    codigo.append('   fsubp st1, st0')
                elif self.operador[1] == '*':
                    codigo.append('   fmulp st1, st0')
                elif self.operador[1] == '/':
                    codigo.append('   fdivp st1, st0')
                return '\n'.join(codigo)
            elif vars[izq.nombre[1]] == 'int' and isinstance(der.valor, float):
                self.tipo = 'float'
                codigo = []
                codigo.append(izq.generar_codigo(vars))
                codigo.append("sub esp, 4\n   mov [esp], eax\n   fild dword [esp]\n   add esp, 4") # sirve para convertir el (identificador / numero) entero a flotante y dejarlo en pila
                codigo.append(der.generar_codigo(vars))
                if self.operador[1] == '+':
                    codigo.append('   faddp st1, st0')  # st1 = st1 + st0, pop st0
                elif self.operador[1] == '-':
                    codigo.append('   fsubp st1, st0')
                elif self.operador[1] == '*':
                    codigo.append('   fmulp st1, st0')
                elif self.operador[1] == '/':
                    codigo.append('   fdivp st1, st0')

                # Guardar resultado en memoria (puedes usar una temp o pasar por eax si deseas imprimir)
                return '\n'.join(codigo)
            else:
                self.tipo = 'float'
                codigo = []
                codigo.append(izq.generar_codigo(vars))
                codigo.append(der.generar_codigo(vars))
                if self.operador[1] == '+':
                    codigo.append('   faddp st1, st0')  # st1 = st1 + st0, pop st0
                elif self.operador[1] == '-':
                    codigo.append('   fsubp st1, st0')
                elif self.operador[1] == '*':
                    codigo.append('   fmulp st1, st0')
                elif self.operador[1] == '/':
                    codigo.append('   fdivp st1, st0')

                # Guardar resultado en memoria (puedes usar una temp o pasar por eax si deseas imprimir)
                return '\n'.join(codigo)

        elif isinstance(izq, NodoNumero) and isinstance(der, NodoIdentificador):
            if vars[der.nombre[1]] == 'int' and isinstance(izq.valor, int):
                self.tipo = 'int'
                return self.codigo_enteros(izq, der, vars)
            elif vars[der.nombre[1]] == 'float' and isinstance(izq.valor, int):
                self.tipo = 'float'
                codigo = []
                codigo.append(izq.generar_codigo())
                codigo.append("sub esp, 4\n   mov [esp], eax\n   fild dword [esp]\n   add esp, 4") # sirve para convertir el (identificador / numero) entero a flotante y dejarlo en pila
                codigo.append(der.generar_codigo())

                if self.operador[1] == '+':
                    codigo.append('   faddp st1, st0')  # st1 = st1 + st0, pop st0
                elif self.operador[1] == '-':
                    codigo.append('   fsubp st1, st0')
                elif self.operador[1] == '*':
                    codigo.append('   fmulp st1, st0')
                elif self.operador[1] == '/':
                    codigo.append('   fdivp st1, st0')
                return '\n'.join(codigo)
            elif vars[der.nombre[1]] == 'int' and isinstance(izq.valor, float):
                self.tipo = 'float'
                codigo = []
                codigo.append(izq.generar_codigo(vars))
                codigo.append(der.generar_codigo(vars))
                codigo.append("sub esp, 4\n   mov [esp], eax\n   fild dword [esp]\n   add esp, 4") # sirve para convertir el (identificador / numero) entero a flotante y dejarlo en pila
                if self.operador[1] == '+':
                    codigo.append('   faddp st1, st0')  # st1 = st1 + st0, pop st0
                elif self.operador[1] == '-':
                    codigo.append('   fsubp st1, st0')
                elif self.operador[1] == '*':
                    codigo.append('   fmulp st1, st0')
                elif self.operador[1] == '/':
                    codigo.append('   fdivp st1, st0')

                # Guardar resultado en memoria (puedes usar una temp o pasar por eax si deseas imprimir)
                return '\n'.join(codigo)
            else:
                self.tipo = 'float'
                codigo = []
                codigo.append(izq.generar_codigo(vars))
                codigo.append(der.generar_codigo(vars))
                if self.operador[1] == '+':
                    codigo.append('   faddp st1, st0')  # st1 = st1 + st0, pop st0
                elif self.operador[1] == '-':
                    codigo.append('   fsubp st1, st0')
                elif self.operador[1] == '*':
                    codigo.append('   fmulp st1, st0')
                elif self.operador[1] == '/':
                    codigo.append('   fdivp st1, st0')

                # Guardar resultado en memoria (puedes usar una temp o pasar por eax si deseas imprimir)
                return '\n'.join(codigo)

        elif isinstance(izq, NodoOperacion):
            codigo = []
            codigo.append(izq.generar_codigo(vars))

            return '\n'.join(codigo)

class NodoRetorno(NodoAST):
    # Nodo que representa a la sentencia return
    def __init__(self, expresion):
        self.expresion = expresion
        
    def traducir(self):
        return f"return {self.expresion.traducir()}"

    def generar_codigo(self, vars):
        codigo = self.expresion.generar_codigo()
        return f"{codigo}\n   ret ; Retornar desde la subrutina"

class NodoIdentificador(NodoAST):
    # Nodo que representa a un identificador
    def __init__(self, nombre, tipo):
        self.nombre = nombre # Formato ('tipo', 'valor')
        self.tipo = tipo

    def traducir(self):
        return self.nombre[1]

    def generar_codigo(self, vars):
        if self.tipo == 'int':
            return f'   mov eax, [{self.nombre[1]}] ; Cargar variable {self.nombre[1]} en eax'
        elif self.tipo == 'float':
            return f'   fld qword [{self.nombre[1]}] ; Cargar float {self.nombre[1]} en FPU'
        elif self.tipo == 'str':
            return f'   mov eax, {self.nombre[1]} ; Cargar variable {self.nombre[1]} en eax'
        elif self.tipo == 'char':
            return f'   mov eax, [{self.nombre[1]}] ; Cargar variable {self.nombre[1]} en eax'
        else:
            
            return f'   mov eax, [{self.nombre[1]}] ; Cargar variable {self.nombre[1]} en eax'

class NodoNumero(NodoAST):
    def __init__(self, valor):
        self.valor = valor

    def traducir(self):
        return str(self.valor)
    
    def generar_codigo(self, vars):
        if isinstance(self.valor, float):
            nombre_const = f"const_float_{str(self.valor).replace('.', '_')}"
            print(nombre_const)
            return f"   fld qword [{nombre_const}] ; Cargar float {self.valor} en ST0" 
        return f'   mov eax, {self.valor} ; Cargar número {self.valor} en eax'



class NodoDeclaracionVariable(NodoAST):
    def __init__(self, nombre, tipo):
        self.nombre = nombre
        self.tipo = tipo

    def generar_codigo(self, vars):
        return '' # No se necesita código, ya que se declara en la sección de datos
    

class NodoWhile(NodoAST):
    # Nodo que representa a un ciclo while
    def __init__(self, condicion, cuerpo):
        self.condicion = condicion
        self.cuerpo = cuerpo

    def generar_codigo(self, vars):
        etiqueta_inicio = f'etiqueta_inicio_{id(self)}'
        etiqueta_fin = f'etiqueta_fin_while_{id(self)}'

        codigo = []
        codigo.append(f'{etiqueta_inicio}:')
        codigo.append(self.condicion.generar_codigo(vars))
        codigo.append('   cmp eax, 0 ; Comparar resultado con 0')
        codigo.append(f'   jne {etiqueta_fin} ; Saltar al final si la condición es falsa')

        for instruccion in self.cuerpo:
            codigo.append(instruccion.generar_codigo(vars))

        codigo.append(f'   jmp {etiqueta_inicio} ; Saltar al inicio del ciclo')
        codigo.append(f'{etiqueta_fin}:')

        return '\n'.join(codigo)

class NodoIf(NodoAST):
    # Nodo que representa una sentencia if
    def __init__(self, condicion, cuerpo, sino=None):
        self.condicion = condicion
        self.cuerpo = cuerpo
        self.sino = sino

    def generar_codigo(self, vars):
        etiqueta_else = f'etiqueta_else_{id(self)}'
        etiqueta_fin = f'etiqueta_fin_if_{id(self)}'

        codigo = []
        codigo.append(self.condicion.generar_codigo(vars))
        codigo.append('   cmp eax, 0 ; Comparar resultado con 0')

        if self.sino:
            codigo.append(f'   jne {etiqueta_else} ; Saltar a else si la condición es falsa')
        else:
            codigo.append(f'   je {etiqueta_fin} ; Saltar al final si la condición es falsa')

        # Código del cuerpo del if
        for instruccion in self.cuerpo:
            codigo.append(instruccion.generar_codigo(vars))

        if self.sino:
            codigo.append(f'   jmp {etiqueta_fin} ; Saltar al final del if')
            codigo.append(f'{etiqueta_else}:')
            for instruccion in self.sino:
                codigo.append(instruccion.generar_codigo(vars))

        codigo.append(f'{etiqueta_fin}:')
        return '\n'.join(codigo)
    

class NodoFor(NodoAST):
    def __init__(self, inicializacion, condicion, actualizacion, cuerpo):
        self.inicializacion = inicializacion  # Debe ser una NodoAsignacion
        self.condicion = condicion            # Expresión booleana
        self.actualizacion = actualizacion    # Debe ser una NodoAsignacion
        self.cuerpo = cuerpo

    def generar_codigo(self, vars):
        etiqueta_inicio = "for_inicio"
        etiqueta_fin = "for_fin"
        
        codigo = []
        # Inicialización
        codigo.append(self.inicializacion.generar_codigo(vars))
        
        # Etiqueta de inicio del bucle
        codigo.append(f"{etiqueta_inicio}:")
        
        # Condición
        codigo.append(self.condicion.generar_codigo(vars))
        codigo.append("   cmp eax, 0")
        codigo.append(f"   jne {etiqueta_fin}")
        
        # Cuerpo del for, ejecuta todas las instrucciones dentro del for
        for instruccion in self.cuerpo:
            codigo.append(instruccion.generar_codigo(vars))
        
        # Actualización, ejecuta la instrucción de actualización
        codigo.append(self.actualizacion.generar_codigo(vars))
        
        # Salto al inicio del for
        codigo.append(f"   jmp {etiqueta_inicio}")
        
        # Etiqueta de fin
        codigo.append(f"{etiqueta_fin}:")
        
        return "\n".join(codigo)


class NodoInput(NodoAST):
    # Nodo que representa la función input
    def __init__(self, variable):
        self.variable = variable  # Puede ser un NodoIdentificador

    def generar_codigo(self, vars):
        codigo = []
        # Segun el tipo de variable (str o int), se debe cargar el valor en eax
        # Si self.variable.tipo == 'int':
        if self.variable.tipo == 'int':
            codigo.append(f'   mov eax, {self.variable.nombre[1]} ; Cargar dirección de la variable en eax')
            codigo.append(f'   call inputNum')
        elif self.variable.tipo == 'str':
            codigo.append(f'   mov eax, {self.variable.nombre[1]} ; Cargar dirección de la variable en eax')
            codigo.append(f'   call inputStr')
        elif self.variable.tipo == 'float':
            codigo.append(f'   push {self.variable.nombre[1]}')
            codigo.append(f'   push fmt_in_float')
            codigo.append(f'   call scanf')
            codigo.append(f'   add esp, 8')
        else:
            raise Exception(f"Error: Tipo de variable '{self.variable.nombre[1]}' no soportado en input")

        # Guardar el resultado en la variable
        return "\n".join(codigo)

    
class NodoPrint(NodoAST):
    # Nodo que representa a la función print
    def __init__(self, variable):
        self.variable = variable # Puede ser un NodoIdentificador, NodoNumero o NodoCadena

    def generar_codigo(self, vars):
        codigo = []
        # Cargar la variable en eax
        
        # Determinar el tipo de variable para llamar a la función correcta
        if self.variable.tipo != 'float':
            codigo.append(self.variable.generar_codigo())
        if isinstance(self.variable, NodoIdentificador):
            # print(f"Generando código para print: {self.variable.nombre[1]} de tipo {self.variable.tipo}")
            # Verificar si es una cadena (comienza con "cadena_")
            if self.variable.nombre[1].startswith('cadena_'):
                codigo.append('   call printStr')
            elif self.variable.tipo == 'str':
                # Si es una cadena, llamar a la función de impresión de cadenas
                codigo.append('   call printStr')
            elif self.variable.tipo == 'int':
                # Si es un entero, llamar a la función de impresión de enteros
                codigo.append('   call printnum')
            elif self.variable.tipo == 'float':
                codigo.append(f'   fld qword [{self.variable.nombre[1]}]')  # Cargar el double
                codigo.append(f'   sub esp, 8')                              # Reservar espacio
                codigo.append(f'   fstp qword [esp]')                        # Guardar en la pila
                codigo.append(f'   push fmt_float')
                codigo.append(f'   call printf')
                codigo.append(f'   add esp, 12')  # 8 del valor + 4 del puntero

        elif isinstance(self.variable, NodoCadena):
            # Para cadenas directas (aunque normalmente se convierten a identificadores)
            codigo.append('   call printStr')
        elif isinstance(self.variable, NodoNumero):
            codigo.append('   call printnum')
            
        return "\n".join(codigo)
    
class NodoPrintList(NodoAST):
    # Nodo que representa a la función print
    def __init__(self, variables):
        self.variables = variables # Es una lista de NodoPrint

    def generar_codigo(self, vars):
        codigo = []
        for variable in self.variables:
            # Cargar la variable en eax
            codigo.append(variable.generar_codigo(vars))
     
        return "\n".join(codigo)

class NodoCadena(NodoAST):
    def __init__(self, valor):
        self.valor = valor

    def traducir(self):
        return f'"{self.valor}"'
    
    def generar_codigo(self, vars):
        return f'   mov eax, {self.valor} ; Cargar cadena {self.valor} en eax'


class NodoLlamadaFuncion(NodoAST):
    def __init__(self, nombre, argumentos):
        self.nombre = nombre
        self.argumentos = argumentos

    def generar_codigo(self, vars):
        codigo = []
        # Empujar argumentos en orden inverso
        for arg in reversed(self.argumentos):
            codigo.append(arg.generar_codigo())
            codigo.append("   push eax")
        
        codigo.append(f"   call {self.nombre[1]}")
        
        # Limpiar la pila (4 bytes por argumento)
        if self.argumentos:
            codigo.append(f"   add esp, {4*len(self.argumentos)}")
        
        return "\n".join(codigo)
    


#------------------------- Análisis semántico -------------------------
class TablaSimbolos:
    def __init__(self):
        self.variables = {} # Almacena variables {nombre: tipo}
        self.funciones = {} # Almacena funciones {nombre: (tipo_retorno, [parametros])}
        self.cadenas = {} # Almacena cadenas {nombre: valor}
        self.flotantes = {}

    def declarar_flotante(self, nombre, valor):
        if nombre in self.flotantes:
            raise Exception(f"Error: Numero '{nombre}' ya declarado")
        self.flotantes[nombre] = valor
    def declarar_cadena(self, nombre, valor):
        if nombre in self.cadenas:
            raise Exception(f"Error: Cadena '{nombre}' ya declarada")
        self.cadenas[nombre] = valor

    def declarar_variable(self, nombre, tipo):
        if nombre in self.variables:
            raise Exception(f"Error: Variable '{nombre}' ya declarada")
        self.variables[nombre] = tipo

    def obtener_tipo_variable(self, nombre):
        if nombre not in self.variables:
            raise Exception(f"Error: Variable '{nombre}' no declarada")
        return self.variables[nombre]

    def declarar_funcion(self, nombre, tipo_retorno, parametros):
        if nombre in self.funciones:
            raise Exception(f"Error: Función '{nombre}' ya declarada")
        self.funciones[nombre] = (tipo_retorno, parametros)
    
    def obtener_info_funcion(self, nombre):
        if nombre not in self.funciones:
            raise Exception(f"Error: Función '{nombre}' no declarada")
        return self.funciones[nombre]

# start llama a main

class AnalizadorSemantico:
    def __init__(self):
        self.tabla_simbolos = TablaSimbolos()
        self.contador_cadenas = 0
    def analizar(self, nodo):
        if isinstance(nodo, NodoAsignacion):
            tipo_expr = self.analizar(nodo.expresion)
            # Verificar si la variable ya existe (puede ser un parámetro)
            if nodo.nombre[1] not in self.tabla_simbolos.variables:
                self.tabla_simbolos.declarar_variable(nodo.nombre[1], tipo_expr)
            else:
                # Si ya existe, verificar que los tipos coincidan
                tipo_existente = self.tabla_simbolos.obtener_tipo_variable(nodo.nombre[1])
                if tipo_existente != tipo_expr:
                    raise Exception(f"Error: Tipo incompatible en asignación para '{nodo.nombre[1]}' (esperaba {tipo_existente}, recibió {tipo_expr})")
        elif isinstance(nodo, NodoPrint):
    # Verificar si el contenido del print es una cadena para agregarla a la tabla de símbolos
            if isinstance(nodo.variable, NodoCadena):
                nombre_cadena = f"cadena_{self.contador_cadenas}"
                self.contador_cadenas += 1
                self.tabla_simbolos.declarar_cadena(nombre_cadena, nodo.variable.valor)
                print(f"Cadena '{nombre_cadena}' agregada a la tabla de símbolos")
                nodo.variable = NodoIdentificador(('IDENTIFIER', nombre_cadena), 'str')  # Reemplazar la cadena por su nombre
            elif isinstance(nodo.variable, NodoIdentificador):
                # Verificar si la variable existe
                tipo = self.tabla_simbolos.obtener_tipo_variable(nodo.variable.nombre[1])
                if tipo == 'str':
                    nodo.variable.tipo = 'str'
                elif tipo == 'int':
                    nodo.variable.tipo = 'int'
                elif tipo == 'float':
                    nodo.variable.tipo = 'float'
                elif tipo == 'char':
                    nodo.variable.tipo = 'char'
                else:
                    raise Exception(f"Error: Tipo de variable '{nodo.variable.nombre[1]}' no soportado en print")            

        elif isinstance(nodo, NodoNumero):
            # Comprobar si el número es entero o decimal
            if isinstance(nodo.valor, int):
                return "int"
            elif isinstance(nodo.valor, float):
                const_float = f"const_float_{str(nodo.valor).replace('.', '_')}"
                self.tabla_simbolos.declarar_flotante(const_float, nodo.valor)
                self.tabla_simbolos.declarar_variable(const_float, 'float')
                return "float"
            return "int"  # Por defecto, consideramos que es un entero


        elif isinstance(nodo, NodoPrintList): # NodoPrintList es una lista que contiene varios NodoPrint
            for variablePrint in nodo.variables:
                self.analizar(variablePrint)


        elif isinstance(nodo, NodoDeclaracionVariable):
            # Verificar si la variable ya existe
            if nodo.nombre[1] in self.tabla_simbolos.variables:
                raise Exception(f"Error: Variable '{nodo.nombre[1]}' ya declarada")
            # Declarar la variable en la tabla de símbolos
            self.tabla_simbolos.declarar_variable(nodo.nombre[1], nodo.tipo)
        elif isinstance(nodo, NodoIdentificador):
            return self.tabla_simbolos.obtener_tipo_variable(nodo.nombre[1])

        elif isinstance(nodo, NodoCadena):
            return "str"
        elif isinstance(nodo, NodoAsignacionCadena):
            nombre_cadena = nodo.nombre[1]
            cadena = nodo.expresion
            # Verificar si la cadena ya existe
            self.tabla_simbolos.declarar_cadena(nombre_cadena, cadena)
            self.tabla_simbolos.declarar_variable(nombre_cadena, 'str')
        elif isinstance(nodo, NodoOperacion):
            new = nodo.simplificar()
            tipo_izq = self.analizar(new.izquierda)
            tipo_der = self.analizar(new.derecha)
            if tipo_izq == tipo_der:
                nodo.tipo = tipo_izq
                return tipo_izq
            elif 'float' in [tipo_izq, tipo_der] and 'int' in [tipo_izq, tipo_der]:
                nodo.tipo = 'float'
                return 'float'
            else:
                raise Exception(f"Error: Tipos incompatibles en operación: {tipo_izq} {nodo.operador[1]} {tipo_der}")

        elif isinstance(nodo, NodoFuncion):
            # Registrar la función en la tabla de símbolos
            self.tabla_simbolos.declarar_funcion(nodo.nombre[1], nodo.tipo_retorno[1], nodo.parametros)

            # Registrar los parámetros en la tabla de variables
            for param in nodo.parametros:
                self.tabla_simbolos.declarar_variable(param.nombre[1], param.tipo[1])            
            # Analizar el cuerpo de la función
            for instruccion in nodo.cuerpo:
                self.analizar(instruccion)
        elif isinstance(nodo, NodoIf):
            # Analizar la condición
            tipo_condicion = self.analizar(nodo.condicion)
            if tipo_condicion != 'int':
                raise Exception(f"Error: Tipo de condición no válida en if (esperado 'int', recibido '{tipo_condicion}')")
            # Analizar el cuerpo del if
            for instruccion in nodo.cuerpo:
                self.analizar(instruccion)
            # Analizar el cuerpo del else (si existe)
            if nodo.sino:
                for instruccion in nodo.sino:
                    self.analizar(instruccion)
        elif isinstance(nodo, NodoWhile):
            # Analizar la condición
            tipo_condicion = self.analizar(nodo.condicion)
            if tipo_condicion != 'int':
                raise Exception(f"Error: Tipo de condición no válida en while (esperado 'int', recibido '{tipo_condicion}')")
            # Analizar el cuerpo del while
            for instruccion in nodo.cuerpo:
                self.analizar(instruccion)

                
        elif isinstance(nodo, NodoLlamadaFuncion):
            tipo_retorno, parametros = self.tabla_simbolos.obtener_info_funcion(nodo.nombre[1])
            if len(nodo.argumentos) != len(parametros):
                raise Exception(f"Error: La función '{nodo.nombre[1]}' espera {len(parametros)} argumentos, pero recibió {len(nodo.argumentos)}")
            return tipo_retorno
        elif isinstance(nodo, NodoPrograma):
            for funcion in nodo.funciones:
                self.analizar(funcion)
        elif isinstance(nodo, NodoInput):
            # Verificar si la variable existe
            if isinstance(nodo.variable, NodoIdentificador):
                tipo = self.tabla_simbolos.obtener_tipo_variable(nodo.variable.nombre[1])
                # Cambiar el tipo de la variable a 'int' o 'str' dependiendo de la entrada
                if tipo == 'int':
                    nodo.variable.tipo = 'int'
                elif tipo == 'str':
                    nodo.variable.tipo = 'str'
                elif tipo == 'float':
                    nodo.variable.tipo = 'float'
                elif tipo == 'char':
                    nodo.variable.tipo = 'char'
                else:
                    raise Exception(f"Error: Tipo de variable '{nodo.variable.nombre[1]}' no soportado en input")
                
            else:
                raise Exception(f"Error: La variable '{nodo.variable}' no está declarada")
        elif isinstance(nodo, NodoRetorno):
            tipo_expr = self.analizar(nodo.expresion)

