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
apt-get install -y apache2 mysql-server git unzip python3-pip python3-venv rsync curl

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
echo "Descargando Moodle desde ZIP local..."
mkdir -p /var/www/html/moodle
rm -rf /tmp/moodle_source

echo "Buscando zip local en /vagrant/..."

MOODLE_ZIP=$(find /vagrant -maxdepth 1 -name "moodle*.zip" | head -1)

if [ -n "$MOODLE_ZIP" ]; then
    echo "Usando zip local: $MOODLE_ZIP"
    apt-get install -y unzip
    mkdir -p /tmp/moodle_source
    mkdir -p /tmp/moodle_unzip
    unzip -q "$MOODLE_ZIP" -d /tmp/moodle_unzip

    # El zip de Moodle contiene una carpeta 'moodle' dentro
    if [ -d "/tmp/moodle_unzip/moodle" ]; then
        mv /tmp/moodle_unzip/moodle/* /tmp/moodle_source/
    else
        mv /tmp/moodle_unzip/*/* /tmp/moodle_source/ 2>/dev/null || \
        mv /tmp/moodle_unzip/* /tmp/moodle_source/
    fi

    rm -rf /tmp/moodle_unzip
    echo "Zip local descomprimido correctamente"
else
    echo "ERROR: No se encontró ningún moodle*.zip en /vagrant/"
    echo "Descarga Moodle 4.1 desde https://download.moodle.org/ y ponlo en la carpeta del proyecto"
    exit 1
fi

# Copiar a destino final
rsync -av --remove-source-files /tmp/moodle_source/ /var/www/html/moodle/
rm -rf /tmp/moodle_source
mkdir -p /var/www/moodledata
echo "Moodle instalado correctamente"

# --- 6. Configurar Apache ---
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

# --- 8. Configurar NBGrader y dependencias ---
echo "Configurando NBGrader y dependencias..."

# Directorios para NBGrader
mkdir -p /opt/nbgrader_course/{source,release,submitted,feedback}
chown -R www-data:www-data /opt/nbgrader_course
chmod -R 777 /opt/nbgrader_course

# Instalar dependencias Python en el sistema (para www-data)
echo "Instalando dependencias Python en el sistema..."
apt-get install -y python3-pip
pip3 install nbformat nbconvert nbgrader flask ipykernel

# Instalar también para el usuario www-data (el que ejecuta Apache)
echo "Instalando dependencias para usuario www-data..."
sudo -u www-data pip3 install --user nbformat nbconvert nbgrader

# --- 9. Configurar API de NBGrader ---
echo "Configurando API de NBGrader dentro de la VM..."

# Crear directorio para la API
mkdir -p /opt/nbgrader_api

# Copiar archivos de la API desde el host
if [ -d "/vagrant/api" ]; then
    cp -r /vagrant/api/* /opt/nbgrader_api/
fi

if [ -d "/vagrant/autocorreccion" ]; then
    cp -r /vagrant/autocorreccion /opt/nbgrader_api/
fi

# Crear entorno virtual para la API
cd /opt/nbgrader_api
python3 -m venv venv
source venv/bin/activate

# Instalar dependencias (versiones compatibles)
pip install --upgrade pip
pip install nbgrader==0.9.4
pip install jupyter==1.0.0
pip install flask==2.3.3
pip install nbformat==5.9.2
pip install nbconvert==7.14.2
pip install ipykernel==6.29.5
pip install jsonschema==4.17.3
pip install lark==1.1.9
pip install requests

# Instalar kernel de Jupyter
python -m ipykernel install --user --name python3 --display-name "Python 3"

# Crear script de inicio para la API
cat << 'SCRIPT_EOF' > /opt/nbgrader_api/start_api.sh
#!/bin/bash
cd /opt/nbgrader_api
source venv/bin/activate
export FLASK_APP=nbgrader_api.py
export FLASK_ENV=production
exec python nbgrader_api.py
SCRIPT_EOF

chmod +x /opt/nbgrader_api/start_api.sh

# Crear servicio systemd
cat << 'SERVICE_EOF' > /etc/systemd/system/nbgrader-api.service
[Unit]
Description=NBGrader API Service
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/nbgrader_api
ExecStart=/opt/nbgrader_api/start_api.sh
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
SERVICE_EOF

# Habilitar e iniciar el servicio
systemctl daemon-reload
systemctl enable nbgrader-api.service
systemctl start nbgrader-api.service

# Verificar instalaciones
echo "Verificando instalación..."
python3 -c "import nbformat; print('nbformat disponible en sistema')"
sudo -u www-data python3 -c "import nbformat; print('nbformat disponible para www-data')"

echo ""
echo "=========================================="
echo "¡Todo listo! Vagrant se ha completado correctamente"
echo "=========================================="
echo ""
echo "Moodle descargado correctamente"
echo "NOTA: Debes completar la instalación de Moodle desde el navegador"
echo ""
echo "Moodle:       http://localhost:8080"
echo "API NBGrader: http://localhost:5000"
echo ""
echo "La API se ejecuta automáticamente dentro de la VM"
echo "Para ver logs de la API: vagrant ssh -c 'sudo journalctl -u nbgrader-api -f'"
echo "=========================================="