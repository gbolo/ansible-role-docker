#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# (c) 2020-2023, Bodo Schulz <bodo@boone-schulz.de>
# BSD 2-clause (see LICENSE or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import absolute_import, division, print_function
import os
import pwd
import grp
import shutil
import json
import base64
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.bodsch.core.plugins.module_utils.directory import create_directory
from ansible_collections.bodsch.core.plugins.module_utils.checksum import Checksum
from ansible_collections.bodsch.core.plugins.module_utils.module_results import results

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


class DockerClientConfigs(object):
    """
    """
    module = None

    def __init__(self, module):
        """
          Initialize all needed Variables
        """
        self.module = module
        self.configs = module.params.get("configs")
        pid = os.getpid()
        self.tmp_directory = os.path.join("/run/.ansible", f"docker_client_configs.{str(pid)}")
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
        create_directory(directory=self.tmp_directory, mode="0750")

        self.checksum = Checksum(self.module)

        result_state = []

        if isinstance(self.configs, list):
            """
            """
            for conf in self.configs:
                destination = conf.get("location", None)

                if destination:
                    res = {}
                    res[destination] = self.client(conf)

                    result_state.append(res)

        # define changed for the running tasks
        _state, _changed, _failed, state, changed, failed = results(self.module, result_state)

        result = dict(
            changed = _changed,
            failed = _failed,
            msg = result_state
        )

        shutil.rmtree(self.tmp_directory)

        return result

    def client(self, client_data):
        """
            {
                'location': '/root/.docker/config.json',
                'enabled': True,
                'auths': {
                    'registry.gitfoo.tld': {
                        'auth': 'amVua2luczpydWJiZWwtZGllLWthdHotZHUtZHVtbXNjaHfDpHR6ZXIxCg=='
                    },
                    'test.tld': {'username': 'FOO-was-sonst', 'passwort': 'ja-toll-schon-wieder-alles-scheisse!'}},
                'formats': {}
            }

        """
        destination = client_data.get("location", None)
        state = client_data.get("state", "present")
        auths = client_data.get("auths", {})
        formats = client_data.get("formats", {})
        enabled = client_data.get("enabled", True)
        owner = client_data.get("owner", None)
        group = client_data.get("group", None)
        mode = client_data.get("mode", "0644")

        location_directory = os.path.dirname(destination)

        hashed_dest = self.checksum.checksum(destination)
        # checksum_file is obsolete
        checksum_file_name = os.path.join(self.cache_directory, f"client_{hashed_dest}.checksum")

        if os.path.exists(checksum_file_name):
            os.remove(checksum_file_name)

        if state == 'absent':
            """
                remove created files
            """
            config_file_exist = False
            config_checksum_exists = False
            msg = "The Docker Client configuration does not exist."

            if os.path.isfile(destination):
                config_file_exist = True
                os.remove(destination)
                msg = "The Docker Client configuration has been removed."

            if os.path.isfile(checksum_file_name):
                config_checksum_exists = True
                os.remove(checksum_file_name)

            return dict(
                changed = (config_file_exist & config_checksum_exists),
                failed = False,
                msg = msg
            )

        if not enabled:
            msg = "The creation of the Docker Client configuration has been deactivated."

            if os.path.isfile(destination):
                msg += "\nBut the configuration file has already been created!\nTo finally remove it, the 'state' must be configured to 'absent'."

            return dict(
                failed=False,
                changed=False,
                msg=msg
            )

        if not destination:
            return dict(
                failed=True,
                msg="No location has been configured."
            )

        if state not in ["absent", "present"]:
            return dict(
                failed=True,
                msg=f"Wrong state '{state}'. Only these are supported: 'absent', 'present'."
            )

        if not isinstance(auths, dict):
            return dict(
                failed = True,
                msg = "'auths' must be an dictionary."
            )

        if not isinstance(formats, dict):
            return dict(
                failed = True,
                msg = "'formats' must be an dictionary."
            )

        # create destination directory
        create_directory(directory=location_directory, mode="0750", owner=owner, group=group)
        create_directory(directory=self.tmp_directory, mode="0750")

        if not os.path.isfile(destination):
            """
                clean manual removements
            """
            if os.path.isfile(checksum_file_name):
                os.remove(checksum_file_name)

        invalid_authentications, authentications = self._handle_authentications(auths)
        formats = self._handle_formats(formats)

        if len(invalid_authentications) > 0:
            return dict(
                failed = True,
                msg = invalid_authentications
            )

        data = {
            **authentications,
            **formats
        }

        tmp_file     = os.path.join(self.tmp_directory, f"client_{hashed_dest}")

        self.__write_config(tmp_file, data)
        new_checksum = self.checksum.checksum_from_file(tmp_file)
        old_checksum = self.checksum.checksum_from_file(destination)
        changed = not (new_checksum == old_checksum)
        new_file = False
        msg = "The Docker Client configuration has not been changed."

        if changed:
            new_file = (old_checksum is None)
            self.__write_config(destination, data)
            msg = "The Docker Client configuration was successfully changed."

        if new_file:
            msg = "The Docker Client configuration was successfully created."

        if os.path.isfile(destination):
            self.change_owner(destination, owner, group, mode)

        return dict(
            changed = changed,
            failed = False,
            msg = msg
        )

    def _handle_authentications(self, auths):
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

        copy_auths = auths.copy()

        for k, v in auths.items():
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

        auths_dict = dict()
        auths_dict["auths"] = dict()

        for k, v in copy_auths.items():
            """
                Ensure that the auth string is a base64 encoded thing.
                the content of an existing base64 string is not checked here!
            """
            auth = self.__base64_auth(v)
            auths_dict["auths"].update({
                k: {"auth": auth}
            })

        return invalid_authentications, auths_dict

    def _handle_formats(self, formats):
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

        for k, v in formats.items():
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

    def change_owner(self, destination, owner=None, group=None, mode=None):
        """
        """
        if mode is not None:
            os.chmod(destination, int(mode, base=8))

        if owner is not None:
            try:
                owner = pwd.getpwnam(owner).pw_uid
            except KeyError:
                owner = int(owner)
                pass
        else:
            owner = 0

        if group is not None:
            try:
                group = grp.getgrnam(group).gr_gid
            except KeyError:
                group = int(group)
                pass
        else:
            group = 0

        if os.path.exists(destination) and owner and group:
            os.chown(destination, int(owner), int(group))


# ---------------------------------------------------------------------------------------
# Module execution.
#


def main():

    args = dict(
        configs = dict(
            required=True,
            type=list
        )
    )

    module = AnsibleModule(
        argument_spec = args,
        supports_check_mode = True,
    )

    dcc = DockerClientConfigs(module)
    result = dcc.run()

    module.log(msg=f"= result: {result}")

    module.exit_json(**result)


# import module snippets
if __name__ == '__main__':
    main()
