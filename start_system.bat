@echo off
chcp 65001 >nul
echo ==========================================
echo    SISTEMA DE AUTO-CORRECCION MOODLE
echo ==========================================

echo Iniciando maquina virtual...
vagrant up
if %errorlevel% neq 0 (
    echo ERROR: No se pudo iniciar la maquina virtual
    pause
    exit /b 1
)

echo Configurando entorno Python...
if not exist "nbgrader_venv" (
    python -m venv nbgrader_venv
    if %errorlevel% neq 0 exit /b 1
)

call nbgrader_venv\Scripts\activate.bat

echo Instalando Flask primero...
pip install flask --disable-pip-version-check
if %errorlevel% neq 0 (
    echo ERROR: No se pudo instalar Flask
    pause
    exit /b 1
)

echo Instalando dependencias basicas...
pip install requests nbformat nbconvert --disable-pip-version-check

echo Instalando NBGrader...
pip install nbgrader --disable-pip-version-check

echo Instalando kernel de Python para Jupyter...
python -m ipykernel install --user --name python3 --display-name "Python 3" 2>nul || echo ¡Kernel ya existe o no es necesario!

echo Verificando instalacion...
python -c "import flask; print('¡Sistema listo!')"

echo.
echo ==========================================
echo      SISTEMA INICIADO CORRECTAMENTE
echo ==========================================
echo Moodle:  http://localhost:8080
echo API:     http://localhost:5000
echo.
echo NOTA: Algunas advertencias son normales en Windows
echo La API se esta iniciando...
echo Para detener: Ctrl+C
echo ==========================================

python api\nbgrader_api.py
pause