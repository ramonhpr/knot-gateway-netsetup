import os
from setuptools import setup, find_packages

# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


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
    extras_require={
        'dev': [
            'lockfile',
            'dbus-python',
            'pygobject',
            'python-daemon'
        ]
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Topic :: Utilities",
        "License :: OSI Approved :: Apache Software License",
    ],
)
