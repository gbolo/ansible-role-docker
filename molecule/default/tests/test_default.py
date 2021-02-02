
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
    pp.pprint(cwd)
    pp.pprint(os.listdir(cwd))

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

    # pp.pprint(" => '{}' / '{}'".format(base_dir, molecule_dir))

    file_defaults = "file={}/defaults/main.yml name=role_defaults".format(base_dir)
    file_vars = "file={}/vars/main.yml name=role_vars".format(base_dir)
    file_molecule = "file={}/group_vars/all/vars.yml name=test_vars".format(molecule_dir)

    # pp.pprint(file_defaults)
    # pp.pprint(file_vars)
    # pp.pprint(file_molecule)

    defaults_vars = host.ansible("include_vars", file_defaults).get("ansible_facts").get("role_defaults")
    vars_vars = host.ansible("include_vars", file_vars).get("ansible_facts").get("role_vars")
    molecule_vars = host.ansible("include_vars", file_molecule).get("ansible_facts").get("test_vars")

    ansible_vars = defaults_vars
    ansible_vars.update(vars_vars)
    ansible_vars.update(molecule_vars)

    templar = Templar(loader=DataLoader(), variables=ansible_vars)
    result = templar.template(ansible_vars, fail_on_undefined=False)

    return result


def test_user(host, get_vars):
    user_name = get_vars.get('acme_sh_become_user')

    assert host.group(user_name).exists
    assert host.user(user_name).exists
    assert user_name in host.user(user_name).groups


@pytest.mark.parametrize("dirs", [
    "/etc/ssl/ansible",
    "/srv/www/letsencrypt/.well-known/acme-challenge"
])
def test_directories(host, dirs):

    d = host.file(dirs)
    assert d.is_directory
    assert d.exists


def test_files(host, get_vars):
    user_name = get_vars.get('acme_sh_become_user')

    file = "/var/lib/{user}/src/acme.sh/acme.sh".format(user=user_name)

    f = host.file(file)
    assert f.exists
    assert f.is_file
