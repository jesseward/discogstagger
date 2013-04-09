import logging
import re
import discogs_client as discogs

logger = logging.getLogger(__name__)

class TrackContainer(object):
    """ Class used to describe a tracklisting, typical properties are
        artist, title, position, orig_file, new_file """

    pass

class DiscogsAlbum(object):
    """ Wraps the discogs-client-api script, abstracting the minimal set of
        artist data required to tag an album/release 

        >>> from discogstagger.discogsalbum import DiscogsAlbum
        >>> release = DiscogsAlbum(40522) # fetch discogs release id 40522
        >>> print "%s - %s (%s / %s)" % (release.artist, release.title, release.catno,
        >>> release.label)
        
        Blunted Dummies - House For All (12DEF006 / Definitive Recordings)

        >>> for song in release.tracks: print "[ %.2d ] %s - %s" % (song.position,
        >>> song.artist, song.title)

        [ 01 ] Blunted Dummies - House For All (Original Mix)
        [ 02 ] Blunted Dummies - House For All (House 4 All Robots Mix)
        [ 03 ] Blunted Dummies - House For All (Eddie Richard's Mix)
        [ 04 ] Blunted Dummies - House For All (J. Acquaviva's Mix)
        [ 05 ] Blunted Dummies - House For All (Ruby Fruit Jungle Mix) """


    def __init__ (self, releaseid):

        self.release = discogs.Release(releaseid)
        discogs.user_agent = "discogstagger +http://github.com/jesseward"
        logger.info("Fetching %s - %s (%s)" % (self.artist, self.title,
                        releaseid))

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
        for song in self.tracks:
            r += "%.2d. %s - %s\n" % (song.position, song.artist, song.title)
        return r

    @property
    def releaseid(self):
        """ retuns the discogs release id """

        return self.release._id

    @property
    def catno(self):
        """ Returns the release catalog number """

        return self.release.data["labels"][0]["catno"]

    @property
    def label(self):
        """ Returns the release Label name """

        return self.clean_name(self.release.data["labels"][0]["name"])
    
    @property
    def images(self):
        """ return a single list of images for the given album """

        try:
            return [ x["uri"] for x in self.release.data["images"] ]
        except KeyError:
            pass
    
    @property
    def title(self):
        """ return the album release name from discogs API """

        return self.release.title
   
    @property 
    def year(self):
        """ returns the album release year obtained from API 2.0 """

        good_year = re.compile("\d\d\d\d")
        try:
            return good_year.match(str(self.release.data["year"])).group(0)
        except IndexError:
            return "1900"

    @property
    def master_id(self):
        """ returns the master release id """

        try:
            return self.release.data["master_id"]
        except KeyError:
            return None

    @property
    def genre(self):
        """ obtain the album genre """ 

        return self.release.data["styles"][0]

    def _gen_artist(self, artist_data):
        """ yields a list of normalized release artists name properties """

        for x in artist_data:
            yield x.name

    @property
    def artist(self):
        """ obtain the album artist """

        rel_artist = " & ".join(self._gen_artist(self.release.artists))
        return self.clean_name(rel_artist)
    
    @property
    def tracks(self):
        """ provides the tracklist of the given release id """
        
        track_list = []
        for i, t in enumerate((x for x in self.release.tracklist
                 if x["type"] == "Track") ):
            try:
                artist = self.clean_name(t["artists"][0].name)
            except IndexError:
                artist = self.artist

            track = TrackContainer()
            track.position = i + 1 
            track.artist = artist
            track.title = t["title"]
            track_list.append(track)
        return track_list

    @staticmethod
    def clean_name(clean_target):
        """ Cleans up the format of the artist or label name provided by Discogs. 
            Examples:
                'Goldie (12)' becomes 'Goldie'
                  or
                'Aphex Twin, The' becomes 'The Aphex Twin' 
            Accepts a string to clean, returns a cleansed version """

        groups = {
            "(.*),\sThe$" : "The",
        }

        # remove discogs duplicate handling eg : John (1)
        clean_target = re.sub("\s\(\d+\)", "", clean_target)

        for regex in groups:
            if re.search(r"%s" % regex, clean_target):
                clean_target = "%s %s" % (groups[regex], re.search("%s" % regex,
                clean_target).group(1))
        return clean_target
