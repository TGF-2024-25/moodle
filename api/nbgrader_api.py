#!/usr/bin/env python3
"""
API para Auto-Corrección - Integración real con evaluate_nbgrader.py
"""
import os
import sys
import json
import tempfile
import subprocess
from flask import Flask, request, jsonify

# Añadir ruta al plugin Moodle para importar evaluate_nbgrader
current_dir = os.path.dirname(os.path.abspath(__file__))
autocorreccion_path = os.path.join(current_dir, '../autocorreccion')
sys.path.append(autocorreccion_path)

try:
    from evaluate_nbgrader import evaluar_notebook
    EVALUATION_ENGINE_AVAILABLE = True
except ImportError as e:
    print(f"No se pudo importar evaluate_nbgrader: {e}")
    EVALUATION_ENGINE_AVAILABLE = False

app = Flask(__name__)

def evaluar_con_nbgrader_real(notebook_path, student_id, assignment_name):
    """Usa el evaluate_nbgrader.py real para evaluación"""
    try:
        if not EVALUATION_ENGINE_AVAILABLE:
            return {
                'estado': 'error',
                'error': 'Motor de evaluación no disponible',
                'nota': 0,
                'retroalimentacion': 'Error: Sistema de evaluación no configurado correctamente'
            }
        
        # Evaluar usando el motor real
        resultado = evaluar_notebook(notebook_path)
        
        # Asegurar que el resultado tiene el formato esperado
        if isinstance(resultado, dict):
            return resultado
        else:
            return {
                'estado': 'error',
                'error': 'Formato de respuesta inválido del motor de evaluación',
                'nota': 0,
                'retroalimentacion': 'Error interno del sistema de evaluación'
            }
            
    except Exception as e:
        return {
            'estado': 'error',
            'error': f"Error en evaluación NBGrader: {str(e)}",
            'nota': 0,
            'retroalimentacion': f"Error durante la evaluación: {str(e)}"
        }

def evaluar_con_script_externo(notebook_path, student_id, assignment_name):
    """Método alternativo: ejecutar evaluate_nbgrader.py como subprocess"""
    try:
        # Ruta al script evaluate_nbgrader.py
        evaluate_script = os.path.join(autocorreccion_path, 'evaluate_nbgrader.py')
        
        if not os.path.exists(evaluate_script):
            return {
                'estado': 'error',
                'error': f"Script de evaluación no encontrado: {evaluate_script}",
                'nota': 0,
                'retroalimentacion': 'Sistema de evaluación no configurado'
            }
        
        # Ejecutar como subprocess
        command = [
            sys.executable,  # Usar el mismo Python
            evaluate_script,
            notebook_path,
            student_id
        ]
        
        result = subprocess.run(
            command, 
            capture_output=True, 
            text=True, 
            timeout=120,  # 2 minutos timeout
            cwd=autocorreccion_path  # Ejecutar desde el directorio del plugin
        )
        
        if result.returncode == 0:
            # Parsear resultado JSON
            try:
                return json.loads(result.stdout)
            except json.JSONDecodeError:
                return {
                    'estado': 'error',
                    'error': 'Respuesta JSON inválida del motor de evaluación',
                    'nota': 0,
                    'retroalimentacion': f"Salida cruda: {result.stdout[:200]}..."
                }
        else:
            return {
                'estado': 'error',
                'error': f"Error en ejecución (código {result.returncode})",
                'nota': 0,
                'retroalimentacion': f"Error: {result.stderr}"
            }
            
    except subprocess.TimeoutExpired:
        return {
            'estado': 'error',
            'error': 'Timeout en evaluación (más de 2 minutos)',
            'nota': 0,
            'retroalimentacion': 'La evaluación tardó demasiado tiempo'
        }
    except Exception as e:
        return {
            'estado': 'error',
            'error': f"Error en evaluación externa: {str(e)}",
            'nota': 0,
            'retroalimentacion': f"Error del sistema: {str(e)}"
        }

