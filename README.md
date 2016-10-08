Docker - Ansible Role
=========

This role will fully configure your docker installation on CentOS 7

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
docker_config_authorization_plugins: []
docker_config_dns: []
docker_config_dns_opts: []
docker_config_dns_search: []
docker_config_exec_opts: []
docker_config_exec_root: ""
docker_config_storage_driver: ""
docker_config_storage_opts: []
docker_config_labels: []
docker_config_live_restore: true
docker_config_log_driver: ""
docker_config_log_opts: {}
docker_config_mtu: 1500
docker_config_pidfile: "/var/run/docker.pid"
docker_config_graph: "/var/lib/docker"
docker_config_cluster_store: ""
docker_config_cluster_store_opts: {}
docker_config_cluster_advertise: ""
docker_config_max_concurrent_downloads: 3
docker_config_max_concurrent_uploads: 5
docker_config_debug: false
docker_config_hosts:
  - "unix:///var/run/docker.sock"
docker_config_log_level: ""
# disable tls for now because tlsverify option implemented strangely
# https://github.com/docker/docker/issues/27105
##docker_config_tls: ~
# broken if you specify anything but true for tlsverify
##docker_config_tlsverify: ~
##docker_config_tlscacert: ""
##docker_config_tlscert: ""
##docker_config_tlskey: ""
docker_config_swarm_default_advertise_addr: ""
docker_config_api_cors_header: ""
docker_config_selinux_enabled: false
docker_config_userns_remap: ""
docker_config_group: "{{ docker_group }}"
docker_config_cgroup_parent: ""
docker_config_default_ulimits: {}
docker_config_ipv6: false
docker_config_iptables: true
docker_config_ip_forward: true
docker_config_ip_masq: true
docker_config_userland_proxy: true
docker_config_ip: "0.0.0.0"
docker_config_bridge: ~
docker_config_bip: "172.16.0.1/24"
docker_config_fixed_cidr: "172.16.0.0/24"
docker_config_fixed_cidr_v6: ""
docker_config_default_gateway: ""
docker_config_default_gateway_v6: ""
docker_config_icc: true
docker_config_raw_logs: false
docker_config_registry_mirrors: []
docker_config_insecure_registries: []
docker_config_disable_legacy_registry: false
docker_config_default_runtime: "runc"
docker_config_oom_score_adjust: -500
```

Dependencies
------------

A list of other roles hosted on Galaxy should go here, plus any details in regards to parameters that may need to be set for other roles, or variables that are used from other roles.

Example Playbook
----------------

Including an example of how to use your role (for instance, with variables passed in as parameters) is always nice for users too:

    - hosts: servers
      roles:
         - { role: username.rolename, x: 42 }

License
-------

BSD

Author Information
------------------

An optional section for the role authors to include contact information, or a website (HTML is not allowed).
