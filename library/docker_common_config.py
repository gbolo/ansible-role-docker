#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# (c) 2020-2022, Bodo Schulz <bodo@boone-schulz.de>
# BSD 2-clause (see LICENSE or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import absolute_import, division, print_function
import os
import json
import hashlib

import difflib
import itertools
import textwrap
import typing
import docker

from pathlib import Path
from ansible.module_utils.basic import AnsibleModule

__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '0.1',
    'status': ['preview'],
    'supported_by': 'community'
}

# ---------------------------------------------------------------------------------------


class SideBySide:
    """
      -> https://gist.github.com/jlumbroso/3ef433b4402b4f157728920a66cc15ed
    """

    def __init__(self, module, left, right):
        """
          Initialize all needed Variables
        """
        self.module = module

        if isinstance(left, dict):
            left = json.dumps(left, indent=2)

        if isinstance(right, dict):
            right = json.dumps(right, indent=2)

        if isinstance(left, str):
            left = left.split("\n")

        if isinstance(right, str):
            right = right.split("\n")

        self.left        = left
        self.right       = right
        self.width       = 140
        self.as_string   = True
        self.left_title  = "  Original"
        self.right_title = "  Update"

    def side_by_side(self,
                     left: typing.List[str],
                     right: typing.List[str],
                     width: int = 78,
                     as_string: bool = False,
                     separator: typing.Optional[str] = None,
                     left_title: typing.Optional[str] = None,
                     right_title: typing.Optional[str] = None,
                     ) -> typing.Union[str, typing.List[str]]:
        """
            Returns either the list of lines, or string of lines, that results from
            merging the two lists side-by-side.

            :param left: Lines of text to place on the left side
            :type left: typing.List[str]
            :param right: Lines of text to place on the right side
            :type right: typing.List[str]
            :param width: Character width of the overall output, defaults to 78
            :type width: int, optional
            :param as_string: Whether to return a string (as opposed to a list of strings), defaults to False
            :type as_string: bool, optional
            :param separator: String separating the left and right side, defaults to " | "
            :type separator: typing.Optional[str], optional
            :param left_title: Title to place on the left side, defaults to None
            :type left_title: typing.Optional[str], optional
            :param right_title: Title to place on the right side, defaults to None
            :type right_title: typing.Optional[str], optional
            :return: Lines or text of the merged side-by-side output.
            :rtype: typing.Union[str, typing.List[str]]
        """

        DEFAULT_SEPARATOR = " | "
        separator = separator or DEFAULT_SEPARATOR

        mid_width = (width - len(separator) - (1 - width % 2)) // 2

        tw = textwrap.TextWrapper(
            width=mid_width,
            break_long_words=False,
            replace_whitespace=False
        )

        def reflow(lines):
            wrapped_lines = list(map(tw.wrap, lines))
            wrapped_lines_with_linebreaks = [
                [""] if len(wls) == 0 else wls
                for wls in wrapped_lines
            ]
            return list(itertools.chain.from_iterable(wrapped_lines_with_linebreaks))

        left  = reflow(left)
        right = reflow(right)

        zip_pairs = itertools.zip_longest(left, right)

        if left_title is not None or right_title is not None:
            left_title = left_title or ""
            right_title = right_title or ""
            zip_pairs = [
                (left_title, right_title),
                (mid_width * "-", mid_width * "-")
            ] + list(zip_pairs)

        lines = []
        for left, right in zip_pairs:
            left = left or ""
            right = right or ""
            spaces = (" " * max(0, mid_width - len(left)))

            line = f"{left}{spaces}{separator}{right}"
            lines.append(line)

        if as_string:
            return "\n".join(lines)

        return lines

    def better_diff(self,
                    left: typing.List[str],
                    right: typing.List[str],
                    width: int = 78,
                    as_string: bool = False,
                    separator: typing.Optional[str] = None,
                    left_title: typing.Optional[str] = None,
                    right_title: typing.Optional[str] = None,
                    ) -> typing.Union[str, typing.List[str]]:
        """
            Returns a side-by-side comparison of the two provided inputs, showing
            common lines between both inputs, and the lines that are unique to each.

            :param left: Lines of text to place on the left side
            :type left: typing.List[str]
            :param right: Lines of text to place on the right side
            :type right: typing.List[str]
            :param width: Character width of the overall output, defaults to 78
            :type width: int, optional
            :param as_string: Whether to return a string (as opposed to a list of strings), defaults to False
            :type as_string: bool, optional
            :param separator: String separating the left and right side, defaults to " | "
            :type separator: typing.Optional[str], optional
            :param left_title: Title to place on the left side, defaults to None
            :type left_title: typing.Optional[str], optional
            :param right_title: Title to place on the right side, defaults to None
            :type right_title: typing.Optional[str], optional
            :return: Lines or text of the merged side-by-side diff comparison output.
            :rtype: typing.Union[str, typing.List[str]]
        """

        differ = difflib.Differ()

        left_side = []
        right_side = []

        if isinstance(left, str):
            left = left.split("\n")

        if isinstance(right, str):
            right = right.split("\n")

        # adapted from
        # LINK: https://stackoverflow.com/a/66091742/408734
        difflines = list(differ.compare(left, right))

        for line in difflines:
            """
            """
            op = line[0]
            tail = line[2:]

            if op == " ":
                # line is same in both
                left_side.append(f" {tail}")
                right_side.append(f" {tail}")

            elif op == "-":
                # line is only on the left
                left_side.append(f" {tail}")
                right_side.append("-")

            elif op == "+":
                # line is only on the right
                left_side.append("+")
                right_side.append(f" {tail}")

        return self.side_by_side(
            left=left_side,
            right=right_side,
            width=width,
            as_string=as_string,
            separator=separator,
            left_title=left_title,
            right_title=right_title,
        )

    def diff(self,
             width: int = 78,
             as_string: bool = False,
             separator: typing.Optional[str] = None,
             left_title: typing.Optional[str] = None,
             right_title: typing.Optional[str] = None,
             ) -> typing.Union[str, typing.List[str]]:
        """
        """
        return self.better_diff(self.left, self.right, width, as_string, separator, left_title, right_title)

