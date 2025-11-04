import sys
import os
import json
import nbformat
from nbconvert.preprocessors import ExecutePreprocessor
import re

def convertir_asserts_a_captura(codigo):
    """Convierte asserts normales en llamadas a capturar_assert"""
    # Patrones para asserts
    patterns = [
        # assert x == y
        (r'assert\s+([^#\n]+)\s*==\s*([^#\n]+)(\s*#.*)?$', r'capturar_assert(\1, \2, "\1 == \2")'),
        # assert condicion
        (r'assert\s+([^#\n]+)(\s*#.*)?$', r'capturar_assert(bool(\1), True, "\1")')
    ]
    
    for pattern, replacement in patterns:
        codigo = re.sub(pattern, replacement, codigo, flags=re.MULTILINE)
    
    return codigo

def evaluar_notebook(ruta_notebook):
    """Evaluar notebook con manejo de errores mejorado"""
    try:
        with open(ruta_notebook, 'r', encoding='utf-8') as f:
            notebook = nbformat.read(f, as_version=4)
    except Exception as e:
        return {
            "estado": "error",
            "error": f"No se pudo leer el notebook: {str(e)}",
            "nota": 0,
            "retroalimentacion": f"Error al leer el archivo: {str(e)}"
        }

    # Debug: mostrar asserts encontrados (no para output)
    contenido_original = ""
    for celda in notebook.cells:
        if celda.cell_type == 'code':
            contenido_original += celda.source + "\n"

    asserts_encontrados = re.findall(r'assert\s+', contenido_original)

    # Crear un nuevo notebook con el sistema de captura
    notebook_evaluacion = nbformat.v4.new_notebook()
    
    # Añadir código de inicialización
    codigo_inicial = '''
# === SISTEMA DE EVALUACIÓN AUTOMÁTICA ===
resultados_tests = []

def capturar_assert(actual, esperado, descripcion):
    """Captura el resultado de un assert sin detener la ejecución"""
    try:
        if actual == esperado:
            resultados_tests.append({
                "funcion": descripcion.split('(')[0] if '(' in descripcion else "test",
                "puntos": 5,
                "obtenido": 5,
                "error": None,
                "descripcion": descripcion
            })
            return True
        else:
            resultados_tests.append({
                "funcion": descripcion.split('(')[0] if '(' in descripcion else "test", 
                "puntos": 5,
                "obtenido": 0,
                "error": f"Esperado: {esperado}, Obtenido: {actual}",
                "descripcion": descripcion
            })
            return False
    except Exception as e:
        resultados_tests.append({
            "funcion": descripcion.split('(')[0] if '(' in descripcion else "test",
            "puntos": 5,
            "obtenido": 0,
            "error": f"Error: {str(e)}",
            "descripcion": descripcion
        })
        return False

def mostrar_resultados_finales():
    """Muestra los resultados de forma organizada"""
    print("=== RESULTADOS DETALLADOS ===")
    
    if not resultados_tests:
        print("No se evaluaron tests")
        return 0, 0, 0
    
    # Agrupar por función (mejor extracción del nombre de función)
    resultados_por_funcion = {}
    for test in resultados_tests:
        # Mejor extracción del nombre de función
        descripcion = test["descripcion"]
        if '(' in descripcion and ')' in descripcion:
            funcion = descripcion.split('(')[0].strip()
        else:
            # Para asserts simples como assert True == True
            funcion = "test_general"
        
        if funcion not in resultados_por_funcion:
            resultados_por_funcion[funcion] = {
                "puntos_totales": 0,
                "puntos_obtenidos": 0,
                "errores": []
            }
        
        resultados_por_funcion[funcion]["puntos_totales"] += test["puntos"]
        resultados_por_funcion[funcion]["puntos_obtenidos"] += test["obtenido"]
        if test["error"]:
            resultados_por_funcion[funcion]["errores"].append(test["error"])
    
    # Mostrar resultados por función
    for funcion, datos in resultados_por_funcion.items():
        puntuacion = f"{datos['puntos_obtenidos']}/{datos['puntos_totales']}"
        if datos['puntos_obtenidos'] < datos['puntos_totales'] and datos['errores']:
            # Mostrar solo el primer error para no saturar
            primer_error = datos['errores'][0]
            if len(primer_error) > 50:  # Acortar errores muy largos
                primer_error = primer_error[:47] + "..."
            print(f"{funcion}: {puntuacion} - Error: {primer_error}")
        else:
            print(f"{funcion}: {puntuacion}")
    
    # Calcular nota final
    total_puntos = sum(datos["puntos_totales"] for datos in resultados_por_funcion.values())
    puntos_obtenidos = sum(datos["puntos_obtenidos"] for datos in resultados_por_funcion.values())
    
    if total_puntos > 0:
        nota_final = (puntos_obtenidos / total_puntos) * 10
        print(f"\\nNOTA FINAL: {nota_final:.2f}/10")
        return nota_final, puntos_obtenidos, total_puntos
    else:
        print("No se evaluaron tests")
        return 0, 0, 0
'''
    
    # Añadir celda de inicialización
    celda_inicial = nbformat.v4.new_code_cell(codigo_inicial)
    notebook_evaluacion.cells.append(celda_inicial)
    
    # Procesar cada celda del notebook original
    for celda in notebook.cells:
        if celda.cell_type == 'code':
            # Convertir asserts a capturar_assert
            codigo_modificado = convertir_asserts_a_captura(celda.source)
            nueva_celda = nbformat.v4.new_code_cell(codigo_modificado)
            notebook_evaluacion.cells.append(nueva_celda)
        else:
            notebook_evaluacion.cells.append(celda)
    
    # Añadir celda final para mostrar resultados
    celda_final = nbformat.v4.new_code_cell('''
nota_final, puntos_obtenidos, total_puntos = mostrar_resultados_finales()
''')
    notebook_evaluacion.cells.append(celda_final)
    
    # Ejecutar el notebook de evaluación
    try:
        ejecutor = ExecutePreprocessor(timeout=120, kernel_name='python3', allow_errors=True)
        ejecutor.preprocess(notebook_evaluacion, {'metadata': {'path': os.path.dirname(ruta_notebook)}})
        
        # Capturar la salida de la última celda
        retroalimentacion = ""
        if notebook_evaluacion.cells and notebook_evaluacion.cells[-1].outputs:
            for output in notebook_evaluacion.cells[-1].outputs:
                if hasattr(output, 'text'):
                    retroalimentacion += output.text + "\n"
                elif hasattr(output, 'data') and 'text/plain' in output.data:
                    retroalimentacion += output.data['text/plain'] + "\n"

        # Limpiar saltos de línea literales
        retroalimentacion = retroalimentacion.replace('\\n', '\n')
        
        # Buscar la nota final en la retroalimentación
        nota_final = 0
        if "NOTA FINAL:" in retroalimentacion:
            lineas = retroalimentacion.split('\n')
            for linea in lineas:
                if "NOTA FINAL:" in linea:
                    try:
                        nota_str = linea.split(":")[1].strip().split("/")[0]
                        nota_final = float(nota_str)
                    except:
                        pass
        
        return {
            "estado": "ok",
            "nota": round(nota_final, 2),
            "retroalimentacion": retroalimentacion
        }
        
    except Exception as e:
        return {
            "estado": "error",
            "error": f"Error en ejecución: {str(e)}",
            "nota": 0,
            "retroalimentacion": f"Error durante la evaluación: {str(e)}"
        }

# Ejecución principal
if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(json.dumps({"estado": "error", "error": "Se requieren 2 argumentos: notebook y usuario"}))
        sys.exit(1)

    ruta_notebook = sys.argv[1]
    estudiante = sys.argv[2]

    try:
        resultado = evaluar_notebook(ruta_notebook)
        print(json.dumps(resultado))
    except Exception as e:
        print(json.dumps({
            "estado": "error",
            "error": f"No se pudo evaluar el notebook: {str(e)}"
        }))