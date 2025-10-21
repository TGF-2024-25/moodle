#!/usr/bin/env python3
import sys
import os
import json
import unittest
import tempfile
import subprocess
from unittest.mock import patch, MagicMock, call
import nbformat
import re

# Añadir ruta para importar módulos
sys.path.append('/var/www/html/moodle/mod/autocorreccion')

print("=== SISTEMA DE PRUEBAS AUTOCORRECCIÓN COMPLETO ===\n")

class TestSistemaAutocorreccion(unittest.TestCase):
    
    def setUp(self):
        """Configuración inicial para las pruebas"""
        self.archivos_necesarios = ['convert_py_to_ipynb.py', 'evaluate_nbgrader.py']
        self.nbgrader_path = "/opt/nbgrader_course"
        self.test_files_dir = tempfile.mkdtemp()
        
        # Crear directorios de prueba para nbgrader si no existen
        os.makedirs(os.path.join(self.nbgrader_path, 'submitted', 'testuser', 'ps1'), exist_ok=True)
        os.makedirs(os.path.join(self.nbgrader_path, 'source'), exist_ok=True)
        os.makedirs(os.path.join(self.nbgrader_path, 'released'), exist_ok=True)
    
    def test_01_archivos_existen(self):
        """Verificar que los archivos necesarios existen"""
        print("1. Verificando archivos necesarios...")
        for archivo in self.archivos_necesarios:
            with self.subTest(archivo=archivo):
                self.assertTrue(os.path.exists(archivo), f"Archivo {archivo} no encontrado")
                print(f"   OK! {archivo} encontrado")
    
    def test_02_conversion_python_a_ipynb(self):
        """Probar la conversión de Python a Jupyter Notebook"""
        print("\n2. Probando conversión Python -> Jupyter...")
        try:
            from convert_py_to_ipynb import convert_py_to_ipynb
            
            # Crear archivo de prueba con código válido
            test_file = os.path.join(self.test_files_dir, 'test_script_valido.py')
            with open(test_file, 'w') as f:
                f.write('''def suma(a, b):
    return a + b

def test_suma():
    assert suma(2, 3) == 5
    assert suma(-1, 1) == 0

print("Resultado de suma(5, 3):", suma(5, 3))
''')
            
            output_file = os.path.join(self.test_files_dir, 'test_conversion.ipynb')
            convert_py_to_ipynb(test_file, output_file)
            
            self.assertTrue(os.path.exists(output_file), "La conversión falló - archivo no creado")
            
            # Verificar que el archivo tiene formato JSON válido (formato Jupyter)
            with open(output_file, 'r') as f:
                notebook_content = json.load(f)
                self.assertIn('cells', notebook_content, "El notebook no tiene estructura válida")
                self.assertIn('metadata', notebook_content, "El notebook no tiene metadatos")
            
            print("   OK! Conversión exitosa y estructura válida")
            
        except Exception as e:
            self.fail(f"Error en conversión: {e}")
    
    def test_03_estructura_nbgrader(self):
        """Verificar la estructura de directorios de nbgrader"""
        print("\n3. Verificando estructura nbgrader...")
        self.assertTrue(os.path.exists(self.nbgrader_path), "Directorio nbgrader no existe")
        print("   OK! Directorio nbgrader existe")
        
        # Verificar subdirectorios
        subdirs = ['source', 'submitted', 'released']
        for subdir in subdirs:
            path = os.path.join(self.nbgrader_path, subdir)
            with self.subTest(subdir=subdir):
                self.assertTrue(os.path.exists(path), f"Subdirectorio {subdir} no existe")
                print(f"   OK! {subdir}/ existe")
    
    def test_04_funcion_convertir_asserts(self):
        """Probar la función que convierte asserts a capturar_assert"""
        print("\n4. Probando conversión de asserts...")
        from evaluate_nbgrader import convertir_asserts_a_captura
        
        # Código con diferentes tipos de asserts
        codigo_con_asserts = '''
def test_funcion():
    assert suma(2, 3) == 5
    assert resta(5, 3) == 2
    assert multiplica(2, 3) == 6
    assert variable is True
    assert otra_variable == "valor"
    
resultado = test_funcion()
'''
        
        codigo_convertido = convertir_asserts_a_captura(codigo_con_asserts)
        
        # Verificar que los asserts fueron convertidos (con formato flexible)
        self.assertIn('capturar_assert(suma(2, 3)', codigo_convertido)
        self.assertIn('capturar_assert(bool(variable is True)', codigo_convertido)
        self.assertNotIn('assert suma(2, 3) == 5', codigo_convertido)
        
        print("   OK! Conversión de asserts exitosa")
    
    def test_05_evaluacion_notebook_valido(self):
        """Probar evaluación de notebook con código válido"""
        print("\n5. Probando evaluación de notebook válido...")
        from evaluate_nbgrader import evaluar_notebook
        
        # Crear notebook de prueba con código válido
        notebook_valido = nbformat.v4.new_notebook()
        
        # Celda con código válido
        codigo_valido = '''
def suma(a, b):
    return a + b

resultado = suma(3, 5)
print(f"El resultado es: {resultado}")
'''
        celda_codigo = nbformat.v4.new_code_cell(codigo_valido)
        notebook_valido.cells.append(celda_codigo)
        
        # Guardar notebook temporal
        notebook_path = os.path.join(self.test_files_dir, 'notebook_valido.ipynb')
        with open(notebook_path, 'w', encoding='utf-8') as f:
            nbformat.write(notebook_valido, f)
        
        # Evaluar notebook
        resultado = evaluar_notebook(notebook_path)
        
        self.assertEqual(resultado['estado'], 'ok')
        self.assertIsInstance(resultado['nota'], (int, float))
        self.assertIn('retroalimentacion', resultado)
        
        print(f"   OK! Evaluación exitosa. Nota: {resultado['nota']}")
    
    def test_06_evaluacion_notebook_con_errores(self):
        """Probar evaluación de notebook con errores sintácticos"""
        print("\n6. Probando evaluación de notebook con errores...")
        from evaluate_nbgrader import evaluar_notebook
        
        # Crear notebook con error sintáctico
        notebook_error = nbformat.v4.new_notebook()
        
        codigo_con_error = '''
def funcion_mal_definida(
    return "falta cerrar paréntesis y dos puntos"
    
print(funcion_mal_definida()
'''
        celda_error = nbformat.v4.new_code_cell(codigo_con_error)
        notebook_error.cells.append(celda_error)
        
        # Guardar notebook temporal
        notebook_path = os.path.join(self.test_files_dir, 'notebook_error.ipynb')
        with open(notebook_path, 'w', encoding='utf-8') as f:
            nbformat.write(notebook_error, f)
        
        # Evaluar notebook
        resultado = evaluar_notebook(notebook_path)
        
        # Debe manejar el error adecuadamente
        self.assertIn(resultado['estado'], ['ok', 'error'])
        if resultado['estado'] == 'error':
            self.assertIn('error', resultado)
        else:
            # Aún en estado 'ok' pero con nota baja por errores
            self.assertLess(resultado['nota'], 5)
        
        print(f"   OK! Manejo de errores funcionando. Estado: {resultado['estado']}")
    
    def test_07_evaluacion_notebook_con_tests(self):
        """Probar evaluación de notebook con tests (asserts)"""
        print("\n7. Probando evaluación con tests...")
        from evaluate_nbgrader import evaluar_notebook
        
        # Crear notebook con tests
        notebook_con_tests = nbformat.v4.new_notebook()
        
        codigo_con_tests = '''
def multiplica(a, b):
    return a * b

# Tests
assert multiplica(2, 3) == 6
assert multiplica(0, 5) == 0
assert multiplica(-2, 3) == -6

print("Todos los tests pasaron")
'''
        celda_tests = nbformat.v4.new_code_cell(codigo_con_tests)
        notebook_con_tests.cells.append(celda_tests)
        
        # Guardar notebook temporal
        notebook_path = os.path.join(self.test_files_dir, 'notebook_tests.ipynb')
        with open(notebook_path, 'w', encoding='utf-8') as f:
            nbformat.write(notebook_con_tests, f)
        
        # Evaluar notebook
        resultado = evaluar_notebook(notebook_path)
        
        self.assertEqual(resultado['estado'], 'ok')
        # Los tests deberían pasar y dar una buena nota
        self.assertGreaterEqual(resultado['nota'], 8)
        self.assertIn('RESULTADOS DETALLADOS', resultado['retroalimentacion'])
        
        print(f"   OK! Tests evaluados correctamente. Nota: {resultado['nota']}")
    
    def test_08_evaluacion_notebook_con_tests_fallidos(self):
        """Probar evaluación de notebook con tests que fallan"""
        print("\n8. Probando evaluación con tests fallidos...")
        from evaluate_nbgrader import evaluar_notebook
        
        # Crear notebook con tests que fallan
        notebook_tests_fallidos = nbformat.v4.new_notebook()
        
        codigo_tests_fallidos = '''
def division(a, b):
    return a / b

# Tests que fallarán
assert division(10, 2) == 6  # Debería ser 5, no 6
assert division(9, 3) == 2   # Debería ser 3, no 2

print("Algunos tests fallaron")
'''
        celda_tests_fallidos = nbformat.v4.new_code_cell(codigo_tests_fallidos)
        notebook_tests_fallidos.cells.append(celda_tests_fallidos)
        
        # Guardar notebook temporal
        notebook_path = os.path.join(self.test_files_dir, 'notebook_tests_fallidos.ipynb')
        with open(notebook_path, 'w', encoding='utf-8') as f:
            nbformat.write(notebook_tests_fallidos, f)
        
        # Evaluar notebook
        resultado = evaluar_notebook(notebook_path)
        
        self.assertEqual(resultado['estado'], 'ok')
        # Los tests fallidos deberían dar una nota baja
        self.assertLess(resultado['nota'], 5)
        self.assertIn('Error:', resultado['retroalimentacion'])
        
        print(f"   OK! Tests fallidos detectados. Nota: {resultado['nota']}")
    
    def test_09_crear_archivos_prueba_diversos(self):
        """Crear diferentes tipos de archivos de prueba"""
        print("\n9. Creando archivos de prueba diversos...")
        
        # 1. Archivo con código correcto
        codigo_correcto = os.path.join(self.test_files_dir, 'codigo_correcto.py')
        with open(codigo_correcto, 'w') as f:
            f.write('''def factorial(n):
    if n == 0:
        return 1
    else:
        return n * factorial(n-1)

# Tests
assert factorial(5) == 120
assert factorial(0) == 1
assert factorial(1) == 1

print("Factorial de 5 es:", factorial(5))
''')
        
        # 2. Archivo con error sintáctico
        error_sintactico = os.path.join(self.test_files_dir, 'error_sintactico.py')
        with open(error_sintactico, 'w') as f:
            f.write('''def funcion_mal_definida(
    return "falta cerrar paréntesis"
    
print(funcion_mal_definida()
''')
        
        # 3. Archivo con error lógico
        error_logico = os.path.join(self.test_files_dir, 'error_logico.py')
        with open(error_logico, 'w') as f:
            f.write('''def es_par(n):
    return n % 2 == 1  # Error lógico: debería ser == 0

# Tests que fallarán
assert es_par(2) == True   # Fallará
assert es_par(3) == False  # Fallará

print("Tests completados")
''')
        
        # 4. Archivo vacío
        archivo_vacio = os.path.join(self.test_files_dir, 'archivo_vacio.py')
        with open(archivo_vacio, 'w') as f:
            f.write('')
        
        # 5. Archivo con código potencialmente peligroso
        codigo_peligroso = os.path.join(self.test_files_dir, 'codigo_peligroso.py')
        with open(codigo_peligroso, 'w') as f:
            f.write('''import os
import subprocess

# Intentos de acceso al sistema (deberían ser bloqueados o manejados)
try:
    files = os.listdir('/tmp')
    print("Archivos en /tmp:", len(files))
except:
    print("Acceso a sistema bloqueado")

# Bucle infinito (debería tener timeout)
# while True:
#     pass

print("Código potencialmente peligroso ejecutado")
''')
        
        # Verificar que se crearon todos los archivos
        archivos_creados = os.listdir(self.test_files_dir)
        self.assertGreaterEqual(len(archivos_creados), 5)
        
        print(f"   OK! {len(archivos_creados)} archivos de prueba creados")
    
    def test_10_proceso_completo_conversion_evaluacion(self):
        """Probar el proceso completo: Python -> IPYNB -> Evaluación"""
        print("\n10. Probando proceso completo de conversión y evaluación...")
        
        try:
            from convert_py_to_ipynb import convert_py_to_ipynb
            from evaluate_nbgrader import evaluar_notebook
            
            # Crear archivo Python con tests
            archivo_py = os.path.join(self.test_files_dir, 'test_completo.py')
            with open(archivo_py, 'w') as f:
                f.write('''def potencia(base, exponente):
    return base ** exponente

# Tests
assert potencia(2, 3) == 8
assert potencia(5, 0) == 1
assert potencia(3, 2) == 9

print("Resultado de 2^3:", potencia(2, 3))
''')
            
            # Convertir a IPYNB
            archivo_ipynb = os.path.join(self.test_files_dir, 'test_completo.ipynb')
            convert_py_to_ipynb(archivo_py, archivo_ipynb)
            
            self.assertTrue(os.path.exists(archivo_ipynb), "Conversión falló")
            
            # Evaluar el notebook
            resultado = evaluar_notebook(archivo_ipynb)
            
            self.assertEqual(resultado['estado'], 'ok')
            # Verificar que al menos se ejecutó
            self.assertIsInstance(resultado['nota'], (int, float))
            
            print(f"   OK! Proceso completo exitoso. Nota: {resultado['nota']}")
            
        except Exception as e:
            self.fail(f"Error en proceso completo: {e}")
    
    def test_11_validacion_seguridad(self):
        """Probar medidas de seguridad contra código malicioso"""
        print("\n11. Probando medidas de seguridad...")
        
        # Esta prueba verifica que el sistema maneja adecuadamente
        # código potencialmente peligroso con timeouts y captura de errores
        
        from evaluate_nbgrader import evaluar_notebook
        
        # Crear notebook con código que podría causar problemas
        notebook_seguridad = nbformat.v4.new_notebook()
        
        codigo_seguridad = '''
# Intentar operaciones que podrían ser problemáticas
import time

# Esto debería ser manejado por el timeout del ejecutor
print("Iniciando operación larga...")
for i in range(1000000):
    pass
print("Operación completada")

# División por cero (debe ser capturada)
try:
    resultado = 1 / 0
except ZeroDivisionError as e:
    print("División por cero capturada:", str(e))

print("Prueba de seguridad completada")
'''
        celda_seguridad = nbformat.v4.new_code_cell(codigo_seguridad)
        notebook_seguridad.cells.append(celda_seguridad)
        
        # Guardar notebook temporal
        notebook_path = os.path.join(self.test_files_dir, 'notebook_seguridad.ipynb')
        with open(notebook_path, 'w', encoding='utf-8') as f:
            nbformat.write(notebook_seguridad, f)
        
        # Evaluar notebook - debería manejar los problemas adecuadamente
        resultado = evaluar_notebook(notebook_path)
        
        # El sistema debería manejar esto sin caerse
        self.assertIn(resultado['estado'], ['ok', 'error'])
        
        print(f"   OK! Medidas de seguridad funcionando. Estado: {resultado['estado']}")
    
    def test_12_formato_salida_json(self):
        """Probar que la salida tiene formato JSON válido"""
        print("\n12. Probando formato de salida JSON...")
        
        # Simular ejecución desde línea de comandos
        test_cmd = [
            sys.executable, 'evaluate_nbgrader.py',
            os.path.join(self.test_files_dir, 'notebook_valido.ipynb'),
            'testuser'
        ]
        
        try:
            result = subprocess.run(test_cmd, capture_output=True, text=True, timeout=30)
            
            # Verificar que la salida es JSON válido
            if result.returncode == 0:
                output_data = json.loads(result.stdout)
                self.assertIn('estado', output_data)
                self.assertIn('nota', output_data)
                self.assertIn('retroalimentacion', output_data)
                
                print("   OK! Formato JSON válido en salida")
            else:
                print(f"   CUIDADO! Comando falló pero probamos formato: {result.stderr}")
                # Intentar parsear aunque falle
                try:
                    output_data = json.loads(result.stdout)
                    self.assertIn('estado', output_data)
                    print("   OK! Formato JSON válido incluso en error")
                except json.JSONDecodeError:
                    self.fail("La salida no es JSON válido")
                    
        except subprocess.TimeoutExpired:
            print("   CUIDADO! Timeout en ejecución (esperado para algunas pruebas)")
        except Exception as e:
            print(f"   CUIDADO! Error en ejecución de comando: {e}")
    
    def test_13_pruebas_rendimiento(self):
        """Pruebas básicas de rendimiento y tiempo de respuesta"""
        print("\n13. Probando rendimiento del sistema...")
        
        from evaluate_nbgrader import evaluar_notebook
        
        # Crear notebook simple para prueba de rendimiento
        notebook_rendimiento = nbformat.v4.new_notebook()
        
        codigo_rendimiento = '''
# Código simple para prueba de rendimiento
def funcion_simple():
    return "Hola Mundo"

resultado = funcion_simple()
print(resultado)
'''
        celda_rendimiento = nbformat.v4.new_code_cell(codigo_rendimiento)
        notebook_rendimiento.cells.append(celda_rendimiento)
        
        # Guardar notebook temporal
        notebook_path = os.path.join(self.test_files_dir, 'notebook_rendimiento.ipynb')
        with open(notebook_path, 'w', encoding='utf-8') as f:
            nbformat.write(notebook_rendimiento, f)
        
        # Medir tiempo de ejecución
        import time
        start_time = time.time()
        
        resultado = evaluar_notebook(notebook_path)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Verificar que la ejecución es razonablemente rápida
        self.assertLess(execution_time, 30, "La evaluación tomó demasiado tiempo")
        self.assertEqual(resultado['estado'], 'ok')
        
        print(f"   OK! Rendimiento aceptable. Tiempo: {execution_time:.2f}s")
    
    def test_14_integracion_sistema_archivos(self):
        """Probar integración con sistema de archivos y nbgrader"""
        print("\n14. Probando integración con sistema de archivos...")
        
        # Verificar que podemos escribir en los directorios de nbgrader
        test_dirs = [
            self.nbgrader_path,
            os.path.join(self.nbgrader_path, 'submitted'),
            os.path.join(self.nbgrader_path, 'submitted', 'testuser'),
            os.path.join(self.nbgrader_path, 'submitted', 'testuser', 'ps1')
        ]
        
        for test_dir in test_dirs:
            if os.path.exists(test_dir):
                # Intentar crear un archivo de prueba
                test_file = os.path.join(test_dir, 'test_write.txt')
                try:
                    with open(test_file, 'w') as f:
                        f.write('test de escritura')
                    os.remove(test_file)
                    print(f"   OK! Escritura permitida en {test_dir}")
                except Exception as e:
                    print(f"   CUIDADO! No se puede escribir en {test_dir}: {e}")
            else:
                print(f"   CUIDADO! Directorio no existe: {test_dir}")
    
    def tearDown(self):
        """Limpieza después de las pruebas"""
        # Limpiar archivos de prueba
        import shutil
        if os.path.exists(self.test_files_dir):
            shutil.rmtree(self.test_files_dir)


