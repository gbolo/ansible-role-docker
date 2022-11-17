#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# (c) 2020, Bodo Schulz <bodo@boone-schulz.de>
# BSD 2-clause (see LICENSE or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import absolute_import, division, print_function
import os
import json
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


class DockerPlugins():
    """
      Main Class to implement the installation of docker plugins
    """
    module = None

    def __init__(self, module):
        """
          Initialize all needed Variables
        """
        self.module = module
        self.state = module.params.get("state")
        #
        self.plugin_source = module.params.get("plugin_source")
        self.plugin_version = module.params.get("plugin_version")
        self.plugin_alias = module.params.get("plugin_alias")

        self.checksum_directory = f"{Path.home()}/.ansible/cache/docker"
        self.plugin_information_file = os.path.join(self.checksum_directory, f"plugin_{self.plugin_alias}")

        self.docker_socket = "/var/run/docker.sock"

    def run(self):
        """
            run
        """
        docker_status = False
        # TODO
        # with broken ~/.docker/daemon.json will this fail!
        try:
            if os.path.exists(self.docker_socket):
                # self.module.log("use docker.sock")
                self.docker_client = docker.DockerClient(base_url=f"unix://{self.docker_socket}")
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

        self.__create_directory(self.checksum_directory)

        self.plugin_state, self.plugin_version_equal, plugin_state_message = self.check_plugin()

        if self.state == "test":
            """
            """
            return dict(
                changed = False,
                installed = self.plugin_state,
                equal_versions = self.plugin_version_equal,
                msg = plugin_state_message
            )

        if self.state == "absent":
            return self.uninstall_plugin()

        return self.install_plugin()

    def check_plugin(self):
        """
        """
        installed_plugin_name = None
        installed_plugin_shortname = None
        installed_plugin_version = None
        installed_plugin_id = None
        installed_plugin_enabled = None

        equal_versions = True

        msg = f"plugin {self.plugin_alias} ist not installed"

        try:
            p_list = self.docker_client.plugins.list()

            for plugin in p_list:
                installed_plugin_enabled = plugin.enabled

                if installed_plugin_enabled:
                    installed_plugin_name = plugin.name
                    installed_plugin_shortname = plugin.name.split(':')[0]
                    installed_plugin_version = plugin.name.split(':')[1]
                    installed_plugin_id = plugin.short_id

                    break

        except docker.errors.APIError as e:
            error = str(e)
            self.module.log(msg=f"{error}")

        except Exception as e:
            error = str(e)
            self.module.log(msg=f"{error}")

        # self.module.log(msg=f"  name     : {installed_plugin_name}")
        # self.module.log(msg=f"  shortname: {installed_plugin_shortname}")
        # self.module.log(msg=f"  version  : {installed_plugin_version}")
        # self.module.log(msg=f"  id       : {installed_plugin_id}")
        # self.module.log(msg=f"  enabled  : {installed_plugin_enabled}")
        #
        # self.module.log(msg=f"  version wanted: {self.plugin_version}")

        self.installed_plugin_data = dict(
            id = installed_plugin_id,
            name = installed_plugin_name,
            short_name = installed_plugin_shortname,
            version = installed_plugin_version,
            enabled = installed_plugin_enabled
        )

        if installed_plugin_name and installed_plugin_version:
            msg  = f"plugin {installed_plugin_shortname} is installed in version '{installed_plugin_version}'"

            if self.plugin_version == installed_plugin_version:
                self.__write_plugin_information(self.installed_plugin_data)
            else:
                equal_versions = False
                msg += f", but versions are not equal! (your choise {self.plugin_version} vs. installed {installed_plugin_version})"

            return True, equal_versions, msg
        else:
            return False, False, msg

    def install_plugin(self):
        """
        """

        installed_plugin = self.installed_plugin_data.get('name', None)

        if not self.plugin_version_equal and installed_plugin:
            """
                disable old plugin
            """
            self.module.log(msg=f"disable other plugin version ({installed_plugin})")
            try:
                installed_plugin = self.docker_client.plugins.get(f"{installed_plugin}")

                if installed_plugin:
                    installed_plugin.disable(force=True)

            except docker.errors.APIError as e:
                error = str(e)
                self.module.log(msg=f"{error}")

            except Exception as e:
                error = str(e)
                self.module.log(msg=f"{error}")

        self.module.log(msg=f"test already installed plugin version ({self.plugin_alias}:{self.plugin_version})")

        try:
            installed_plugin = self.docker_client.plugins.get(f"{self.plugin_alias}:{self.plugin_version}")
        except docker.errors.APIError as e:
            error = str(e)
            self.module.log(msg=f"{error}")
            installed_plugin = None
            pass

        if installed_plugin:
            try:
                self.module.log(msg="re-enable plugin")
                installed_plugin.enable(timeout=10)
            except docker.errors.APIError as e:
                error = str(e)
                self.module.log(msg=f"{error}")
                pass

            try:
                self.module.log(msg="reload plugin attrs")
                installed_plugin.reload()
            except docker.errors.APIError as e:
                error = str(e)
                self.module.log(msg=f"{error}")
                pass

            result = dict(
                changed = True,
                failed = False,
                msg = f"plugin {self.plugin_alias} was successfully re-enabled in version {self.plugin_version}"
            )

        else:

            try:
                self.module.log(msg=f"install plugin in version {self.plugin_version}")

                plugin = self.docker_client.plugins.install(
                    remote_name=f"{self.plugin_source}:{self.plugin_version}",
                    local_name=f"{self.plugin_alias}:{self.plugin_version}")

                try:
                    self.module.log(msg="enable plugin")
                    plugin.enable(timeout=10)
                except docker.errors.APIError as e:
                    error = str(e)
                    self.module.log(msg=f"{error}")
                    pass

                try:
                    self.module.log(msg="reload plugin attrs")
                    plugin.reload()
                except docker.errors.APIError as e:
                    error = str(e)
                    self.module.log(msg=f"{error}")
                    pass

                installed_plugin_shortname = plugin.name.split(':')[0]
                installed_plugin_version = plugin.name.split(':')[1]

                result = dict(
                    changed = True,
                    failed = False,
                    msg = f"plugin {installed_plugin_shortname} was successfully installed in version {installed_plugin_version}"
                )

            except docker.errors.APIError as e:
                error = str(e)
                self.module.log(msg=f"{error}")

                result = dict(
                    changed = False,
                    failed = True,
                    msg = error
                )

            except Exception as e:
                error = str(e)
                self.module.log(msg=f"{error}")

                result = dict(
                    changed = False,
                    failed = True,
                    msg = error
                )

        return result

    def uninstall_plugin(self):
        """
        """
        installed_plugin = self.installed_plugin_data.get('name', None)

        if installed_plugin:
            """
                disable old plugin
            """
            try:
                installed_plugin = self.docker_client.plugins.get(f"{installed_plugin}")

                if installed_plugin:
                    self.module.log(msg=f"disable plugin version ({installed_plugin})")
                    installed_plugin.disable(force=True)

                    self.module.log(msg="remove plugin")
                    installed_plugin.remove(force=True)

                    self.__remove_plugin_information()

                result = dict(
                    changed = True,
                    failed = False,
                    msg = f"plugin {installed_plugin} was successfully removed."
                )

            except docker.errors.APIError as e:
                error = str(e)
                self.module.log(msg=f"{error}")

                result = dict(
                    changed = False,
                    failed = True,
                    msg = error
                )

            except Exception as e:
                error = str(e)
                self.module.log(msg=f"{error}")

                result = dict(
                    changed = False,
                    failed = True,
                    msg = error
                )
        else:
            result = dict(
                changed = False,
                failed = False,
                msg = "plugin is not installed."
            )

        return result

    def __write_plugin_information(self, data):
        """
        """
        self.module.log(msg=f"  write information to '{self.plugin_information_file}'")

        with open(self.plugin_information_file, 'w') as fp:
            json.dump(data, fp, indent=2, sort_keys=False)

    def __remove_plugin_information(self):
        """
        """
        if os.path.exists(self.plugin_information_file):
            os.remove(self.plugin_information_file)

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

# ---------------------------------------------------------------------------------------
# Module execution.
#


def main():
    module = AnsibleModule(
        argument_spec = dict(
            state = dict(
                default="present",
                choices=["absent", "present", "test"]
            ),
            #
            plugin_source = dict(
                required = True,
                type='str'
            ),
            plugin_version = dict(
                required = False,
                type="str",
                default = "latest"
            ),
            plugin_alias = dict(
                required = True,
                type='str'
            )

        ),
        supports_check_mode = True,
    )

    dp = DockerPlugins(module)
    result = dp.run()

    module.log(msg="= result: {}".format(result))

    module.exit_json(**result)


# import module snippets
if __name__ == '__main__':
    main()
