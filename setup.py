from setuptools import setup, find_packages

setup(name='Microlog',
    version='0.1',
    description='Python Application Intelligence',
    author='Chris Laffra',
    author_email='laffra@gmail.com',
    url='https://www.chrislaffra.org/',
    packages=find_packages(include=[
        'microlog',
        'microlog.dashboard',
    ]),
    install_requires=[
        'appdata',
        'jupyter',
        'matplotlib',
        'pandas',
        'pydot',
    ]
)