#!/usr/bin/env python3
"""
Script para crear ejercicios de ejemplo para el sistema de Auto-Corrección
"""
import json
import os

def crear_directorio():
    """Crea el directorio si no existe"""
    if not os.path.exists('notebooks_ejemplo'):
        os.makedirs('notebooks_ejemplo')
        print("✅ Directorio 'notebooks_ejemplo' creado")

def crear_notebook_profesor():
    """Crea el notebook de referencia para el profesor"""
    notebook = {
        "cells": [
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "# Ejercicio - Funciones Básicas en Python\n",
                    "## Curso: Programación Python\n",
                    "\n",
                    "Complete las siguientes funciones según las especificaciones."
                ]
            },
            {
                "cell_type": "markdown", 
                "metadata": {},
                "source": [
                    "### Ejercicio 1: Suma de elementos\n",
                    "Escriba una función que reciba una lista de números y devuelva la suma de todos los elementos."
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "def suma_lista(numeros):\n",
                    "    \"\"\"\n",
                    "    Calcula la suma de todos los elementos en una lista.\n",
                    "    \n",
                    "    Args:\n",
                    "        numeros (list): Lista de números\n",
                    "        \n",
                    "    Returns:\n",
                    "        float: Suma de todos los elementos\n",
                    "    \"\"\"\n",
                    "    # TODO: Implementar la función\n",
                    "    pass"
                ]
            },
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "### Ejercicio 2: Encontrar máximo\n", 
                    "Escriba una función que encuentre el valor máximo en una lista de números."
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "def encontrar_maximo(numeros):\n",
                    "    \"\"\"\n",
                    "    Encuentra el valor máximo en una lista.\n",
                    "    \n",
                    "    Args:\n",
                    "        numeros (list): Lista de números\n",
                    "        \n",
                    "    Returns:\n",
                    "        float: Valor máximo de la lista\n",
                    "    \"\"\"\n",
                    "    # TODO: Implementar la función\n",
                    "    pass"
                ]
            },
            {
                "cell_type": "markdown",
                "metadata": {}, 
                "source": [
                    "### Ejercicio 3: Contar vocales\n",
                    "Escriba una función que cuente el número de vocales en una cadena de texto."
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "def contar_vocales(texto):\n",
                    "    \"\"\"\n",
                    "    Cuenta el número de vocales en un texto.\n",
                    "    \n",
                    "    Args:\n",
                    "        texto (str): Cadena de texto\n",
                    "        \n",
                    "    Returns:\n",
                    "        int: Número de vocales en el texto\n",
                    "    \"\"\"\n",
                    "    # TODO: Implementar la función\n",
                    "    pass"
                ]
            },
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "### Tests de verificación\n",
                    "Las siguientes celdas verifican que las funciones funcionen correctamente."
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "# Tests para suma_lista\n",
                    "assert suma_lista([1, 2, 3, 4, 5]) == 15\n",
                    "assert suma_lista([-1, 0, 1]) == 0\n", 
                    "assert suma_lista([10, 20, 30]) == 60\n",
                    "print(\"✓ Tests de suma_lista pasados\")"
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "# Tests para encontrar_maximo\n",
                    "assert encontrar_maximo([1, 5, 3, 9, 2]) == 9\n",
                    "assert encontrar_maximo([-5, -2, -10]) == -2\n",
                    "assert encontrar_maximo([100]) == 100\n",
                    "print(\"✓ Tests de encontrar_maximo pasados\")"
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "# Tests para contar_vocales\n",
                    "assert contar_vocales(\"Hola Mundo\") == 4\n",
                    "assert contar_vocales(\"Python\") == 1\n",
                    "assert contar_vocales(\"AEIOUaeiou\") == 10\n",
                    "assert contar_vocales(\"BCD\") == 0\n",
                    "print(\"✓ Tests de contar_vocales pasados\")"
                ]
            },
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "¡Todos los tests pasaron! Ejercicio completado correctamente."
                ]
            }
        ],
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python", 
                "name": "python3"
            },
            "language_info": {
                "name": "python",
                "version": "3.8.10"
            }
        },
        "nbformat": 4,
        "nbformat_minor": 4
    }
    
    with open('notebooks_ejemplo/ejercicio_funciones.ipynb', 'w', encoding='utf-8') as f:
        json.dump(notebook, f, indent=2, ensure_ascii=False)
    
    print("✅ Notebook del profesor creado: ejercicio_funciones.ipynb")

def crear_archivos_estudiante():
    """Crea los archivos .py para estudiantes"""
    
    # Estudiante bueno
    contenido_bueno = '''# Ejercicio - Funciones Básicas en Python
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
'''
    
    with open('notebooks_ejemplo/estudiante_bueno.py', 'w', encoding='utf-8') as f:
        f.write(contenido_bueno)
    print("✅ Archivo del estudiante bueno creado: estudiante_bueno.py")
    
    # Estudiante malo
    contenido_malo = '''# Ejercicio - Funciones Básicas en Python
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
'''
    
    with open('notebooks_ejemplo/estudiante_malo.py', 'w', encoding='utf-8') as f:
        f.write(contenido_malo)
    print("✅ Archivo del estudiante malo creado: estudiante_malo.py")

def main():
    """Función principal"""
    print("🎯 CREADOR DE EJERCICIOS PARA AUTO-CORRECCIÓN")
    print("=" * 50)
    
    crear_directorio()
    crear_notebook_profesor() 
    crear_archivos_estudiante()
    
    print("=" * 50)
    print("🎉 Todos los archivos creados correctamente!")
    print("\n📁 Archivos creados en la carpeta 'notebooks_ejemplo':")
    print("   • ejercicio_funciones.ipynb - Para el profesor")
    print("   • estudiante_bueno.py - Ejercicio bien resuelto (~8/10)")
    print("   • estudiante_malo.py - Ejercicio mal resuelto (~3/10)")
    print("\n💡 Instrucciones:")
    print("   1. Sube 'ejercicio_funciones.ipynb' como referencia en Moodle")
    print("   2. Los estudiantes pueden subir los archivos .py o .ipynb")
    print("   3. El sistema convertirá automáticamente .py a .ipynb")

if __name__ == "__main__":
    main()