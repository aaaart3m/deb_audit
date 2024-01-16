# Package Vulnerability Scanner

This Python application is designed to scan Debian packages for potential vulnerabilities by analyzing their dependencies. It provides information about direct and transitive dependencies, checks for differences in the system state before and after installing the package, and identifies potential vulnerabilities using `debsecan`.

## Installation

1. Clone the repository:
    
    bashCopy code
    
    `git clone <repository-url>`
    
2. Change into the application directory:
    
    bashCopy code
    
    `cd <repository-directory>`
    
3. Build the Docker image:
    
    bashCopy code
    
    `docker build -t deb_scanner .`
    

## Usage

Run the Docker container with the Debian package file to perform the vulnerability scan:

bashCopy code

`docker run -it --name deb_audit --rm -v ./<package_name>.deb:/app/files/z<package_name>.deb deb_scanner /app/files/<package_name>.deb`

Replace `<package_name>.deb` with the actual name of your Debian package file.

## Dependencies

The application uses the following tools and libraries:

- `apt-rdepends`: To retrieve package dependencies.
- `dpkg-dev`: For extracting package information.
- `debsecan`: For scanning vulnerabilities.
- `tabulate`: For formatting the output in a tabular form.

## Main Script - `main.py`

The main script provides the following functionalities:

- **create_temporary_directory**: Creates a temporary directory named 'temp'.
- **delete_temporary_directory**: Deletes the temporary directory.
- **get_package_info(filepath: str)**: Retrieves information about the Debian package from the control file.
- **get_dependency_info_tuple(dependency: str) -> tuple**: Parses dependency information into a tuple.
- **get_direct_components(package_info: dict) -> dict**: Retrieves direct dependencies from the package information.
- **get_transitive_components(direct_components: dict) -> dict**: Retrieves transitive dependencies for each direct dependency.
- **check_diff_after_install(deb_file: str, architecture: str)**: Checks the system state difference before and after installing the Debian package.
- **parse_to_vulners_input_format(transitive_components: dict, architecture: str)**: Converts transitive dependencies into Vulners input format.
- **debsecan_scanning() -> dict**: Runs `debsecan` to obtain information about Common Vulnerabilities and Exposures (CVEs).
- **check_vulnerability_in_dependencies(dependencies)**: Checks for vulnerabilities in the provided dependencies.
- **main(deb_file: str)**: The main function orchestrating the entire scanning process.

## Note

Make sure to provide the path to the Debian package file as a command-line argument when running the application. If no argument is provided, a usage message will be displayed.

Feel free to customize the Dockerfile or the main script based on your specific requirements.
