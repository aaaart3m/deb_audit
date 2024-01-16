import os
import re
import shutil
import sys
import subprocess

from tabulate import tabulate


def create_temporary_directory():
    try:
        os.mkdir('temp')
    except OSError as e:
        print(f"Failed to create folder: {e}")


def delete_temporary_directory():
    try:
        shutil.rmtree('temp')
    except FileNotFoundError:
        print("Folder not found")
    except Exception as e:
        print(f"Failed to delete folder: {e}")


def get_package_info(filepath: str):
    try:
        dpkg_deb = ['dpkg-deb', '-R', filepath, './temp']
        subprocess.run(dpkg_deb, check=True, capture_output=True, text=True)
        package_info_filename = './temp/DEBIAN/control'

        with open(package_info_filename, 'r') as info_file:
            info_file_content = info_file.read()
            package_info = {
                key.strip(): value.strip()
                for element in info_file_content.split('\n')
                if ':' in element
                for key, value in [element.split(':', 1)]
            }

        # print(f'Get package info:\n {package_info}')
        return package_info
    except subprocess.CalledProcessError as sp_called_error:
        print('incorrect request', sp_called_error)


def get_dependency_info_tuple(dependency: str) -> tuple:
    dependency_tuple = dependency.strip().split('(', 1)
    if len(dependency_tuple) < 2:
        dependency_tuple.append('0')
    dependency_info_tuple = (dependency_tuple[0].strip(), re.search(r'\d[^)]*', dependency_tuple[1]).group(0))
    return dependency_info_tuple


def get_direct_components(package_info: dict) -> dict:
    direct_components = dict()
    # direct_components[package_info['Package']] = package_info['Version']
    components = package_info['Depends'].split(',')

    for dependency in components:

        if '|' in dependency:
            alternative_components = dependency.strip().split('|')
            for component in alternative_components:
                dependency_tuple = get_dependency_info_tuple(component)
                direct_components[dependency_tuple[0]] = dependency_tuple[1]
        else:
            dependency_tuple = get_dependency_info_tuple(dependency)
            direct_components[dependency_tuple[0]] = dependency_tuple[1]

        # if len(dependency_tuple) == 2:
        #     direct_components[dependency_tuple[0].strip()] = re.search(r'\d[^)]*', dependency_tuple[1]).group(0)
        #     # direct_components[dependency_tuple[0].strip()] = dependency_tuple[1].strip().split(' ')[1][:-1]
        # else:
        #     direct_components[dependency_tuple[0].strip()] = None
    # print(f'Get direct components:\n {direct_components}')
    return direct_components


def _get_dependency_version_in_repo(utility: str):
    apt_show = ['apt-cache', 'show', utility]
    apt_info = subprocess.run(apt_show, check=True, capture_output=True, text=True)
    apt_info_dict = {
        key.strip(): value.strip()
        for line in apt_info.stdout.split('\n')
        if ':' in line
        for key, value in [line.split(':', 1)]
    }
    # print(f'Apt show {apt_info_dict}')
    return apt_info_dict['Version']


def get_transitive_components(direct_components: dict) -> dict:
    transitive_components = dict()
    for dependency in list(direct_components):
        apt_rdepends = ['apt-rdepends', dependency]
        apt_info = subprocess.run(apt_rdepends, check=True, capture_output=True, text=True)
        # print(f'Transitive for {dependency}:\n', apt_info.stdout.split('\n')[3:-1])
        depend_info = dict()
        for line in apt_info.stdout.split('\n')[:-1]:
            if 'Depends:' not in line:
                try:
                    depend_info[line.strip()] = _get_dependency_version_in_repo(line.strip())
                except KeyError:
                    continue
        # depend_info = {
        #     line.strip(): _get_dependency_version_in_repo(line.strip())
        #     for line in apt_info.stdout.split('\n')[:-1]
        #     if 'Depends:' not in line
        # }
        # print(f'{dependency} dependencies:\n {depend_info}')
        transitive_components[dependency] = depend_info
    # print(f'Get transitive dependencies:\n {transitive_components}')
    return transitive_components


def _all_utilities_in_system():
    dpkg_w = ['dpkg-query', '-W']
    return subprocess.run(dpkg_w, check=True, capture_output=True, text=True).stdout.split('\n')


