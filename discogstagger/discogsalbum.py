import logging
import os
import re
import shutil

import requests

logger = logging.getLogger(__name__)


class memoized_property(object):

    def __init__(self, fget, doc=None):
        self.fget = fget
        self.__doc__ = doc or fget.__doc__
        self.__name__ = fget.__name__

    def __get__(self, obj, cls):
        if obj is None:
            return self
        obj.__dict__[self.__name__] = result = self.fget(obj)
        return result


class TrackContainer(object):

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

    # remove all not needed parameters (these should be not handled in here)
    def __init__(self, discogs_handler, releaseid, split_artists, split_genres_and_styles):
        """Fetches a release from the discogs.com API

        :param discogs_handle: An instance of the DiscogsWrapper
        :param releaseid: A discogs release id
        :param split_artists: Boolean value indicating if artists should be split
        :param split_genres_and_styles: Boolean value indicating if genre/styles should be split."""

        self.release = discogs_handler.release(int(releaseid))

        self.split_artists = split_artists
        self.split_genres_and_styles = split_genres_and_styles

        self.discs = {}
        logger.info("Fetching %s - %s (%s)" % (self.artist, self.title,
                    releaseid))

    def __str__(self):

        return "<%s - %s>" % (self.artist, self.title)

    @property
    def album_info(self):
        """ Dumps the release data to a formatted text string. Formatted for
            .nfo file  """

        logger.debug("Writing nfo file")
        div = "_ _______________________________________________ _ _\n"
        r = div
        r += "  Name : %s - %s\n" % (self.artist, self.title)
        r += " Label : %s\n" % (self.label)
        r += " Genre : %s\n" % (self.genre)
        r += " Catno : %s\n" % (self.catno)
        r += "  Year : %s\n" % (self.year)
        r += "   URL : %s\n" % (self.url)

        if self.master_id:
            r += "Master : http://www.discogs.com/master/%s\n" % self.master_id

        r += div
        for song in self.tracks:
            r += "%.2d. %s - %s\n" % (song.position, song.artist, song.title)
        return r

    @property
    def releaseid(self):
        """ retuns the discogs release id """

        return self.release.id

    @property
    def url(self):
        """ returns the discogs url of this release """

        return "http://www.discogs.com/release/{0}".format(self.release.id)

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
            return [x["uri"] for x in self.release.data["images"]]
        except KeyError:
            pass

    @property
    def title(self):
        """ return the album release name from discogs API """

        return self.release.title

    @property
    def year(self):
        """ returns the album release year obtained from API 2.0.

        :return: A string representing the year in which the item was released."""

        good_year = re.compile("\d\d\d\d")
        release_date = self.release.data.get("year", "1900")
        parsed_year = good_year.match(str(release_date))

        # return a default year in the event the release did not include a year
        if not parsed_year:
            return "1900"

        return parsed_year.group(0)

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

        return self.release.data["genres"][0]

    @property
    def genres(self):
        """ obtain the album genre """

        rel_genres = self.split_genres_and_styles.join(self.release.data["genres"])
        return rel_genres

    @property
    def style(self):
        """ obtain the album styles """

        try:
            return self.release.data["styles"][0]
        except KeyError:
            return "Undefined"

    @property
    def styles(self):
        """ obtain the album styles in one field """

        # bugfix : add support for releases where the style is not set/defined
        # in the discogs database.
        try:
            all_styles = self.release.data["styles"]
        except KeyError:
            all_styles = ["Undefined", ]

        rel_styles = self.split_genres_and_styles.join(all_styles)
        return rel_styles

    def _gen_artist(self, artist_data):
        """ yields a list of normalized release artists name properties """

        for x in artist_data:
            # bugfix to avoid the following scenario, or ensure we're yielding
            # and artist object.
            # AttributeError: 'unicode' object has no attribute 'name'
            # [<Artist "A.D.N.Y*">, u'Presents', <Artist "Leiva">]
            try:
                yield self.clean_name(x.name)
            except AttributeError:
                pass

    @property
    def country(self):
        """ Obtain the country - a not so easy field, because it could mean
            the label country, the recording country, or.... """

        try:
            return self.release.data["country"]
        except KeyError:
            return "Unknown"

    @property
    def artists(self):
        """ obtain the album artists """

        return self._gen_artist(self.release.artists)

    @property
    def artist(self):
        """ obtain the album artist """

        return self.split_artists.join(self._gen_artist(self.release.artists))

    @property
    def sort_artist(self):
        """ obtain the album artist """

        return self.clean_name(self.release.artists[0].name)

    @property
    def note(self):
        """ obtain the note """
        value = False
        if "notes" in self.release.data:
            value = self.release.data["notes"]
        return value

    def disc_and_track_no(self, position):
        """ obtain the disc and tracknumber from given position """

        # some variance in how discogs releases spanning multiple discs
        # or formats are kept, add regexs here as failures are encountered
        NUMBERING_SCHEMES = (
            "^CD(?P<discnumber>\d+)-(?P<tracknumber>\d+)$",  # CD01-12
            "^(?P<discnumber>\d+)-(?P<tracknumber>\d+)$",    # 1-02
            "^(?P<discnumber>\d+).(?P<tracknumber>\d+)$",    # 1.05
        )

        for scheme in NUMBERING_SCHEMES:
            re_match = re.search(scheme, position)

            if re_match:

                logging.debug("Found a disc and track number")
                return {'tracknumber': re_match.group("tracknumber"),
                        'discnumber': re_match.group("discnumber")}

        logging.error("Unable to match multi-disc track/position")
        return False

    @property
    def disctotal(self):
        """ Obtain the number of discs for the given release. """

        # allows tagging of digital releases and vinyl.
        # sample format <format name="File" qty="2" text="320 kbps">
        # assumes all releases of name=File is 1 disc.
        if self.release.data["formats"][0]["name"] in ["File", "Vinyl"]:
            return 1

        return int(self.release.data["formats"][0]["qty"])

    def tracktotal_on_disc(self, discnumber):
        logger.debug("discs: %s" % self.discs)
        return self.discs[discnumber]

    @property
    def is_compilation(self):
        if self.release.data["artists"][0]["name"] == "Various":
            return True

        for format in self.release.data["formats"]:
            if "descriptions" in format:
                for description in format["descriptions"]:
                    if description == "compilation":
                        return True

        return False

    @memoized_property
    def tracks(self):
        """ provides the tracklist of the given release id """

        track_list = []
        discsubtitle = None

        for i, t in enumerate((x for x in self.release.tracklist
                              if x.position != '')):

            # this is pretty much the same as the artist
            # stuff in the album, try to refactor it
            try:
                sort_artist = self.clean_name(t.artists[0].name)
                artist = self.split_artists.join(self._gen_artist(t.artists))
            except IndexError:
                artist = self.artist
                sort_artist = self.sort_artist

            track = TrackContainer()

            # on multiple discs there do appears a subtitle as the first "track"
            # on the cd in discogs, this seems to be wrong, but we would like to
            # handle it anyway
            if t.title and not t.position and not t.duration:
                discsubtitle = t.title
                continue

            track.position = i + 1

            # if this is a multidisc release, fetch the disc number and
            # track details from disc_and_track_no .
            if self.disctotal > 1:
                pos = self.disc_and_track_no(t.position)
                track.tracknumber = int(pos["tracknumber"])
                track.discnumber = int(pos["discnumber"])

            # single disc release, we attempt to assign the track # from the
            # tracklist object. If we fail with a ValueError, this is a high
            # likelyhood of a non standard naming/numbering scheme (vinyl
            # releases), we then use the enumerate counter to assign the track
            # number
            else:
                try:
                    track.tracknumber = int(t.position)
                except ValueError:
                    track.tracknumber = i+1

                track.discnumber = 1
            self.discs[int(track.discnumber)] = int(track.tracknumber)

            if discsubtitle:
                track.discsubtitle = discsubtitle

            track.sortartist = sort_artist
            track.artist = artist

            track.title = t.title
            track_list.append(track)
        return track_list

    @staticmethod
    def clean_name(clean_target):
        """ Cleans up the format of the artist or label name provided by
            Discogs.
            Examples:
                'Goldie (12)' becomes 'Goldie'
                  or
                'Aphex Twin, The' becomes 'The Aphex Twin'
            Accepts a string to clean, returns a cleansed version """

        groups = (
            ("(.*)\s\(\d+\)", r"\g<1>"),   # Metro Area (3)->Metro Area
            ("(.*),\sThe$", "The \g<1>"),  # Aphex Twin, The->The Aphex Twin
        )

        for regex in groups:
            clean_target = re.sub(regex[0], regex[1], clean_target)

        return clean_target

    def get_images(self, dest_dir_name, images_format, first_image_name):
        """Download and store any available images to local disk

        :param dest_dir_name: target save location for images
        :param images_format: image file naming format
        :param first_image_name: file name format for the first image."""

        if not self.images:
            logger.info("No images to download.")
            return

        for i, image in enumerate(self.images, 0):
            picture_name = ""
            if i == 0:
                picture_name = first_image_name
            else:
                picture_name = images_format + "-%.2d.jpg" % i

            response = requests.get(image, stream=True)
            if response.status_code == 200:
                logger.debug(u"Downloaded image. release-id={release},url={url}".format(release=self.releaseid, url=image))
                with open(os.path.join(dest_dir_name, picture_name), "wb") as out_file:
                    shutil.copyfileobj(response.raw, out_file)
                del response
            else:
                logger.error(u"error response. http status code={code}, url={url}".format(code=response.status_code, url=image))
