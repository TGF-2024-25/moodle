@echo off
chcp 65001 >nul
echo ==========================================
echo    SISTEMA DE AUTO-CORRECCION MOODLE
echo ==========================================

echo Iniciando sistema...

echo Iniciando maquina virtual...
vagrant up

if %errorlevel% neq 0 (
    echo ERROR: No se pudo iniciar la maquina virtual
    pause
    exit /b 1
)

echo.
echo Configurando NBGrader...
if not exist "nbgrader_venv" (
    python -m venv nbgrader_venv
    if %errorlevel% neq 0 (
        echo ERROR: No se pudo crear el entorno virtual
        pause
        exit /b 1
    )
)

call nbgrader_venv\Scripts\activate.bat

if not exist "nbgrader_venv\Lib\site-packages\nbgrader" (
    echo Instalando nbgrader...
    pip install nbgrader jupyter
    if %errorlevel% neq 0 (
        echo ERROR: No se pudieron instalar las dependencias
        pause
        exit /b 1
    )
)

echo.
echo ==========================================
echo    ✅ SISTEMA INICIADO CORRECTAMENTE
echo ==========================================
echo Moodle:  http://localhost:8080
echo API:     http://localhost:5000
echo.
echo La API se esta iniciando...
echo Para detener: Ctrl+C
echo ==========================================
echo.

python ..\api\nbgrader_api.py

pause