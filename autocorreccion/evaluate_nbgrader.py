import sys
import os
import json
import nbformat
from nbconvert.preprocessors import ExecutePreprocessor

# === Función principal de evaluación ===
def evaluar_notebook(ruta_notebook):
    """Ejecuta y evalúa un notebook de forma automática"""
    with open(ruta_notebook, 'r', encoding='utf-8') as f:
        notebook = nbformat.read(f, as_version=4)

    # Ejecutar todas las celdas del notebook
    ejecutor = ExecutePreprocessor(timeout=120, kernel_name='python3')
    ejecutor.preprocess(notebook, {'metadata': {'path': os.path.dirname(ruta_notebook)}})

    # Inicializar variables de evaluación
    nota_total = 0
    nota_maxima = 0
    retroalimentacion = []

    for celda in notebook.cells:
        metadatos = celda.get('metadata', {}).get('nbgrader', {})
        if metadatos.get('grade', False):
            puntos = metadatos.get('points', 0)
            identificador = metadatos.get('grade_id', 'sin_id')
            nota_maxima += puntos

            aprobada = True
            if celda['cell_type'] == 'code':
                for salida in celda.get('outputs', []):
                    if salida.output_type == 'error' or 'AssertionError' in str(salida):
                        aprobada = False
                        break

            puntos_obtenidos = puntos if aprobada else 0
            nota_total += puntos_obtenidos
            retroalimentacion.append(f"{identificador}: {puntos_obtenidos}/{puntos}")

    return {
        "estado": "ok",
        "nota": round(nota_total, 2),
        "retroalimentacion": "\n".join(retroalimentacion)
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
