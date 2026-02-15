from setuptools import setup
import os
from glob import glob
package_name = 'plantroid_neck'

setup(
    name=package_name,
    version='1.0.0',
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
    description="Package responsible for implementing the server that moves Plantroid's head up and down.",
    license='Apache License 2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': ["neck_server = plantroid_neck.NeckServoServer:main"
        ],
    },
)
