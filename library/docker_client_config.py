#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# (c) 2020, Bodo Schulz <bodo@boone-schulz.de>
# BSD 2-clause (see LICENSE or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import absolute_import, division, print_function
import os
import json
import hashlib
import base64

from ansible.module_utils.basic import AnsibleModule

__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '0.1',
    'status': ['preview'],
    'supported_by': 'community'
}

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

        self.config_checksum = f"{self.dest}.checksum"
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
        if self.state == 'absent':
            """
                remove created files
            """

            config_file_exist = False
            config_checksum_exists = False
            msg = f"docker config {self.dest} not found"

            if os.path.isfile(self.dest):
                config_file_exist = True
                os.remove(self.dest)

                msg = f"docker config {self.dest} removed"

            if os.path.isfile(self.config_checksum):
                config_checksum_exists = True
                os.remove(self.config_checksum)

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

        invalid_authentications, authentications = self._handle_authentications()
        formats = self._handle_formats()

        _old_checksum = ''
        _data_changed = False

        data = {
            **authentications,
            **formats
        }

        _checksum = self.__checksum(json.dumps(data, sort_keys=True))

        if os.path.isfile(self.config_checksum):
            with open(self.config_checksum, "r") as _sum:
                _old_checksum = _sum.readlines()[0]

        # compare both checksums
        if _old_checksum != _checksum:
            with open(self.dest, 'w') as fp:
                json.dump(data, fp, indent=2, sort_keys=False)

            with open(self.config_checksum, 'w') as fp:
                fp.write(_checksum)

            _data_changed = True

        return dict(
            changed = _data_changed,
            failed = False,
            msg = f"docker config {self.dest} successfully created."
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
            if len(v) != 0:
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
            # message = auth
            # message_bytes = message.encode('utf8')
            # base64_bytes = base64.standard_b64decode(message_bytes)
            # base64_message = base64_bytes.decode('utf8')
            # self.module.log(msg=f" = {base64_message}")
            return auth

        d_bytes = f"{username}:{password}".encode('utf-8')

        base64_bytes = base64.standard_b64encode(d_bytes)
        base64_message = base64_bytes.decode('utf8')

        # self.module.log(msg=f" = {base64_message}")

        return base64_message

    def __checksum(self, plaintext):
        """
            create checksum from string
        """
        password_bytes = plaintext.encode('utf-8')
        password_hash = hashlib.sha256(password_bytes)
        checksum = password_hash.hexdigest()

        return checksum


# ---------------------------------------------------------------------------------------
# Module execution.
#

def main():
    module = AnsibleModule(
        argument_spec = dict(
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
        ),
        supports_check_mode = True,
    )

    dcc = DockerClientConfig(module)
    result = dcc.run()

    module.exit_json(**result)


# import module snippets
if __name__ == '__main__':
    main()
