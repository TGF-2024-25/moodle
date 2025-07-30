import sys
import subprocess
import os

# Script que recibe el archivo a corregir y lo ejecuta, devolviendo sallida o errores.

def evaluar_codigo(filepath):
    try:
        # Verifica si el archivo existe antes de intentar ejecutarlo
        if not os.path.exists(filepath):
            return f"El archivo no existe: {filepath}"
        
        # Ejecutar el archivo Python
        resultado = subprocess.run(["python3", filepath], capture_output=True, text=True, timeout=10)
        if resultado.returncode == 0:
            return f"Correcto: {resultado.stdout}"
        else:
            return f"Error en el código:\n{resultado.stderr}"
    except Exception as e:
        return f"Error al ejecutar: {str(e)}"

if __name__ == "__main__":
    archivo = sys.argv[1]
    resultado = evaluar_codigo(archivo)
    print(resultado)
