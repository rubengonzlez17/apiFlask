# -*- coding: iso-8859-1 -*-
from setuptools import setup

requirements = ['flask', 'flask_cors', 'requests', 'pymongo', 'celery', 'flask_mongoengine', 'mongoengine',
                'bs4', 'more-itertools']

setup(
    name='manager',
    version='',
    packages=[''],
    url='',
    license='',
    author='rubengonzlez17',
    author_email='',
    description='',
    entry_points={
        'console_scripts': [
            'manager=manager.run:main'
        ],
        'gui_scripts': [
        ],

    },
    install_requires=requirements
)
