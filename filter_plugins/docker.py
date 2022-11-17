# python 3 headers, required if submitting to Ansible

from __future__ import (absolute_import, print_function)
__metaclass__ = type

from ansible.utils.display import Display

display = Display()


class FilterModule(object):
    """
        Ansible file jinja2 tests
    """

    def filters(self):
        return {
            'validate_log_driver': self.validate_log_driver,
        }

    def validate_log_driver(self, data):
        """
        """
        build_in_driver = [
            "awslogs", "fluentd", "gcplogs",
            "gelf", "journald", "json-file",
            "local", "logentries", "splunk",
            "syslog",
        ]

        log_driver = data.get("log_driver", None)

        if log_driver and log_driver not in build_in_driver:
            """
                custom plugin
            """
            if ":" not in log_driver:
                return dict(
                    valid = False,
                    msg = "The format for the desired log driver is wrong!\nPlease use the following format: $driver:$driver_version"
                )
            else:
                # plugin_name = log_driver.split(":")[0]
                plugin_version = log_driver.split(":")[1]

                if len(plugin_version) == 0:
                    return dict(
                        valid = False,
                        msg = "A plugin version is missing!\nPlease use the following format: $driver:$driver_version"
                    )

        return dict(
            valid = True,
            msg = "valid"
        )