# ---------------------------------------------------------------------------------------


class DockerCommonConfig(object):
    """
      Main Class to implement the Icinga2 API Client
    """
    module = None

    def __init__(self, module):
        """
          Initialize all needed Variables
        """
        self.module = module
        self.state = module.params.get("state")
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
        # self.config_checksum = "/etc/docker/.checksum"

        self.checksum_directory = f"{Path.home()}/.ansible/cache/docker"
        self.config_checksum = os.path.join(self.checksum_directory, "daemon.checksum")

    def run(self):
        """
            run
        """
        self.__create_directory(self.checksum_directory)

        if self.state == 'absent':
            """
                remove created files
            """
            if os.path.isfile(self.config_file):
                os.remove(self.config_file)

            if os.path.isfile(self.config_checksum):
                os.remove(self.config_checksum)

            return dict(
                changed = True,
                failed = False,
                msg = "config removed"
            )

        if not os.path.isfile(self.config_file):
            if os.path.isfile(self.config_checksum):
                os.remove(self.config_checksum)

        _old_checksum = None
        _data_changed = False
        _msg = "The configuration has not been changed."
        _diff = []

        self.__docker_client()

        data = dict()

        if self.__validate(self.authorization_plugins):
            data["authorization-plugins"] = self.authorization_plugins

        if self.__validate(self.bip):
            data["bip"] = self.bip

        if self.__validate(self.bridge):
            data["bridge"] = self.bridge

        if self.__validate(self.data_root):
            data["data-root"] = self.data_root

        if self.__validate(self.debug):
            data["debug"] = self.debug

        if self.__validate(self.default_gateway):
            data["default-gateway"] = self.default_gateway

        if self.__validate(self.default_gateway_v6):
            data["default-gateway-v6"] = self.default_gateway_v6

        if self.__validate(self.default_shm_size):
            data["default-shm-size"] = self.default_shm_size

        if self.__validate(self.default_ulimits):
            data["default-ulimits"] = self.default_ulimits

        if self.__validate(self.dns):
            data["dns"] = self.dns

        if self.__validate(self.dns_opts):
            data["dns-opts"] = self.dns_opts

        if self.__validate(self.dns_search):
            data["dns-search"] = self.dns_search

        if self.__validate(self.experimental):
            data["experimental"] = self.experimental

        if self.__validate(self.fixed_cidr):
            data["fixed-cidr"] = self.fixed_cidr

        if self.__validate(self.fixed_cidr_v6):
            data["fixed-cidr-v6"] = self.fixed_cidr_v6

        if self.__validate(self.group):
            data["group"] = self.group

        if self.__validate(self.hosts):
            data["hosts"] = self.hosts

        if self.__validate(self.insecure_registries):
            data["insecure-registries"] = self.insecure_registries

        if self.__validate(self.ip):
            data["ip"] = self.ip

        if self.__validate(self.ip_forward):
            data["ip-forward"] = self.ip_forward

        if self.__validate(self.ip_masq):
            data["ip-masq"] = self.ip_masq

        if self.__validate(self.iptables):
            data["iptables"] = self.iptables

        if self.__validate(self.ip6tables):
            data["ip6tables"] = self.ip6tables

        if self.__validate(self.ipv6):
            data["ipv6"] = self.ipv6

        if self.__validate(self.labels):
            data["labels"] = self.labels

        if self.__validate(self.log_level) and self.log_level in ["debug", "info", "warn", "error", "fatal"]:
            data["log-level"] = self.log_level

        if self.__validate(self.log_driver):
            if "loki" in self.log_driver:
                plugin_valid, plugin_state_message = self.__check_plugin()

                if not plugin_valid:
                    self.module.log(msg="ERROR: log_driver are not valid!")
                    self.module.log(msg=f"ERROR: {plugin_state_message}")
                    self.log_driver = "json-file"

            data["log-driver"] = self.log_driver

        if self.__validate(self.log_opts):
            data["log-opts"] = self.__values_as_string(self.log_opts)

        if self.__validate(self.max_concurrent_downloads):
            data["max-concurrent-downloads"] = self.max_concurrent_downloads

        if self.__validate(self.max_concurrent_uploads):
            data["max-concurrent-uploads"] = self.max_concurrent_uploads

        if self.__validate(self.max_download_attempts):
            data["max-download-attempts"] = self.max_download_attempts

        if self.__validate(self.metrics_addr):
            data["metrics-addr"] = self.metrics_addr
            data["experimental"] = True

        if self.__validate(self.oom_score_adjust):
            data["oom-score-adjust"] = self.oom_score_adjust

        if self.__validate(self.pidfile):
            data["pidfile"] = self.pidfile

        if self.__validate(self.raw_logs):
            data["raw-logs"] = self.raw_logs

        if self.__validate(self.registry_mirrors):
            data["registry-mirrors"] = self.registry_mirrors

        if self.__validate(self.seccomp_profile):
            data["seccomp-profile"] = self.seccomp_profile

        if self.__validate(self.selinux_enabled):
            data["selinux-enabled"] = self.selinux_enabled

        if self.__validate(self.shutdown_timeout):
            data["shutdown-timeout"] = self.shutdown_timeout

        if self.__validate(self.storage_driver):
            self.module.log(msg=f"  - {self.storage_driver}")
            self.module.log(msg=f"  - {self.storage_opts}")
            valid_storage_drivers = ["aufs", "devicemapper", "btrfs", "zfs", "overlay", "overlay2", "fuse-overlayfs"]
            if self.storage_driver in valid_storage_drivers:
                data["storage-driver"] = self.storage_driver

                if self.__validate(self.storage_opts):
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

            if self.__validate(self.tls_verify):
                data["tlsverify"] = self.tls_verify

            if self.__validate(self.tls_ca_cert):
                data["tlscacert"] = self.tls_ca_cert

            if self.__validate(self.tls_cert):
                data["tlscert"] = self.tls_cert

            if self.__validate(self.tls_key):
                data["tlskey"] = self.tls_key

        # create checksum of our data
        _checksum = self.__checksum(json.dumps(data, sort_keys=True))

        if os.path.isfile(self.config_checksum):
            with open(self.config_checksum, "r") as _sum:
                _old_checksum = _sum.readlines()[0]

        if not _old_checksum:
            """
            """
            difference = self.create_diff(self.config_file, data)

            self.__write_data(data, _checksum)

            _data_changed = True
            _msg = "The configuration has been created successfully."
            _diff = difference
        else:
            # compare both checksums
            if _old_checksum != _checksum:

                difference = self.create_diff(self.config_file, data)

                self.__write_data(data, _checksum)

                _data_changed = True
                _msg = "The configuration has been successfully updated."
                _diff = difference

        return dict(
            changed = _data_changed,
            failed = False,
            msg = _msg,
            diff = _diff
        )

    def create_diff(self, config_file, data):
        """
        """
        old_data = dict()

        if os.path.isfile(config_file):
            with open(config_file) as json_file:
                old_data = json.load(json_file)

        side_by_side = SideBySide(self.module, old_data, data)
        diff_side_by_side = side_by_side.diff(width=140, as_string=True, left_title="  Original", right_title= "  Update")

        return diff_side_by_side

    def __validate(self, value, default=None):
        """
        """
        if value:
            if isinstance(value, str) or isinstance(value, list) or isinstance(value, dict):
                if len(value) > 0:
                    return value

            if isinstance(value, int):
                return int(value)

            if isinstance(value, bool):
                return bool(value)

        return default

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

    def __checksum(self, plaintext):
        """
            create checksum from string
        """
        password_bytes = plaintext.encode('utf-8')
        password_hash = hashlib.sha256(password_bytes)
        checksum = password_hash.hexdigest()

        return checksum

    def __write_data(self, data, _checksum):
        """
        """
        with open(self.config_file, 'w') as fp:
            json.dump(data, fp, indent=2, sort_keys=False)

        with open(self.config_checksum, 'w') as fp:
            fp.write(_checksum)

    def __create_directory(self, dir):
        """
        """
        try:
            os.makedirs(dir, exist_ok=True)
        except FileExistsError:
            pass

        if os.path.isdir(dir):
            return True
        else:
            return False

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
    module = AnsibleModule(
        argument_spec = dict(
            state = dict(default="present", choices=["absent", "present"]),
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
        ),
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
