import discogs_client as discogs
import re

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
        """ ...  """
        
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
    def catno(self):
        """ Returns the release catalog number """

        return self.release.data['labels'][0]['catno']

    @property
    def label(self):
        """ Returns the release Label name """

        return self.release.data['labels'][0]['name']
    
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
        return  self.__clean_name(artist.data['name'])
    
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

    def __clean_name(self, clean_target):
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
