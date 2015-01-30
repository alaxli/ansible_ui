About
=====
该平台为[ansible](https://github.com/ansible/ansible)系统的web程序


Function
=====
* 按照项目来组织布局，更为直观，上手简单
* 提供简单易懂的主机管理界面
* 提供用户密钥管理功能
* 提供yml文件界面管理功能
* 提供任务部署功能
* 提供文件传输功能
* 提供命令执行功能
* 提供预约执行功能
* 提供任务模板功能
* 提供log功能
* 提供邮件通知功能
* 基于celery队列进行任务分发，便于扩展

UserManual
=====
[ansible_ui平台用户手册](https://github.com/alaxli/ansible_ui/tree/master/documents)

Requirements
=====
* pip
* virtualenv
* mysql-server,mysql-devel
* openldap-devel

Install
=====
* 系统为CentOS6.5
* 添加系统用户

    
        useradd ansible
        su - ansible


* 配置virtualenv环境


        virtualenv envansible
        source envansible/bin/active


* 下载源码


        git clone https://github.com/alaxli/ansible_ui.git


* 安装依赖库


        cd ansible-ui
        pip install -r requirements.txt
        pip install PIL --allow-external PIL --allow-unverified PIL
    

* 配置ldap、数据库和邮件信息


        cd desktop/core/internal
        vim settings_local.py 
        # 修改 LDAP Datebase Mail 和ansible_playbook命令位置(which ansible_playbook)配置
        如果需要使用ldap，还需要修改settings.py，去掉下面行的注释
        #'desktop.core.auth.backend.LdapBackend',


* 配置数据库


        create database ansible CHARACTER SET utf8;
        grant all on ansible.* to ansibleuser@'localhost' identified by '******';


* 初始化数据库

        python manage.py schemamigration desktop.apps.account --init
        python manage.py schemamigration desktop.apps.ansible --init
        python manage.py syncdb
        python manage.py migrate ansible
        python manage.py migrate account
        python manage.py migrate kombu.transport.django
        python manage.py migrate djcelery
        python manage.py migrate guardian


* 配置celery


        修改celery-conf/supervisord.conf
        [inet_http_server] #配置web管理supervisor
        [program:ansible_celeryd] #修改command中 virtualenv 和 ansible_ui home


* 启动celery


        supervisord -c celery-conf/supervisord.conf


* 配置ansible


        cp ansible-conf/ansible.cfg ~/.ansible.cfg


* Vagrant + Ansible

    感谢[yunlzheng](https://github.com/yunlzheng)提供了使用vagrant+ansible自动构建开发环境的方式[Vagrantfile](https://github.com/alaxli/ansible_ui/blob/master/Vagrantfile)+[playbook.yml](https://github.com/alaxli/ansible_ui/blob/master/playbook.yml),具体操作推荐阅读yunlzheng的[《利用Ansible将开发环境纳入版本管理》](http://yunlzheng.github.io/2014/08/08/vagrant-with-ansible/)


Run
=====
* 直接运行


        python manage.py runserver ip:8000


* apache + wsgi

        修改apache-conf/ansible.cfg : ansible_ui_dir，指向实际目录
        修改django.wsgi : yourvirtualenv 指向实际目录
        拷贝apache-conf/ansible.cfg 到apache配置目录下
        重启 httpd


Demo
=====
* http://115.28.87.99:8888 用户名:admin 密码:ansible (由于服务器资源紧张，暂时关闭)

Problem
=====
* 已知问题：在单核CPU服务器上任务无法运行(在调用pexpect时会报“ValueError: I/O operation on closed file”错误，类似这个[问题](http://stackoverflow.com/questions/24524162/pexpect-runs-failed-when-use-multiprocessing),如果要在单核CPU服务器上运行，请将pexpect降为2.4版本
