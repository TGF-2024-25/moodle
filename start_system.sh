#!/bin/bash
echo "=========================================="
echo "   SISTEMA DE AUTO-CORRECCION MOODLE"
echo "=========================================="

echo "Iniciando sistema..."

echo "Iniciando maquina virtual..."
vagrant up

if [ $? -ne 0 ]; then
    echo "ERROR: No se pudo iniciar la maquina virtual"
    exit 1
fi

echo ""
echo "Configurando NBGrader en HOST..."

# Detectar SO
if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
    PYTHON_CMD="python"
    VENV_ACTIVATE="nbgrader_venv/Scripts/activate"
else
    PYTHON_CMD="python3"
    VENV_ACTIVATE="nbgrader_venv/bin/activate"
fi

# Crear entorno virtual
if [ ! -d "nbgrader_venv" ]; then
    echo "Creando entorno virtual..."
    $PYTHON_CMD -m venv nbgrader_venv
    if [ $? -ne 0 ]; then
        echo "ERROR: No se pudo crear el entorno virtual"
        exit 1
    fi
fi

# Activar y instalar dependencias
source $VENV_ACTIVATE

echo "Instalando/verificando dependencias..."
pip install nbgrader jupyter flask --disable-pip-version-check

echo "Instalando kernel de Python para Jupyter..."
python -m ipykernel install --user --name python3 --display-name "Python 3" 2>/dev/null || echo "¡Kernel ya existe o no es necesario!"

echo ""
echo "=========================================="
echo "     SISTEMA INICIADO CORRECTAMENTE"
echo "=========================================="
echo "Moodle:  http://localhost:8080"
echo "API:     http://localhost:5000"
echo ""
echo "Iniciando API NBGrader..."
echo "Para detener: Ctrl+C"
echo "=========================================="
echo ""

python api/nbgrader_api.py