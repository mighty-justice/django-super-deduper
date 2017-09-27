from setuptools import find_packages, setup

if __name__ == '__main__':
    with open('requirements.txt') as requirements:
        setup(
            name='django-super-deduper',
            description='Utilities for deduping Django model instances',
            url='https://github.com/mighty-justice/django-super-deduper',
            version='0.0.1',

            packages=find_packages(exclude=['tests']),

            install_requires=requirements.readlines(),

            test_suite='tests',
        )
