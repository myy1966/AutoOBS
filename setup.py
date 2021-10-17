from setuptools import setup, find_packages


setup(
    name="AUtoOBS",
    version = 0.1,

    description="A simple GUI tool to automatically control the OBS Studio",

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
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Programming Language :: Python :: 3.7',
    ],

    keywords='OBS Qt PyQt',

    packages=['AutoOBS'],
    package_dir={'AUtoOBS': 'AutoOBS'},
    package_data={"AutoOBS": ["images/*.png"]},
    
    entry_points={
        'gui_scripts': [
            'AutoOBS = AutoOBS.__main__:main']
    },



    # data_files=[
    #     ("images", ["AutoOBS/images/stopped.png",
    #                 "AutoOBS/images/recording.png",
    #                 "AutoOBS/images/paused.png"])
    # ]
)
