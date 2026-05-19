#!/usr/bin/env python3
"""
Pruebas de integración del sistema de autocorrección.
Verifican el flujo completo: .py -> conversión -> evaluación -> resultado.
"""

import os
import sys
import shutil
import tempfile
import unittest
import nbformat

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MOODLE_PLUGIN_DIR = os.path.dirname(SCRIPT_DIR)
sys.path.append(MOODLE_PLUGIN_DIR)

from evaluate_nbgrader import evaluar_notebook, convertir_asserts_a_captura
from convert_py_to_ipynb import convert_py_to_ipynb


class TestFlujoCompletoConversion(unittest.TestCase):
    """
    Pruebas de integración: flujo completo Python -> IPYNB -> Evaluación.
    Simulan exactamente lo que hace el sistema cuando un estudiante sube un archivo.
    """

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _crear_py(self, nombre, contenido):
        path = os.path.join(self.temp_dir, nombre)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(contenido)
        return path

    def test_flujo_completo_codigo_correcto(self):
        """
        Flujo completo con código correcto
        """
        codigo = (
            'def potencia(base, exponente):\n'
            '    return base ** exponente\n\n'
            'assert potencia(2, 3) == 8\n'
            'assert potencia(5, 0) == 1\n'
            'assert potencia(3, 2) == 9\n'
        )
        py = self._crear_py('potencia.py', codigo)
        ipynb = os.path.join(self.temp_dir, 'potencia.ipynb')

        # Paso 1: conversión
        convert_py_to_ipynb(py, ipynb)
        self.assertTrue(os.path.exists(ipynb), "El .ipynb debe generarse")

        # Paso 2: evaluación
        resultado = evaluar_notebook(ipynb)
        self.assertEqual(resultado['estado'], 'ok')
        self.assertEqual(resultado['nota'], 10.0,
                         "Código correcto debe obtener nota 10")

    def test_flujo_completo_codigo_incorrecto(self):
        """
        Flujo completo con código incorrecto
        """
        codigo = (
            'def potencia(base, exponente):\n'
            '    return base + exponente  # bug\n\n'
            'assert potencia(2, 3) == 8\n'
            'assert potencia(5, 0) == 1\n'
            'assert potencia(3, 2) == 9\n'
        )
        py = self._crear_py('potencia_mal.py', codigo)
        ipynb = os.path.join(self.temp_dir, 'potencia_mal.ipynb')

        convert_py_to_ipynb(py, ipynb)
        resultado = evaluar_notebook(ipynb)

        self.assertEqual(resultado['estado'], 'ok')
        self.assertLess(resultado['nota'], 10.0,
                        "Código con bug debe obtener nota menor que 10")

    def test_flujo_completo_multiples_funciones(self):
        """
        Flujo completo con múltiples funciones y asserts:
        verifica que todas las funciones se evalúan independientemente
        """
        codigo = (
            'def suma(a, b):\n    return a + b\n\n'
            'def resta(a, b):\n    return a - b\n\n'
            'assert suma(2, 3) == 5\n'
            'assert suma(0, 0) == 0\n'
            'assert resta(5, 3) == 2\n'
            'assert resta(0, 0) == 0\n'
        )
        py = self._crear_py('operaciones.py', codigo)
        ipynb = os.path.join(self.temp_dir, 'operaciones.ipynb')

        convert_py_to_ipynb(py, ipynb)
        resultado = evaluar_notebook(ipynb)

        self.assertEqual(resultado['estado'], 'ok')
        self.assertEqual(resultado['nota'], 10.0)

    def test_flujo_completo_error_sintaxis(self):
        """
        Flujo con archivo que tiene error de sintaxis:
        debe procesarse sin lanzar excepción y devolver feedback al estudiante
        """
        codigo = 'def f(\n    pass\n'  # SyntaxError
        py = self._crear_py('sintaxis.py', codigo)
        ipynb = os.path.join(self.temp_dir, 'sintaxis.ipynb')

        # La conversión no debe lanzar excepción
        convert_py_to_ipynb(py, ipynb)
        self.assertTrue(os.path.exists(ipynb))

        # La evaluación debe completarse (con nota 0 o estado ok/error)
        resultado = evaluar_notebook(ipynb)
        self.assertIn(resultado['estado'], ['ok', 'error'])

    def test_flujo_completo_codigo_parcialmente_correcto(self):
        """
        Flujo con código mitad correcto, mitad incorrecto:
        nota debe estar entre 0 y 10 exclusive
        """
        codigo = (
            'def doble(x):\n    return x * 2\n\n'   # correcto
            'def triple(x):\n    return x\n\n'       # bug
            'assert doble(3) == 6\n'
            'assert triple(3) == 9\n'
        )
        py = self._crear_py('parcial.py', codigo)
        ipynb = os.path.join(self.temp_dir, 'parcial.ipynb')

        convert_py_to_ipynb(py, ipynb)
        resultado = evaluar_notebook(ipynb)

        self.assertEqual(resultado['estado'], 'ok')
        self.assertGreater(resultado['nota'], 0.0)
        self.assertLess(resultado['nota'], 10.0)


class TestCapturaAssertsIntegracion(unittest.TestCase):
    """
    Pruebas de integración para el sistema de captura de asserts:
    verifica que los asserts transformados se ejecutan y acumulan correctamente.
    """

    def test_todos_los_asserts_se_ejecutan_aunque_fallen(self):
        """
        Si hay varios asserts y el primero falla, los siguientes deben
        ejecutarse igualmente (el sistema no debe detenerse en el primer fallo)
        """
        nb = nbformat.v4.new_notebook()
        codigo = (
            'def f(x):\n    return x  # bug: siempre devuelve x\n\n'
            'assert f(2) == 4\n'   # falla
            'assert f(3) == 9\n'   # falla
            'assert f(0) == 0\n'   # pasa 
        )
        nb.cells.append(nbformat.v4.new_code_cell(codigo))

        tmp = tempfile.NamedTemporaryFile(suffix='.ipynb', mode='w',
                                          delete=False, encoding='utf-8')
        nbformat.write(nb, tmp)
        tmp.close()

        try:
            resultado = evaluar_notebook(tmp.name)
            self.assertEqual(resultado['estado'], 'ok')
            # Debe haber evaluado los 3 asserts, no solo el primero
            self.assertIn('RESULTADOS', resultado['retroalimentacion'])
        finally:
            os.unlink(tmp.name)

    def test_retroalimentacion_contiene_info_de_errores(self):
        """El feedback debe incluir información sobre qué falló"""
        nb = nbformat.v4.new_notebook()
        codigo = (
            'def cuadrado(x):\n    return x  # bug\n\n'
            'assert cuadrado(4) == 16\n'
        )
        nb.cells.append(nbformat.v4.new_code_cell(codigo))

        tmp = tempfile.NamedTemporaryFile(suffix='.ipynb', mode='w',
                                          delete=False, encoding='utf-8')
        nbformat.write(nb, tmp)
        tmp.close()

        try:
            resultado = evaluar_notebook(tmp.name)
            self.assertEqual(resultado['estado'], 'ok')
            self.assertIn('Error', resultado['retroalimentacion'])
        finally:
            os.unlink(tmp.name)


if __name__ == '__main__':
    unittest.main(verbosity=2)