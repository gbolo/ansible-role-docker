#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# (c) 2020-2022, Bodo Schulz <bodo@boone-schulz.de>
# BSD 2-clause (see LICENSE or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import absolute_import, division, print_function
import os
import json

import docker

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.bodsch.core.plugins.module_utils.directory import create_directory
from ansible_collections.bodsch.core.plugins.module_utils.checksum import Checksum
from ansible_collections.bodsch.core.plugins.module_utils.diff import SideBySide
from ansible_collections.bodsch.core.plugins.module_utils.validate import validate

__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '0.1',
    'status': ['preview'],
    'supported_by': 'community'
}

# ---------------------------------------------------------------------------------------


class DockerCommonConfig(object):
    """
    """
    module = None

    def __init__(self, module):
        """
          Initialize all needed Variables
        """
        self.module = module
        self.state = module.params.get("state")
        self.diff_output = module.params.get("diff_output")
        #
        #
        self.authorization_plugins = module.params.get("authorization_plugins")
        self.bip = module.params.get("bip")
        self.bridge = module.params.get("bridge")
        self.data_root = module.params.get("data_root")
        self.debug = module.params.get("debug")
        self.default_gateway = module.params.get("default_gateway")
        self.default_gateway_v6 = module.params.get("default_gateway_v6")
        self.default_shm_size = module.params.get("default_shm_size")
        self.default_ulimits = module.params.get("default_ulimits")
        self.dns = module.params.get("dns")
        self.dns_opts = module.params.get("dns_opts")
        self.dns_search = module.params.get("dns_search")
        self.experimental = module.params.get("experimental")
        self.fixed_cidr = module.params.get("fixed_cidr")
        self.fixed_cidr_v6 = module.params.get("fixed_cidr_v6")
        self.group = module.params.get("group")
        self.hosts = module.params.get("hosts")
        self.insecure_registries = module.params.get("insecure_registries")
        self.ip = module.params.get("ip")
        self.ip6tables = module.params.get("ip6tables")
        self.ip_forward = module.params.get("ip_forward")
        self.ip_masq = module.params.get("ip_masq")
        self.iptables = module.params.get("iptables")
        self.ipv6 = module.params.get("ipv6")
        self.labels = module.params.get("labels")
        self.log_driver = module.params.get("log_driver")
        self.log_level = module.params.get("log_level")
        self.log_opts = module.params.get("log_opts")
        self.max_concurrent_downloads = module.params.get("max_concurrent_downloads")
        self.max_concurrent_uploads = module.params.get("max_concurrent_uploads")
        self.max_download_attempts = module.params.get("max_download_attempts")
        self.metrics_addr = module.params.get("metrics_addr")
        self.oom_score_adjust = module.params.get("oom_score_adjust")
        self.pidfile = module.params.get("pidfile")
        self.raw_logs = module.params.get("raw_logs")
        self.registry_mirrors = module.params.get("registry_mirrors")
        self.seccomp_profile = module.params.get("seccomp_profile")
        self.selinux_enabled = module.params.get("selinux_enabled")
        self.shutdown_timeout = module.params.get("shutdown_timeout")
        self.storage_driver = module.params.get("storage_driver")
        self.storage_opts = module.params.get("storage_opts")
        self.tls_ca_cert = module.params.get("tls_ca_cert")
        self.tls_cert = module.params.get("tls_cert")
        self.tls_key = module.params.get("tls_key")
        self.tls_verify = module.params.get("tls_verify")

        self.config_file = "/etc/docker/daemon.json"
        # self.checksum_file_name = "/etc/docker/.checksum"

        self.cache_directory = "/var/cache/ansible/docker"
        self.checksum_file_name = os.path.join(self.cache_directory, "daemon.checksum")

    def run(self):
        """
            run
        """
        create_directory(self.cache_directory)

        checksum = Checksum(self.module)

        if self.state == 'absent':
            """
                remove created files
            """
            if os.path.isfile(self.config_file):
                os.remove(self.config_file)

            if os.path.isfile(self.checksum_file_name):
                os.remove(self.checksum_file_name)

            return dict(
                changed = True,
                failed = False,
                msg = "config removed"
            )

        if not os.path.isfile(self.config_file):
            if os.path.isfile(self.checksum_file_name):
                os.remove(self.checksum_file_name)

        _msg = "The configuration has not been changed."
        _diff = []

        self.__docker_client()

        data = self.config_opts()

        changed, new_checksum, old_checksum = checksum.validate(self.checksum_file_name, data)

        # self.module.log(f" changed       : {changed}")
        # self.module.log(f" new_checksum  : {new_checksum}")
        # self.module.log(f" old_checksum  : {old_checksum}")

        if changed:
            with open(self.config_file, 'w') as fp:
                json_data = json.dumps(data, indent=2, sort_keys=False)
                fp.write(f'{json_data}\n')

            checksum.write_checksum(self.checksum_file_name, new_checksum)

            if self.diff_output:
                difference = self.create_diff(self.config_file, data)
                _diff = difference

            _msg = "The configuration has been successfully updated."

        return dict(
            changed = changed,
            failed = False,
            msg = _msg,
            diff = _diff
        )

    def config_opts(self):

        data = dict()

        if validate(self.authorization_plugins):
            data["authorization-plugins"] = self.authorization_plugins

        if validate(self.bip):
            data["bip"] = self.bip

        if validate(self.bridge):
            data["bridge"] = self.bridge

        if validate(self.data_root):
            data["data-root"] = self.data_root

        if validate(self.debug):
            data["debug"] = self.debug

        if validate(self.default_gateway):
            data["default-gateway"] = self.default_gateway

        if validate(self.default_gateway_v6):
            data["default-gateway-v6"] = self.default_gateway_v6

        if validate(self.default_shm_size):
            data["default-shm-size"] = self.default_shm_size

        if validate(self.default_ulimits):
            data["default-ulimits"] = self.default_ulimits

        if validate(self.dns):
            data["dns"] = self.dns

        if validate(self.dns_opts):
            data["dns-opts"] = self.dns_opts

        if validate(self.dns_search):
            data["dns-search"] = self.dns_search

        if validate(self.experimental):
            data["experimental"] = self.experimental

        if validate(self.fixed_cidr):
            data["fixed-cidr"] = self.fixed_cidr

        if validate(self.fixed_cidr_v6):
            data["fixed-cidr-v6"] = self.fixed_cidr_v6

        if validate(self.group):
            data["group"] = self.group

        if validate(self.hosts):
            data["hosts"] = self.hosts

        if validate(self.insecure_registries):
            data["insecure-registries"] = self.insecure_registries

        if validate(self.ip):
            data["ip"] = self.ip

        if validate(self.ip_forward):
            data["ip-forward"] = self.ip_forward

        if validate(self.ip_masq):
            data["ip-masq"] = self.ip_masq

        if validate(self.iptables):
            data["iptables"] = self.iptables

        if validate(self.ip6tables):
            data["ip6tables"] = self.ip6tables

        if validate(self.ipv6):
            data["ipv6"] = self.ipv6

        if validate(self.labels):
            data["labels"] = self.labels

        if validate(self.log_level) and self.log_level in ["debug", "info", "warn", "error", "fatal"]:
            data["log-level"] = self.log_level

        if validate(self.log_driver):
            if "loki" in self.log_driver:
                plugin_valid, plugin_state_message = self.__check_plugin()

                if not plugin_valid:
                    self.module.log(msg="ERROR: log_driver are not valid!")
                    self.module.log(msg=f"ERROR: {plugin_state_message}")
                    self.log_driver = "json-file"

            data["log-driver"] = self.log_driver

        if validate(self.log_opts):
            data["log-opts"] = self.__values_as_string(self.log_opts)

        if validate(self.max_concurrent_downloads):
            data["max-concurrent-downloads"] = self.max_concurrent_downloads

        if validate(self.max_concurrent_uploads):
            data["max-concurrent-uploads"] = self.max_concurrent_uploads

        if validate(self.max_download_attempts):
            data["max-download-attempts"] = self.max_download_attempts

        if validate(self.metrics_addr):
            data["metrics-addr"] = self.metrics_addr
            data["experimental"] = True

        if validate(self.oom_score_adjust):
            data["oom-score-adjust"] = self.oom_score_adjust

        if validate(self.pidfile):
            data["pidfile"] = self.pidfile

        if validate(self.raw_logs):
            data["raw-logs"] = self.raw_logs

        if validate(self.registry_mirrors):
            data["registry-mirrors"] = self.registry_mirrors

        if validate(self.seccomp_profile):
            data["seccomp-profile"] = self.seccomp_profile

        if validate(self.selinux_enabled):
            data["selinux-enabled"] = self.selinux_enabled

        if validate(self.shutdown_timeout):
            data["shutdown-timeout"] = self.shutdown_timeout

        if validate(self.storage_driver):
            self.module.log(msg=f"  - {self.storage_driver}")
            self.module.log(msg=f"  - {self.storage_opts}")
            valid_storage_drivers = ["aufs", "devicemapper", "btrfs", "zfs", "overlay", "overlay2", "fuse-overlayfs"]
            if self.storage_driver in valid_storage_drivers:
                data["storage-driver"] = self.storage_driver

                if validate(self.storage_opts):
                    """
                    # TODO
                    #  validate storage_opts
                    # -> https://docs.docker.com/engine/reference/commandline/dockerd/#options-per-storage-driver
                    # Options for
                    #   - devicemapper are prefixed with dm
                    #   - zfs start with zfs
                    #   - btrfs start with btrfs
                    #   - overlay2 start with ...
                    """
                    data["storage-opts"] = self.storage_opts

        if self.tls_ca_cert and self.tls_cert and self.tls_key:
            """
            """
            data["tls"] = True

            if validate(self.tls_verify):
                data["tlsverify"] = self.tls_verify

            if validate(self.tls_ca_cert):
                data["tlscacert"] = self.tls_ca_cert

            if validate(self.tls_cert):
                data["tlscert"] = self.tls_cert

            if validate(self.tls_key):
                data["tlskey"] = self.tls_key

        return data

    def create_diff(self, config_file, data):
        """
        """
        old_data = dict()

        if os.path.isfile(config_file):
            with open(config_file) as json_file:
                old_data = json.load(json_file)

        side_by_side = SideBySide(self.module, old_data, data)
        diff_side_by_side = side_by_side.diff(width=140, left_title="  Original", right_title= "  Update")

        return diff_side_by_side

    def __values_as_string(self, values):
        """
        """
        result = {}
        # self.module.log(msg=f"{json.dumps(values, indent=2, sort_keys=False)}")

        if isinstance(values, dict):
            for k, v in sorted(values.items()):
                if isinstance(v, bool):
                    v = str(v).lower()
                result[k] = str(v)

        # self.module.log(msg=f"{json.dumps(result, indent=2, sort_keys=False)}")

        return result

    def __docker_client(self):
        """
        """
        docker_status = False
        docker_socket = "/var/run/docker.sock"
        # TODO
        # with broken ~/.docker/daemon.json will this fail!
        try:
            if os.path.exists(docker_socket):
                # self.module.log("use docker.sock")
                self.docker_client = docker.DockerClient(base_url=f"unix://{docker_socket}")
            else:
                self.docker_client = docker.from_env()

            docker_status = self.docker_client.ping()
        except docker.errors.APIError as e:
            self.module.log(
                msg=f" exception: {e}"
            )
        except Exception as e:
            self.module.log(
                msg=f" exception: {e}"
            )

        if not docker_status:
            return dict(
                changed = False,
                failed = True,
                msg = "no running docker found"
            )

    def __check_plugin(self):
        """
        """
        installed_plugin_name = None
        installed_plugin_shortname = None
        installed_plugin_version = None
        installed_plugin_enabled = None

        plugin_valid = False

        msg = f"plugin {self.log_driver} ist not installed"

        try:
            p_list = self.docker_client.plugins.list()

            for plugin in p_list:

                installed_plugin_enabled = plugin.enabled

                if installed_plugin_enabled:
                    installed_plugin_name = plugin.name
                    installed_plugin_shortname = plugin.name.split(':')[0]
                    installed_plugin_version = plugin.name.split(':')[1]

                    break

        except docker.errors.APIError as e:
            error = str(e)
            self.module.log(msg=f"{error}")

        except Exception as e:
            error = str(e)
            self.module.log(msg=f"{error}")

        if installed_plugin_name and installed_plugin_version:
            msg  = f"plugin {installed_plugin_shortname} is installed in version '{installed_plugin_version}'"

            if self.log_driver == installed_plugin_name:
                plugin_valid = True
            else:
                plugin_valid = False
                msg += ", but versions are not equal!"

            return plugin_valid, msg
        else:
            return plugin_valid, msg


