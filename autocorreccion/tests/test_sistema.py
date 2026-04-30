#!/usr/bin/env python3
"""
Pruebas del sistema de autocorrección
"""

import os
import sys
import json
import tempfile
import subprocess

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MOODLE_PLUGIN_DIR = os.path.dirname(SCRIPT_DIR)  # autocorreccion/
sys.path.append(MOODLE_PLUGIN_DIR)

from evaluate_nbgrader import evaluar_notebook, convertir_asserts_a_captura
from convert_py_to_ipynb import convert_py_to_ipynb

import nbformat

def run_all_tests():
    """Ejecutar todas las pruebas del sistema"""
    
    print("=" * 60)
    print("SISTEMA DE PRUEBAS - AUTO-CORRECCIÓN MOODLE")
    print("=" * 60)
    print()
    
    results = []
    
    # Test 1: Verificar que los archivos existen
    print("1. Verificando archivos necesarios...")
    archivos = ['convert_py_to_ipynb.py', 'evaluate_nbgrader.py']
    for archivo in archivos:
        path = os.path.join(MOODLE_PLUGIN_DIR, archivo)
        if os.path.exists(path):
            print(f"   {archivo} encontrado")
        else:
            print(f"   {archivo} NO encontrado")
            results.append(False)
    
    # Test 2: Probar conversión
    print("\n2. Probando conversión Python -> Jupyter...")
    try:
        from convert_py_to_ipynb import convert_py_to_ipynb
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write('def suma(a, b):\n    return a + b\nassert suma(2, 3) == 5')
            py_path = f.name
        
        ipynb_path = tempfile.mktemp(suffix='.ipynb')
        convert_py_to_ipynb(py_path, ipynb_path)
        
        if os.path.exists(ipynb_path):
            print("   Conversión exitosa")
            results.append(True)
        else:
            print("   Conversión falló")
            results.append(False)
            
        os.unlink(py_path)
        os.unlink(ipynb_path)
    except Exception as e:
        print(f"   Error: {e}")
        results.append(False)
    
    # Test 3: Probar evaluación básica
    print("\n3. Probando evaluación de notebook...")
    try:
        from evaluate_nbgrader import evaluar_notebook
        
        notebook = nbformat.v4.new_notebook()
        celda = nbformat.v4.new_code_cell('print("Hola Mundo")')
        notebook.cells.append(celda)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ipynb', delete=False) as f:
            nbformat.write(notebook, f)
            notebook_path = f.name
        
        resultado = evaluar_notebook(notebook_path)
        
        if resultado['estado'] == 'ok':
            print(f"   Evaluación exitosa. Nota: {resultado['nota']}/10")
            results.append(True)
        else:
            print(f"   Error en evaluación: {resultado.get('error', '')}")
            results.append(False)
            
        os.unlink(notebook_path)
    except Exception as e:
        print(f"   Error: {e}")
        results.append(False)
    
    # Test 4: Probar evaluación con tests
    print("\n4. Probando evaluación con tests...")
    try:
        from evaluate_nbgrader import evaluar_notebook
        
        notebook = nbformat.v4.new_notebook()
        codigo = '''
def multiplica(a, b):
    return a * b

assert multiplica(2, 3) == 6
assert multiplica(0, 5) == 0
print("Tests pasados")
'''
        celda = nbformat.v4.new_code_cell(codigo)
        notebook.cells.append(celda)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ipynb', delete=False) as f:
            nbformat.write(notebook, f)
            notebook_path = f.name
        
        resultado = evaluar_notebook(notebook_path)
        
        if resultado['estado'] == 'ok' and resultado['nota'] >= 8:
            print(f"   Tests evaluados correctamente. Nota: {resultado['nota']}/10")
            results.append(True)
        else:
            print(f"   Problema con tests. Nota: {resultado['nota']}/10")
            results.append(False)
            
        os.unlink(notebook_path)
    except Exception as e:
        print(f"   Error: {e}")
        results.append(False)
    
    # Test 5: Probar conversión de asserts
    print("\n5. Probando conversión de asserts...")
    try:
        from evaluate_nbgrader import convertir_asserts_a_captura
        
        codigo = 'assert suma(2, 3) == 5'
        convertido = convertir_asserts_a_captura(codigo)
        
        if 'capturar_assert' in convertido:
            print("   Conversión de asserts funciona")
            results.append(True)
        else:
            print("   Conversión de asserts falló")
            results.append(False)
    except Exception as e:
        print(f"   Error: {e}")
        results.append(False)
    
    # Resumen final
    print("\n" + "=" * 60)
    print("RESUMEN FINAL")
    print("=" * 60)
    
    total = len(results)
    exitosos = sum(results)
    
    print(f"Pruebas exitosas: {exitosos}/{total}")
    
    if exitosos == total:
        print("\nTODAS LAS PRUEBAS PASARON EXITOSAMENTE")
        return 0
    else:
        print("\nALGUNAS PRUEBAS FALLARON")
        return 1

if __name__ == '__main__':
    sys.exit(run_all_tests())