import sys
import nbformat
import re

def extract_functions_and_tests(code):
    """Extrae funciones y tests del código Python"""
    functions = []
    current_function = None
    lines = code.split('\n')
    
    for i, line in enumerate(lines):
        # Detectar funciones
        if line.strip().startswith('def '):
            func_name = line.split('def ')[1].split('(')[0].strip()
            current_function = {
                'name': func_name,
                'start_line': i,
                'tests': []
            }
            functions.append(current_function)
        
        # Detectar asserts (tests)
        elif 'assert ' in line and current_function:
            # Verificar si el assert está relacionado con la función actual
            if current_function['name'] in line:
                current_function['tests'].append(line.strip())
    
    return functions

def convert_py_to_ipynb(py_file, ipynb_file):
    nb = nbformat.v4.new_notebook()
    
    with open(py_file, 'r', encoding='utf-8') as f:
        code = f.read()
    
    # Extraer funciones y tests
    functions = extract_functions_and_tests(code)
    
    # Crear celdas para cada función con sus tests
    for i, func in enumerate(functions):
        # Crear código para esta celda
        cell_code = ""
        
        # Añadir líneas de la función (desde start_line hasta siguiente función o final)
        start_line = func['start_line']
        end_line = len(code.split('\n'))
        
        if i + 1 < len(functions):
            end_line = functions[i + 1]['start_line']
        
        func_lines = code.split('\n')[start_line:end_line]
        cell_code = '\n'.join(func_lines)
        
        # Añadir tests específicos de esta función
        if func['tests']:
            cell_code += '\n\n# Tests\n'
            for test in func['tests']:
                cell_code += test + '\n'
        
        # Crear celda con metadata nbgrader
        cell = nbformat.v4.new_code_cell(cell_code)
        cell.metadata = {
            "nbgrader": {
                "grade": True,
                "grade_id": f"funcion_{func['name']}",
                "points": 5,
                "locked": False
            }
        }
        
        nb.cells.append(cell)
    
    # Si no se detectaron funciones, crear una celda general
    if not functions:
        cell = nbformat.v4.new_code_cell(code)
        cell.metadata = {
            "nbgrader": {
                "grade": True,
                "grade_id": "codigo_principal",
                "points": 10,
                "locked": False
            }
        }
        nb.cells.append(cell)
    
    with open(ipynb_file, 'w', encoding='utf-8') as f:
        nbformat.write(nb, f, version=4)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Uso: convert_py_to_ipynb.py archivo_entrada.py archivo_salida.ipynb")
        sys.exit(1)
    
    convert_py_to_ipynb(sys.argv[1], sys.argv[2])