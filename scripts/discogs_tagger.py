#!/usr/bin/python
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

import os, errno

def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc: # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else: raise

p = OptionParser()
p.add_option("-r", "--releaseid", action="store", dest="releaseid",
             help="The discogs.com release id of the target album")
p.add_option("-s", "--source", action="store", dest="sdir",
             help="The directory that you wish to tag")
p.add_option("-d", "--destination", action="store", dest="destdir",
             help="The (base) directory to copy the tagged files to")
p.add_option("-c", "--conf", action="store", dest="conffile",
             help="The discogstagger configuration file.")

p.set_defaults(conffile="/etc/discogstagger/discogs_tagger.conf")
(options, args) = p.parse_args()

if not options.sdir or not os.path.exists(options.sdir):
    p.error("Please specify a valid source directory ('-s')")

config = ConfigParser.ConfigParser()
config.read(options.conffile)

logging.basicConfig(level=config.getint("logging", "level"))

if not options.destdir:
    destdir = options.sdir
else:
    destdir = options.destdir
    logging.info("destdir set to %s", options.destdir)

logging.info("Using destination directory: %s", destdir)

id_file = config.get("batch", "id_file")
id_tag = config.get("batch", "id_tag")

if not options.releaseid:
    if not os.path.exists(os.path.join(options.sdir, id_file)):
        p.error("Please specify the discogs.com releaseid ('-r')")
    else:
        myids = {}
        with open(os.path.join(options.sdir, id_file)) as idFile:
            for line in idFile:
                name, var = line.partition("=")[::2]
                myids[name.strip()] =  var
        if id_tag in myids:
            releaseid = myids[id_tag].strip()
else:
    releaseid = options.releaseid

if not releaseid:
    p.error("Please specify the discogs.com releaseid ('-r')")

keep_original = config.getboolean("details", "keep_original")
embed_coverart = config.getboolean("details", "embed_coverart")
use_style = config.getboolean("details", "use_style")
use_lower_filenames = config.getboolean("details", "use_lower_filenames")
keep_tags = config.get("details", "keep_tags")
use_folder_jpg = config.getboolean("details", "use_folder_jpg")

release = TaggerUtils(options.sdir, destdir, use_lower_filenames, releaseid)
release.nfo_format = config.get("file-formatting", "nfo")
release.m3u_format = config.get("file-formatting", "m3u")
release.dir_format = config.get("file-formatting", "dir")
release.song_format = config.get("file-formatting", "song")
images_format = config.get("file-formatting", "images")
release.group_name = config.get("details", "group")

first_image_name = "folder.jpg"

if not use_folder_jpg:
    first_image_name = images_format + "-01.jpg"

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

dest_dir_name = release.dest_dir_name

if os.path.exists(dest_dir_name):
    logging.error("Destination already exists %s" % dest_dir_name)
    sys.exit("%s directory already exists, aborting." % dest_dir_name)
else:
    logging.info("Creating destination directory '%s'" %
                 dest_dir_name)
    mkdir_p(dest_dir_name)

logging.info("Downloading and storing images")
get_images(release.album.images, dest_dir_name, images_format, first_image_name)

for track in release.tag_map:
    logging.info("Writing file %s" % os.path.join(dest_dir_name,
                track.new_file))
    logging.debug("metadata -> %.2d %s - %s" % (track.position, track.artist,
                 track.title))

    # copy old file into new location
    shutil.copyfile(os.path.join(options.sdir, track.orig_file),
                    os.path.join(dest_dir_name, track.new_file))

    # load metadata information
    metadata = MediaFile(os.path.join(
                         dest_dir_name, track.new_file))

    # read already existing (and still wanted) properties
    keepTags = {}
    for name in keep_tags.split(","):
        if getattr(metadata, name):
            keepTags[name] = getattr(metadata, name)

    # remove current metadata
    metadata.delete()

    # set album metadata
    metadata.album = release.album.title
    metadata.composer = release.album.artist
    metadata.albumartist = release.album.artist
    metadata.albumartist_sort = release.album.sort_artist
    metadata.label = release.album.label
    metadata.year = release.album.year
    metadata.country = release.album.country
    metadata.url = release.album.url
    # add styles to the grouping tag (right now, we can just use one)
    metadata.grouping = release.album.styles[0]

    # adding two as there is no standard. discogstagger pre v1
    # used (TXXX desc="Catalog #")
    # mediafile uses TXXX desc="CATALOGNUMBER"
    metadata.catalognum = release.album.catno
    metadata.catalognumber = release.album.catno

    # use the correct genre field, on config use the first style
    genre = release.album.genre
    if use_style:
        genre = release.album.styles[0]

    metadata.genre = genre
    metadata.discogs_id = releaseid

    if release.album.disctotal and release.album.disctotal > 1 and track.discnumber:
        logging.info("writing disctotal and discnumber")
        metadata.disc = track.discnumber
        metadata.disctotal = release.album.disctotal

    if release.album.artist == "Various":
        metadata.comp = True

    metadata.comments = release.album.note

    # set track metadata
    metadata.title = track.title
    metadata.artist = track.artist
    metadata.artist_sort = track.sortartist
    metadata.track = track.position

    # the following value will be wrong, if the disc has a name
    metadata.tracktotal = len(release.tag_map)

    first_image_name = release.first_image_name

    if embed_coverart and os.path.exists(os.path.join(dest_dir_name,
                                         first_image_name)):
        imgdata = open(os.path.join(dest_dir_name,
                       first_image_name)).read()
        imgtype = imghdr.what(None, imgdata)

        if imgtype in ("jpeg", "png"):
            logging.info("Embedding album art.")
            metadata.art = imgdata

    if not keepTags is None:
        for name in keepTags:
            setattr(metadata, name, keepTags[name])

    metadata.save()

#
# start supplementary actions
#
logging.info("Generating .nfo file")
create_nfo(release.album.album_info, dest_dir_name, release.nfo_filename)

logging.info("Generating .m3u file")
create_m3u(release.tag_map, dest_dir_name, release.m3u_filename)

# remove source directory, if configured as such.
if not keep_original:
    logging.info("Deleting source directory '%s'" % options.sdir)
    shutil.rmtree(options.sdir)

logging.info("Tagging complete.")
