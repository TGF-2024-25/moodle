# Ejercicio - Funciones Básicas en Python
# Curso: Programación Python

"""
Complete las siguientes funciones según las especificaciones.
"""

def suma_lista(numeros):
    """
    Calcula la suma de todos los elementos en una lista.
    
    Args:
        numeros (list): Lista de números
        
    Returns:
        float: Suma de todos los elementos
    """
    # TODO: Implementar la función
    pass

def encontrar_maximo(numeros):
    """
    Encuentra el valor máximo en una lista.
    
    Args:
        numeros (list): Lista de números
        
    Returns:
        float: Valor máximo de la lista
    """
    # TODO: Implementar la función
    pass

def contar_vocales(texto):
    """
    Cuenta el número de vocales en un texto.
    
    Args:
        texto (str): Cadena de texto
        
    Returns:
        int: Número de vocales en el texto
    """
    # TODO: Implementar la función
    pass

# Tests de verificación
# Las siguientes líneas verifican que las funciones funcionen correctamente.

# Tests para suma_lista
assert suma_lista([1, 2, 3, 4, 5]) == 15
assert suma_lista([-1, 0, 1]) == 0
assert suma_lista([10, 20, 30]) == 60
print("✓ Tests de suma_lista pasados")

# Tests para encontrar_maximo
assert encontrar_maximo([1, 5, 3, 9, 2]) == 9
assert encontrar_maximo([-5, -2, -10]) == -2
assert encontrar_maximo([100]) == 100
print("✓ Tests de encontrar_maximo pasados")

# Tests para contar_vocales
assert contar_vocales("Hola Mundo") == 4
assert contar_vocales("Python") == 1
assert contar_vocales("AEIOUaeiou") == 10
assert contar_vocales("BCD") == 0
print("✓ Tests de contar_vocales pasados")

print("¡Todos los tests pasaron! Ejercicio completado correctamente.")