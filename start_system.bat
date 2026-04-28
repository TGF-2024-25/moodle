@echo off
chcp 65001 >nul
echo ==========================================
echo    SISTEMA DE AUTO-CORRECCION MOODLE
echo ==========================================
echo.

echo Iniciando maquina virtual...
vagrant up

if %errorlevel% neq 0 (
    echo.
    echo ERROR: No se pudo iniciar la maquina virtual
    echo.
    echo Posibles soluciones:
    echo 1. Verifica que VirtualBox esta instalado
    echo 2. Verifica que Vagrant esta instalado
    echo 3. Ejecuta como Administrador
    echo.
    pause
    exit /b 1
)

echo.
echo ==========================================
echo      SISTEMA INICIADO CORRECTAMENTE
echo ==========================================
echo.
echo Moodle:        http://localhost:8080
echo API NBGrader:  http://localhost:5000
echo.
echo La VM se esta ejecutando en segundo plano
echo Para detener el sistema: vagrant halt
echo Para destruir la VM: vagrant destroy -f
echo.
echo ==========================================
echo.

echo Abriendo Moodle en el navegador...
start http://localhost:8080

echo.
echo Presiona cualquier tecla para cerrar esta ventana
echo (La VM se sigue ejecutando en segundo plano)
pause >nul