#!/usr/bin/env python3
"""
Prueba de integración completa que simula el flujo completo:
1. Creación directa de notebook con tests
2. Evaluación con nbgrader
3. Generación de resultados
"""

import os
import tempfile
import subprocess
import sys
import nbformat
import json

# Configuración
TEST_DIR = tempfile.mkdtemp()
PYTHON_EXEC = "/home/vagrant/nbgrader_env/bin/python"
MOODLE_DIR = "/var/www/html/moodle/mod/autocorreccion"

def test_integracion_directa():
    """Prueba de integración creando notebook directamente"""
    
    print("=== PRUEBA DE INTEGRACIÓN DIRECTA ===")
    
    # Crear notebook directamente con tests
    notebook = nbformat.v4.new_notebook()
    
    # Código más explícito para asegurar que los asserts se detecten
    codigo_completo = '''
def es_palindromo(texto):
    texto = texto.lower().replace(" ", "")
    return texto == texto[::-1]

# Tests muy explícitos
test1 = es_palindromo("ana") == True
test2 = es_palindromo("reconocer") == True  
test3 = es_palindromo("python") == False
test4 = es_palindromo("A nut for a jar of tuna") == True

# Asserts explícitos
assert test1, "ana debería ser palíndromo"
assert test2, "reconocer debería ser palíndromo"
assert test3, "python NO debería ser palíndromo"
assert test4, "frase debería ser palíndromo"

print("Todos los tests pasaron!")
'''
    celda_completa = nbformat.v4.new_code_cell(codigo_completo)
    notebook.cells.append(celda_completa)
    
    # Guardar notebook
    notebook_path = os.path.join(TEST_DIR, "test_palindromo_directo.ipynb")
    with open(notebook_path, 'w', encoding='utf-8') as f:
        nbformat.write(notebook, f)
    
    print("OK! Notebook creado directamente con tests")
    
    # Evaluar con nbgrader
    cmd_evaluar = [
        PYTHON_EXEC,
        os.path.join(MOODLE_DIR, "evaluate_nbgrader.py"),
        notebook_path,
        "testuser"
    ]
    
    try:
        result_eval = subprocess.run(cmd_evaluar, capture_output=True, text=True, timeout=60)
        
        if result_eval.returncode == 0:
            # Parsear resultado JSON
            resultado = json.loads(result_eval.stdout)
            
            print("OK! Evaluación completada")
            print(f"  Estado: {resultado['estado']}")
            print(f"  Nota: {resultado['nota']}")
            
            if len(resultado['retroalimentacion']) > 100:
                print(f"  Feedback: {resultado['retroalimentacion'][:100]}...")
            else:
                print(f"  Feedback: {resultado['retroalimentacion']}")
            
            # Verificar que los tests pasaron
            if resultado['nota'] >= 8:
                print("OK! Tests pasaron correctamente")
                return True
            else:
                print("MAL! Tests fallaron o no se detectaron")
                return False
                
        else:
            print("MAL! Error en evaluación:", result_eval.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print("MAL! Timeout en evaluación")
        return False
    except json.JSONDecodeError:
        print("MAL! Respuesta no es JSON válido:", result_eval.stdout)
        return False
    except Exception as e:
        print(f"MAL! Error inesperado: {e}")
        return False

def test_integracion_conversion():
    """Prueba de integración con conversión Python -> IPYNB"""
    
    print("=== PRUEBA DE INTEGRACIÓN CON CONVERSIÓN ===")
    
    # 1. Crear archivo Python de prueba
    codigo_prueba = '''def potencia(base, exponente):
    return base ** exponente

# Tests explícitos
test1 = potencia(2, 3) == 8
test2 = potencia(5, 0) == 1
test3 = potencia(3, 2) == 9

assert test1, "2^3 debería ser 8"
assert test2, "5^0 debería ser 1" 
assert test3, "3^2 debería ser 9"

print("Todos los tests de potencia pasaron!")
'''
    
    archivo_py = os.path.join(TEST_DIR, "test_potencia.py")
    with open(archivo_py, 'w') as f:
        f.write(codigo_prueba)
    
    print("OK! Archivo Python creado")
    
    # 2. Convertir a Jupyter Notebook
    archivo_ipynb = os.path.join(TEST_DIR, "test_potencia.ipynb")
    cmd_convertir = [
        PYTHON_EXEC, 
        os.path.join(MOODLE_DIR, "convert_py_to_ipynb.py"),
        archivo_py,
        archivo_ipynb
    ]
    
    try:
        result_convert = subprocess.run(cmd_convertir, capture_output=True, text=True, timeout=30)
        if result_convert.returncode == 0:
            print("OK! Conversión Python -> IPYNB exitosa")
            
            # Verificar que el archivo se creó
            if os.path.exists(archivo_ipynb):
                print("OK! Archivo IPYNB creado correctamente")
            else:
                print("MAL! Archivo IPYNB no se creó")
                return False
        else:
            print("MAL! Error en conversión:", result_convert.stderr)
            return False
    except subprocess.TimeoutExpired:
        print("MAL! Timeout en conversión")
        return False
    
    # 3. Evaluar con nbgrader
    cmd_evaluar = [
        PYTHON_EXEC,
        os.path.join(MOODLE_DIR, "evaluate_nbgrader.py"),
        archivo_ipynb,
        "testuser"
    ]
    
    try:
        result_eval = subprocess.run(cmd_evaluar, capture_output=True, text=True, timeout=60)
        
        if result_eval.returncode == 0:
            # Parsear resultado JSON
            resultado = json.loads(result_eval.stdout)
            
            print("BIEN! Evaluación completada")
            print(f"  Estado: {resultado['estado']}")
            print(f"  Nota: {resultado['nota']}")
            
            # Verificar que los tests se detectaron
            if resultado['estado'] == 'ok' and resultado['nota'] > 0:
                print("BIEN! Tests detectados y evaluados correctamente")
                return True
            else:
                print("MAL! Tests no se detectaron adecuadamente")
                print(f"  Feedback: {resultado['retroalimentacion'][:200]}...")
                return False
                
        else:
            print("MAL! Error en evaluación:", result_eval.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print("MAL! Timeout en evaluación")
        return False
    except json.JSONDecodeError:
        print("MAL! Respuesta no es JSON válido:", result_eval.stdout)
        return False

def test_sistema_captura_assert():
    """Prueba específica del sistema de captura de asserts"""
    
    print("=== PRUEBA DEL SISTEMA DE CAPTURA DE ASSERTS ===")
    
    from evaluate_nbgrader import convertir_asserts_a_captura
    
    # Probar la conversión con diferentes tipos de asserts
    codigo_con_asserts = '''
assert suma(2, 3) == 5
assert resta(5, 3) == 2
assert variable is True
assert otra_variable == "valor"
'''
    
    codigo_convertido = convertir_asserts_a_captura(codigo_con_asserts)
    print("Código convertido:")
    print(codigo_convertido)
    
    # Verificar que la conversión funcionó
    if 'capturar_assert' in codigo_convertido:
        print("BIEN! Conversión de asserts funcionó")
        return True
    else:
        print("MAL! Conversión de asserts falló")
        return False

if __name__ == "__main__":
    # Probar diferentes aspectos
    exito_captura = test_sistema_captura_assert()
    exito_directo = test_integracion_directa()
    exito_conversion = test_integracion_conversion()
    
    # Limpieza
    import shutil
    shutil.rmtree(TEST_DIR, ignore_errors=True)
    
    print("\n" + "="*50)
    print("RESUMEN DE RESULTADOS")
    print("="*50)
    print(f"Sistema captura asserts: {'BIEN!' if exito_captura else 'MAL!'}")
    print(f"Integración directa: {'BIEN!' if exito_directo else 'MAL!'}")
    print(f"Integración con conversión: {'BIEN!' if exito_conversion else 'MAL!'}")
    
    if exito_captura and exito_directo and exito_conversion:
        print("\nBIEN! TODAS LAS PRUEBAS EXITOSAS")
        sys.exit(0)
    elif exito_captura:
        print("\nCUIDADO! El sistema de captura funciona, pero la evaluación falla")
        sys.exit(1)
    else:
        print("\nMAL! EL SISTEMA DE CAPTURA DE ASSERTS NO FUNCIONA")
        sys.exit(1)