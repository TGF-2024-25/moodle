#!/usr/bin/env python3
"""
Prueba de integración que simula el flujo real del sistema:
1. Archivo Python con tests
2. Conversión a Jupyter Notebook
3. Evaluación con nbgrader
"""

import os
import tempfile
import sys

# Añadir ruta al plugin Moodle
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MOODLE_PLUGIN_DIR = os.path.dirname(SCRIPT_DIR)  # autocorreccion/
sys.path.append(MOODLE_PLUGIN_DIR)

from evaluate_nbgrader import evaluar_notebook, convertir_asserts_a_captura
from convert_py_to_ipynb import convert_py_to_ipynb

# Configuración
TEST_DIR = tempfile.mkdtemp()

def test_integracion_conversion():
    """Prueba de integración con conversión Python -> IPYNB"""
    
    print("=== PRUEBA DE INTEGRACIÓN ===")
    
    # 1. Crear archivo Python de prueba
    codigo_prueba = '''def potencia(base, exponente):
    return base ** exponente

# Asserts directos
assert potencia(2, 3) == 8
assert potencia(5, 0) == 1 
assert potencia(3, 2) == 9

print("Todos los tests de potencia pasaron!")
'''
    
    archivo_py = os.path.join(TEST_DIR, "test_potencia.py")
    with open(archivo_py, 'w') as f:
        f.write(codigo_prueba)
    
    print("Archivo Python creado")
    
    # 2. Convertir a Jupyter Notebook
    archivo_ipynb = os.path.join(TEST_DIR, "test_potencia.ipynb")
    
    try:
        convert_py_to_ipynb(archivo_py, archivo_ipynb)
        
        if os.path.exists(archivo_ipynb):
            print("Conversión Python -> IPYNB exitosa")
        else:
            print("Archivo IPYNB no se creó")
            return False
            
    except Exception as e:
        print(f"Error en conversión: {e}")
        return False
    
    # 3. Evaluar con nbgrader
    try:
        resultado = evaluar_notebook(archivo_ipynb)
        
        if resultado['estado'] == 'ok':
            print(f"Evaluación completada")
            print(f"  Nota: {resultado['nota']}/10")
            
            if resultado['nota'] >= 8:
                print("Tests detectados y evaluados correctamente")
                return True
            else:
                print(f"Nota baja: {resultado['nota']}/10")
                return False
        else:
            print(f"Error en evaluación: {resultado.get('error', 'Error desconocido')}")
            return False
            
    except Exception as e:
        print(f"Error en evaluación: {e}")
        return False

def test_sistema_captura_assert():
    """Prueba específica del sistema de captura de asserts"""
    
    print("\n=== PRUEBA DEL SISTEMA DE CAPTURA DE ASSERTS ===")
    
    codigo_con_asserts = '''
assert suma(2, 3) == 5
assert resta(5, 3) == 2
assert variable is True
assert otra_variable == "valor"
'''
    
    codigo_convertido = convertir_asserts_a_captura(codigo_con_asserts)
    
    if 'capturar_assert' in codigo_convertido:
        print("Conversión de asserts funciona")
        return True
    else:
        print("Conversión de asserts falló")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("SISTEMA DE PRUEBAS DE INTEGRACIÓN - AUTO-CORRECCIÓN")
    print("=" * 60)
    print()
    
    exito_captura = test_sistema_captura_assert()
    exito_conversion = test_integracion_conversion()
    
    # Limpieza
    import shutil
    shutil.rmtree(TEST_DIR, ignore_errors=True)
    
    print("\n" + "=" * 60)
    print("RESUMEN DE RESULTADOS")
    print("=" * 60)
    print(f"Sistema captura asserts: {'OK' if exito_captura else 'FALLÓ'}")
    print(f"Integración: {'OK' if exito_conversion else 'FALLÓ'}")
    
    if exito_captura and exito_conversion:
        print("\nTODAS LAS PRUEBAS EXITOSAS")
        sys.exit(0)
    else:
        print("\nALGUNAS PRUEBAS FALLARON")
        sys.exit(1)