import discogs_client as discogs
import re

class Album(object):

    def __init__ (self, releaseid):

        try:
            self.release = discogs.Release(releaseid)
            discogs.user_agent = 'jwtest'
        except:
            print "error"

        self.alb_images = self.__album_images()
        self.title = self.__album_title()
        self.year = self.__album_year()
        self.tracks = self.__album_tracks()
        self.genre = self.__album_genre()
        self.artist = self.__album_artist()
        #self.alb_label

    def album_info(self):
        """ ...  """
        div = "_ _______________________________________________ _ _\n"
        r = div
        r += " Name : %s - %s\n" % (self.artist, self.title)
        #r += "Label : %s\n" % (self.label)
        r += "Genre : %s\n" % (self.genre)
        #r += "Catno : %s\n" % (self.cat_num)
        r += " Year : %s\n" % (self.year)
        r += "  URL : http:/www.discogs.com/release/%s\n" % (self.release)
        r += div
        for key, value in self.tracks.items():
            r += "%.2d. %s - %s\n" % (key, self.artist, self.tracks[key])

        return r

    def __album_images(self):
        """ return a single list of images for the given album """
        return [ x['uri'] for x in self.release.data['images'] ]

    def __album_title(self):
        """ return the album release name from discogs API """
        return self.release.title
    
    def __album_year(self):
        """ returns the album release year obtained from API 2.0 """
        good_year = re.compile('\d\d\d\d')
        try:
            return good_year.match(str(self.release.data['year'])).group(0)
        except IndexError:
            return '1900'

    def __album_genre(self):
        """ obtain the album genre """ 
        return self.release.data['styles'][0]

    def __album_artist(self):
        """ obtain the album artist """
        artist = self.release.artists[0]
        return  artist.data['name']

    def __album_tracks(self):
        """ provides the tracklist of the given release id """
        tlist = [ tracklist['title'] for tracklist in self.release.tracklist \
                 if tracklist['type'] == 'Track' ]
        return dict(zip(xrange(1, len(tlist)+1), tlist))

    def __clean_name(self, clean_target, reposition=True):
        """ Cleans up the format of the artist or label name. 
            Examples:
                Goldie (12) , becomes Goldie
                  or
                'Aphex Twin, The' becomes 'The Aphex Twin' """

        groups = {
            '(.*),\sThe$' : 'The',
        }

        # remove discogs duplicate handling eg : John (1)
        clean_target = re.sub('\s\(\d+\)', '', clean_target)

        if reposition:
            for regex in groups:
                if re.search(r'%s' % regex, clean_target):
                    clean_target = "%s %s" % (groups[regex], re.search('%s' % regex,\
                    clean_target).group(1))
        return clean_target

class FileAction(object):
    
   def __init__(self, target_dir):
        self.target_dir = target_dir
        self.file_list = self.__get_file_list()

   def __get_file_list(self):
        file_list = []
        try:
            dir_list = os.listdir(target_dir)
            dir_list.sort()
        except :
            print "dir does not exist"

class Tagger(Album):

    def __init__(self, target_dir, releaseid):
        Album.__init__(releaseid) 
        FileAction.__init__(target_dir)
         
    def _do_mp3(self):
        pass        

    def _do_flac(self):
        pass

    def tag_release(self):
        """ calls the approprirate method for metadata modification """
        for track in tracks:
            if track.lower().endswith('.mp3'):
                self._do_mp3(track)
            elif track.lower().endswith('.flac'):
                self._do_flac(track)
