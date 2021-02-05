
from ansible.parsing.dataloader import DataLoader
from ansible.template import Templar
import pytest
import os
import testinfra.utils.ansible_runner

import pprint
pp = pprint.PrettyPrinter()

testinfra_hosts = testinfra.utils.ansible_runner.AnsibleRunner(
    os.environ['MOLECULE_INVENTORY_FILE']).get_hosts('all')


def base_directory():
    cwd = os.getcwd()

    if('group_vars' in os.listdir(cwd)):
        directory = "../.."
        molecule_directory = "."
    else:
        directory = "."
        molecule_directory = "molecule/{}".format(os.environ.get('MOLECULE_SCENARIO_NAME'))

    return directory, molecule_directory


@pytest.fixture()
def get_vars(host):
    """

    """
    base_dir, molecule_dir = base_directory()

    file_defaults = "file={}/defaults/main.yml name=role_defaults".format(base_dir)
    file_vars = "file={}/vars/main.yml name=role_vars".format(base_dir)
    file_molecule = "file={}/group_vars/all/vars.yml name=test_vars".format(molecule_dir)

    defaults_vars = host.ansible("include_vars", file_defaults).get("ansible_facts").get("role_defaults")
    vars_vars = host.ansible("include_vars", file_vars).get("ansible_facts").get("role_vars")
    molecule_vars = host.ansible("include_vars", file_molecule).get("ansible_facts").get("test_vars")

    ansible_vars = defaults_vars
    ansible_vars.update(vars_vars)
    ansible_vars.update(molecule_vars)

    templar = Templar(loader=DataLoader(), variables=ansible_vars)
    result = templar.template(ansible_vars, fail_on_undefined=False)

    return result


@pytest.mark.parametrize("packages", [
    "iptables",
    "docker-ce",
])
def test_packages(host, packages):
    """
    """
    p = host.package(packages)
    assert p.is_installed


@pytest.mark.parametrize("dirs", [
    "/etc/docker",
])
def test_directories(host, dirs):

    d = host.file(dirs)
    assert d.is_directory
    assert d.exists


def test_listening_socket(host, get_vars):

    socket_name = get_vars.get('docker_service_socket')

    # for i in host.socket.get_listening_sockets():
    #     pp.pprint(i)

    socket = host.socket('unix://{}'.format(socket_name))

    assert socket.is_listening


def test_service_running_and_enabled(host):

    service = host.service('docker')
    assert service.is_running
    assert service.is_enabled
