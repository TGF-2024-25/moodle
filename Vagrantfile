# Vagrantfile
Vagrant.configure("2") do |config|
  # Usaremos Ubuntu 22.04 (Jammy)
  config.vm.box = "ubuntu/jammy64"
  
  config.vm.network "private_network", ip: "192.168.56.10"
  config.vm.network "forwarded_port", guest: 80, host: 8080, auto_correct: true
  
  config.vm.boot_timeout = 600

  # Sincronizamos la carpeta "autocorreccion" del repositorio donde está el código
  # con la carpeta de módulos de Moodle dentro de la máquina virtual.
  config.vm.synced_folder "./autocorreccion", "/var/www/html/moodle/mod/autocorreccion"

  config.vm.provider "virtualbox" do |vb|
    vb.memory = "4096" # Aumentamos memoria a 4GB para mejorar rendimiento
    vb.cpus = 2
    vb.customize ["modifyvm", :id, "--natdnshostresolver1", "on"]
    vb.name = "moodle-autocorreccion-tfg-pruebas"
  end

  # Ejecutamos el script de instalación externo
  config.vm.provision "shell", path: "infraestructura/provision.sh"
end