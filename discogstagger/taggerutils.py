# -*- coding: utf-8 -*-

from urllib import FancyURLopener
import os
import re
import sys
import logging
from unicodedata import normalize

from discogsalbum import DiscogsAlbum, TrackContainer
from discogsauth import DiscogsAuth, USER_AGENT

reload(sys)
sys.setdefaultencoding("utf-8")

logger = logging.getLogger(__name__)

class TagOpener(FancyURLopener, object):

    version = USER_AGENT

    def __init__(self):
        FancyURLopener.__init__(self)


class TaggerUtils(object):
    """ Accepts a destination directory name and discogs release id.
        TaggerUtils returns a the corresponding metadata information , in which
        we can write to disk. The assumption here is that the destination
        direcory contains a single album in a support format (mp3 or flac).

        The class also provides a few methods that create supplimental files,
        relvant to a given album (m3u, nfo file and album art grabber.)"""


    # supported file types.
    FILE_TYPE = (".mp3", ".flac",)

    def __init__(self, sourcedir, destdir, use_lower, ogsrelid, split_artists, 
            split_genres_and_styles, copy_other_files, char_exceptions):

        self.group_name = "jW"
        self.dir_format = "%ALBARTIST%-%ALBTITLE%-(%CATNO%)-%YEAR%-%GROUP%"
        self.m3u_format = "00-%ALBARTIST%-%ALBTITLE%.m3u"
        self.nfo_format = "00-%ALBARTIST%-%ALBTITLE%.nfo"
        self.song_format = "%TRACKNO%-%ARTIST%-%TITLE%%TYPE%"
        self.va_song_format = "%TRACKNO%-%ARTIST%-%TITLE%%TYPE%"
        self.images_format = "00-image"
        self.first_image_name = "folder.jpg"

        self.copy_other_files = copy_other_files
        self.char_exceptions = char_exceptions

        self.sourcedir = sourcedir
        self.destdir = destdir
        result = self._get_target_list()
        self.files_to_tag = result["target_list"]
        if self.copy_other_files:
            self.copy_files = result["copy_files"]
        self.album = DiscogsAlbum(ogsrelid, split_artists, split_genres_and_styles)
        self.use_lower = use_lower

        if len(self.files_to_tag) == len(self.album.tracks):
            self.tag_map = self._get_tag_map()
        else:
            self.tag_map = False

    def _value_from_tag_format(self, format, trackno=1, position=1, filetype=".mp3"):
        """ Fill in the used variables using the track information """

        logger.debug("parameters given: format: %s" % format)
        logger.debug("parameters given: trackno: %d" % trackno)
        logger.debug("parameters given: position: %d" % position)
        logger.debug("paramerter avail: position: %d" % len(self.album.tracks))

        property_map = {
            "%ALBTITLE%": self.album.title,
            "%ALBARTIST%": self.album.artist,
            "%YEAR%": self.album.year,
            "%CATNO%": self.album.catno,
            "%GENRE%": self.album.genre,
            "%STYLE%": self.album.style,
            "%GROUP%": self.group_name,
# could go wrong on multi discs (because of empty tracks with subdisc names)
            "%ARTIST%": self.album.tracks[position].artist,
# see artist
            "%TITLE%": self.album.tracks[position].title,
            "%DISCNO%": self.album.tracks[position].discnumber,
            "%TRACKNO%": "%.2d" % trackno,
            "%TYPE%": filetype,
            "%LABEL%": self.album.label,
        }

        for hashtag in property_map.keys():
            format = format.replace(hashtag,
                                            str(property_map[hashtag]))

        logger.debug("format output: %s" % format)

        return format

    def _value_from_tag(self, format, trackno=1, position=1, filetype=".mp3"):
        """ Generates the filename tagging map """

        format = self._value_from_tag_format(format, trackno, position, filetype)

        if self.use_lower:
            format = format.lower()

        format = self._get_clean_filename(format)

        logger.debug("output: %s" % format)

        return format

    def _get_target_list(self):
        """ fetches a list of files in the self.sourcedir location. """

        copy_files = None
        try:
            dir_list = os.listdir(self.sourcedir)
            dir_list.sort()

            # strip unwanted files
            target_list = [os.path.join(self.sourcedir, x) for x in dir_list
                             if x.lower().endswith(TaggerUtils.FILE_TYPE)]
            if self.copy_other_files:
                copy_files = [os.path.join(self.sourcedir, x) for x in 
                    dir_list if not x.lower().endswith(TaggerUtils.FILE_TYPE)]

            if not target_list:
                logger.debug("target_list empty, try to retrieve subfolders")
                for y in dir_list:
                    tmp_list = []
                    logger.debug("subfolder: %s" % y)
                    sub_dir = os.path.join(self.sourcedir, y)
                    if os.path.isdir(sub_dir):
                        tmp_list.extend(os.listdir(sub_dir))
                        tmp_list.sort()
                        tmp_list = [os.path.join(sub_dir, y) for y in tmp_list]

			# strip unwanted files
			target_list.extend([z for z in tmp_list if 
				    z.lower().endswith(TaggerUtils.FILE_TYPE)])
			if self.copy_other_files:
			    copy_files = [z for z in tmp_list if not 
				    z.lower().endswith(TaggerUtils.FILE_TYPE)]

        except OSError, e:
            if e.errno == errno.EEXIST:
                logger.error("No such directory '%s'", self.sourcedir)
                raise IOError("No such directory '%s'", self.sourcedir)
            else:
                raise IOError("General IO system error '%s'" % errno[e])

        return {"target_list": target_list, "copy_files": copy_files}

    def _get_tag_map(self):
        """ matches the old with new via TargetTagMap object. """

        tag_map = []

        # ignore files that do not match FILE_TYPE
        for position, filename in enumerate(self.files_to_tag):
            logger.debug("track position: %d" % position)
            # add the found files to the tag_map list
            logger.debug("mapping file %s --to--> %s - %s" % (filename,
                         self.album.tracks[position].artist,
                         self.album.tracks[position].title))
            pos = position + 1
            track = self.album.tracks[position]
            track.orig_file = filename
            fileext = os.path.splitext(filename)[1]

            # special handling for Various Artists discs
            if self.album.artist == "Various":
                newfile = self._value_from_tag(self.va_song_format,
                                           track.tracknumber, position, fileext)
            else:
                newfile = self._value_from_tag(self.song_format,
                                           track.tracknumber, position, fileext)

            track.new_file = self._get_clean_filename(newfile)
            tag_map.append(track)

        return tag_map

    @property
    def dest_dir_name(self):
        """ generates new album directory name """

        # determine if an absolute base path was specified.
        if os.path.isabs(self.destdir):
            path_name = os.path.normpath(self.destdir)
        else:
            path_name = os.path.dirname(os.path.normpath(self.destdir))

        dest_dir = ""
        for ddir in self.dir_format.split("/"):
            d_dir = self._get_clean_filename(self._value_from_tag(ddir))
            if dest_dir == "":
                dest_dir = d_dir
            else:
                dest_dir = dest_dir + "/" + d_dir

        dir_name = os.path.join(path_name, dest_dir)

        return dir_name

    @property
    def album_folder_name(self):
        """ returns the album as the name for the sub-dir for multi disc 
            releases"""

        folder_name = "%s%s" % (self._get_clean_filename(str(self.album.title)), self.disc_folder_name)

        if self.use_lower:
            folder_name = folder_name.lower()

        return folder_name

    @property
    def m3u_filename(self):
        """ generates the m3u file name """

        m3u = self._value_from_tag(self.m3u_format)
        return self._get_clean_filename(m3u)

    @property
    def nfo_filename(self):
        """ generates the nfo file name """

        nfo = self._value_from_tag(self.nfo_format)
        return self._get_clean_filename(nfo)


    def _get_clean_filename(self, f):
        """ Removes unwanted characters from file names """

        filename, fileext = os.path.splitext(f)

        if not fileext in TaggerUtils.FILE_TYPE and not fileext in [".m3u", ".nfo"]:
            logger.debug("fileext: %s" % fileext)
            filename = f
            fileext = ""

        a = unicode(filename, "utf-8")

        for k, v in self.char_exceptions.iteritems():
            a = a.replace(k, v)

        a = normalize("NFKD", a).encode("ascii", "ignore")

        cf = re.compile(r"[^-\w.\(\)_]")
        cf = cf.sub("", str(a))

        cf = cf.replace(" ", "_")
        cf = cf.replace("__", "_")
        cf = cf.replace("_-_", "-")

        return "%s%s" % (cf, fileext)


