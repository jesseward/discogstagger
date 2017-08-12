import os

from setuptools import setup

NAME = 'discogstagger'
VERSION = '3.0.2'


user = os.getenv('USER')
if os.getenv('SUDO_USER') is not None:
    user = os.getenv('SUDO_USER')

setup(
    name=NAME,
    version=VERSION,
    description=('Console based audio-file metadata tagger that uses the Discogs.com api'),
    author='Jesse Ward',
    author_email='jesse@jesseward.com',
    url='https://github.com/jesseward/discogstagger',
    entry_points={
        'console_scripts': [
            'discogs-tagger = discogstagger.main:tagger'
        ]
    },
    packages=['discogstagger'],
    data_files=[(
        os.path.expanduser('~{0}/.config/{1}/'.format(user, NAME)),
        ['conf/discogs_tagger.conf']),
        ('share/{0}'.format(NAME), ['README.md'])],
    install_requires=[
        'click>=6.7',
        'discogs-client>=2.2.0',
        'mutagen>=1.21',
        'mediafile>=0.0.1',
        'requests>=1.2.0',
        'six>=1.10.0',
    ],
)
