from setuptools import setup
import os


ROOT_PATH = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(ROOT_PATH, "README.md"), encoding='utf-8') as f:
    LONG_DESC = f.read()

# with open("requirements.txt", 'r', encoding='utf-8') as f:
#     REQU = [x.strip() for x in f.readlines() if x]


setup(
    name="AutoOBS",
    version = 0.1,

    description="A simple GUI tool to automatically control the OBS Studio",
    long_description=LONG_DESC,
    url="https://github.com/myy1966/AutoOBS",

    author="myy1966",
    author_email='mxh1966@gmail.com',

    license='GPL v3.0',

    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 3 - Alpha',

        'Intended Audience :: End Users/Desktop',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Multimedia :: Video',

        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',

        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.8',
    ],

    keywords='OBS obs-websocket, Qt PyQt',

    # install_requires=REQU,

    packages=['AutoOBS'],

    entry_points={
        'gui_scripts': [
            'AutoOBS = AutoOBS.__main__:main']
    }
)
