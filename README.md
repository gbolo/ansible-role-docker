
# Ansible Role:  `docker`

This role will fully configure and install [dockerd](https://www.docker.com/).

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

* ArchLinux
* Debian based
    - Debian 10 / 11
    - Ubuntu 20.04
* RedHat based
    - Alma Linux 8
    - Rocky Linux 8
    - OracleLinux 8

**this role only supports docker versions 1.11+**.

## Role Variables

The following variables can be used to customize the docker installation:

```yaml
## choose centos docker repo channel enable status
docker_repo:
  channel:
    stable_enabled: true
    test_enabled: false
    nightly_enabled: false

## state of package (present, absent, etc.)
docker_state: present

## should docker daemon start on boot?
docker_service:
  enable: true
  ## name of docker service
  name: docker

## install docker-compose in version
docker_compose: {}
# as example:
# docker_compose:
#   install: true
#   version: 1.29.2

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

Enable authentication for the Docker Registry.

Here it is possible to create a configuration for different users.

The password stored here is base64 encoded and not encrypted!
The creation of a corresponding string can be carried out as follows:

```bash
echo "jenkins$robot:rubbel-die-katz-du-dummschwätzer1" | base64
amVua2luczpydWJiZWwtZGllLWthdHotZHUtZHVtbXNjaHfDpHR6ZXIxCg==
```

```yaml
docker_client_config:
  ## the location we should push client configuration
  - location: "/root/.docker/config.json"
    enabled: false
    auths:
      registry.gitfoo.tld:
        auth: amVua2luczpydWJiZWwtZGllLWthdHotZHUtZHVtbXNjaHfDpHR6ZXIxCg==
```

Alternatively, you can also enter your user name and password.
The Ansible module will make a valid Base64 encoded string out of it.

```yaml
docker_client_config:
    ## the location we should push client configuration
  - location: "/var/tmp/foo/config.json"
    enabled: false
    auths:
      "test.tld":
        username: "FOO-was-sonst"
        passwort: "ja-toll-schon-wieder-alles-scheisse!"
```

Since version 3.1.0 it is now also possible to configure the output format of `docker ps` or `docker image`.
Here the fed parameters have to be defined as a list:

```yaml
docker_client_config:
  ## the location we should push client configuration
  - location: "/root/.docker/config.json"
    enabled: false
    auths:
      registry.gitfoo.tld:
        auth: amVua2luczpydWJiZWwtZGllLWthdHotZHUtZHVtbXNjaHfDpHR6ZXIxCg==
    formats:
      ps:
        - ".ID"
        - ".Names"
        - ".Status"
        - ".Labels"
        - ".RunningFor"
        - ".Ports"
      images:
        - ".ID"
        - ".Repository"
        - ".Tag"
        - ".CreatedAt"
```


### default dockerd configuration options

[configuration reference](https://docs.docker.com/engine/reference/commandline/dockerd/#/linux-configuration-file)

currently supported options:

| options                    | type     | default           | description       |
| :-----                     | :----    | :----             | :-----            |
| `log_driver`               | `string` | `json-file`       | Default driver for container logs |
| `log_opts`                 | `dict`   | `{}`              | Default log driver options for containers |
| `log_level`                | `string` | `info`            | Set the logging level (`debug`,`info`,`warn`,`error`,`fatal`) |
| `dns`                      | `list`   | `[]`              | DNS server to use |
| `dns_opts`                 | `list`   | `[]`              | DNS options to use |
| `dns_search`               | `list`   | `[]`              | DNS search domains to use |
| `data_root`                | `string` | `/var/lib/docker` | Root directory of persistent Docker state |
| `max_concurrent_downloads` | `int`    | `3`               | Set the max concurrent downloads for each pull |
| `max_concurrent_uploads`   | `int`    | `5`               | Set the max concurrent uploads for each push |
| `max_download_attempts`    | `int`    | `5`               | Set the max download attempts for each pull |
| `metrics_addr`             | `string` | `-`               | Set default address and port to serve the metrics api on |
| `debug`                    | `bool`   | `false`           | Enable debug mode |
| `selinux_enabled`          | `bool`   | `false`           | Enable selinux support |
| `seccomp_profile`          | `string` | `-`               | Path to seccomp profile |
| `experimental`             | `bool`   | `false`           | Enable experimental features |
| `storage_driver`           | `string` | `-`               | Storage driver to use |
| `storage_opts`             | `list`   | `[]`              | Storage driver options |
| `group`                    | `group`  | `docker`          | Group for the unix socket |
| `bridge`                   | `string` | `-`               | Attach containers to a network bridge |
| `bip`                      | `string` | `-`               | Specify network bridge IP |
| `ip`                       | `string` | `0.0.0.0`         | Default IP when binding container ports |
| `fixed_cidr`               | `string` | `-`               | IPv4 subnet for fixed IPs |
| `fixed_cidr_v6`            | `string` | `-`               | IPv6 subnet for fixed IPs |
| `default_gateway`          | `string` | `-`               | Container default gateway IPv4 address |
| `default_gateway_v6`       | `string` | `-`               | Container default gateway IPv6 address |
| `hosts`                    | `list`   | `[]`              | Daemon socket(s) to connect to |
| `insecure_registries`      | `list`   | `[]`              | Enable insecure registry communication |
| `shutdown_timeout`         | `int`    | `15`              | Set the default shutdown timeout |



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

Adds an **existing user** to the `docker` group.

Furthermore, it tries to set the access rights to the docker socker by means of `setfacl`.

```yaml
docker_users:
  - jenkins
```

### docker_plugins options

Install and activate custom plugins.

(Currently only tested with [Loki](https://grafana.com/docs/loki/latest/clients/docker-driver/)!)

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
  vars:
    docker_repo:
      channel:
        nightly_enabled: true
  roles:
     - role: docker
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
---

## Author and License

- original `docker` role written by:
  - George Bolo | [linuxctl.com](https://linuxctl.com)

- modified:
  - Bodo Schulz

## License

MIT

`FREE SOFTWARE, HELL YEAH!`
