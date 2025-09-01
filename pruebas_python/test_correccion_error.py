def saludar(nombre):
    """Saluda a una persona"""
    return f"Hola, {nombre}!"

# Tests que deben pasar
assert saludar("Moodle") == "Hola, Moodle!"
assert saludar("Estudiante") == "Hola, Estudiante!"

def calcular_area_rectangulo(base, altura):
    """Calcula el área de un rectángulo"""
    return base * altura + 1  # ERROR: +1 sobra

# Tests que deben pasar  
assert calcular_area_rectangulo(4, 5) == 20
assert calcular_area_rectangulo(0, 10) == 0
assert calcular_area_rectangulo(3, 7) == 21