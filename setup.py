NAME = "discogstagger"
VERSION = "0.8"

from distutils.core import setup

setup (
    name = NAME,
    version = VERSION,
    description = ("Console based audio-file metadata tagger that uses the Discogs.com api"),
    author = "Jesse Ward",
    author_email = "jesse@housejunkie.ca",
    url = "https://github.com/jesseward/discogstagger",
    scripts = ["src/discogs_tagger.py"],
    data_files = [(
        "/etc/%s/" % NAME, ["conf/discogs_tagger.conf"]),
        ("share/%s" % NAME, ["README.md"])]
) 
