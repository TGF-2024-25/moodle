#!/bin/bash
set -e

# --- 1. Actualizar sistema y dependencias ---
export DEBIAN_FRONTEND=noninteractive
echo "Actualizando sistema (Ubuntu 22.04)..."
apt-get update
apt-get upgrade -y

# Instalar Apache y MySQL
apt-get install -y apache2 mysql-server git unzip python3-pip python3-venv rsync

# --- 2. Instalar PHP 8.1 y extensiones necesarias (Desde repositorios oficiales) ---
echo "Instalando PHP 8.1 y extensiones (sin PPA)..."
apt-get install -y php8.1 libapache2-mod-php8.1 php8.1-mysql php8.1-curl php8.1-gd php8.1-intl php8.1-mbstring php8.1-soap php8.1-xml php8.1-xmlrpc php8.1-zip

# --- 3. Configurar PHP para Moodle ---
echo "Configurando php.ini para PHP 8.1..."
PHP_INI_PATH="/etc/php/8.1/apache2/php.ini"
sed -i 's/memory_limit = .*/memory_limit = 512M/' $PHP_INI_PATH
sed -i 's/upload_max_filesize = .*/upload_max_filesize = 200M/' $PHP_INI_PATH
sed -i 's/post_max_size = .*/post_max_size = 200M/' $PHP_INI_PATH
sed -i 's/max_execution_time = .*/max_execution_time = 300/' $PHP_INI_PATH
sed -i "s/;*max_input_vars = .*/max_input_vars = 5000/" $PHP_INI_PATH

# --- 4. Configurar MySQL ---
echo "Configurando MySQL..."

# Usamos "IF NOT EXISTS" para evitar errores
mysql -e "CREATE DATABASE IF NOT EXISTS moodle DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# Creamos el usuario (si ya existe, el siguiente comando de GRANT es suficiente)
mysql -e "CREATE USER 'moodleuser'@'localhost' IDENTIFIED BY 'password123';" || true
mysql -e "GRANT ALL PRIVILEGES ON moodle.* TO 'moodleuser'@'localhost';"
mysql -e "FLUSH PRIVILEGES;"
mysql -e "SET GLOBAL sql_mode = 'NO_ENGINE_SUBSTITUTION';"

# Configuración permanente de MySQL
echo "[mysqld]" | tee -a /etc/mysql/mysql.conf.d/mysqld.cnf
echo "sql_mode = NO_ENGINE_SUBSTITUTION" | tee -a /etc/mysql/mysql.conf.d/mysqld.cnf
echo "default_storage_engine = innodb" | tee -a /etc/mysql/mysql.conf.d/mysqld.cnf
echo "innodb_file_per_table = 1" | tee -a /etc/mysql/mysql.conf.d/mysqld.cnf

systemctl restart mysql

# --- 5. Descargar Moodle y configurar directorios ---
echo "Descargando Moodle y configurando directorios..."

mkdir -p /var/www/html/moodle

# Clonar Moodle en una carpeta temporal para no interferir.
rm -rf /tmp/moodle_source

# Descargar Moodle 4.1 en una carpeta llamada "moodle"
git clone -b MOODLE_401_STABLE --depth 1 https://github.com/moodle/moodle.git /tmp/moodle_source

# Usamos rsync para copiar el contenido de Moodle al directorio final.
# rsync no borrará la carpeta "autocorreccion" que ya existe.
rsync -av --remove-source-files /tmp/moodle_source/ /var/www/html/moodle/

# Crear el directorio de datos de Moodle
mkdir -p /var/www/moodledata

# --- 6. Configurar Apache ---
echo "Configurando Apache..."

# Asegurarse de que Apache escuche en el puerto 80 (guest)
cat <<EOF > /etc/apache2/ports.conf
Listen 80

<IfModule ssl_module>
    Listen 443
</IfModule>

<IfModule mod_gnutls.c>
    Listen 443
</IfModule>
EOF

