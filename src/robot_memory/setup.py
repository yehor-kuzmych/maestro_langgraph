from setuptools import setup
import os
from glob import glob

package_name = 'robot_memory'

setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', glob('launch/*launch.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Antonio Galiza Cerdeira Gonzalez',
    maintainer_email='antonio@mizuuchi.lab.tuat.ac.jp',
    description='TODO: Package description',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': ["memory_server = robot_memory.MemoryServer:main"
        ],
    },
)
