"""
convert_py_to_ipynb.py

Convierte un archivo Python (.py) a un Jupyter Notebook (.ipynb) listo para
ser evaluado por el motor de autocorrección.
"""

import sys
import ast
import nbformat
from pathlib import Path


def convert_py_to_ipynb(py_file, ipynb_file):
    """Convierte archivo Python a Jupyter Notebook para evaluación."""

    source = Path(py_file).read_text(encoding='utf-8')

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

    if not source.strip():
        nb.cells.append(nbformat.v4.new_code_cell(""))
    else:
        nb.cells.append(nbformat.v4.new_code_cell(source))

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
            print(f"Conversion exitosa: {sys.argv[1]} -> {sys.argv[2]}")
        else:
            print("Error en la conversion")
            sys.exit(1)
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)