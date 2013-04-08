#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import errno
import shutil
import logging

from taggerutils import TaggerUtils

if __name__ == "__main__":

    import ConfigParser
    from optparse import OptionParser
    
    p = OptionParser()
    p.add_option("-r", "--releaseid", action="store", dest="releaseid",
                 help="The discogs.com release id of the target album")
    p.add_option("-s", "--source", action="store", dest="sdir",
                 help="The directory that you wish to tag")
    p.add_option("-c", "--conf", action="store", dest="conffile",
                 help="The discogstagger configuration file.")

    p.set_defaults(conffile="/etc/discogstagger/discogs_tagger.conf")
    (options, args) = p.parse_args()

    if not options.releaseid:
        p.error("Please specify the discogs.com releaseid ('-r')")

    if not options.sdir or not os.path.exists(options.sdir):
        p.error("Please specify a valid source directory ('-s')")

    config = ConfigParser.ConfigParser()
    config.read(options.conffile)

    logging.basicConfig(level=config.getint("logging", "level"))

    release = TaggerUtils(options.sdir, options.releaseid)
    release.keep_original = config.getboolean("details", "keep_original")
    release.nfo_format = config.get("file-formatting","nfo")
    release.m3u_format = config.get("file-formatting","m3u")
    release.dir_format = config.get("file-formatting","dir")
    release.song_format = config.get("file-formatting","song")
    release.group_name = config.get("details", "group")

    logging.info("Tagging album '%s - %s'" % (release.artist, release.title))
    release.tag_album()
    logging.info("Generating .nfo file")
    release.create_nfo()
    logging.info("Generating .m3u file")
    release.create_m3u()
    logging.info("Downloading and storing images")
    release.get_images()

    logging.info("Tagging complete.")