def _system_states_difference(first_state, second_state, architecture):
    difference = [line.strip() for line in second_state if line not in first_state]

    # difference_dict = dict()
    # for line in difference:
    #     if ':arm64' in line:
    #         difference_dict[line.split(':arm64')[0]] = line.split(':arm64')[1].split()[-1].strip()
    #     else:
    #         difference_dict[line.split()[0]] = line.split()[-1].strip()
    difference_utilities = set()
    for line in difference:
        if ':arm64' in line:
            difference_utilities.add(f'{line.split(":arm64")[0]} '
                                     f'{line.split(":arm64")[1].split()[-1].strip()} '
                                     f'{architecture}')
        elif ':amd64' in line:
            difference_utilities.add(f'{line.split(":amd64")[0]} '
                                     f'{line.split(":amd64")[1].split()[-1].strip()} '
                                     f'{architecture}')
        else:
            difference_utilities.add(f'{line.split()[0]} '
                                     f'{line.split()[-1].strip()} '
                                     f'{architecture}')
    return difference_utilities


def check_diff_after_install(deb_file: str, architecture: str):
    if os.path.isfile(deb_file):
        # print(f"{filepath} is file")
        try:
            system_before_installing = _all_utilities_in_system()
            # print('before: ', len(system_before_installing))
            # print('===========')

            apt_get_install = ['apt-get', 'install', '-f', '-y', deb_file]
            subprocess.run(apt_get_install, check=True, capture_output=True, text=True)
            system_after_installing = _all_utilities_in_system()
            # print('after: ', len(system_after_installing))
            # print('===========')

            # uname_m = ['uname', '-m']
            # architecture = subprocess.run(uname_m, check=True, capture_output=True, text=True).stdout
            difference_utilities = _system_states_difference(
                first_state=system_before_installing,
                second_state=system_after_installing,
                architecture=architecture)
            return difference_utilities
        except subprocess.CalledProcessError as sp_called_error:
            print('incorrect request', sp_called_error)
            print("Return Code:", sp_called_error.returncode)
            print("Output:", sp_called_error.output)
            print("Error output:", sp_called_error.stderr)
    else:
        print(f"File '{deb_file}' not found.")


def parse_to_vulners_input_format(transitive_components: dict, architecture: str):
    vulners_input_format_components = set()
    # print(transitive_components)
    for component in transitive_components.values():
        for utility, version in component.items():
            vulners_input_format_components.add(f'{utility} {version} {architecture}')
    return list(vulners_input_format_components)


def debsecan_scanning() -> dict:
    debsecan_output = subprocess.run('debsecan', check=True, capture_output=True, text=True).stdout.split('\n')[:-1]
    cve_dict = dict()

    for line in debsecan_output:
        parts = line.split()
        cve = parts[0]
        utility = parts[1]

        if utility in cve_dict:
            cve_dict[utility].append(cve)
        else:
            cve_dict[utility] = [cve]

    return cve_dict


def check_vulnerability_in_dependencies(dependencies):
    cve_dict = debsecan_scanning()
    utilities_from_dependencies = [line.split()[0] for line in dependencies]
    utilities_from_debsecan = list(cve_dict.keys())

    for utility in utilities_from_debsecan:
        if utility not in utilities_from_dependencies:
            cve_dict.pop(utility)

    table_data = [(utility, '\n'.join(cve_list)) for utility, cve_list in cve_dict.items()]

    return table_data


def main(deb_file: str):
    try:
        create_temporary_directory()
        package_info = get_package_info(deb_file)
        print("Package manifest json:\n", package_info)
        direct_dependencies = get_direct_components(package_info)
        # print("direct: ", direct_dependencies)
        transitive_dependencies = get_transitive_components(direct_dependencies)
        # print("transitive: ", transitive_dependencies)
        architecture = package_info['Architecture']
        if package_info['Architecture'] == 'all':
            architecture = 'amd64'
        deps_from_file = parse_to_vulners_input_format(transitive_dependencies, architecture=architecture)
        print("=======================\ndependencies from file:")
        print(*deps_from_file, sep='\n')

        # print('\n'.join(check_diff_after_install(filepath)))
        print('===============================\ndependencies from installation:')
        system_before_installation = _all_utilities_in_system()
        try:
            deps_from_install = list(check_diff_after_install(deb_file, architecture=architecture))
        except TypeError as te:
            print(f"Installation was failed: {te}")
            system_after_fail_installation = _all_utilities_in_system()
            deps_from_install = list(_system_states_difference(
                first_state=system_before_installation,
                second_state=system_after_fail_installation,
                architecture=architecture))

        print(*deps_from_install, sep='\n')
        all_dependencies = set(deps_from_install + deps_from_file)
        print('===================\ntotal dependencies:')
        print(*all_dependencies, sep='\n')

        table_data = check_vulnerability_in_dependencies(all_dependencies)
        table = tabulate(tabular_data=table_data, headers=['Utility', 'CVE'], tablefmt='simple_grid')
        print('================================\nvulnerabilities in dependencies:')
        print(table)
        delete_temporary_directory()
    except KeyError as ke:
        print(f'Scan executed with error: {ke}')


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python main.py <path/to/file>")
    else:
        path_to_deb_file = sys.argv[1]
        main(path_to_deb_file)
