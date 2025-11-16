#!/bin/bash
set -e

# --- 1. Actualizar sistema y dependencias ---
export DEBIAN_FRONTEND=noninteractive
echo "Actualizando sistema (Ubuntu 22.04)..."

# Limpiar y configurar sources.list correctamente
cat <<EOF > /etc/apt/sources.list
deb http://archive.ubuntu.com/ubuntu jammy main restricted universe multiverse
deb http://archive.ubuntu.com/ubuntu jammy-updates main restricted universe multiverse
deb http://archive.ubuntu.com/ubuntu jammy-backports main restricted universe multiverse
deb http://security.ubuntu.com/ubuntu jammy-security main restricted universe multiverse
EOF

apt-get update
apt-get upgrade -y

# Instalar Apache y MySQL
apt-get install -y apache2 mysql-server git unzip python3-pip python3-venv rsync

# --- 2. Instalar PHP 8.1 ---
echo "Instalando PHP 8.1 y extensiones..."
apt-get install -y software-properties-common
add-apt-repository -y ppa:ondrej/php
apt-get update
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

MYSQL_ROOT_PASSWORD="password123"
MYSQL_USER_PASSWORD="password123"

debconf-set-selections <<< "mysql-server mysql-server/root_password password $MYSQL_ROOT_PASSWORD"
debconf-set-selections <<< "mysql-server mysql-server/root_password_again password $MYSQL_ROOT_PASSWORD"

mysql -uroot -p$MYSQL_ROOT_PASSWORD -e "CREATE DATABASE IF NOT EXISTS moodle DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;" || true
mysql -uroot -p$MYSQL_ROOT_PASSWORD -e "CREATE USER IF NOT EXISTS 'moodleuser'@'localhost' IDENTIFIED BY '$MYSQL_USER_PASSWORD';" || true
mysql -uroot -p$MYSQL_ROOT_PASSWORD -e "GRANT ALL PRIVILEGES ON moodle.* TO 'moodleuser'@'localhost';" || true
mysql -uroot -p$MYSQL_ROOT_PASSWORD -e "FLUSH PRIVILEGES;" || true

# Configuración permanente de MySQL
echo "[mysqld]" | tee -a /etc/mysql/mysql.conf.d/mysqld.cnf
echo "sql_mode = NO_ENGINE_SUBSTITUTION" | tee -a /etc/mysql/mysql.conf.d/mysqld.cnf
echo "default_storage_engine = innodb" | tee -a /etc/mysql/mysql.conf.d/mysqld.cnf
echo "innodb_file_per_table = 1" | tee -a /etc/mysql/mysql.conf.d/mysqld.cnf

systemctl restart mysql

# --- 5. Descargar Moodle ---
echo "Descargando Moodle y configurando directorios..."
mkdir -p /var/www/html/moodle
rm -rf /tmp/moodle_source
git clone -b MOODLE_401_STABLE --depth 1 https://github.com/moodle/moodle.git /tmp/moodle_source
rsync -av --remove-source-files /tmp/moodle_source/ /var/www/html/moodle/
mkdir -p /var/www/moodledata

# --- 6. Configurar Apache ---

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

echo "Configurando Apache..."
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
systemctl restart apache2

# --- 7. Configurar permisos ---
echo "Configurando permisos..."
chown -R www-data:www-data /var/www
chmod -R 755 /var/www/html/moodle
chmod -R 777 /var/www/moodledata

# --- 8. Configurar NBGrader en VM ---
echo "Configurando directorios para NBGrader..."
mkdir -p /opt/nbgrader_course/{source,release,submitted,feedback}
chown -R www-data:www-data /opt/nbgrader_course
chmod -R 777 /opt/nbgrader_course

# Instalar dependencias Python en VM
echo "Instalando dependencias Python en VM..."
apt-get install -y python3-pip
pip3 install nbformat nbconvert flask

# Ejecutar actualización de Moodle
echo "Moodle descargado correctamente"
echo "NOTA: Debes completar la instalación de Moodle desde el navegador"

echo "¡Todo listo! Vagrant se ha completado correctamente"
echo "Moodle disponible en http://192.168.56.10/ y http://localhost:8080/"
echo "NBGrader configurado en: /opt/nbgrader_env"