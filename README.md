Docker - Ansible Role
=========

[![Build Status](https://travis-ci.org/gbolo/ansible-role-docker.svg?branch=master)](https://travis-ci.org/gbolo/ansible-role-docker)

This role will fully configure and install [Docker](https://www.docker.com/) on RHEL/CentOS 7. In it's current form, **this role only supports docker versions 1.11+**.

Requirements
------------

- OS: CentOS 7
- Internet Connectivity

Role Variables
--------------

The following variables can be used to customize the docker installation:
```yaml
# OS related -------------------------------------------------------------------
## use official docker repository
docker_repo_enabled: true
## choose docker repo branch: main, experimental, testing
docker_repo_branch: "main"
## name of docker package to install
docker_pkg_name: "docker-engine"
## state of package (present, latest, exc.)
docker_pkg_state: present
## name of docker service
docker_service_name: "docker"
## should docker daemon start on boot?
docker_service_enable: true
## name group for docker socket file
docker_group: "docker"

# docker client configuration --------------------------------------------------
## enable authentication for docker registry
docker_client_config_enabled: false
## the location we should push client configuration
docker_client_config_location: "/root/.docker/config.json"
# for auth (docker login) use something like:
#docker_client_config:
#  auths:
#    "https://test.tld:1234":
#      auth: "SOME_STRING"
#      email: "SOME_EMAIL"

# default dockerd configuration options ----------------------------------------
## https://docs.docker.com/engine/reference/commandline/dockerd/#/linux-configuration-file
docker_config_hosts:
  - "unix:///var/run/docker.sock"
docker_config_graph: "/var/lib/docker"
docker_config_log_driver: ""
docker_config_log_opts: {}
docker_config_max_concurrent_downloads: 3
docker_config_max_concurrent_uploads: 5
docker_config_debug: false
docker_config_log_level: ""
docker_config_bridge: ~
docker_config_bip: "172.16.0.1/24"
docker_config_fixed_cidr: "172.16.0.0/24"
docker_config_fixed_cidr_v6: ""
docker_config_default_gateway: ""
docker_config_default_gateway_v6: ""
docker_config_selinux_enabled: false
docker_config_ip: "0.0.0.0"
docker_config_group: "{{ docker_group }}"
docker_config_insecure_registries: []

# additional custom docker settings can be added to this dict:
docker_config_custom: {}
```

Example Playbooks
----------------

Install latest docker **stable** release on your local centos server
```
- hosts: localhost
  roles:
     - { role: gbolo.docker, docker_pkg_state: latest }
```
Install latest docker **experimental** release on your local centos server
```
- hosts: localhost
  roles:
     - { role: gbolo.docker, docker_pkg_state: latest, docker_repo_branch: experimental }
```
Install older docker **stable** release on your local centos server
```
- hosts: localhost
  roles:
     - { role: gbolo.docker, docker_pkg_name: docker-engine-1.11.2 }
```
Advanced playbook with various variables applied
```yaml
- hosts: localhost
  vars:
    # store docker containers/images to /opt/docker
    docker_config_graph: /opt/docker
    # change default docker bridge subnet
    docker_config_bip: 172.16.77.77/24
    # set default log driver to journald
    docker_config_log_driver: journald
    # use docker_config_custom to define additional settings not listed above
    docker_config_custom:
      # enable experimental mode
      experimental: true
      # set default search domains
      dns-search:
        - lab1.linuxctl.com
        - lab2.linuxctl.com

  roles:
    - role: gbolo.docker
```

Author and License
-------
`docker` role written by:
- George Bolo | [linuxctl.com](https://linuxctl.com)

License: **MIT**

`FREE SOFTWARE, HELL YEAH!`
