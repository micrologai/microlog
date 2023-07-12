import atexit
import datetime
import os
import setuptools
import shutil
import site
import sys

from microlog import sitecustomize 


pip = f"{sys.executable} -m pip install -r requirements.txt"
os.system(pip)

def _post_install():
    sitepackages = site.getsitepackages()[0]
    original = sitecustomize.__file__
    target = os.path.join(sitepackages, os.path.basename(original))
    if os.path.exists(target):
        with open(target, "a") as file:
            file.write("#\n")
            file.write(f"# Microlog installation time: {datetime.datetime.now()}\n")
            file.write(f"# Microlog location: {original}\n")
            file.write(open(sitecustomize.__file__).read())
    else:
        shutil.copy(sitecustomize.__file__, sitepackages)
    print('Installed', sitecustomize.__file__, "into", target)


atexit.register(_post_install)


setuptools.setup(name='Microlog',
    version='0.1.1',
    description='Python Application Intelligence',
    author='Chris Laffra',
    author_email='laffra@gmail.com',
    url='https://www.chrislaffra.org/',
    packages=setuptools.find_packages(include=[
        'microlog',
        'dashboard',
    ]),
)