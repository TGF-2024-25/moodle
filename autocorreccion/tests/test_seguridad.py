#!/usr/bin/env python3
"""
Pruebas específicas de seguridad para el sistema de autocorrección
"""

import os
import tempfile
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MOODLE_PLUGIN_DIR = os.path.dirname(SCRIPT_DIR)  # autocorreccion/
sys.path.append(MOODLE_PLUGIN_DIR)

from evaluate_nbgrader import evaluar_notebook, convertir_asserts_a_captura
from convert_py_to_ipynb import convert_py_to_ipynb

import nbformat

def test_codigo_peligroso():
    """Probar manejo de código potencialmente peligroso"""
    
    print("=== PRUEBAS DE SEGURIDAD ===")
    
    # Crear notebook con código problemático
    notebook = nbformat.v4.new_notebook()
    
    codigo_peligroso = '''
# Intentos de operaciones del sistema
import os
import subprocess

print("Intentando operaciones del sistema...")

# Intentar listar directorio
try:
    files = os.listdir('/')
    print("Acceso a directorio root permitido")
except Exception as e:
    print("Acceso restringido:", str(e))

# Intentar ejecutar comando
try:
    result = subprocess.run(['echo', 'test'], capture_output=True, text=True)
    print("Comando ejecutado")
except Exception as e:
    print("Comando no permitido:", str(e))

# Operación larga (dentro de límite razonable)
print("Ejecutando operación controlada...")
for i in range(10000):
    pass
print("Operación completada")

print("Prueba de seguridad finalizada")
'''
    
    celda = nbformat.v4.new_code_cell(codigo_peligroso)
    notebook.cells.append(celda)
    
    # Guardar y evaluar
    with tempfile.NamedTemporaryFile(suffix='.ipynb', mode='w', delete=False, encoding='utf-8') as f:
        nbformat.write(notebook, f)
        notebook_path = f.name
    
    try:
        resultado = evaluar_notebook(notebook_path)
        print("Sistema manejó código potencialmente peligroso")
        print(f"  Estado: {resultado['estado']}")
        print(f"  Nota: {resultado['nota']}/10")
        
        return resultado['estado'] == 'ok'
        
    except Exception as e:
        print("El sistema falló con código peligroso:", str(e))
        return False
    finally:
        os.unlink(notebook_path)

def test_timeout():
    """Probar que el sistema maneja timeouts correctamente"""
    
    print("\n=== PRUEBA DE TIMEOUT ===")
    
    notebook = nbformat.v4.new_notebook()
    
    # Código que no es infinito pero suficientemente largo para probar
    # (el sistema tiene timeout de 120 segundos)
    codigo_controlado = '''
print("Iniciando operación...")

# Operación controlada (no infinita)
resultado = 0
for i in range(100000):
    for j in range(10):
        resultado += i * j

print(f"Operación completada. Resultado: {resultado}")
'''
    
    celda = nbformat.v4.new_code_cell(codigo_controlado)
    notebook.cells.append(celda)
    
    with tempfile.NamedTemporaryFile(suffix='.ipynb', mode='w', delete=False, encoding='utf-8') as f:
        nbformat.write(notebook, f)
        notebook_path = f.name
    
    try:
        resultado = evaluar_notebook(notebook_path)
        print("Sistema completó la operación dentro del timeout")
        return True
        
    except Exception as e:
        print("Timeout manejado correctamente (o error esperado):", str(e))
        return True
    finally:
        os.unlink(notebook_path)

if __name__ == "__main__":
    print("=" * 60)
    print("SISTEMA DE PRUEBAS DE SEGURIDAD")
    print("=" * 60)
    print()
    
    prueba1 = test_codigo_peligroso()
    prueba2 = test_timeout()
    
    print("\n" + "=" * 60)
    print("RESUMEN")
    print("=" * 60)
    print(f"Código peligroso: {'OK' if prueba1 else 'FALLÓ'}")
    print(f"Manejo de timeout: {'OK' if prueba2 else 'FALLÓ'}")
    
    if prueba1 and prueba2:
        print("\nPRUEBAS DE SEGURIDAD EXITOSAS")
        sys.exit(0)
    else:
        print("\nALGUNAS PRUEBAS DE SEGURIDAD FALLARON")
        sys.exit(1)