
# Ansible Role:  `docker`

This role will fully configure and install [Docker](https://www.docker.com/).

[![GitHub Workflow Status](https://img.shields.io/github/workflow/status/bodsch/ansible-icinga2/CI)][ci]
[![GitHub issues](https://img.shields.io/github/issues/bodsch/ansible-role-docker)][issues]
[![GitHub release (latest by date)](https://img.shields.io/github/v/release/bodsch/ansible-role-docker)][releases]

[ci]: https://github.com/bodsch/ansible-role-docker/actions
[issues]: https://github.com/bodsch/ansible-role-docker/issues?q=is%3Aopen+is%3Aissue
[releases]: https://github.com/bodsch/ansible-role-docker/releases


## Requirements & Dependencies

- Connectivity to docker-ce package [repository](https://download.docker.com)

### Operating systems

Tested on

- Debian 9 / 10
- Ubuntu 18.04 / 20.04
- CentOS 8
- OracleLinux 8

**this role only supports docker versions 1.11+**.

## Role Variables

The following variables can be used to customize the docker installation:

```yaml
## choose docker repo channel enable status
docker_repo:
  channel:
    stable_enabled: true
    test_enabled: false
    nightly_enabled: false

## state of package (present, absent, exc.)
docker_state: "present"

## should docker daemon start on boot?
docker_service:
  enable: true
  ## name of docker service
  name: "docker"

docker_containerd_socket: /run/containerd/containerd.sock

## name group for docker socket file
docker_group: "docker"

## install docker-compose in version
docker_compose:
  install: true
  version: 1.29.2

docker_users: []

docker_plugins: []
```

### Proxy related
should docker daemon use a proxy for outbound connections?

```yaml
docker_proxy:
  enabled: false
  ## list of env variables we should set (comment out the ones you don't need)
  env:
    - "HTTP_PROXY=http://proxy.example.com:80/"
    - "HTTP_PROXY=https://proxy.example.com:443/"
    - "NO_PROXY=localhost,127.0.0.1,internalhub.example.com"
```

### docker client configuration

enable authentication for docker registry

```yaml
docker_client_config:
  enabled: false
  ## the location we should push client configuration
  location: "/root/.docker/config.json"
```

#### for auth (docker login) use something like

```yaml
docker_client_config:
  auths:
    "https://test.tld:1234":
      auth: "SOME_STRING"
      email: "SOME_EMAIL"
```

### default dockerd configuration options

[configuration reference](https://docs.docker.com/engine/reference/commandline/dockerd/#/linux-configuration-file)

currently supported options:

| options                    | type     | description       |
| :-----                     | :----    | :-----            |
| `log_driver`               | `string` | Default driver for container logs (default "json-file") |
| `log_opts`                 | ``       | Default log driver options for containers (default map[]) |
| `log_level`                | `string` | Set the logging level ("debug"|"info"|"warn"|"error"|"fatal") (default "info") |
| `dns`                      | `list`   | DNS server to use (default [] ) |
| `dns_opts`                 | `list`   | DNS options to use |
| `dns_search`               | `list`   | DNS search domains to use |
| `data_root`                | `string` | Root directory of persistent Docker state (default "/var/lib/docker") |
| `max_concurrent_downloads` | `int`    | Set the max concurrent downloads for each pull (default 3) |
| `max_concurrent_uploads`   | `int`    | Set the max concurrent uploads for each push (default 5) |
| `max_download_attempts`    | `int`    | Set the max download attempts for each pull (default 5) |
| `metrics_addr`             | `string` | Set default address and port to serve the metrics api on |
| `debug`                    | `bool`   | Enable debug mode |
| `selinux_enabled`          | `bool`   | Enable selinux support |
| `seccomp_profile`          | `string` | Path to seccomp profile |
| `experimental`             | `bool`   | Enable experimental features |
| `storage_driver`           | `string` | Storage driver to use |
| `storage_opts`             | `list`   | Storage driver options |
| `group`                    | `group`  | Group for the unix socket (default "docker") |
| `bridge`                   | `string` | Attach containers to a network bridge |
| `bip`                      | `string` | Specify network bridge IP |
| `ip`                       | `string` | Default IP when binding container ports (default 0.0.0.0) |
| `fixed_cidr`               | `string` | IPv4 subnet for fixed IPs |
| `fixed_cidr_v6`            | `string` | IPv6 subnet for fixed IPs |
| `default_gateway`          | `string` | Container default gateway IPv4 address |
| `default_gateway_v6`       | `string` | Container default gateway IPv6 address |
| `hosts`                    | `list`   | Daemon socket(s) to connect to |
| `insecure_registries`      | `list`   | Enable insecure registry communication |
| `shutdown_timeout`         | `int`    | Set the default shutdown timeout (default 15) |



```yaml
docker_config:
  log_driver: ""
  log_opts: {}
  #  env: "os,customer"
  #  "max-file": "5"
  #  "max-size": "10m"
  max_concurrent_downloads: 3
  max_concurrent_uploads: 5
  debug: false
  log_level: ""
  bridge: ""
  bip: "172.16.0.1/24"
  fixed_cidr: "172.16.0.0/24"
  fixed_cidr_v6: ""
  default_gateway: ""
  default_gateway_v6: ""
  selinux_enabled: false
  experimental: false
  ip: "0.0.0.0"
  group: "{{ docker_group }}"
  insecure_registries: []
```

### docker_users options

planned

### docker_plugins options

To install, enable custom plugins

```yaml
docker_plugins:
  - alias: loki
    source: grafana/loki-docker-driver:latest
    state: present
```


## Examples

Install latest docker **stable** release on your local centos server

```yaml
- hosts: localhost
  roles:
     - role: docker
```

Install latest docker **edge** release on your local centos server

```yaml
- hosts: localhost
  roles:
     - role: docker
       docker_pkg_state: latest
       docker_repo_channel_edge_enabled: true
```

Install older docker **stable** release on your local centos server

```yaml
- hosts: localhost
  roles:
     - role: docker
       docker_pkg_name: docker-ce-18.03.1.ce-1.el7.centos
```

Advanced playbook with various variables applied

[configuration reference](https://docs.docker.com/engine/reference/commandline/dockerd/#daemon-configuration-file)

```yaml
- hosts: localhost
  vars:
    docker_config:
      # store docker containers/images to /opt/docker
      data_root: /opt/docker
      # change default docker bridge subnet
      bip: 172.16.77.77/24
      # set default log driver to journald
      log_driver: journald
      # enable experimental mode
      experimental: true
      # expose docker api over socket file and tcp
      hosts:
        - unix:///var/run/docker.sock
        - tcp://0.0.0.0:2376
      # set default search domains
      dns_search:
        - lab1.linuxctl.com
        - lab2.linuxctl.com
      # configure logging options
      log_opts:
        "max-size": 10m
        "max-file": "3"
        labels: molecule
        env: "os,customer"

  roles:
    - role: docker
```

## Author and License

- original `docker` role written by:
  - George Bolo | [linuxctl.com](https://linuxctl.com)

- modified:
  - Bodo Schulz

## License

MIT

`FREE SOFTWARE, HELL YEAH!`
