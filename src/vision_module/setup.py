from setuptools import setup
import os
from glob import glob

package_name = 'vision_module'

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
    install_requires=['setuptools', 'python-polylabel', 'opencv-python'],
    zip_safe=True,
    maintainer='Antonio Galiza Cerdeira Gonzalez',
    maintainer_email='antonio@mizuuchi.lab.tuat.ac.jp',
    description='Package related to Plantroid vision, implements functions of obtaining emotion estimation, detecting sunlight and shadow and labeling what the robot sees.',
    license='Apache License 2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': ["vision_server = vision_module.Vision:main", 
                            "fake_vision_server = vision_module.Vision_Fake:main"
        ],
    },
)
