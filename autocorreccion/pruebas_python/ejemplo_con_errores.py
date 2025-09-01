# Este archivo tiene errores intencionales para testing

def suma_incorrecta(a, b):
    """Suma incorrecta para probar detección de errores"""
    return a - b  # Error: debería ser suma, no resta

def lista_al_cuadrado(lista):
    """Eleva todos los elementos al cuadrado"""
    resultado = []
    for num in lista:
        resultado.append(num ** 2)
    return resultado

# Tests que fallarán
if __name__ == "__main__":
    # Este test fallará
    assert suma_incorrecta(2, 3) == 5
    
    # Este test pasará
    assert lista_al_cuadrado([1, 2, 3]) == [1, 4, 9]
    
    print("Algunos tests completados")