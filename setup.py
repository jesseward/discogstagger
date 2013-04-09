NAME = "discogstagger"
VERSION = "1.0"

from distutils.core import setup

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
        "/etc/%s/" % NAME, ["conf/discogs_tagger.conf"]),
        ("share/%s" % NAME, ["README.md"])]
) 
