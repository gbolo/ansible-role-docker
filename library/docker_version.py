#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# (c) 2020, Bodo Schulz <bodo@boone-schulz.de>
# BSD 2-clause (see LICENSE or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import absolute_import, division, print_function
import os
import json
import docker

from ansible.module_utils.basic import AnsibleModule

__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '0.1',
    'status': ['preview'],
    'supported_by': 'community'
}

# ---------------------------------------------------------------------------------------


class DockerVersion():
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
        self.docker_socket = "/var/run/docker.sock"

    def run(self):
        """
            run
        """
        docker_status = False
        docker_version = None
        docker_versions = dict()

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

        docker_version = self.docker_client.version()

        # self.module.log(msg=f" = {json.dumps(docker_version, sort_keys=True)}")

        if docker_version:
            docker_versions.update({"api_version": docker_version.get("ApiVersion", None)})
            docker_versions.update({"docker_version": docker_version.get("Version", None)})

            self.module.log(msg=f" = {json.dumps(docker_versions, sort_keys=True)}")

        return dict(
            failed = False,
            changed = False,
            versions = docker_versions
        )


# ---------------------------------------------------------------------------------------
# Module execution.
#


def main():

    args = dict(
        state = dict(
            default="present",
            choices=[
                "absent",
                "present",
                "test"
            ]
        ),
    )

    module = AnsibleModule(
        argument_spec = args,
        supports_check_mode = True,
    )

    dp = DockerVersion(module)
    result = dp.run()

    module.log(msg=f"= result: {result}")

    module.exit_json(**result)


# import module snippets
if __name__ == '__main__':
    main()
