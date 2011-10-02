#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import os
import errno
import re
import time
import shutil
import logging
import unicodedata
from urllib import FancyURLopener
from mutagen.flac import FLAC
import mutagen
from mutagen.id3 import ID3, TIT2, TPE1, TALB, TCOM, TPUB, TRCK, TDRC, TXXX, \
                        TCON, COMM
import discogs_client as discogs

reload(sys)
sys.setdefaultencoding('utf-8')

__version__ = '0.3'

class TagOpener(FancyURLopener, object):
    version = 'discogstagger +http://github.com/jesseward'

class memoized_property(object):
    """A read-only @property that is only evaluated once. Direct copy from 
       http://www.reddit.com/r/Python/comments/ejp25/cached_property_decorator_that_is_memory_friendly/ """


    def __init__(self, fget, doc=None):
        self.fget = fget
        self.__doc__ = doc or fget.__doc__
        self.__name__ = fget.__name__

    def __get__(self, obj, cls):
        if obj is None:
            return self
        obj.__dict__[self.__name__] = result = self.fget(obj)
        return result

class DiscogsTaggerError(BaseException):
    pass
 
class Album(object):
    """ Wraps the discogs-client-api script, abstracting the minimal set of
        artist data required to tag an album/release """


    def __init__ (self, releaseid):

        self.release = discogs.Release(releaseid)
        discogs.user_agent = 'discogstagger +http://github.com/jesseward'

    def __str__(self):
        
        return "<%s - %s>" % (self.artist, self.title)

    @property
    def album_info(self):
        """ Dumps the release data to a formatted text string. Formatted for
            .nfo file  """
        
        div = "_ _______________________________________________ _ _\n"
        r = div
        r += "  Name : %s - %s\n" % (self.artist, self.title)
        r += " Label : %s\n" % (self.label)
        r += " Genre : %s\n" % (self.genre)
        r += " Catno : %s\n" % (self.catno)
        r += "  Year : %s\n" % (self.year)
        r += "   URL : http://www.discogs.com/release/%s\n" % self.release._id
        
        if self.master_id:
            r += "Master : http://www.discogs.com/master/%s\n" % self.master_id 
        
        r += div
        for key, value in self.tracks.items():
            r += "%.2d. %s - %s\n" % (key, value[0], value[1])
        return r

    @property
    def releaseid(self):
        """ retuns the discogs release id """

        return self.release._id

    @property
    def catno(self):
        """ Returns the release catalog number """

        return self.release.data['labels'][0]['catno']

    @property
    def label(self):
        """ Returns the release Label name """

        return self.clean_name(self.release.data['labels'][0]['name'])
    
    @property
    def images(self):
        """ return a single list of images for the given album """

        return [ x['uri'] for x in self.release.data['images'] ]
    
    @property
    def title(self):
        """ return the album release name from discogs API """

        return self.release.title
   
    @property 
    def year(self):
        """ returns the album release year obtained from API 2.0 """

        good_year = re.compile('\d\d\d\d')
        try:
            return good_year.match(str(self.release.data['year'])).group(0)
        except IndexError:
            return '1900'

    @property
    def master_id(self):
        """ returns the master release id """

        try:
            return self.release.data['master_id']
        except KeyError:
            return None

    @property
    def genre(self):
        """ obtain the album genre """ 

        return self.release.data['styles'][0]

    @property
    def artist(self):
        """ obtain the album artist """

        artist = self.release.artists[0]
        return self.clean_name(artist.data['name'])
    
    @property
    def tracks(self):
        """ provides the tracklist of the given release id """
        
        tracklist = {}
        i = 1
        for t in self.release.tracklist:
            if t['type'] == 'Track':
                try:
                    artist = self.clean_name(t['artists'][0].name)
                except IndexError:
                    artist = self.artist
                tracklist[i] = [artist, t['title']]
                i += 1
        return tracklist

    @staticmethod
    def clean_name(clean_target):
        """ Cleans up the format of the artist or label name provided by Discogs. 
            Examples:
                'Goldie (12)' becomes 'Goldie'
                  or
                'Aphex Twin, The' becomes 'The Aphex Twin' 
            Accepts a string to clean, returns a cleansed version """

        groups = {
            '(.*),\sThe$' : 'The',
        }

        # remove discogs duplicate handling eg : John (1)
        clean_target = re.sub('\s\(\d+\)', '', clean_target)

        for regex in groups:
            if re.search(r'%s' % regex, clean_target):
                clean_target = "%s %s" % (groups[regex], re.search('%s' % regex,\
                clean_target).group(1))
        return clean_target

