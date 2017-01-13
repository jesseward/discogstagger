NAME = "discogstagger"
VERSION = "2.1.0"

import os
from distutils.core import setup

user = os.getenv("USER")
if os.getenv("SUDO_USER") is not None:
    user = os.getenv("SUDO_USER")

setup (
    name = NAME,
    version = VERSION,
    description = ("Console based audio-file metadata tagger that uses the Discogs.com api"),
    author = "Jesse Ward",
    author_email = "jesse@housejunkie.ca",
    url = "https://github.com/jesseward/discogstagger",
    scripts = ["scripts/discogs_tagger.py"],
    packages = ["discogstagger", "discogstagger.ext"],
    data_files = [(
        os.path.expanduser("~{0}/.config/{1}/".format(user, NAME)),
            ["conf/discogs_tagger.conf"]),
        ("share/{0}".format(NAME), ["README.md"])]
) 
