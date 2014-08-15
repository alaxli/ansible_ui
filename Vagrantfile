# -*- mode: ruby -*-
# vi: set ft=ruby :

# Vagrantfile API/syntax version. Don't touch unless you know what you're doing!
VAGRANTFILE_API_VERSION = "2"

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  config.vm.box = "base"

  config.vm.network "private_network", ip: "10.2.3.4"

  config.vm.provision "ansible" do |ansible|
    ansible.playbook  = "playbook.yml"
  end

end
