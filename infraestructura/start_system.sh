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
echo "Configurando NBGrader..."
if [ ! -d "nbgrader_venv" ]; then
    python3 -m venv nbgrader_venv
    if [ $? -ne 0 ]; then
        echo "ERROR: No se pudo crear el entorno virtual"
        exit 1
    fi
fi

source nbgrader_venv/bin/activate

if [ ! -d "nbgrader_venv/lib/python3.*/site-packages/nbgrader" ]; then
    echo "Instalando nbgrader..."
    pip install nbgrader jupyter
    if [ $? -ne 0 ]; then
        echo "ERROR: No se pudieron instalar las dependencias"
        exit 1
    fi
fi

echo ""
echo "=========================================="
echo "     SISTEMA INICIADO CORRECTAMENTE"
echo "=========================================="
echo "Moodle:  http://localhost:8080"
echo "API:     http://localhost:5000"
echo ""
echo "La API se esta iniciando..."
echo "Para detener: Ctrl+C"
echo "=========================================="
echo ""

python ../api/nbgrader_api.py