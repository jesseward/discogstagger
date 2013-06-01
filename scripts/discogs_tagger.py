#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import errno
import shutil
import logging
import sys
import imghdr
import ConfigParser
from optparse import OptionParser
from discogstagger.ext.mediafile import MediaFile
from discogstagger.taggerutils import (
    TaggerUtils,
    create_nfo,
    create_m3u,
    get_images)

logger = logging.getLogger(__name__)

p = OptionParser()
p.add_option("-r", "--releaseid", action="store", dest="releaseid",
             help="The discogs.com release id of the target album")
p.add_option("-s", "--source", action="store", dest="sdir",
             help="The directory that you wish to tag")
p.add_option("-c", "--conf", action="store", dest="conffile",
             help="The discogstagger configuration file.")

p.set_defaults(conffile="/etc/discogstagger/discogs_tagger.conf")
(options, args) = p.parse_args()

if not options.sdir or not os.path.exists(options.sdir):
    p.error("Please specify a valid source directory ('-s')")

if not options.releaseid:
    if not os.path.exists(os.path.join(options.sdir, "id.txt")):
        p.error("Please specify the discogs.com releaseid ('-r')")
    else:
        myids = {}
        with open(os.path.join(options.sdir, "id.txt")) as idFile:
            for line in idFile:
                name, var = line.partition("=")[::2]
                myids[name.strip()] =  var
        if "discogs_id" in myids:
            releaseid = myids["discogs_id"].strip()
else:
    releaseid = options.releaseid

if not releaseid:
    p.error("Please specify the discogs.com releaseid ('-r')")

config = ConfigParser.ConfigParser()
config.read(options.conffile)

logging.basicConfig(level=config.getint("logging", "level"))
logging.info("Determine discogs release: %s", releaseid)

keep_original = config.getboolean("details", "keep_original")
embed_coverart = config.getboolean("details", "embed_coverart")

release = TaggerUtils(options.sdir, releaseid)
release.nfo_format = config.get("file-formatting", "nfo")
release.m3u_format = config.get("file-formatting", "m3u")
release.dir_format = config.get("file-formatting", "dir")
release.song_format = config.get("file-formatting", "song")
release.group_name = config.get("details", "group")

# ensure we were able to map the release appropriately.
if not release.tag_map:
    logging.error("Unable to match file list to discogs release '%s'" %
                  releaseid)
    sys.exit()

#
# start tagging actions.
#
logging.info("Tagging album '%s - %s'" % (release.album.artist,
             release.album.title))

if os.path.exists(release.dest_dir_name):
    logging.error("Destination already exists %s" % release.dest_dir_name)
    sys.exit("%s directory already exists, aborting." % release.dest_dir_name)
else:
    logging.info("Creating destination directory '%s'" %
                 release.dest_dir_name)
    os.mkdir(release.dest_dir_name)

logging.info("Downloading and storing images")
get_images(release.album.images, release.dest_dir_name)

for track in release.tag_map:
    logger.info("Writing file %s" % os.path.join(release.dest_dir_name,
                track.new_file))
    logger.debug("metadata -> %.2d %s - %s" % (track.position, track.artist,
                 track.title))

    # copy old file into new location
    shutil.copyfile(os.path.join(options.sdir, track.orig_file),
                    os.path.join(release.dest_dir_name, track.new_file))

    # load metadata information
    metadata = MediaFile(os.path.join(
                         release.dest_dir_name, track.new_file))
    # remove current metadata
    metadata.delete()
    metadata.title = track.title
    metadata.artist = track.artist
    metadata.album = release.album.title
    metadata.composer = release.album.artist
    metadata.albumartist = release.album.artist
    metadata.label = release.album.label
    metadata.year = release.album.year
    # adding two are there is no standard. discogstagger pre v1
    # used (TXXX desc="Catalog #")
    # mediafile uses TXXX desc="CATALOGNUMBER"
    metadata.catalognum = release.album.catno
    metadata.catalognumber = release.album.catno
    metadata.genre = release.album.genre
    metadata.track = track.position
    metadata.tracktotal = len(release.tag_map)

    if embed_coverart and os.path.exists(os.path.join(release.dest_dir_name,
                                         "00-image-01.jpg")):
        imgdata = open(os.path.join(release.dest_dir_name,
                       "00-image-01.jpg")).read()
        imgtype = imghdr.what(None, imgdata)

        if imgtype in ("jpeg", "png"):
            logger.info("Embedding album art.")
            metadata.art = imgdata

    metadata.save()

#
# start supplementary actions
#
logging.info("Generating .nfo file")
create_nfo(release.album.album_info, release.dest_dir_name,
           release.nfo_filename)

logging.info("Generating .m3u file")
create_m3u(release.tag_map, release.dest_dir_name, release.m3u_filename)

# remove source directory, if configured as such.
if not keep_original:
    logging.info("Deleting source directory '%s'" % options.sdir)
    shutil.rmtree(options.sdir)

logging.info("Tagging complete.")
