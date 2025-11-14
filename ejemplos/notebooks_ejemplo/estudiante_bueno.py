# Ejercicio - Funciones Básicas en Python
# Curso: Programación Python

def suma_lista(numeros):
    """
    Calcula la suma de todos los elementos en una lista.
    """
    total = 0
    for num in numeros:
        total += num
    return total

def encontrar_maximo(numeros):
    """
    Encuentra el valor máximo en una lista.
    """
    if not numeros:
        return None
    max_valor = numeros[0]
    for num in numeros:
        if num > max_valor:
            max_valor = num
    return max_valor

def contar_vocales(texto):
    """
    Cuenta el número de vocales en un texto.
    """
    vocales = "aeiouAEIOU"
    contador = 0
    for char in texto:
        if char in vocales:
            contador += 1
    return contador

# Tests para suma_lista
assert suma_lista([1, 2, 3, 4, 5]) == 15
assert suma_lista([-1, 0, 1]) == 0
assert suma_lista([10, 20, 30]) == 60
print("OK! Tests de suma_lista pasados")

# Tests para encontrar_maximo
assert encontrar_maximo([1, 5, 3, 9, 2]) == 9
assert encontrar_maximo([-5, -2, -10]) == -2
assert encontrar_maximo([100]) == 100
print("OK! Tests de encontrar_maximo pasados")

# Tests para contar_vocales
assert contar_vocales("Hola Mundo") == 4
assert contar_vocales("Python") == 1
assert contar_vocales("AEIOUaeiou") == 10
assert contar_vocales("BCD") == 0
print("OK! Tests de contar_vocales pasados")

print("¡Todos los tests pasaron! Ejercicio completado correctamente.")