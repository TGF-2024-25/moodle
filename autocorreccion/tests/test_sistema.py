#!/usr/bin/env python3
"""
Pruebas unitarias del sistema de autocorrección.
"""

import os
import sys
import json
import tempfile
import unittest
import nbformat

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MOODLE_PLUGIN_DIR = os.path.dirname(SCRIPT_DIR)
sys.path.append(MOODLE_PLUGIN_DIR)

from evaluate_nbgrader import evaluar_notebook, convertir_asserts_a_captura
from convert_py_to_ipynb import convert_py_to_ipynb


class TestConversionPyAIpynb(unittest.TestCase):
    """Pruebas unitarias para convert_py_to_ipynb.py"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _crear_py(self, nombre, contenido):
        path = os.path.join(self.temp_dir, nombre)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(contenido)
        return path

    def test_conversion_archivo_valido(self):
        """Archivo .py correcto se convierte a .ipynb"""
        py = self._crear_py('valido.py', 'def suma(a, b):\n    return a + b\n')
        ipynb = os.path.join(self.temp_dir, 'valido.ipynb')
        convert_py_to_ipynb(py, ipynb)
        self.assertTrue(os.path.exists(ipynb), "El archivo .ipynb debe crearse")

    def test_conversion_genera_notebook_valido(self):
        """El notebook generado debe ser parseable por nbformat"""
        py = self._crear_py('nb.py', 'x = 1\nprint(x)\n')
        ipynb = os.path.join(self.temp_dir, 'nb.ipynb')
        convert_py_to_ipynb(py, ipynb)
        with open(ipynb, encoding='utf-8') as f:
            nb = nbformat.read(f, as_version=4)
        self.assertGreater(len(nb.cells), 0, "El notebook debe tener al menos una celda")

    def test_conversion_funciones_en_misma_celda(self):
        """Todo el código debe quedar en una sola celda para preservar el contexto de ejecución"""
        codigo = 'def f1():\n    pass\n\ndef f2():\n    pass\n'
        py = self._crear_py('funciones.py', codigo)
        ipynb = os.path.join(self.temp_dir, 'funciones.ipynb')
        convert_py_to_ipynb(py, ipynb)
        with open(ipynb, encoding='utf-8') as f:
            nb = nbformat.read(f, as_version=4)
        self.assertEqual(len(nb.cells), 1, "Todo el código debe estar en una sola celda")

    def test_conversion_funciones_y_asserts_en_misma_celda(self):
        """Funciones y asserts deben estar en la misma celda para que los asserts puedan llamar a las funciones"""
        codigo = 'def doble(x):\n    return x * 2\n\nassert doble(3) == 6\n'
        py = self._crear_py('doble.py', codigo)
        ipynb = os.path.join(self.temp_dir, 'doble.ipynb')
        convert_py_to_ipynb(py, ipynb)
        with open(ipynb, encoding='utf-8') as f:
            nb = nbformat.read(f, as_version=4)
        self.assertEqual(len(nb.cells), 1, "Funciones y asserts deben estar juntos en una celda")

    def test_conversion_archivo_con_error_sintaxis(self):
        """Archivo con error de sintaxis debe convertirse en una celda con el código original"""
        py = self._crear_py('sintaxis_error.py', 'def f(\n    pass\n')
        ipynb = os.path.join(self.temp_dir, 'sintaxis_error.ipynb')
        convert_py_to_ipynb(py, ipynb)
        self.assertTrue(os.path.exists(ipynb), "Debe crearse el notebook aunque haya error de sintaxis")

    def test_conversion_archivo_vacio(self):
        """Archivo Python vacío debe generar un notebook válido"""
        py = self._crear_py('vacio.py', '')
        ipynb = os.path.join(self.temp_dir, 'vacio.ipynb')
        convert_py_to_ipynb(py, ipynb)
        self.assertTrue(os.path.exists(ipynb))


class TestConvertirAsserts(unittest.TestCase):
    """Pruebas unitarias para convertir_asserts_a_captura() en evaluate_nbgrader.py"""

    def test_assert_igualdad_simple(self):
        """assert x == y debe convertirse en capturar_assert(x, y, ...)"""
        resultado = convertir_asserts_a_captura('assert suma(2, 3) == 5')
        self.assertIn('capturar_assert', resultado)

    def test_assert_booleano(self):
        """assert condicion (sin ==) debe convertirse correctamente"""
        resultado = convertir_asserts_a_captura('assert es_par(4)')
        self.assertIn('capturar_assert', resultado)

    def test_assert_con_string_igual(self):
        """assert con == dentro de un string no debe confundirse con el operador"""
        codigo = 'assert "==" in texto'
        resultado = convertir_asserts_a_captura(codigo)
        self.assertIn('capturar_assert', resultado)

    def test_assert_dentro_de_funcion_no_se_toca(self):
        """Los asserts dentro de definiciones de función no son top-level: no deben transformarse aquí"""
        codigo = 'assert resultado == 42'
        resultado = convertir_asserts_a_captura(codigo)
        self.assertIn('capturar_assert', resultado)

    def test_codigo_sin_asserts_no_cambia(self):
        """Código sin asserts debe devolverse sin modificaciones relevantes"""
        codigo = 'x = 1\nprint(x)\n'
        resultado = convertir_asserts_a_captura(codigo)
        self.assertNotIn('capturar_assert', resultado)

    def test_codigo_con_error_sintaxis_se_devuelve_intacto(self):
        """Código con error de sintaxis debe devolverse sin modificar"""
        codigo = 'def f(\n    pass'
        resultado = convertir_asserts_a_captura(codigo)
        self.assertEqual(resultado, codigo)

    def test_multiples_asserts(self):
        """Múltiples asserts deben transformarse todos"""
        codigo = 'assert f(1) == 1\nassert f(2) == 4\nassert f(3) == 9\n'
        resultado = convertir_asserts_a_captura(codigo)
        self.assertEqual(resultado.count('capturar_assert'), 3)


class TestEvaluarNotebook(unittest.TestCase):
    """Pruebas unitarias para evaluar_notebook() en evaluate_nbgrader.py"""

    def _notebook_con_codigo(self, codigo):
        nb = nbformat.v4.new_notebook()
        nb.cells.append(nbformat.v4.new_code_cell(codigo))
        tmp = tempfile.NamedTemporaryFile(suffix='.ipynb', mode='w',
                                          delete=False, encoding='utf-8')
        nbformat.write(nb, tmp)
        tmp.close()
        return tmp.name

    def tearDown(self):
        pass  # Los archivos temporales se limpian en cada test individualmente

    def test_evaluacion_notebook_correcto(self):
        """Notebook con todos los asserts correctos debe obtener nota 10"""
        codigo = (
            'def doble(x):\n    return x * 2\n\n'
            'assert doble(3) == 6\n'
            'assert doble(0) == 0\n'
        )
        path = self._notebook_con_codigo(codigo)
        try:
            resultado = evaluar_notebook(path)
            self.assertEqual(resultado['estado'], 'ok')
            self.assertEqual(resultado['nota'], 10.0)
        finally:
            os.unlink(path)

    def test_evaluacion_notebook_con_fallos(self):
        """Notebook con asserts fallidos debe obtener nota menor que 10"""
        codigo = (
            'def doble(x):\n    return x  # bug: no multiplica\n\n'
            'assert doble(3) == 6\n'
            'assert doble(0) == 0\n'
        )
        path = self._notebook_con_codigo(codigo)
        try:
            resultado = evaluar_notebook(path)
            self.assertEqual(resultado['estado'], 'ok')
            self.assertLess(resultado['nota'], 10.0)
        finally:
            os.unlink(path)

    def test_evaluacion_notebook_sin_asserts(self):
        """Notebook sin asserts debe devolver estado ok y nota 0"""
        path = self._notebook_con_codigo('print("Hola mundo")\n')
        try:
            resultado = evaluar_notebook(path)
            self.assertEqual(resultado['estado'], 'ok')
            self.assertEqual(resultado['nota'], 0.0)
        finally:
            os.unlink(path)

    def test_evaluacion_notebook_error_sintaxis(self):
        """Notebook con error de sintaxis debe devolver estado ok (allow_errors=True)"""
        path = self._notebook_con_codigo('def f(\n    pass\n')
        try:
            resultado = evaluar_notebook(path)
            self.assertIn(resultado['estado'], ['ok', 'error'])
        finally:
            os.unlink(path)

    def test_evaluacion_archivo_inexistente(self):
        """Ruta inexistente debe devolver estado error"""
        resultado = evaluar_notebook('/tmp/archivo_que_no_existe_abc123.ipynb')
        self.assertEqual(resultado['estado'], 'error')
        self.assertIn('error', resultado)

    def test_evaluacion_notebook_vacio(self):
        """Notebook sin celdas debe devolver estado ok y nota 0"""
        nb = nbformat.v4.new_notebook()
        tmp = tempfile.NamedTemporaryFile(suffix='.ipynb', mode='w',
                                          delete=False, encoding='utf-8')
        nbformat.write(nb, tmp)
        tmp.close()
        try:
            resultado = evaluar_notebook(tmp.name)
            self.assertEqual(resultado['estado'], 'ok')
            self.assertEqual(resultado['nota'], 0.0)
        finally:
            os.unlink(tmp.name)

    def test_evaluacion_parcialmente_correcta(self):
        """Notebook con la mitad de asserts correctos debe dar nota 5"""
        codigo = (
            'def triple(x):\n    return x  # bug\n\n'
            'def identidad(x):\n    return x\n\n'
            'assert triple(3) == 9\n'       # falla
            'assert identidad(5) == 5\n'    # pasa
        )
        path = self._notebook_con_codigo(codigo)
        try:
            resultado = evaluar_notebook(path)
            self.assertEqual(resultado['estado'], 'ok')
            self.assertAlmostEqual(resultado['nota'], 5.0, places=1)
        finally:
            os.unlink(path)


if __name__ == '__main__':
    unittest.main(verbosity=2)