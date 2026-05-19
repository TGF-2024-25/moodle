#!/usr/bin/env python3
"""
Pruebas de seguridad del sistema de autocorrección.
Verifican el comportamiento ante entradas maliciosas, código peligroso y casos límite.
"""

import os
import sys
import tempfile
import unittest
import nbformat

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MOODLE_PLUGIN_DIR = os.path.dirname(SCRIPT_DIR)
sys.path.append(MOODLE_PLUGIN_DIR)

from evaluate_nbgrader import evaluar_notebook, convertir_asserts_a_captura
from convert_py_to_ipynb import convert_py_to_ipynb


class TestCodigoPotencialmentePeligroso(unittest.TestCase):
    """
    Verifica que el sistema no se rompe ante código que intenta
    acceder al sistema de archivos, ejecutar subprocesos, o hacer
    operaciones no relacionadas con la tarea.
    """

    def _evaluar_codigo(self, codigo):
        nb = nbformat.v4.new_notebook()
        nb.cells.append(nbformat.v4.new_code_cell(codigo))
        tmp = tempfile.NamedTemporaryFile(suffix='.ipynb', mode='w', delete=False, encoding='utf-8')
        nbformat.write(nb, tmp)
        tmp.close()
        try:
            return evaluar_notebook(tmp.name)
        finally:
            os.unlink(tmp.name)

    def test_codigo_con_import_os(self):
        """Código que importa os y lista directorios debe manejarse sin excepción"""
        codigo = (
            'import os\n'
            'files = os.listdir("/")\n'
            'print("Archivos encontrados:", len(files))\n'
        )
        resultado = self._evaluar_codigo(codigo)
        self.assertIn(resultado['estado'], ['ok', 'error'], "El sistema no debe lanzar excepción no controlada")

    def test_codigo_con_subprocess(self):
        """Código que usa subprocess debe manejarse sin romper el evaluador"""
        codigo = (
            'import subprocess\n'
            'r = subprocess.run(["echo", "test"], capture_output=True, text=True)\n'
            'print("Salida:", r.stdout)\n'
        )
        resultado = self._evaluar_codigo(codigo)
        self.assertIn(resultado['estado'], ['ok', 'error'])

    def test_codigo_con_bucle_largo_controlado(self):
        """Operación costosa dentro del timeout debe completarse correctamente"""
        codigo = (
            'resultado = 0\n'
            'for i in range(100000):\n'
            '    resultado += i\n'
            'assert resultado == 4999950000\n'
        )
        resultado = self._evaluar_codigo(codigo)
        self.assertEqual(resultado['estado'], 'ok')
        self.assertEqual(resultado['nota'], 10.0)

    def test_notebook_con_celdas_multiples_peligrosas(self):
        """Múltiples celdas con operaciones del sistema no deben romper el evaluador"""
        nb = nbformat.v4.new_notebook()
        nb.cells.append(nbformat.v4.new_code_cell('import os\nprint(os.getcwd())'))
        nb.cells.append(nbformat.v4.new_code_cell('import sys\nprint(sys.version)'))
        nb.cells.append(nbformat.v4.new_code_cell(
            'def suma(a, b):\n    return a + b\nassert suma(1, 1) == 2\n'
        ))

        tmp = tempfile.NamedTemporaryFile(suffix='.ipynb', mode='w',
                                          delete=False, encoding='utf-8')
        nbformat.write(nb, tmp)
        tmp.close()
        try:
            resultado = evaluar_notebook(tmp.name)
            self.assertIn(resultado['estado'], ['ok', 'error'])
        finally:
            os.unlink(tmp.name)


class TestCasosLimiteEntrada(unittest.TestCase):
    """
    Pruebas de robustez ante entradas límite o inesperadas.
    """

    def test_archivo_no_existente(self):
        """Ruta a archivo inexistente debe devolver estado error, no excepción"""
        resultado = evaluar_notebook('/ruta/que/no/existe/notebook.ipynb')
        self.assertEqual(resultado['estado'], 'error')
        self.assertIn('error', resultado)
        self.assertIsInstance(resultado['error'], str)

    def test_notebook_json_invalido(self):
        """Archivo con JSON malformado debe devolver estado error"""
        tmp = tempfile.NamedTemporaryFile(suffix='.ipynb', mode='w', delete=False, encoding='utf-8')
        tmp.write('{ esto no es json valido }{{}')
        tmp.close()
        try:
            resultado = evaluar_notebook(tmp.name)
            self.assertEqual(resultado['estado'], 'error')
        finally:
            os.unlink(tmp.name)

    def test_notebook_sin_celdas(self):
        """Notebook válido pero sin celdas debe devolver nota 0 sin error"""
        nb = nbformat.v4.new_notebook()
        tmp = tempfile.NamedTemporaryFile(suffix='.ipynb', mode='w', delete=False, encoding='utf-8')
        nbformat.write(nb, tmp)
        tmp.close()
        try:
            resultado = evaluar_notebook(tmp.name)
            self.assertEqual(resultado['estado'], 'ok')
            self.assertEqual(resultado['nota'], 0.0)
        finally:
            os.unlink(tmp.name)

    def test_assert_con_string_que_contiene_operador(self):
        """assert con == dentro de un string no debe romper el parser AST"""
        codigo = 'assert "a == b" == "a == b"'
        try:
            resultado = convertir_asserts_a_captura(codigo)
            self.assertIn('capturar_assert', resultado)
        except Exception as e:
            self.fail(f"convertir_asserts_a_captura lanzó excepción inesperada: {e}")

    def test_codigo_vacio_no_rompe_conversor(self):
        """Cadena vacía no debe lanzar excepción en convertir_asserts_a_captura"""
        try:
            resultado = convertir_asserts_a_captura('')
            self.assertEqual(resultado, '')
        except Exception as e:
            self.fail(f"Excepción inesperada con código vacío: {e}")

    def test_conversion_py_archivo_solo_comentarios(self):
        """Archivo .py con solo comentarios debe convertirse sin error"""
        tmp_py = tempfile.NamedTemporaryFile(suffix='.py', mode='w', delete=False, encoding='utf-8')
        tmp_py.write('# Solo un comentario\n# Otra línea de comentario\n')
        tmp_py.close()
        tmp_ipynb = tmp_py.name.replace('.py', '.ipynb')
        try:
            convert_py_to_ipynb(tmp_py.name, tmp_ipynb)
            self.assertTrue(os.path.exists(tmp_ipynb))
        finally:
            os.unlink(tmp_py.name)
            if os.path.exists(tmp_ipynb):
                os.unlink(tmp_ipynb)


if __name__ == '__main__':
    unittest.main(verbosity=2)