# moodle
Implementación de un plugin para Moodle

Descripción:
Plugin para Moodle que permite la autocorrección de tareas de programación en Python mediante integración con NBGrader. Evalúa automáticamente notebooks Jupyter (.ipynb) y scripts Python (.py), proporcionando feedback inmediato a estudiantes.

Características Principales:
  - Evaluación automática de código Python y Jupyter Notebooks
  - Conversión automática de scripts .py a notebooks .ipynb
  - Sistema de rúbricas configurable (numérica o apto/no apto)
  - Feedback detallado con resultados de tests
  - Historial completo de entregas
  - Integración con el libro de calificaciones de Moodle

Instalación:
  - git clone https://github.com/TGF-2024-25/moodle.git
  - cd moodle
  - vagrant up
  
  - Accede a: http://moodle.local

Requisitos:
  - Sistema Operativo: Windows 10/11, macOS 10.14+, Ubuntu 18.04+
  - RAM: 8GB mínimo recomendado
  - Espacio disco: 20GB mínimo
  - Vagrant: 2.3.7+
  - VirtualBox: 7.0.12+

Desarrollado como parte de un Trabajo de Fin de Grado en Ingeniería del Software


---------------------------------------------------
---------------------------------------------------


# Sistema Auto-Corrección Moodle

## 🚀 Uso Rápido

### Windows:
- Doble clic en `start_system.bat`

### Linux/Mac:
- Ejecutar `./start_system.sh` en terminal

## 📍 URLs
- Moodle: http://localhost:8080
- API: http://localhost:5000

## ⏹️ Detener
- Ctrl+C en la terminal
- `vagrant halt` si es necesario