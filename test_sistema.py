#!/usr/bin/env python3
import sys
import os
sys.path.append('/var/www/html/moodle/mod/autocorreccion')

print("=== TEST DEL SISTEMA AUTOCORRECCIÓN ===\n")

# 1. Probar que los archivos existen
print("1. Verificando archivos necesarios...")
archivos_necesarios = ['convert_py_to_ipynb.py', 'evaluate_nbgrader.py']
for archivo in archivos_necesarios:
    if os.path.exists(archivo):
        print(f"   ✓ {archivo} encontrado")
    else:
        print(f"   ✗ {archivo} NO encontrado")

# 2. Probar conversión
print("\n2. Probando conversión Python → Jupyter...")
try:
    from convert_py_to_ipynb import convert_py_to_ipynb
    
    # Crear archivo de prueba
    with open('test_script.py', 'w') as f:
        f.write('def test():\n    return "Hola Mundo"\n\nprint(test())')
    
    convert_py_to_ipynb('test_script.py', 'test_conversion.ipynb')
    
    if os.path.exists('test_conversion.ipynb'):
        print("   ✓ Conversión exitosa")
        os.remove('test_script.py')
    else:
        print("   ✗ La conversión falló")
        
except Exception as e:
    print(f"   ✗ Error en conversión: {e}")

# 3. Probar estructura nbgrader
print("\n3. Verificando estructura nbgrader...")
nbgrader_path = "/home/vagrant/mycourse"
if os.path.exists(nbgrader_path):
    print("   ✓ Directorio nbgrader existe")
    
    # Verificar subdirectorios
    subdirs = ['source', 'submitted', 'released']
    for subdir in subdirs:
        path = os.path.join(nbgrader_path, subdir)
        if os.path.exists(path):
            print(f"   ✓ {subdir}/ existe")
        else:
            print(f"   ✗ {subdir}/ NO existe")
else:
    print("   ✗ Directorio nbgrader NO existe")

print("\n=== TEST COMPLETADO ===")
