Vagrant.configure("2") do |config|
  config.vm.boot_timeout = 600
  config.vm.box = "ubuntu/focal64" # Ubuntu 20.04
  config.vm.network "private_network", ip: "192.168.56.10"
  config.vm.network "forwarded_port", guest: 8888, host: 8888

  # Sincronizar carpeta local con la VM
  config.vm.synced_folder "C:/Users/kikeebp/Desktop/Universidad/FIN/TFG/VSCodeTFG", "/var/www/html/moodle"

  config.vm.provider "virtualbox" do |vb|
    vb.memory = "4096" # Aumentamos memoria a 4GB para mejor rendimiento
    vb.cpus = 2
    vb.customize ["modifyvm", :id, "--natdnshostresolver1", "on"]
    vb.customize ["modifyvm", :id, "--natdnsproxy1", "on"]

  end

  config.vm.provision "shell", inline: <<-SHELL
    sudo apt update && sudo apt upgrade -y

    # Instalar Apache y MySQL
    sudo apt install -y apache2 mysql-server unzip git

    # Instalar PHP 8.0 y extensiones necesarias
    sudo add-apt-repository ppa:ondrej/php -y
    sudo apt update
    sudo apt install -y php8.0 php8.0-cli php8.0-mysql php8.0-xml php8.0-curl php8.0-zip \
                        php8.0-mbstring php8.0-gd php8.0-intl php8.0-soap php8.0-xmlrpc

    # Configurar PHP
    sudo sed -i "s/post_max_size = .*/post_max_size = 100M/" /etc/php/8.0/apache2/php.ini
    sudo sed -i "s/upload_max_filesize = .*/upload_max_filesize = 100M/" /etc/php/8.0/apache2/php.ini
    sudo sed -i "s/memory_limit = .*/memory_limit = 512M/" /etc/php/8.0/apache2/php.ini
    sudo sed -i "s/max_execution_time = .*/max_execution_time = 300/" /etc/php/8.0/apache2/php.ini

    # Habilitar módulos necesarios de Apache
    sudo a2enmod rewrite
    sudo systemctl restart apache2

    # Configurar MySQL
    sudo mysql -u root -e "CREATE DATABASE moodle DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
    sudo mysql -u root -e "CREATE USER 'moodleuser'@'localhost' IDENTIFIED BY 'password123';"
    sudo mysql -u root -e "GRANT ALL PRIVILEGES ON moodle.* TO 'moodleuser'@'localhost';"
    sudo mysql -u root -e "FLUSH PRIVILEGES;"
    
    # Deshabilitar SQL Strict Mode (puede causar problemas en Moodle)
    echo "[mysqld]" | sudo tee -a /etc/mysql/mysql.conf.d/mysqld.cnf
    echo "sql_mode = \"NO_ENGINE_SUBSTITUTION\"" | sudo tee -a /etc/mysql/mysql.conf.d/mysqld.cnf
    sudo systemctl restart mysql

    # Descargar Moodle 4.1
    # cd /var/www/html
    # sudo rm -rf moodle
    # sudo git clone -b MOODLE_401_STABLE https://github.com/moodle/moodle.git
    # sudo chown -R www-data:www-data moodle
    # sudo chmod -R 755 moodle

    # Crear VirtualHost para Moodle
    sudo tee /etc/apache2/sites-available/moodle.conf <<EOF
<VirtualHost *:80>
    ServerAdmin admin@moodle.local
    DocumentRoot /var/www/html/moodle
    ServerName moodle.local

    <Directory /var/www/html/moodle>
        Options FollowSymlinks
        AllowOverride All
        Require all granted
    </Directory>

    ErrorLog \${APACHE_LOG_DIR}/error.log
    CustomLog \${APACHE_LOG_DIR}/access.log combined
</VirtualHost>
EOF

    sudo a2ensite moodle.conf
    sudo systemctl reload apache2

  SHELL
end