# ---------------------------------------------------------------------------------------
# Module execution.
#


def main():

    args = dict(
        state = dict(
            default="present",
            choices=[
                "absent",
                "present"
            ]
        ),
        diff_output = dict(
            required=False,
            type='bool',
            default=False
        ),
        #
        authorization_plugins = dict(required=False, type='list'),
        bip = dict(required=False, type='str'),
        bridge = dict(required=False, type='str'),
        data_root = dict(required=False, type='str'),
        debug = dict(required=False, type="bool", default=False),
        default_gateway = dict(required=False, type='str'),
        default_gateway_v6 = dict(required=False, type='str'),
        default_shm_size = dict(required=False, type='str'),
        default_ulimits = dict(required=False, type='dict'),
        dns = dict(required=False, type='list'),
        dns_opts = dict(required=False, type='list'),
        dns_search = dict(required=False, type='list'),
        experimental = dict(required=False, type="bool", default=False),
        fixed_cidr = dict(required=False, type='str'),
        fixed_cidr_v6 = dict(required=False, type='str'),
        group = dict(required=False, type='str'),
        hosts = dict(required=False, type='list'),
        insecure_registries = dict(required=False, type='list'),
        ip = dict(required=False, type='str'),
        ip_forward = dict(required=False, type='bool'),
        ip_masq = dict(required=False, type='bool'),
        iptables = dict(required=False, type='bool'),
        ip6tables = dict(required=False, type='bool'),
        ipv6 = dict(required=False, type='bool'),
        labels = dict(required=False, type='list'),
        log_driver = dict(required=False, type='str'),
        log_level = dict(required=False, type='str'),
        log_opts = dict(required=False, type='dict'),
        max_concurrent_downloads = dict(required=False, type="int"),
        max_concurrent_uploads = dict(required=False, type='int'),
        max_download_attempts = dict(required=False, type='int'),
        metrics_addr = dict(required=False, type='str'),
        oom_score_adjust = dict(required=False, type='int'),
        pidfile = dict(required=False, type="str"),
        raw_logs = dict(required=False, type='bool'),
        registry_mirrors = dict(required=False, type='list'),
        seccomp_profile = dict(required=False, type='str'),
        selinux_enabled = dict(required=False, type="bool", default=False),
        shutdown_timeout = dict(required=False, type='int'),
        storage_driver = dict(required=False, type='str'),
        storage_opts = dict(required=False, type='list'),
        tls_ca_cert = dict(required=False, type='str'),
        tls_cert = dict(required=False, type='str'),
        tls_key = dict(required=False, type='str'),
        tls_verify = dict(required=False, type="bool", default=False),
    )

    module = AnsibleModule(
        argument_spec = args,
        supports_check_mode = True,
    )

    dcc = DockerCommonConfig(module)
    result = dcc.run()

    module.exit_json(**result)


