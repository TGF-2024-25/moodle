# Sistema de Auto-Corrección Moodle con NBGrader
Implementación de un plugin para Moodle que permite la autocorrección automática de tareas de programación en Python mediante integración con NBGrader

## Descripción
Este proyecto implementa un plugin para Moodle que evalúa automáticamente notebooks Jupyter (.ipynb) y scripts Python (.py), proporcionando feedback inmediato a los estudiantes. Desarrollado como Trabajo de Fin de Grado en Ingeniería de Software.

## Características Principales
  - Evaluación Automática: Corrección automática de código Python y Jupyter Notebooks
  - Conversión Inteligente: Conversión automática de scripts .py a notebooks .ipynb
  - Sistema de Rúbricas Configurable:
    - Rúbrica numérica con escalas personalizables
    - Rúbrica apto/no apto con umbrales configurables
  - Feedback Detallado: Resultados de tests con formato visual mejorado
  - Gestión Completa de Entregas: Historial completo con estadísticas por estudiante
  - Integración Total: Sincronización automática con el libro de calificaciones de Moodle
  - API REST: Servicio externo para evaluación de notebooks

## Arquitectura del Sistema
  ### Sistema Auto-Corrección Moodle
    - Moodle (Ubuntu 22.04 VM)
      - Plugin Autocorrección
      - Apache + PHP 8.1
      - MySQL
    - NBGrader API (Host)
      - Entorno Virtual Python
      - Servicio Flask REST
      - Motor de Evaluación
    - Sistema de Archivos Compartido

## Inicio Rápido
  ### Para Windows
    1. Doble clic en `start_system.bat` o  ejecutar `.\start_system.bat`
    2. Esperar a que se inicien todos los servicios
    3. Acceder a http://localhost:8080

  ### Para Linux/Mac
    1. `chmod +x start_system.sh`
    2. `./start_system.sh`

  ### URLs del Sistema
    - Moodle: http://localhost:8080
    - API NBGrader: http://localhost:5000
    - Moodle (red interna): http://192.168.56.10

## Instalación Manual
  ### Prerrequisitos
    - Sistema Operativo: Windows 10/11, macOS 10.14+, Ubuntu 18.04+
    - RAM: 8GB mínimo recomendado
    - Espacio en disco: 20GB mínimo
    - Vagrant: 2.3.7+
    - VirtualBox: 7.0.12+
    - Python: 3.8+
    - Git: última versión

  ### Enlaces de Descarga
    - VirtualBox: https://www.virtualbox.org/wiki/Downloads
    - Vagrant: https://developer.hashicorp.com/vagrant/downloads
    - Git: https://git-scm.com/downloads

  ### Pasos de Instalación y Configuración del Entorno
    1. Instalación de Dependencias:
      - Instalación de VirtualBox: Descargar y ejecutar el instalador correspondiente a su sistema operativo (Windows .exe, macOS .dmg)
      - Instalación de Vagrant: Descargar y ejecutar el instalador (.msi para Windows, .dmg para macOS)
      - Instalación de Git: Descargar el cliente más reciente o usar el gestor de paquetes (sudo apt install en Debian/Ubuntu)
      - Para instalar VirtualBox y Vagrant en Linux: Seguir instrucciones de instalación por paquetes según la distribución

    2. Configuración del Proyecto y Entornos
      - Clonar el repositorio: 
        - `git clone https://github.com/TGF-2024-25/moodle.git`
        - `cd moodle`
      - Iniciar la máquina virtual: La ejecución de este comando iniciará la descarga de Ubuntu 22.04 y ejecutará provision.sh
        - `vagrant up`
      - Configurar NBGrader en el host: Se ejecuta automáticamente al usar los scripts de inicio (start_system.sh o start_system.bat). Puede hacerlo manualmente (después de vagrant up):
        - Crear el entorno virtual: `python -m venv nbgrader_venv`
        - Activar el entorno: `source nbgrader_venv/bin/activate` (Linux/Mac) o `.\nbgrader_venv\Scripts\activate.bat` (Windows)
        - Instalar dependencias: `pip install nbgrader jupyter flask`
      - Lanzar la API: Iniciar el servicio REST de Flask para la corrección:
        - `python api/nbgrader_api.py`

    3. Finalizar la instalación Web de Moodle
      - Acceder a http://localhost:8080
      - Seguir el Asistente de Instalación de Moodle con los siguientes datos (establecidos en provision.sh)
        - Ruta de datos: /var/www/moodledata
        - Base de datos: MySQL (o MariaDB)
        - Usuario de la Base de Datos: moodleuser
        - Contraseña de la Base de Datos: password123
        - Base de Datos (nombre): moodle
        - Prefijo de tablas: mdl_
      - Completar los pasos restantes (configuración del administrador, configuración del sitio...)

    4. Detención del Sistema
      - Detener la API: Presionar `Ctrl + C` en la terminal donde se está ejecutando start_system o nbgrader_api.py
      - Apagar la VM (Opcional): Para liberar la memoria y recursos del host, usar el comando (desde la carpeta /moodle): 
        - `vagrant halt`

