#!/usr/bin/env python
# -*- coding: utf-8 -*-

# (c) 2020, Bodo Schulz <bodo@boone-schulz.de>
# BSD 2-clause (see LICENSE or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import absolute_import, division, print_function
import re
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

    def run(self):
        """
            run
        """
        docker_status = False
        try:
            client = docker.from_env()
            docker_status = client.ping()
        except Exception as e:
            self.module.log(
                msg=" exception: {} ({})".format(e, type(e))
            )

        if not docker_status:
            return dict(
                changed = False,
                failed = True,
                msg = "no running docker found"
            )

        state, message = self.check_plugin()

        if state:
            return dict(
                changed = False,
                msg = message
            )

        if(self.state == "absent"):
            return dict(
                changed = True,
                failed = False,
                msg = "plugin remove are not implemented yet"
            )

        args = ["docker"]
        args.append("plugin")
        args.append("install")
        args.append("{}:{}".format(self.plugin_source, self.plugin_version))
        args.append("--alias")
        args.append(self.plugin_alias)
        args.append("--grant-all-permissions")

        rc, out, err = self._exec(args)

        if rc == 0:
            return dict(
                changed = True,
                failed = False,
                msg = "plugin {} succesfull installed".format(self.plugin_alias)
            )
        else:
            return dict(
                changed = False,
                failed = True,
                error = err,
                msg = "plugin {} could not be installed".format(self.plugin_alias)
            )

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

                msg  = "plugin {} already in version '{}' installed".format(plugin, version)
                return True, msg

        msg = "plugin {} ist not installed".format(self.plugin_alias)
        return False, msg

    def _exec(self, cmd):
        """
        """
        self.module.log(msg="cmd: {}".format(cmd))

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
                choices=["absent", "present"]
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