# import module snippets
if __name__ == '__main__':
    main()


"""
{
  "allow-nondistributable-artifacts": [],
  "api-cors-header": "",
  "authorization-plugins": [],
  "bip": "",
  "bridge": "",
  "cgroup-parent": "",
  "cluster-advertise": "",
  "cluster-store": "",
  "cluster-store-opts": {},
  "containerd": "/run/containerd/containerd.sock",
  "containerd-namespace": "docker",
  "containerd-plugin-namespace": "docker-plugins",
  "data-root": "",
  "debug": true,
  "default-address-pools": [
    {
      "base": "172.30.0.0/16",
      "size": 24
    },
    {
      "base": "172.31.0.0/16",
      "size": 24
    }
  ],
  "default-cgroupns-mode": "private",
  "default-gateway": "",
  "default-gateway-v6": "",
  "default-runtime": "runc",
  "default-shm-size": "64M",
  "default-ulimits": {
    "nofile": {
      "Hard": 64000,
      "Name": "nofile",
      "Soft": 64000
    }
  },
  "dns": [],
  "dns-opts": [],
  "dns-search": [],
  "exec-opts": [],
  "exec-root": "",
  "experimental": false,
  "features": {},
  "fixed-cidr": "",
  "fixed-cidr-v6": "",
  "group": "",
  "hosts": [],
  "icc": false,
  "init": false,
  "init-path": "/usr/libexec/docker-init",
  "insecure-registries": [],
  "ip": "0.0.0.0",
  "ip-forward": false,
  "ip-masq": false,
  "iptables": false,
  "ip6tables": false,
  "ipv6": false,
  "labels": [],
  "live-restore": true,
  "log-driver": "json-file",
  "log-level": "",
  "log-opts": {
    "cache-disabled": "false",
    "cache-max-file": "5",
    "cache-max-size": "20m",
    "cache-compress": "true",
    "env": "os,customer",
    "labels": "somelabel",
    "max-file": "5",
    "max-size": "10m"
  },
  "max-concurrent-downloads": 3,
  "max-concurrent-uploads": 5,
  "max-download-attempts": 5,
  "mtu": 0,
  "no-new-privileges": false,
  "node-generic-resources": [
    "NVIDIA-GPU=UUID1",
    "NVIDIA-GPU=UUID2"
  ],
  "oom-score-adjust": -500,
  "pidfile": "",
  "raw-logs": false,
  "registry-mirrors": [],
  "runtimes": {
    "cc-runtime": {
      "path": "/usr/bin/cc-runtime"
    },
    "custom": {
      "path": "/usr/local/bin/my-runc-replacement",
      "runtimeArgs": [
        "--debug"
      ]
    }
  },
  "seccomp-profile": "",
  "selinux-enabled": false,
  "shutdown-timeout": 15,
  "storage-driver": "",
  "storage-opts": [],
  "swarm-default-advertise-addr": "",
  "tls": true,
  "tlscacert": "",
  "tlscert": "",
  "tlskey": "",
  "tlsverify": true,
  "userland-proxy": false,
  "userland-proxy-path": "/usr/libexec/docker-proxy",
  "userns-remap": ""
}
"""