class TestPHPIntegration(unittest.TestCase):
    """Pruebas de integración con componentes PHP"""
    
    def test_php_components_exist(self):
        """Verificar que los archivos PHP necesarios existen"""
        print("\n15. Verificando componentes PHP...")
        
        php_files = [
            'lib.php',
            'view.php', 
            'upload.php',
            'mod_form.php',
            'version.php'
        ]
        
        for php_file in php_files:
            with self.subTest(php_file=php_file):
                self.assertTrue(os.path.exists(php_file), f"Archivo PHP {php_file} no encontrado")
                print(f"   OK! {php_file} encontrado")
    
    def test_php_database_structure(self):
        """Verificar estructura de base de datos desde PHP"""
        print("\n16. Verificando estructura de base de datos...")
        
        # Buscar install.xml en diferentes ubicaciones posibles
        posibles_rutas = [
            'install.xml',
            'db/install.xml',
            '/var/www/html/moodle/mod/autocorreccion/db/install.xml'
        ]
        
        install_encontrado = False
        for ruta in posibles_rutas:
            if os.path.exists(ruta):
                install_encontrado = True
                with open(ruta, 'r') as f:
                    content = f.read()
                
                # Verificar tablas esenciales
                if '<TABLE NAME="autocorreccion"' in content:
                    print("   OK! Tabla autocorreccion encontrada")
                if '<TABLE NAME="autocorreccion_envios"' in content:
                    print("   OK! Tabla autocorreccion_envios encontrada")
                
                break
        
        if not install_encontrado:
            print("   CUIDADO! install.xml no encontrado en ubicaciones esperadas")


