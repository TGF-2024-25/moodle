import sys
import nbformat
import ast
import re
from pathlib import Path

def convert_py_to_ipynb(py_file, ipynb_file):
    """Convierte archivo Python a Jupyter Notebook mejorado para evaluación"""
    
    # Leer el archivo Python
    with open(py_file, 'r', encoding='utf-8') as f:
        code_content = f.read()
    
    # Crear nuevo notebook
    nb = nbformat.v4.new_notebook()
    nb.metadata = {
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3"
        },
        "language_info": {
            "name": "python",
            "version": "3.8.10"
        }
    }
    
    # Estrategia mejorada: mantener asserts y código relacionado juntos
    lines = code_content.split('\n')
    current_cell = []
    cells = []
    
    for i, line in enumerate(lines):
        line_stripped = line.strip()
        
        # Detectar funciones y mantener asserts con su función relacionada
        if (line_stripped.startswith('def ') or 
            line_stripped.startswith('class ') or
            (line_stripped.startswith('assert ') and i > 0 and not lines[i-1].strip().startswith('assert'))):
            
            if current_cell:
                cells.append('\n'.join(current_cell))
                current_cell = []
        
        current_cell.append(line)
    
    if current_cell:
        cells.append('\n'.join(current_cell))
    
    # Crear celdas del notebook, asegurando que asserts estén con su código relacionado
    for cell_content in cells:
        if cell_content.strip():  # No agregar celdas vacías
            cell = nbformat.v4.new_code_cell(cell_content)
            nb.cells.append(cell)
    
    # Guardar el notebook
    with open(ipynb_file, 'w', encoding='utf-8') as f:
        nbformat.write(nb, f, version=4)
    
    return True

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Uso: python convert_py_to_ipynb.py archivo_entrada.py archivo_salida.ipynb")
        sys.exit(1)
    
    try:
        success = convert_py_to_ipynb(sys.argv[1], sys.argv[2])
        if success:
            print(f"Conversión exitosa: {sys.argv[1]} -> {sys.argv[2]}")
        else:
            print("Error en la conversión")
            sys.exit(1)
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)