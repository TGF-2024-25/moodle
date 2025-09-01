import sys
import json
import os
from nbformat import v4 as nbformat

def evaluate_python_file(file_path):
    """Evalúa un archivo Python básico"""
    try:
        with open(file_path, 'r') as f:
            code = f.read()
        
        # Aquí iría tu lógica real de evaluación
        # Esto es solo un ejemplo básico
        
        # Simulamos que encontramos algunas funciones
        has_functions = 'def ' in code
        has_main = 'if __name__ == "__main__":' in code
        lines = code.count('\n') + 1
        
        # Nota simulada basada en características básicas
        nota = 5  # Base
        if has_functions: nota += 2
        if has_main: nota += 1
        if lines > 10: nota += 1
        if lines > 20: nota += 1
        
        nota = min(10, nota)  # Máximo 10
        
        feedback = [
            "Características encontradas:",
            f"- Tiene funciones: {'Sí' if has_functions else 'No'}",
            f"- Tiene bloque main: {'Sí' if has_main else 'No'}",
            f"- Líneas de código: {lines}",
            "\nNota asignada basada en estructura básica"
        ]
        
        return {
            "estado": "ok",
            "nota": nota,
            "retroalimentacion": "\n".join(feedback)
        }
        
    except Exception as e:
        return {
            "estado": "error",
            "error": f"No se pudo evaluar el archivo: {str(e)}"
        }

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(json.dumps({
            "estado": "error",
            "error": "Se requieren 2 argumentos: archivo y usuario"
        }))
        sys.exit(1)
    
    file_path = sys.argv[1]
    usuario = sys.argv[2]
    
    # Primero convertimos a .ipynb
    try:
        # Crear notebook básico
        notebook = nbformat.new_notebook()
        
        # Añadir celda con el código
        with open(file_path, 'r') as f:
            code = f.read()
        
        code_cell = nbformat.new_code_cell(source=code)
        notebook.cells.append(code_cell)
        
        # Guardar temporalmente como .ipynb
        temp_ipynb = f"{file_path}.ipynb"
        with open(temp_ipynb, 'w') as f:
            nbformat.write(notebook, f)
        
        # Aquí normalmente llamarías a evaluate_nbgrader.py
        # Pero para este ejemplo, usamos nuestra evaluación básica
        result = evaluate_python_file(file_path)
        
        # Limpiar
        os.unlink(temp_ipynb)
        
        print(json.dumps(result))
        
    except Exception as e:
        print(json.dumps({
            "estado": "error",
            "error": f"Error en la conversión/evaluación: {str(e)}"
        }))
        sys.exit(1)