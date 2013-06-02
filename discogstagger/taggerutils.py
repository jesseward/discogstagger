# -*- coding: utf-8 -*-

from urllib import FancyURLopener
import os
import re
import sys
import logging
from unicodedata import normalize

from discogsalbum import DiscogsAlbum, TrackContainer

reload(sys)
sys.setdefaultencoding("utf-8")

logger = logging.getLogger(__name__)


class TagOpener(FancyURLopener, object):

    version = "discogstagger +http://github.com/jesseward"

    def __init__(self):
        FancyURLopener.__init__(self)


class TaggerUtils(object):
    """ Accepts a destination directory name and discogs release id.
        TaggerUtils returns a the corresponding metadata information , in which
        we can write to disk. The assumption here is that the destination
        direcory contains a single album in a support format (mp3 or flac).

        The class also provides a few methods that create supplimental files,
        relvant to a given album (m3u, nfo file and album art grabber.)"""

    CHAR_EXCEPTIONS = {
        "&": "and",
        " ": "_",
        "ö": "oe",
        "Ö": "Oe",
        "Ä": "Ae",
        "ä": "ae",
        "Ü": "Ue",
        "ü": "ue",
    }

    # supported file types.
    FILE_TYPE = (".mp3", ".flac",)

    def __init__(self, sourcedir, destdir, use_lower, ogsrelid):
        self.group_name = "jW"
        self.dir_format = "%ALBARTIST%-%ALBTITLE%-(%CATNO%)-%YEAR%-%GROUP%"
        self.m3u_format = "00-%ALBARTIST%-%ALBTITLE%.m3u"
        self.nfo_format = "00-%ALBARTIST%-%ALBTITLE%.nfo"
        self.song_format = "%TRACKNO%-%ARTIST%-%TITLE%%TYPE%"

        self.sourcedir = sourcedir
        self.destdir = destdir
        self.files_to_tag = self._get_target_list()
        self.album = DiscogsAlbum(ogsrelid)
        self.use_lower = use_lower

        if len(self.files_to_tag) == len(self.album.tracks):
            self.tag_map = self._get_tag_map()
        else:
            self.tag_map = False

    def _value_from_tag(self, fileformat, trackno=1, filetype=".mp3"):
        """ Generates the filename tagging map """

        property_map = {
            "%ALBTITLE%": self.album.title,
            "%ALBARTIST%": self.album.artist,
            "%YEAR%": self.album.year,
            "%CATNO%": self.album.catno,
            "%GENRE%": self.album.genre,
            "%STYLE%": self.album.styles[0],
            "%GROUP%": self.group_name,
            "%ARTIST%": self.album.tracks[trackno-1].artist,
            "%TITLE%": self.album.tracks[trackno-1].title,
            "%TRACKNO%": "%.2d" % trackno,
            "%TYPE%": filetype,
            "%LABEL%": self.album.label,
        }

        for hashtag in property_map.keys():
            fileformat = fileformat.replace(hashtag,
                                            str(property_map[hashtag]))

        if self.use_lower:
            fileformat = fileformat.lower()

        return fileformat

    def _get_target_list(self):
        """ fetches a list of files in the self.sourcedir location. """

        try:
            dir_list = os.listdir(self.sourcedir)
            dir_list.sort()
        except OSError, e:
            if e.errno == errno.EEXIST:
                logging.error("No such directory '%s'", self.sourcedir)
                raise IOError("No such directory '%s'", self.sourcedir)
            else:
                raise IOError("General IO system error '%s'" % errno[e])

        # strip unwanted files
        return [x for x in dir_list if x.lower().endswith(TaggerUtils.FILE_TYPE)]

    def _get_tag_map(self):
        """ matches the old with new via TargetTagMap object. """

        tag_map = []

        # ignore files that do not match FILE_TYPE
        for position, filename in enumerate(self.files_to_tag):
            # add the found files to the tag_map list
            logger.debug("mapping file %s --to--> %s - %s" % (filename,
                         self.album.tracks[position].artist,
                         self.album.tracks[position].title))
            track = TrackContainer()
            track.position = position + 1
            track.orig_file = filename
            fileext = os.path.splitext(filename)[1]
            newfile = self._value_from_tag(self.song_format,
                                           track.position, fileext)
            track.new_file = get_clean_filename(newfile)
            track.artist = self.album.tracks[position].artist
            track.title = self.album.tracks[position].title
            tag_map.append(track)

        return tag_map

    @property
    def dest_dir_name(self):
        """ generates new album directory name """

        path_name = os.path.dirname(self.destdir)
        dest_dir = get_clean_filename(self._value_from_tag(self.dir_format))

        return os.path.join(path_name, dest_dir)

    @property
    def m3u_filename(self):
        """ generates the m3u file name """

        m3u = self._value_from_tag(self.m3u_format)
        return get_clean_filename(m3u)

    @property
    def nfo_filename(self):
        """ generates the nfo file name """

        nfo = self._value_from_tag(self.nfo_format)
        return get_clean_filename(nfo)


def get_clean_filename(f):
    """ Removes unwanted characters from file names """

    a = unicode(f, "utf-8")

    for k, v in TaggerUtils.CHAR_EXCEPTIONS.iteritems():
        a = a.replace(k, v)

    a = normalize("NFKD", a).encode("ascii", "ignore")

    cf = re.compile(r"[^-\w.\(\)_]")
    return cf.sub("", str(a))


def write_file(filecontents, filename):
    """ writes a string of data to disk """

    if not os.path.exists(os.path.dirname(filename)):
        os.makedirs(os.path.dirname(filename))

    logging.debug("Writing file '%s' to disk" % filename)

    try:
        with open(filename, "w") as fh:
            fh.write(filecontents)
    except IOError:
        logging.error("Unable to write file '%s'" % filename)

    return True


def create_nfo(nfo, dest_dir, nfo_file):
    """ Writes the .nfo file to disk. """

    return write_file(nfo, os.path.join(dest_dir, nfo_file))


def create_m3u(tag_map, dest_dir_name, m3u_filename):
    """ Generates the playlist for the given albm.
        Adhering to the following m3u format.

        ---
        #EXTM3U
        #EXTINF:233,Artist - Song
        directory\file_name.mp3.mp3
        #EXTINF:-1,My Cool Stream
        http://www.site.com:8000/listen.pls
        ---

        Taken from http://forums.winamp.com/showthread.php?s=&threadid=65772"""

    m3u = "#EXTM3U\n"
    for track in tag_map:
        m3u += "#EXTINF:-1,%s - %s\n" % (track.artist, track.title)
        m3u += "%s\n" % track.new_file

    return write_file(m3u, os.path.join(dest_dir_name, m3u_filename))


def get_images(images, dest_dir_name):
    """ Download and store any available images """

    if images:
        for i, image in enumerate(images, 1):
            logging.debug("Downloading image '%s'" % image)
            try:
                url_fh = TagOpener()
                url_fh.retrieve(image, os.path.join(dest_dir_name,
                                "00-image-%.2d.jpg" % i))
            except Exception as e:
                logging.error("Unable to download image '%s', skipping."
                              % image)
                print e
