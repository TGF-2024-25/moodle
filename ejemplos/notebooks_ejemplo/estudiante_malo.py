# Ejercicio - Funciones Básicas en Python
# Curso: Programación Python

def suma_lista(numeros):
    """
    Calcula la suma de todos los elementos en una lista.
    """
    # Intento de suma pero con error - solo suma los dos primeros
    return numeros[0] + numeros[1]

def encontrar_maximo(numeros):
    """
    Encuentra el valor máximo en una lista.
    """
    # Función incorrecta - siempre devuelve el último elemento
    return numeros[-1]

def contar_vocales(texto):
    """
    Cuenta el número de vocales en un texto.
    """
    # Esta función está bien
    vocales = "aeiouAEIOU"
    contador = 0
    for char in texto:
        if char in vocales:
            contador += 1
    return contador

# Tests para suma_lista
assert suma_lista([1, 2, 3, 4, 5]) == 15  # Este fallará
assert suma_lista([-1, 0, 1]) == 0  # Este fallará
assert suma_lista([10, 20, 30]) == 60  # Este fallará
print("✓ Tests de suma_lista pasados")

# Tests para encontrar_maximo
assert encontrar_maximo([1, 5, 3, 9, 2]) == 9  # Este fallará
assert encontrar_maximo([-5, -2, -10]) == -2  # Este fallará
assert encontrar_maximo([100]) == 100  # Este pasará
print("✓ Tests de encontrar_maximo pasados")

# Tests para contar_vocales
assert contar_vocales("Hola Mundo") == 4  # Este pasará
assert contar_vocales("Python") == 1  # Este pasará
assert contar_vocales("AEIOUaeiou") == 10  # Este pasará
assert contar_vocales("BCD") == 0  # Este pasará
print("✓ Tests de contar_vocales pasados")

print("¡Algunos tests fallaron! Revisa tus funciones.")