## Configuración
  ### Configuración del Plugin en Moodle
    1. Crear una actividad de Auto-Corrección:
      - Ir a un curso -> Añadir actividad -> Auto-Corrección
      - Subir notebook de referencia
      - Configurar tipo de rúbrica (numérica o apto/ no apto)
      - Establecer umbrales de calificación
    2. Tipos de Rúbrica:
      - Numérica: Escala 0-10 con nota de aprobado configurable
      - Apto/No Apto: Con opción "Necesita mejorar" intermedia

  ### Configuración de la API NBGrader
    La API se inicia automáticamente y proporciona:
      - POST /grade: Evaluar notebooks
      - GET /health: Estado del sistema
      - GET /test: Prueba de evaluación

## Estructura del Proyecto
    moodle/
    ├── api/
    │   └── nbgrader_api.py               # Servicio REST para NBGrader
    ├── autocorreccion/                   # Plugin Moodle
    ├── documentacion/
    │   └── README.md                     # Este archivo
    ├── ejemplos/
    │   ├── notebooks_ejemplo/            # Archivos de ejemplo de subida
    │   └── crear_ejercicios.py           # Script de ejemplo para crear archivos .ipynb
    ├── tests/
    │   ├── test_integracion.py
    │   ├── test_seguridad.py
    │   └── test_sistema.py
    ├── provision.sh                      # Script de aprovisionamiento
    ├── start_system.bat                  # Inicio en Windows
    ├── start_system.sh                   # Inicio en Linux/Mac
    └️ Vagrantfile                         # Configuración de la VM

## Uso del Sistema
  ### Para Estudiantes
    1. Acceder a la actividad de Auto-Corrección
    2. Descargar el notebook de referencia
    3. Subir solución (.ipynb o .py)
    4. Recibir feedback inmediato con nota u comentarios detallados

  ### Para Profesores
    1. Revisar entregas de todos los estudiantes
    2. Añadir feedback adicional manualmente
    3. Ver estadísticas de rendimiento
    4. Gestionar calificaciones en el gradebook

## Solución de Problemas
  ### Problemas Comunes
    1. La VM no inicia:
      - Verificar que VirtualBox esté instalado
      - Comprobar que la virtualización está habilitada en BIOS
    2. Error de premios:
      - Ejecutar `vagrant reload --provision`
      - Verificar permisos en `/var/www/html/moodle`
    3. API no responde:
      - Verifiar que el puerto 5000 esté libre
      - Revisar logs en la terminal de la API
    4. Problemas de conversión .py a .ipynb
      - Verificar que `nbformat` y `nbconvert` estén instalados

  ### Comandos útiles
    - Reiniciar con reprovisionamiento
    `vagrant reload --provision`

    - Acceder a la VM
    `vagrant ssh`

    - Ver logs de Apache
    `sudo tail -f /var/log/apache2/error.log`

    - Reiniciar servicios
    `sudo systemctl restart apache2`
    `sudo systemctl restart mysql`

## Características Técnicas
  ### Tecnologías Utilizadas
    - Backend: PHP 8.1, MySQL, Apache
    - Evaluación: Python 3, NBGrader, Jupyter
    - API: Flask, REST
    - Virtualización: Vagrant, VirtualBox
    - Sistema Operativo: Ubuntu 22.04 LTS

  ### Funcionalidades del Plugin
    - Soporte para múltiples formatos (.ipynb, .py)
    - Sistema de archivos integrado con Moodle
    - Gestión de permisos por roles
    - Actualización en tiempo real del gradebook
    - Interfaz responsive y accesible
    - Feedback formateado con CSS personalizado
    - Historial de versiones de entrega

Desarrollado como parte de un Trabajo de Fin de Grado en Ingeniería del Software.
