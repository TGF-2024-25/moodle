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

    nota_total = 0
    nota_maxima = 0
    retroalimentacion = []

    # Ejecutar todo el notebook primero
    try:
        ejecutor = ExecutePreprocessor(timeout=120, kernel_name='python3')
        ejecutor.preprocess(notebook, {'metadata': {'path': os.path.dirname(ruta_notebook)}})
    except Exception as e:
        # Si falla la ejecución completa, intentar celdas individualmente
        pass

    # Evaluar cada celda con metadatos nbgrader
    for i, celda in enumerate(notebook.cells):
        metadatos = celda.get('metadata', {}).get('nbgrader', {})
        
        if metadatos.get('grade', False):
            puntos = metadatos.get('points', 10)  # Por defecto, 10 puntos
            identificador = metadatos.get('grade_id', f'celda_{i}')
            nota_maxima += puntos

            puntos_obtenidos = puntos
            mensaje_error = ""

            # Verificar si la celda tiene errores
            if celda['cell_type'] == 'code':
                for output in celda.get('outputs', []):
                    if output.output_type == 'error':
                        puntos_obtenidos = 0
                        mensaje_error = f"{output.ename}: {output.evalue}"
                        break

            nota_total += puntos_obtenidos
            
            if puntos_obtenidos == puntos:
                retroalimentacion.append(f"{identificador}: {puntos_obtenidos}/{puntos}\n")
            else:
                mensaje_simple = simplificar_error(mensaje_error)
                retroalimentacion.append(f"{identificador}: {puntos_obtenidos}/{puntos} - {mensaje_simple}\n")

    # NORMALIZACIÓN A ESCALA 0-10
    if nota_maxima > 0:
        # Calcular la nota normalizada (proporción de puntos obtenidos * 10)
        nota_final = (nota_total / nota_maxima) * 10
    else:
        nota_final = 0

    return {
        "estado": "ok",
        "nota": round(nota_final, 2),  # Nota normalizada a escala 0-10
        "nota_sin_normalizar": round(nota_total, 2),  # Para debugging
        "nota_maxima_sin_normalizar": nota_maxima,  # Para debugging
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