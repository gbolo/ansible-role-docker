#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# (c) 2020-2023, Bodo Schulz <bodo@boone-schulz.de>
# BSD 2-clause (see LICENSE or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import absolute_import, division, print_function
import os
import shutil
import json
import base64
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.bodsch.core.plugins.module_utils.directory import create_directory
from ansible_collections.bodsch.core.plugins.module_utils.checksum import Checksum

__metaclass__ = type


"""
  creates an user configuration like this:

{
  "auths": {
    "registry.gitlab.com": {
        "auth": "amVua2luczpydWJiZWwtZGllLWthdHotZHUtZHVtbXNjaHfDpHR6ZXIxCg=="
    }
  },
  "psFormat": "table {{.ID}}:\\t{{.Names}}\\t{{.Status}}\\t{{.RunningFor}}\\t{{.Ports}}"",
  "imagesFormat": "table {{.ID}}\\t{{.Repository}}\\t{{.Tag}}\\t{{.CreatedAt}}"
}

"""


# ---------------------------------------------------------------------------------------


class DockerClientConfig(object):
    """
    """
    module = None

    def __init__(self, module):
        """
          Initialize all needed Variables
        """
        self.module = module
        self.state = module.params.get("state")
        self.dest = module.params.get("dest")
        self.auths = module.params.get("auths")
        self.formats = module.params.get("formats")
        pid = os.getpid()
        self.tmp_directory = os.path.join("/run/.ansible", f"docker_client_config.{str(pid)}")
        self.cache_directory = "/var/cache/ansible/docker"

        # TODO
        # maybe later?
        # valid_formate_entries = [
        #     '.ID', '.Repository', '.Tag', '.CreatedAt', '.Names', '.Image', '.Command', '.Labels',
        #     '.Status', '.RunningFor', '.Ports'
        # ]

    def run(self):
        """
            run
        """
        create_directory(self.cache_directory)

        self.checksum = Checksum(self.module)

        hashed_dest = self.checksum.checksum(self.dest)

        self.checksum_file_name = os.path.join(self.cache_directory, f"client_{hashed_dest}.checksum")

        if self.state == 'absent':
            """
                remove created files
            """
            config_file_exist = False
            config_checksum_exists = False
            msg = f"docker client config {self.dest} not found"

            if os.path.isfile(self.dest):
                config_file_exist = True
                os.remove(self.dest)

                msg = f"docker client config {self.dest} removed"

            if os.path.isfile(self.checksum_file_name):
                config_checksum_exists = True
                os.remove(self.checksum_file_name)

            return dict(
                changed = (config_file_exist & config_checksum_exists),
                failed = False,
                msg = msg
            )

        if not isinstance(self.auths, dict):
            return dict(
                changed = False,
                failed = True,
                msg = "'auths' must be an dictionary."
            )

        if not isinstance(self.formats, dict):
            return dict(
                changed = False,
                failed = True,
                msg = "'formats' must be an dictionary."
            )

        create_directory(directory=self.tmp_directory, mode="0750")

        if os.path.exists(self.checksum_file_name):
            os.remove(self.checksum_file_name)

        if not os.path.isfile(self.dest):
            """
                clean manual removements
            """
            if os.path.isfile(self.checksum_file_name):
                os.remove(self.checksum_file_name)

        invalid_authentications, authentications = self._handle_authentications()
        formats = self._handle_formats()

        data = {
            **authentications,
            **formats
        }

        tmp_file     = os.path.join(self.tmp_directory, f"client_{hashed_dest}")

        self.__write_config(tmp_file, data)
        new_checksum = self.checksum.checksum_from_file(tmp_file)
        old_checksum = self.checksum.checksum_from_file(self.dest)
        changed = not (new_checksum == old_checksum)

        self.module.log(f" changed       : {changed}")
        self.module.log(f" new_checksum  : {new_checksum}")
        self.module.log(f" old_checksum  : {old_checksum}")

        # changed, new_checksum, old_checksum = self.checksum.validate(self.checksum_file_name, data)

        if changed:
            self.__write_config(self.dest, data)
            # with open(self.dest, 'w') as fp:
            #     json_data = json.dumps(data, indent=2, sort_keys=False)
            #     fp.write(f'{json_data}\n')
            #
            # self.checksum.write_checksum(self.checksum_file_name, new_checksum)

        shutil.rmtree(self.tmp_directory)

        return dict(
            changed = changed,
            failed = False,
            msg = f"docker client config {self.dest} successfully created."
        )

    def _handle_authentications(self):
        """
          possible  values:
            auths:
              registry.gitlab.com:
                auth: amVua2luczpydWJiZWwtZGllLWthdHotZHUtZHVtbXNjaHfDpHR6ZXIxCg==
              registry.githu.com:
                user: foobar
                password: vaulted_freaking_password

        """
        invalid_authentications = []

        copy_auths = self.auths.copy()

        for k, v in self.auths.items():
            """
                filter broken configs
            """
            res = {}
            valide, validate_msg = self.__validate_auth(v)

            if not valide:
                copy_auths.pop(k)

                res[k] = dict(
                    failed = True,
                    state = validate_msg
                )

                invalid_authentications.append(res)

        auths_dict = {}

        for k, v in copy_auths.items():
            """
                Ensure that the auth string is a base64 encoded thing.
                the content of an existing base64 string is not checked here!
            """
            auths_dict[k] = dict(
                auth=self.__base64_auth(v)
            )

        return invalid_authentications, auths_dict

    def _handle_formats(self):
        """
          "psFormat": "table {{.ID}}\\t{{.Image}}\\t{{.Command}}\\t{{.Labels}}",
          "imagesFormat": "table {{.ID}}\\t{{.Repository}}\\t{{.Tag}}\\t{{.CreatedAt}}",
          "pluginsFormat": "table {{.ID}}\t{{.Name}}\t{{.Enabled}}",
          "statsFormat": "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}",
          "servicesFormat": "table {{.ID}}\t{{.Name}}\t{{.Mode}}",
          "secretFormat": "table {{.ID}}\t{{.Name}}\t{{.CreatedAt}}\t{{.UpdatedAt}}",
          "configFormat": "table {{.ID}}\t{{.Name}}\t{{.CreatedAt}}\t{{.UpdatedAt}}",
          "nodesFormat": "table {{.ID}}\t{{.Hostname}}\t{{.Availability}}",

          possible  values:
            formats:
              ps:
                - ".ID"
                - ".Names"
                - ".Status"
                - ".RunningFor"
                - ".Ports"
                - ".Image"
                - ".Command"
                - ".Labels"
              images:
                - ".ID"
                - ".Image"
                - ".Command"
                - ".Labels"
        """
        def __format_to_string(t):
            """
              input:
                images:
                  - ".ID"
                  - ".Image"
                  - ".Command"
                  - ".Labels"
              result:
                - 'imagesFormat': 'table {{.ID}}\\t{{.Repository}}\\t{{.Tag}}\\t{{.CreatedAt}}'
            """
            _result = "table "
            for i, item in enumerate(t):
                _result += "{{{{{0}}}}}".format(item)
                if not i == len(t) - 1:
                    _result += "\\t"

            return _result

        result = {}

        for k, v in self.formats.items():
            if k in ["ps", "images", "plugins", "stats", "services", "secret", "config", "nodes"] and len(v) != 0:
                result[f"{k}Format"] = __format_to_string(v)

        return result

    def __validate_auth(self, data):
        """
        """
        auth     = data.get("auth", None)
        username = data.get("username", None)
        password = data.get("password", None)

        return_result = False
        return_message = None

        if not auth and not username and not password:
            return_result = True
            return_message = "not authentication defined"

        if auth and (not username and not password):
            return_result = True
            return_message = "base64 authentication defined"

        if auth and (username and password):
            return_result = False
            return_message = "Only one variant can be defined!\nPlease choose between 'auth' or the combination of 'username' and 'password'!"

        if not auth and (not username or not password):
            return_result = False
            return_message = "Either the 'username' or the 'password' is missing!"

        if not auth and (username and password):
            return_result = True
            return_message = "combination of 'username' and 'password' authentication defined"

        return return_result, return_message

    def __base64_auth(self, data):
        """
        """
        auth     = data.get("auth", None)
        username = data.get("username", None)
        password = data.get("password", None)

        if auth:
            return auth

        d_bytes = f"{username}:{password}".encode('utf-8')

        base64_bytes = base64.standard_b64encode(d_bytes)
        base64_message = base64_bytes.decode('utf8')

        return base64_message

    def __write_config(self, file_name, data):
        """
        """
        with open(file_name, 'w') as fp:
            json_data = json.dumps(data, indent=2, sort_keys=False)
            fp.write(f'{json_data}\n')

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
        dest = dict(
            required=True,
            type="path"
        ),
        #
        auths = dict(
            required=False,
            type="dict"
        ),
        formats = dict(
            required=False,
            type="dict"
        )
    )

    module = AnsibleModule(
        argument_spec = args,
        supports_check_mode = True,
    )

    dcc = DockerClientConfig(module)
    result = dcc.run()

    module.log(msg=f"= result: {result}")

    module.exit_json(**result)


# import module snippets
if __name__ == '__main__':
    main()
