import sys
import nbformat
import ast
import re
from pathlib import Path

def extract_functions_with_tests(code_content):
    """
    Extrae funciones y sus tests asociados del código Python
    """
    functions = []
    tree = ast.parse(code_content)
    
    # Encontrar todas las funciones
    function_nodes = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
    
    for func_node in function_nodes:
        func_name = func_node.name
        func_code = ast.get_source_segment(code_content, func_node)
        
        # Buscar tests (asserts) para esta función
        tests = []
        lines = code_content.split('\n')
        
        # Buscar asserts que mencionen esta función
        for line in lines:
            if 'assert ' in line and func_name in line:
                tests.append(line.strip())
        
        functions.append({
            'name': func_name,
            'code': func_code,
            'tests': tests,
            'line': func_node.lineno
        })
    
    return functions

def create_nbgrader_cell(code_content, cell_id, points=5, grade=True, locked=False):
    """Crea una celda con metadatos de nbgrader"""
    cell = nbformat.v4.new_code_cell(code_content)
    cell.metadata = {
        "nbgrader": {
            "grade": grade,
            "grade_id": cell_id,
            "points": points,
            "locked": locked,
            "solution": True,
            "task": False
        }
    }
    return cell

def convert_py_to_ipynb(py_file, ipynb_file):
    """Convierte archivo Python a Jupyter Notebook con nbgrader"""
    
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
        }
    }
    
    # Extraer funciones y tests
    functions = extract_functions_with_tests(code_content)
    
    if not functions:
        # Si no hay funciones, crear una celda general
        cell = create_nbgrader_cell(
            code_content, 
            "codigo_principal", 
            points=10
        )
        nb.cells.append(cell)
    else:
        # Crear celdas para cada función
        for i, func in enumerate(functions):
            # Celda con la función
            cell_code = func['code']
            
            # Añadir tests si existen
            if func['tests']:
                cell_code += '\n\n# Tests\n'
                for test in func['tests']:
                    cell_code += test + '\n'
            
            cell = create_nbgrader_cell(
                cell_code,
                f"funcion_{func['name']}",
                points=5  # Puntos configurables por función
            )
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