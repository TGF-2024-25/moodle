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
    - Moodle (red interna): http://192.168.56.10p

## Instalación Manual
  ### Prerrequisitos
    - Sistema Operativo: Windows 10/11, macOS 10.14+, Ubuntu 18.04+
    - RAM: 8GB mínimo recomendado
    - Espacio en disco: 20GB mínimo
    - Vagrant: 2.3.7+
    - VirtualBox: 7.0.12+
    - Python: 3.8+

  ### Pasos de Instalación
    1. Clonar el repositorio: 
      `git clone https://github.com/TGF-2024-25/moodle.git`
      `cd moodle`
    2. Iniciar la máquina virtual:
      `vagrant up`
    3. Configurar NBGrader en el host:
      - Se ejecuta automáticamente en los scripts de inicio
      - Creación del entorno virtual e instalación de dependencias
    4. Acceder a Moodle:
      - Abrir http://localhost:8080
      - Completar la instalación web de Moodle

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