# Crear VirtualHost para Moodle
cat <<EOF > /etc/apache2/sites-available/moodle.conf
<VirtualHost *:80>
    ServerAdmin admin@moodle.local
    DocumentRoot /var/www/html/moodle
    ServerName moodle.local
    ServerAlias 192.168.56.10 localhost

    <Directory /var/www/html/moodle>
        Options FollowSymLinks
        AllowOverride All
        Require all granted
    </Directory>

    ErrorLog \${APACHE_LOG_DIR}/error.log
    CustomLog \${APACHE_LOG_DIR}/access.log combined
</VirtualHost>
EOF

a2dissite -f 000-default.conf
a2ensite moodle.conf
a2enmod rewrite

# Verificar configuración
echo "Verificando configuración de Apache..."
apache2ctl -t
apache2ctl -S

systemctl restart apache2

# --- 7. Configuración de permisos ---
echo "Configurando permisos para Moodle y NBGrader..."

# Permisos para Moodle
chown -R www-data:www-data /var/www
chmod -R 755 /var/www/html/moodle
chmod -R 777 /var/www/moodledata

# --- 8. Instalar NBGrader en un entorno virtual ---
echo "Creando entorno virtual para NBGrader en /opt/nbgrader_env..."

# Crear directorios con permisos necesarios
echo "Creando directorios de NBGrader con permisos necesarios..."
mkdir -p /opt/nbgrader_course/{source,release,submitted}

# Dar permisos completos después de crear
chown -R www-data:www-data /opt/nbgrader_course
chmod -R 777 /opt/nbgrader_course

# Crear el entorno virtual
mkdir -p /opt/nbgrader_env
python3 -m venv /opt/nbgrader_env

# Instalar dependencias
/opt/nbgrader_env/bin/pip install nbgrader jupyter

# Configurar extensiones (con manejo de errores)
echo "Configurando extensiones con NBGrader..."
/opt/nbgrader_env/bin/jupyter nbextension install --sys-prefix --py nbgrader --overwrite 2>/dev/null || echo "Advertencia: jupyter-nbextension install falló"
/opt/nbgrader_env/bin/jupyter nbextension enable --sys-prefix --py nbgrader 2>/dev/null || echo "Advertencia: jupyter-nbextension enable falló"
/opt/nbgrader_env/bin/jupyter serverextension enable --sys-prefix --py nbgrader 2>/dev/null || echo "Advertencia: jupyter-serverextension enable falló"

# Verificar instalación
echo "Verificando instalación de NBGrader..."
/opt/nbgrader_env/bin/jupyter --version

# --- 9. Permisos finales y configuración crítica ---
echo "Aplicando permisos críticos finales..."

# Asegurar permisos del entorno virtual
chown -R www-data:www-data /opt/nbgrader_env
chmod -R 755 /opt/nbgrader_env

# Asegurar que los directorios tienen permisos correctos
echo "Verificación final de permisos..."
ls -la /opt/ | grep nbgrader

# Crear un directorio de prueba para verificar que www-data puede escribir
sudo -u www-data mkdir -p /opt/nbgrader_course/submitted/test_verification
sudo -u www-data touch /opt/nbgrader_course/submitted/test_verification/test.txt

if [ -f "/opt/nbgrader_course/submitted/test_verification/test.txt" ]; then
    echo "Verificación exitosa: www-data puede escribir en NBGrader"
    sudo rm -rf /opt/nbgrader_course/submitted/test_verification
else
    echo "ERROR: www-data NO puede escribir en NBGrader"
    # Forzar permisos como último recurso
    chmod -R 777 /opt/nbgrader_course
    chown -R www-data:www-data /opt/nbgrader_course
fi

# Configuración de grupos (mantener esto)
usermod -a -G www-data vagrant
usermod -a -G vagrant www-data

# --- 10. Finalizar configuración ---
echo "Finalizando configuración..."

# Agregar entrada al archivo hosts
echo "127.0.0.1 moodle.local" | tee -a /etc/hosts

# Reiniciar servicios
systemctl restart apache2
systemctl restart mysql

# Ejecutar actualización de Moodle
sudo -u www-data php /var/www/html/moodle/admin/cli/upgrade.php --non-interactive

echo "¡Todo listo! Vagrant se ha completado correctamente"
echo "Moodle disponible en http://192.168.56.10/ y http://localhost:8080/"
echo "NBGrader configurado en: /opt/nbgrader_env"