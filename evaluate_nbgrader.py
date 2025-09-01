import sys
import os
import json
import nbformat
from nbconvert.preprocessors import ExecutePreprocessor

def simplificar_error(mensaje_error):
    """Simplifica los mensajes de error para hacerlos más legibles"""
    if "AssertionError" in mensaje_error:
        return "Error: Test fallido - el resultado no es el esperado"
    elif "SyntaxError" in mensaje_error:
        return "Error de sintaxis en el código"
    elif "NameError" in mensaje_error:
        return "Error: Variable o función no definida"
    elif "TypeError" in mensaje_error:
        return "Error: Tipo de dato incorrecto"
    elif "An error occurred while executing the following cell" in mensaje_error:
        # Extraer solo la parte importante del error
        lines = mensaje_error.split('\n')
        if len(lines) > 2:
            return f"Error en ejecución: {lines[0]}"
        return "Error durante la ejecución del código"
    
    # Si el error es muy largo, tomar solo la primera línea
    if '\n' in mensaje_error:
        return mensaje_error.split('\n')[0]
    
    return mensaje_error

def evaluar_notebook(ruta_notebook):
    """Ejecuta y evalúa un notebook de forma automática"""
    with open(ruta_notebook, 'r', encoding='utf-8') as f:
        notebook = nbformat.read(f, as_version=4)

    # Inicializar variables de evaluación
    nota_total = 0
    nota_maxima = 0
    retroalimentacion = []

    # Ejecutar cada celda por separado para capturar errores individuales
    ejecutor = ExecutePreprocessor(timeout=120, kernel_name='python3')
    
    for i, celda in enumerate(notebook.cells):
        metadatos = celda.get('metadata', {}).get('nbgrader', {})
        if metadatos.get('grade', False):
            puntos = metadatos.get('points', 0)
            identificador = metadatos.get('grade_id', f'celda_{i}')
            nota_maxima += puntos

            aprobada = True
            mensaje_error = ""
            
            if celda['cell_type'] == 'code':
                try:
                    # Ejecutar esta celda individualmente
                    celda_ejecutar = nbformat.v4.new_notebook()
                    celda_ejecutar.cells = [celda]
                    
                    ejecutor.preprocess(celda_ejecutar, {'metadata': {'path': os.path.dirname(ruta_notebook)}})
                    
                    # Verificar si hay errores en los outputs
                    for salida in celda.get('outputs', []):
                        if salida.output_type == 'error':
                            aprobada = False
                            mensaje_error = f"{salida.ename}: {salida.evalue}"
                            break
                            
                except Exception as e:
                    aprobada = False
                    mensaje_error = str(e)
                    # Continuar con la siguiente celda aunque esta falle

            puntos_obtenidos = puntos if aprobada else 0
            nota_total += puntos_obtenidos
            
            if aprobada:
                retroalimentacion.append(f"{identificador}: {puntos_obtenidos}/{puntos}\n")
            else:
                mensaje_simple = simplificar_error(mensaje_error)
                retroalimentacion.append(f"{identificador}: {puntos_obtenidos}/{puntos} - {mensaje_simple}\n")

    return {
        "estado": "ok",
        "nota": round(nota_total, 2),
        "retroalimentacion": "".join(retroalimentacion)
    }

# === Ejecución principal del script ===
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