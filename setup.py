from setuptools import setup
from os import path
import codecs

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with codecs.open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='pypatgen',
    version='0.1.3',
    description='TeX hyphenation pattern generator',
    long_description=long_description,
    url='https://github.com/pgmmpk/pypatgen',

    author='Mike Kroutikov',
    author_email='pgmmpk@gmail.com',

    license='MIT',

    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        'Development Status :: 4 - Beta',

        'License :: OSI Approved :: MIT License',

        'Programming Language :: Python :: 3',
    ],

    keywords='TeX hyphenation',

    packages=['patgen'],

    install_requires=[],

    entry_points={
        'console_scripts': [
            'pypatgen=patgen.main:main',
            'pypatgen_validate=patgen.validate:main'
        ],
    },
)
