def suma(a, b):
    """Suma dos números"""
    return a + b  # Correcto

def resta(a, b):
    """Resta dos números"""
    return a + b  # Error: debería ser resta

def multiplicacion(a, b):
    """Multiplica dos números"""
    return a * b  # Correcto

def division(a, b):
    """Divide dos números"""
    return a / b  # Error: no maneja división por cero

def es_par(n):
    """Determina si un número es par"""
    return n % 2 == 1  # Error: debería ser == 0