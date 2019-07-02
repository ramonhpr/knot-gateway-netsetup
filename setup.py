import os
from setuptools import setup, find_packages
from setuptools.command.develop import develop

# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


class PostInstall(develop):
    def run(self):
        develop.run(self)
        os.system('pre-commit install')

setup(
    name="netsetup",
    version="1.0",
    author="Vitor Barros",
    author_email="vba@cesar.org.br",
    description=("Netsetup Daemon"),
    license="Apache-2.0",
    keywords="daemon netsetup gateway iot bluetooth openthread",
    url="https://github.com/CESARBR/knot-gateway-netsetup",
    packages=find_packages(),
    long_description=read("README.md"),
    entry_points={
        "console_scripts": [
            "netsetup = netsetup.__main__:main"
        ]
    },
    cmdclass={'develop': PostInstall},
    extras_require={
        'dev': [
            'lockfile',
            'dbus-python',
            'pygobject',
            'python-daemon',
            'pylint',
            'pre-commit'
        ]
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Topic :: Utilities",
        "License :: OSI Approved :: Apache Software License",
    ],
)