class Tagger(Album):
    """ Provides functionality to modify audio metadata information found in 
        either MP3 or FLAC file formats.  """    
   
    CHAR_EXCEPTIONS = {
        '&' : 'and',
        ' ' : '_', 
    }

    # supported file types.
    FILE_TYPE = ('.mp3', '.flac',)
    
    def __init__(self, sourcedir, ogsrelid):
        self.sourcedir = sourcedir
        self.group_name = 'jW'
        self.keep_original = True
        self.dir_format = '%ALBARTIST%-%ALBTITLE%-(%CATNO%)-%YEAR%-%GROUP%'
        self.m3u_format = '00-%ALBARTIST%-%ALBTITLE%.m3u'
        self.nfo_format = '00-%ALBARTIST%-%ALBTITLE%.nfo'
        self.song_format = '00-%ALBARTIST%-%ALBTITLE%.nfo'
        
        Album.__init__(self, ogsrelid)

    def _value_from_tag(self, fileformat, trackno=1, filetype='.mp3'):
        """ Generates the filename tagging map """

        property_map = {
            "%ALBTITLE%": self.title,
            "%ALBARTIST%": self.artist,
            "%YEAR%": self.year,
            "%CATNO%": self.catno,
            "%GENRE%": self.genre,
            "%GROUP%": self.group_name,
            "%ARTIST%": self.tracks[trackno][0],
            "%TITLE%": self.tracks[trackno][1],
            "%TRACKNO%": "%.2d" % trackno,
            "%TYPE%": filetype,
            "%LABEL%": self.label,
        }

        for hashtag in property_map.keys():
            fileformat = fileformat.replace(hashtag, str(property_map[hashtag]))
        return fileformat

    def _tag_mp3(self, trackno):
        """ Calls the mutagen library to perform metadata changes for MP3 files """
       
        logging.debug("Tagging '%s'" % os.path.join(self.dest_dir_name,\
                        self.file_tag_map[trackno][1]))
 
        try:
            audio = ID3(os.path.join(self.dest_dir_name,\
                        self.file_tag_map[trackno][1]))
            audio.delete()
        except mutagen.id3.ID3NoHeaderError:
            pass
        # add new ID3 tags 
        try:
            id3 = mutagen.id3.ID3(os.path.join(self.dest_dir_name,\
                        self.file_tag_map[trackno][1]))
        except mutagen.id3.ID3NoHeaderError:
            id3 = mutagen.id3.ID3()

        # adding new id3 frames
        id3.add(TIT2(encoding=3, text=self.tracks[trackno][1]))
        id3.add(TPE1(encoding=3, text=self.tracks[trackno][0]))
        id3.add(TALB(encoding=3, text=self.title))
        id3.add(TCOM(encoding=3, text=self.artist))
        id3.add(TPUB(encoding=3, text=self.label))
        id3.add(TDRC(encoding=3, text=self.year))
        id3.add(TXXX(encoding=3, desc='Catalog #', text=self.catno))
        id3.add(TCON(encoding=3, text=self.genre))
        id3.add(TRCK(encoding=3, text=str("%d/%d" % (int(trackno), len(self.tracks)))))
        id3.add(COMM(encoding=3, desc='eng', text='::> Don\'t believe the hype! <::'))
        try:
            id3.save(os.path.join(self.dest_dir_name,\
                        self.file_tag_map[trackno][1]),0)
        except:
            logging.error("Unable to tag '%s'" % self.file_tag_map[trackno][1])
            raise DiscogsTaggerError, "Unable to write tag '%s'" % \
                            self.file_tag_map[trackno][1]


    def _tag_flac(self, trackno):
        """ Calls the mutagen library to perform metadata changes for FLAC files """

        logging.debug("Tagging '%s'" % os.path.join(self.dest_dir_name,\
                    self.file_tag_map[trackno][1]))

        audio = FLAC(os.path.join(self.dest_dir_name,\
                    self.file_tag_map[trackno][1]))
        try:
            encoding = audio["ENCODING"]
        except:
            encoding = ""
            audio.delete()

        # add FLAC tag data
        audio["TITLE"] = self.tracks[trackno][1]
        audio["ARTIST"] = self.tracks[trackno][0]
        audio["ALBUM"] = self.title
        audio["COMPOSER"] = self.artist
        audio["ORGANIZATION"] = self.label
        audio["CATALOGNUM"] = self.catno
        audio["GENRE"] = self.genre
        audio["YEAR"] = self.year
        audio["TRACKNUMBER"] = str(trackno)
        audio["TRACKTOTAL"] = str(len(self.tracks))
        audio["DESCRIPTION"] = '::> Don\'t believe the hype! <::'
        if(len(encoding) != 0):
            audio["ENCODING"] = encoding
        audio.pprint()
        try:
            audio.save()
        except:
            logging.error("Unable to tag '%s'" % self.file_tag_map[trackno][1])
            raise DiscogsTaggerError, "Unable to write tag '%s'" % \
                            self.file_tag_map[trackno][1]

    def tag_album(self, remove=True):
        """ Calls the appropriate actions and methods to tag a given album """

        if os.path.exists(self.dest_dir_name):
            logging.error("Destination already exists, aborting")
            raise DiscogsTaggerError, "'%s' already exists." % \
                        self.dest_dir_name
        else:
            logging.info("Creating destination directory '%s'" \
                            % self.dest_dir_name)
            os.mkdir(self.dest_dir_name)

        for track in self.file_tag_map:
            shutil.copyfile(self.file_tag_map[track][0], \
                os.path.join(self.dest_dir_name, self.file_tag_map[track][1]))

            filetype = os.path.splitext(self.file_tag_map[track][1])[1]
            if filetype == '.mp3':
                self._tag_mp3(track)
            elif filetype == '.flac':
                self._tag_flac(track)

        if not self.keep_original:
            logging.info("Deleting source directory '%s'" % self.sourcedir)
            shutil.rmtree(self.sourcedir) 
            
    @property
    def dest_dir_name(self):
        """ generates new album directory name """

        path_name = os.path.dirname(self.sourcedir)
        dest_dir = self.clean_filename(self._value_from_tag(self.dir_format))
        
        return os.path.join(path_name, dest_dir)

    @property
    def m3u_filename(self):
        """ generates the m3u file name """

        m3u = self._value_from_tag(self.m3u_format)
        return self.clean_filename(m3u)

    @property
    def nfo_filename(self):
        """ generates the nfo file name """
        
        nfo = self._value_from_tag(self.nfo_format)
        return self.clean_filename(nfo)

    @staticmethod
    def write_file(filecontents, filename):
        """ writes a string of data to disk """

        if not os.path.exists(os.path.dirname(filename)):
            os.makedirs(os.path.dirname(filename))

        logging.debug("Writing file '%s' to disk" % filename)

        try:
            fh = open(filename, 'w')
            fh.write(filecontents) 
            fh.close()
        except:
            logging.error("Unable to write file '%s'" % filename)
            
 
    def create_nfo(self):
        """ Writes the .nfo file to disk. """

        return self.write_file(self.album_info, os.path.join(self.dest_dir_name,\
                 self.nfo_filename))
 
    def create_m3u(self):
        """ Generates the playlist for the given albm.
            Adhering to the following m3u format.

            ---
            #EXTM3U
            #EXTINF:233,Artist - Song
            directory\file_name.mp3.mp3
            #EXTINF:-1,My Cool Stream
            http://www.site.com:8000/listen.pls
            ---

            Taken from http://forums.winamp.com/showthread.php?s=&threadid=65772
        """

        m3u =  "#EXTM3U\n"
        for i in self.file_tag_map:
            m3u += "#EXTINF:-1,%s - %s\n" % (self.tracks[i][0], \
                        self.tracks[i][1]) 
            m3u += "%s\n" % self.file_tag_map[i][1]

        return self.write_file(m3u, os.path.join(self.dest_dir_name,\
                        self.m3u_filename))

    @memoized_property
    def file_tag_map(self):
        """ Returns a dict containing the files from the target directory that 
            we wish to tag. 
            { NUM : (oldfilename, newfilename)} """

        file_list = {}
        try:
            target_list = os.listdir(self.sourcedir)
            target_list.sort()
        except OSError, e:
            if e.errno == errno.EEXIST:
                logging.error("No such directory '%s'", self.sourcedir)
                raise DiscogsTaggerError, "No such directory"
            else:
                logging.error("File system error '%s'" % errno[e])
                raise DiscogsTaggerError, "File system error"
            return None
        
        i = 1
        for f in target_list:
            if f.lower().endswith(Tagger.FILE_TYPE):
                fileext = os.path.splitext(f)[1]
                newfile = self._value_from_tag(self.song_format,\
                           i, fileext)
                file_list[i] = (os.path.join(self.sourcedir, f), \
                                self.clean_filename(newfile))
                i += 1
        return file_list

    def get_images(self):
        """ Download and store any available images """

        if self.images:
            for i, image in enumerate(self.images):
                logging.debug("Downloading image '%s'" % image)
                try:
                    url_fh = TagOpener()
                    url_fh.retrieve(image, os.path.join(self.dest_dir_name,\
                            "00-image-%.2d.jpg" % i))
                except:
                    logging.error("Unable to download image '%s', skipping." % image)

    @staticmethod
    def clean_filename(f):
        """ Removes unwanted characters from file names """

        a = unicode(f, "utf-8")

        for k,v in Tagger.CHAR_EXCEPTIONS.iteritems():
            a = a.replace(k, v)

        a = unicodedata.normalize('NFKD', a).encode('ascii', 'ignore')

        cf = re.compile(r'[^-\w.\(\)_]')
        return cf.sub('', str(a))

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

    p.set_defaults(conffile=os.path.join(os.getenv("HOME"),'.discogs_tagger.conf'))
    (options, args) = p.parse_args()

    if not options.releaseid:
        p.error("Please specify the discogs.com releaseid ('-r')")

    if not options.sdir or not os.path.exists(options.sdir):
        p.error("Please specify a valid source directory ('-s')")

    config = ConfigParser.ConfigParser()
    config.read(options.conffile)

    logging.basicConfig(level=config.getint('logging', 'level'))

    release = Tagger(options.sdir, options.releaseid)
    release.keep_original = config.getboolean('details', 'keep_original')
    release.nfo_format = config.get('file-formatting','nfo')
    release.m3u_format = config.get('file-formatting','m3u')
    release.dir_format = config.get('file-formatting','dir')
    release.song_format = config.get('file-formatting','song')
    release.group_name = config.get('details', 'group')

    logging.info("Tagging album '%s - %s'" % (release.artist, release.title))
    release.tag_album()
    logging.info("Generating .nfo file")
    release.create_nfo()
    logging.info("Generating .m3u file")
    release.create_m3u()
    logging.info("Downloading and storing images")
    release.get_images()

    logging.info("Tagging complete.")