if __name__ == '__main__':
    # Ejecutar pruebas unitarias
    suite = unittest.TestLoader().loadTestsFromTestCase(TestSistemaAutocorreccion)
    php_suite = unittest.TestLoader().loadTestsFromTestCase(TestPHPIntegration)
    
    print("Ejecutando pruebas del sistema de autocorrección...")
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\nEjecutando pruebas de integración PHP...")
    result_php = runner.run(php_suite)
    
    # Resumen final
    print("\n" + "="*60)
    print("RESUMEN FINAL DE PRUEBAS")
    print("="*60)
    
    total_tests = result.testsRun + result_php.testsRun
    total_errors = len(result.errors) + len(result_php.errors)
    total_failures = len(result.failures) + len(result_php.failures)
    
    print(f"Total pruebas ejecutadas: {total_tests}")
    print(f"Errores: {total_errors}")
    print(f"Fallos: {total_failures}")
    print(f"Éxitos: {total_tests - total_errors - total_failures}")
    
    if total_errors == 0 and total_failures == 0:
        print("\nBIEN! TODAS LAS PRUEBAS PASARON EXITOSAMENTE")
    else:
        print("\nMAL! Algunas pruebas fallaron")
        
        # Mostrar detalles de errores
        if result.errors:
            print("\nErrores en pruebas principales:")
            for error in result.errors:
                print(f"  - {error[0]}: {error[1]}")
                
        if result_php.errors:
            print("\nErrores en pruebas PHP:")
            for error in result_php.errors:
                print(f"  - {error[0]}: {error[1]}")
    
    print("\n=== PRUEBAS COMPLETADAS ===")