import os.path
import re

import setuptools


def get_version():
    # When some variables are defined in the init of a project, import of version.py can lead to circular
    # dependencies. As a workaround, this function reads the file version.py to get the package version.
    with open(os.path.join(os.path.dirname(__file__), 'canmonitor', 'version.py')) as f:
        regex = re.compile(r'^VERSION = ["\']([^"\']*)["\']$', re.MULTILINE)
        return regex.search(f.read()).group(1)


setuptools.setup(
    name="canmonitor",
    version=get_version(),
    description="Read CAN frames and display them in an easy-to-read table",
    packages=setuptools.find_packages(exclude=['tests*']),
    python_requires='>=3.8',
    entry_points={
        'console_scripts': [
            'canmonitor = canmonitor.canmonitor:run',
        ],
    },
    install_requires=[
        'setuptools>=45.0.0',
        'pyserial==3.2.1',
        'windows-curses>=2.4.0; sys_platform == "win32"',
    ],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Natural Language :: English",
        "Topic :: Scientific/Engineering :: Visualization",
        "Operating System :: POSIX :: Linux",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: MacOS",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    license="MIT",
    keywords=['can', 'can bus', 'automotive'],
)
