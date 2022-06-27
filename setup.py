import re
import subprocess

import setuptools

VERSION = "v0.0.1",
BRANCH = "master"

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

def requirements():
    """Build the requirements list for this project."""
    requirements_list = []

    with open('requirements.txt') as requirements:
        for install in requirements:
            requirements_list.append(install.strip())
    return requirements_list

def exec(cmd):
    """Execute a command and return the output."""
    return subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True).decode().strip()

def git_version_tag():
    """Get the current git version tag."""
    try:
        branch = exec("git rev-parse --abbrev-ref HEAD")
        version = re.match(r"^v[0-9]+(\.[0-9]+)*$", exec("git describe --tags --abbrev=0"))
    except subprocess.CalledProcessError:
        branch = BRANCH
        version = VERSION
    if branch == BRANCH and version:
        return version[0][1:]
    else:
        return VERSION

requirements = requirements()

VERSION = git_version_tag()
print(f"BUILDING Version: {VERSION}")

setuptools.setup(
    name="gdrepl",
    version=VERSION,
    author="Matheus Fillipe",
    author_email="mattf@tilde.club",
    description="Proof of concept repl for godot's gdscript",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/matheusfillipe/GDScript-REPL",
    py_modules=["gdrepl"],
    entry_points={
        'console_scripts': [
            'gdrepl = gdrepl.main:cli',
        ],
    },
    packages=setuptools.find_packages(),
    include_package_data=True,
    install_requires=requirements,
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)
