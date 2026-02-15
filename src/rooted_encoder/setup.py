from setuptools import setup
from glob import glob

package_name = 'rooted_encoder'

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
    install_requires=['setuptools', 'numpy', 'dynamixel_sdk'],
    zip_safe=True,
    maintainer='Antonio Galiza Cerdeira Gonzalez',
    maintainer_email='antonio@mizuuchi.lab.tuat.ac.jp',
    description="ROOTED's servomotor interface package that implements speed control and the encoder.",
    license='Apache License 2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': ["encoder = rooted_encoder.encoder:main",
        ],
    },
)