@app.route('/grade', methods=['POST'])
def grade_notebook():
    """Endpoint para evaluar notebooks usando el motor real"""
    try:
        if 'notebook' not in request.files:
            return jsonify({'estado': 'error', 'error': 'No se proporcionó notebook'}), 400
        
        notebook_file = request.files['notebook']
        student_id = request.form.get('usuario', 'anonymous')
        assignment_name = request.form.get('assignment', 'ps1')
        
        if notebook_file.filename == '':
            return jsonify({'estado': 'error', 'error': 'Nombre de archivo vacío'}), 400
        
        # Validar tipo de archivo
        if not (notebook_file.filename.endswith('.ipynb') or notebook_file.filename.endswith('.py')):
            return jsonify({
                'estado': 'error', 
                'error': 'Tipo de archivo no soportado. Use .ipynb o .py'
            }), 400
        
        # Guardar archivo temporal
        with tempfile.NamedTemporaryFile(
            suffix='.ipynb' if notebook_file.filename.endswith('.ipynb') else '.py', 
            delete=False
        ) as f:
            notebook_file.save(f.name)
            temp_path = f.name
        
        try:
            # Intentar evaluación con método directo primero
            if EVALUATION_ENGINE_AVAILABLE:
                result = evaluar_con_nbgrader_real(temp_path, student_id, assignment_name)
            else:
                # Fallback a método externo
                result = evaluar_con_script_externo(temp_path, student_id, assignment_name)
            
            # Añadir metadatos al resultado
            result['metadata'] = {
                'estudiante': student_id,
                'assignment': assignment_name,
                'archivo': notebook_file.filename
            }
            
            return jsonify(result)
            
        finally:
            # Limpiar archivo temporal
            if os.path.exists(temp_path):
                os.unlink(temp_path)
        
    except Exception as e:
        return jsonify({
            'estado': 'error',
            'error': f'Error interno del servidor: {str(e)}'
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Endpoint de salud del sistema"""
    status = {
        'estado': 'ok',
        'mensaje': 'API funcionando',
        'motor_evaluacion': 'disponible' if EVALUATION_ENGINE_AVAILABLE else 'no disponible',
        'version': '1.0'
    }
    return jsonify(status)

@app.route('/test', methods=['GET'])
def test_evaluation():
    """Endpoint de prueba con ejemplo integrado"""
    try:
        # Crear un notebook de prueba simple
        test_notebook = {
            "cells": [
                {
                    "cell_type": "code",
                    "execution_count": None,
                    "metadata": {},
                    "outputs": [],
                    "source": [
                        "def suma(a, b):\n",
                        "    return a + b\n",
                        "\n",
                        "# Test\n",
                        "assert suma(2, 3) == 5\n",
                        "assert suma(0, 0) == 0\n",
                        "print('Tests pasados correctamente')"
                    ]
                }
            ],
            "metadata": {
                "kernelspec": {
                    "display_name": "Python 3",
                    "language": "python",
                    "name": "python3"
                }
            },
            "nbformat": 4,
            "nbformat_minor": 4
        }
        
        # Guardar notebook temporal
        with tempfile.NamedTemporaryFile(suffix='.ipynb', delete=False, mode='w') as f:
            json.dump(test_notebook, f)
            temp_path = f.name
        
        # Evaluar
        result = evaluar_con_nbgrader_real(temp_path, 'test_user', 'test_assignment')
        
        # Limpiar
        os.unlink(temp_path)
        
        return jsonify({
            'test_result': result,
            'message': 'Prueba de evaluación completada'
        })
        
    except Exception as e:
        return jsonify({
            'error': f'Error en prueba: {str(e)}'
        }), 500

if __name__ == '__main__':
    print("API de Auto-Corrección - Integración NBGrader Real")
    print("URL: http://localhost:5000")
    print("Endpoints disponibles:")
    print("   POST /grade     - Evaluar notebook")
    print("   GET  /health    - Estado del sistema") 
    print("   GET  /test      - Prueba de evaluación")
    print("")
    print(f"Motor de evaluación: {'DISPONIBLE' if EVALUATION_ENGINE_AVAILABLE else 'NO DISPONIBLE'}")
    print("=" * 50)
    
    app.run(host='0.0.0.0', port=5000, debug=False)