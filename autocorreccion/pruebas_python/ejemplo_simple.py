# Este es un archivo Python simple que se convertirá a notebook
# Contiene funciones básicas para probar el sistema

def saludar(nombre):
    """Saluda a una persona"""
    return f"Hola, {nombre}!"

def calcular_area_rectangulo(base, altura):
    """Calcula el área de un rectángulo"""
    return base * altura

# Tests simples
if __name__ == "__main__":
    print(saludar("Moodle"))
    print("Área de rectángulo 5x3:", calcular_area_rectangulo(5, 3))
    
    # Tests de verificación
    assert calcular_area_rectangulo(4, 5) == 20
    assert calcular_area_rectangulo(0, 10) == 0