def write_file(filecontents, filename):
    """ writes a string of data to disk """

    if not os.path.exists(os.path.dirname(filename)):
        os.makedirs(os.path.dirname(filename))

    logger.debug("Writing file '%s' to disk" % filename)

    try:
        with open(filename, "w") as fh:
            fh.write(filecontents)
    except IOError:
        logger.error("Unable to write file '%s'" % filename)

    return True


def create_nfo(nfo, dest_dir, nfo_file):
    """ Writes the .nfo file to disk. """

    return write_file(nfo, os.path.join(dest_dir, nfo_file))


def create_m3u(tag_map, folder_names, dest_dir_name, m3u_filename):
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
        folder_name = folder_names[track.discnumber]
        if folder_name is not "":
            folder_name = "%s/" % folder_name
        m3u += "%s%s\n" % (folder_name, track.new_file)

    return write_file(m3u, os.path.join(dest_dir_name, m3u_filename))


def get_images(images, dest_dir_name, images_format, first_image_name):
    """ Download and store any available images """

    if images:
        discogs_auth = DiscogsAuth()
        for i, image in enumerate(images, 0):
            logger.debug('Downloading image "{0}"'.format(image))
            try:
                picture_name = ''
                if i == 0:
                    picture_name = first_image_name
                else:
                    picture_name = images_format + "-%.2d.jpg" % i

                resp, content = discogs_auth.handle.request(image, 'POST',
                        headers={'user-agent': USER_AGENT })
                if resp['status'] == '200':
                   with open(os.path.join(dest_dir_name, picture_name), 'w') as fh:
                       fh.write(content)
            except Exception as e:
                logger.error("Unable to download image '{0}', skipping. Error: {1}".format(
                    image, e))
