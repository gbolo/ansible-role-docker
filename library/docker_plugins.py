#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# (c) 2020, Bodo Schulz <bodo@boone-schulz.de>
# BSD 2-clause (see LICENSE or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import absolute_import, division, print_function
import re
import os
import docker

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
                client = docker.DockerClient(base_url=f"unix://{self.docker_socket}")
            else:
                client = docker.from_env()

            docker_status = client.ping()
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

        state, message = self.check_plugin()

        if state or self.state == "test":
            return dict(
                changed = False,
                installed = True,
                msg = message
            )

        if self.state == "absent":
            return self.uninstall_plugin()

        return self.install_plugin()

    def check_plugin(self):
        """

        """
        args = ["docker"]
        args.append("plugin")
        args.append("ls")
        args.append("--format")
        args.append('"{{.Name}}"')

        rc, out, err = self._exec(args)

        # self.module.log(msg="  out: '{}' ({}) {}".format(out, type(out), len(out)))

        if len(out) > 0:
            """
            """
            pattern = re.compile(r'^"(?P<plugin>.*):(?P<version>.*)"$')

            match = re.search(pattern, out)

            if match:
                plugin = match.group("plugin")
                version = match.group("version")

                msg  = f"plugin {plugin} already in version '{version}' installed"
                return True, msg

        msg = f"plugin {self.plugin_alias} ist not installed"
        return False, msg

    def install_plugin(self):
        """
        """
        args = ["docker"]
        args.append("plugin")
        args.append("install")
        args.append(f"{self.plugin_source}:{self.plugin_version}")
        args.append("--alias")
        args.append(self.plugin_alias)
        args.append("--grant-all-permissions")

        rc, out, err = self._exec(args)

        if rc == 0:
            return dict(
                changed = True,
                failed = False,
                msg = f"plugin {self.plugin_alias} succesfull installed"
            )
        else:
            return dict(
                changed = False,
                failed = True,
                error = err,
                msg = f"plugin {self.plugin_alias} could not be installed"
            )

    def uninstall_plugin(self):
        """
        """

        return dict(
            changed=True,
            failed=False,
            msg="plugin remove are not implemented yet"
        )

    def _exec(self, cmd):
        """
        """
        self.module.log(msg=f"cmd: {cmd}")

        rc, out, err = self.module.run_command(cmd, check_rc=True)
        # self.module.log(msg="  rc : '{}'".format(rc))
        # self.module.log(msg="  out: '{}' ({}) {}".format(out, type(out), len(out)))
        # self.module.log(msg="  err: '{}'".format(err))
        return rc, out, err

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
