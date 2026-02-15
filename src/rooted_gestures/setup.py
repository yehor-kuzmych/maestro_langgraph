from setuptools import setup
import os
from glob import glob

package_name = 'rooted_gestures'

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
    install_requires=['setuptools', 'rooted_encoder', 'plantroid_neck'],
    zip_safe=True,
    maintainer='Antonio Galiza Cerdeira Gonzalez',
    maintainer_email='antonio@mizuuchi.lab.tuat.ac.jp',
    description='Package responsible for implementing the body language commands of the robot, such as rotating the boddy  clock and cunter-clockwise when it says no, or shaking its head up and down when saying yes.',
    license='Apache License 2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': ["gesture_server = rooted_gestures.GestureServer:main"
        ],
    },
)
