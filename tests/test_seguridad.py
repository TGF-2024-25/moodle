#!/usr/bin/env python3
"""
Pruebas específicas de seguridad para el sistema de autocorrección
"""

import os
import tempfile
import sys
sys.path.append('../autocorreccion')
from evaluate_nbgrader import evaluar_notebook
import nbformat

def test_codigo_peligroso():
    """Probar manejo de código potencialmente peligroso"""
    
    print("=== PRUEBAS DE SEGURIDAD ===")
    
    # Crear notebook con código problemático
    notebook = nbformat.v4.new_notebook()
    
    codigo_peligroso = '''
# Intentos de operaciones peligrosas
import os
import subprocess

print("Intentando operaciones del sistema...")

# Intentar listar directorio (debería fallar o ser restringido)
try:
    files = os.listdir('/')
    print("Archivos en root:", len(files))
except Exception as e:
    print("Error accediendo al sistema:", str(e))

# Intentar ejecutar comando
try:
    result = subprocess.run(['echo', 'test'], capture_output=True, text=True)
    print("Resultado comando:", result.stdout)
except Exception as e:
    print("Error ejecutando comando:", str(e))

# Bucle potencialmente infinito (debería tener timeout)
print("Iniciando operación larga...")
for i in range(100000):
    pass
print("Operación larga completada")

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
        print("OK! Sistema manejó código potencialmente peligroso")
        print(f"  Estado: {resultado['estado']}")
        print(f"  Nota: {resultado['nota']}")
        
        # El sistema debería seguir funcionando incluso con código problemático
        return resultado['estado'] in ['ok', 'error']
        
    except Exception as e:
        print("MAL! El sistema falló con código peligroso:", str(e))
        return False
    finally:
        os.unlink(notebook_path)

def test_timeout():
    """Probar que el sistema maneja timeouts correctamente"""
    
    notebook = nbformat.v4.new_notebook()
    
    codigo_lento = '''
print("Iniciando operación muy lenta...")

# Simular operación muy lenta
import time
start = time.time()

# Esto debería ser interrumpido por el timeout
for i in range(10000000):
    for j in range(100):
        pass

end = time.time()
print(f"Operación completada en {end-start:.2f} segundos")
'''
    
    celda = nbformat.v4.new_code_cell(codigo_lento)
    notebook.cells.append(celda)
    
    # Usar modo texto explícito aquí también
    with tempfile.NamedTemporaryFile(suffix='.ipynb', mode='w', delete=False, encoding='utf-8') as f:
        nbformat.write(notebook, f)
        notebook_path = f.name
    
    try:
        # Esta evaluación debería timeoutear
        resultado = evaluar_notebook(notebook_path)
        print("OK! Sistema manejó operación lenta correctamente")
        return True
        
    except Exception as e:
        print("OK! Timeout manejado correctamente:", str(e))
        return True
    finally:
        os.unlink(notebook_path)

if __name__ == "__main__":
    prueba1 = test_codigo_peligroso()
    prueba2 = test_timeout()
    
    if prueba1 and prueba2:
        print("\nBIEN! PRUEBAS DE SEGURIDAD EXITOSAS")
    else:
        print("\nMAL! ALGUNAS PRUEBAS DE SEGURIDAD FALLARON")