from setuptools import setup


setup(
    name='pypatgen',
    version='0.1.4',
    description='TeX hyphenation pattern generator',

    url='https://github.com/pgmmpk/pypatgen',
    download_url='https://github.com/pgmmpk/pypatgen/0.1.4',
    
    author='Mike Kroutikov',
    author_email='pgmmpk@gmail.com',

    license='MIT',

    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        'Development Status :: 3 - Beta',

        'License :: OSI Approved :: MIT License',

        'Programming Language :: Python :: 2.7',
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
