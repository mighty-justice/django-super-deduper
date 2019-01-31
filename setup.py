from setuptools import find_packages, setup

try:
    import pypandoc
    long_description = pypandoc.convert('README.md', 'rst')
except ImportError:
    long_description = open('README.md').read()

setup(
    use_scm_version=True,
    setup_requires=['setuptools_scm'],
    name='django-super-deduper',
    description='Utilities for deduping Django model instances',
    url='https://github.com/mighty-justice/django-super-deduper',
    long_description=long_description,
    classifiers=[
        'Framework :: Django :: 1.11',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.6',
    ],

    packages=find_packages(exclude=['tests']),
    include_package_data=True,

    install_requires=['django>=1.11'],

    test_suite='tests',
)
