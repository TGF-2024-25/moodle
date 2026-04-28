#!/bin/bash
echo "=========================================="
echo "   SISTEMA DE AUTO-CORRECCION MOODLE"
echo "=========================================="
echo ""

echo "Iniciando maquina virtual..."
vagrant up

if [ $? -ne 0 ]; then
    echo ""
    echo "ERROR: No se pudo iniciar la maquina virtual"
    echo ""
    echo "Posibles soluciones:"
    echo "1. Verifica que VirtualBox esta instalado"
    echo "2. Verifica que Vagrant esta instalado"
    echo ""
    exit 1
fi

echo ""
echo "=========================================="
echo "     SISTEMA INICIADO CORRECTAMENTE"
echo "=========================================="
echo ""
echo "Moodle:        http://localhost:8080"
echo "API NBGrader:  http://localhost:5000"
echo ""
echo "La VM se sigue ejecutando en segundo plano"
echo "Para detener el sistema: vagrant halt"
echo "Para destruir la VM: vagrant destroy -f"
echo ""
echo "=========================================="
echo ""

# Abrir navegador
if command -v xdg-open &>/dev/null; then
    xdg-open http://localhost:8080
elif command -v open &>/dev/null; then
    open http://localhost:8080
fi