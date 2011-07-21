#!/usr/bin/env python

import sys
import os
import errno
import re
import time
import shutil
from urllib import FancyURLopener
import discogs_client as discogs

reload(sys)
sys.setdefaultencoding('utf-8')

# Character substitutions in file name
CHAR_EXCEPTIONS = {
            '&' : 'and',
            ' ' : '_',
            '#' : 'Number',
            }

# supported file types.
FILE_TYPE = ('.mp3', '.flac',)

class TagOpener(FancyURLopener, object):
    version = 'ogstag/1.1 +http://github.com/jesseward'


class Album(object):
    """ Wraps the discogs-client-api script, abstracting the minimal set of
        artist data required to tag an album/release """


    def __init__ (self, releaseid):

        try:
            self.release = discogs.Release(releaseid)
            discogs.user_agent = 'jwtest'
        except:
            print "error"

    def __str__(self):
        
        return "<%s - %s>" % (self.artist, self.title)

    def album_info(self):
        """ Dumps the release data to a formatted text string. Formatted for
            .nfo file  """
        
        div = "_ _______________________________________________ _ _\n"
        r = div
        r += " Name : %s - %s\n" % (self.artist, self.title)
        r += "Label : %s\n" % (self.label)
        r += "Genre : %s\n" % (self.genre)
        r += "Catno : %s\n" % (self.catno)
        r += " Year : %s\n" % (self.year)
        r += "  URL : http:/www.discogs.com/release/%s\n" % (self.release._id)
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
        for i, t in enumerate(self.release.tracklist):
            if t['type'] == 'Track':
                try:
                    artist = t['artists'][0].name
                except IndexError:
                    artist = self.artist
                tracklist[i+1] = [artist, t['title']]
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
    
    
    def __init__(self, destdir, ogsrelid, cfgpar):
        self.destdir = destdir
        self.cfgpar = cfgpar
        Album.__init__(self, ogsrelid)

    def _value_from_tag(self, fileformat, trackno=1, filetype='.mp3'):
        """ Generates the filename tagging map """

        property_map = {
            "%ALBTITLE%": self.title,
            "%ALBARTIST%": self.artist,
            "%YEAR%": self.year,
            "%CATNO%": self.catno,
            "%GENRE%": self.genre,
            "%GROUP%": self.cfgpar.get('details', 'group'),
            "%ARTIST%": self.tracks[trackno][0],
            "%TITLE%": self.tracks[trackno][1],
            "%TRACKNO%": "%.2d" % trackno,
            "%TYPE%": filetype,
        }

        for hashtag in property_map.keys():
            fileformat = fileformat.replace(hashtag, str(property_map[hashtag]))
        return fileformat
    
    @property
    def dest_dir_name(self):
        """ generates the new directory name """

        ddir = os.path.dirname(self.destdir)
        ddir = os.path.join(ddir, \
               self._value_from_tag(self.cfgpar.get('file-formatting','dir')))

        return self.clean_filename(ddir)

    @property
    def m3u_filename(self):
        """ generates the m3u file name """

        m3u = self._value_from_tag(self.cfgpar.get('file-formatting', 'm3u'))
        return self.clean_filename(m3u)

    @property
    def nfo_filename(self):
        """ generates the nfo file name """
        
        nfo = self._value_from_tag(self.cfgpar.get('file-formatting', 'nfo'))
        return self.clean_filename(nfo)

    @staticmethod
    def write_file(filename, filecontents):

        pass
        
    def create_m3u(self):
        """ m3u format
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
        for trk in self.trk_list:
            m3u += "#EXTINF:-1,%s\n%s\n" % (trk[1], trk[0]) 

        return m3u

    @property 
    def file_tag_map(self):
        """ Returns a dict containing the files from the target directory that 
            we wish to tag. 
            { NUM : (oldfilename, newfilename)} """

        file_list = {}
        try:
            target_list = os.listdir(self.destdir)
            target_list.sort()
        except OSError, e:
            if e.errno == errno.EEXIST:
                pass
            else:
                pass
            return None
        
        i = 1
        for f in target_list:
            if f.lower().endswith(FILE_TYPE):
                fileext = os.path.splitext(f)[1]
                newfile = self._value_from_tag(self.cfgpar.get('file-formatting','song'),\
                           i, fileext)
                file_list[i] = (os.path.join(self.destdir, f), newfile)
                i += 1
        return file_list

    @staticmethod
    def clean_filename(f):
        """ Removes unwanted characters from file names """

        a = unicode(f).encode("utf-8")

        for k,v in CHAR_EXCEPTIONS.iteritems():
            a = a.replace(k, v)

        cf = re.compile(r'[^-\w.\(\)_]')
        return cf.sub('', str(a))

if __name__ == "__main__":

    import logging
    import ConfigParser
    from optparse import OptionParser
    
    logging.basicConfig(level=logging.DEBUG)
    p = OptionParser()
    p.add_option("-r", "--releaseid", action="store", dest="releaseid",
                 help="The discogs.com release id of the target album")
    p.add_option("-d", "--dest", action="store", dest="ddir",
                 help="The directory that you wish to tag")
    p.add_option("-c", "--conf", action="store", dest="conffile",
                 help="The discogstagger configuration file.")

    p.set_defaults(conffile=os.path.join(os.getenv("HOME"),'.discogs_tagger.conf'))
    (options, args) = p.parse_args()

    if not options.releaseid:
        p.error("Please specify the discogs.com releaseid ('-r')")

    if not options.ddir or not os.path.exists(options.ddir):
        p.error("Please specify a valid destination directory ('-d')")

    config = ConfigParser.ConfigParser()
    config.read(options.conffile)

    release = Tagger(options.ddir, options.releaseid, config)
    print release.nfo_filename
    print release.m3u_filename
    print release.dest_dir_name
    print release.file_tag_map
