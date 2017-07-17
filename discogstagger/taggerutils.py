# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function

import errno
import os
import re
import logging

from unicodedata import normalize


class TaggerUtils(object):
    """ Accepts a destination directory name and discogs release id.
    TaggerUtils returns a the corresponding metadata information , in which
    we can write to disk. The assumption here is that the destination
    direcory contains a single album in a support format (mp3 or flac).

    The class also provides a few methods that create supplimental files,
    relvant to a given album (m3u, nfo file and album art grabber.)"""

    # supported file types.
    FILE_TYPE = ('.mp3', '.flac',)

    def __init__(self, discogs_album, tagger_config):

        self._log = logging.getLogger(__name__)
        self.tagger_config = tagger_config
        self.sourcedir = tagger_config.source_dir
        self.destdir = tagger_config.dest_dir
        self._dest_dir_name = None

        result = self._get_target_list()
        self.files_to_tag = result['target_list']

        if tagger_config.copy_other_files:
            self.copy_files = result['copy_files']
        self.album = discogs_album

        if len(self.files_to_tag) == len(self.album.tracks):
            self.tag_map = self._get_tag_map()
        else:
            self._log.error('Unbalanced files_to_tag vs album.tracks. len(files_to_tag)={0}, len(album.tracks)={1})'.format(len(self.files_to_tag), len(self.album.tracks)))
            self._log.debug('Unmatched files_to_tag. files_to_tag={0}'.format(self.files_to_tag))
            self._log.debug('Ummatched album.tracks. album.tracks={0}'.format(self.album.tracks))
            self.tag_map = None

    def _value_from_tag_format(self, fmt, trackno=1, position=1, filetype=".mp3"):
        """ Fill in the used variables using the track information """

        self._log.debug('parameters given: fmt: %s' % fmt)
        self._log.debug('parameters given: trackno: %d' % trackno)
        self._log.debug('parameters given: position: %d' % position)
        self._log.debug('paramerter avail: position: %d' % len(self.album.tracks))

        property_map = {
            '%ALBTITLE%': self.album.title,
            '%ALBARTIST%': self.album.artist,
            '%YEAR%': self.album.year,
            '%CATNO%': self.album.catno,
            '%GENRE%': self.album.genre,
            '%STYLE%': self.album.style,
            '%GROUP%': self.tagger_config.group_name,
            # could go wrong on multi discs (because of empty tracks with subdisc names)
            '%ARTIST%': self.album.tracks[position].artist,
            # see artist
            '%TITLE%': self.album.tracks[position].title,
            '%DISCNO%': str(self.album.tracks[position].discnumber),
            '%TRACKNO%': '%.2d' % trackno,
            '%TYPE%': filetype,
            '%LABEL%': self.album.label,
        }

        for hashtag in property_map:
            fmt = fmt.replace(hashtag, property_map[hashtag])
        self._log.debug('fmt output: %s' % fmt)

        return fmt

    def _value_from_tag(self, fmt, trackno=1, position=1, filetype='.mp3'):
        """ Generates the filename tagging map """

        fmt = self._value_from_tag_format(fmt, trackno, position, filetype)

        if self.tagger_config.use_lower_filenames:
            fmt = fmt.lower()

        self._log.debug('output: %s' % fmt)

        return fmt

    def _get_target_list(self):
        """ fetches a list of files in the self.sourcedir location. """

        copy_files = None
        try:
            dir_list = os.listdir(self.sourcedir)
            dir_list.sort()

            # strip unwanted files
            target_list = [os.path.join(self.sourcedir, x) for x in dir_list
                           if x.lower().endswith(TaggerUtils.FILE_TYPE)]
            if self.tagger_config.copy_other_files:
                copy_files = [os.path.join(self.sourcedir, x) for x in
                              dir_list if not x.lower().endswith(TaggerUtils.FILE_TYPE)]

            if not target_list:
                self._log.debug('target_list empty, try to retrieve sub directory')
                for y in dir_list:
                    tmp_list = []
                    self._log.debug('subdirectory: %s' % y)
                    sub_dir = os.path.join(self.sourcedir, y)
                    if os.path.isdir(sub_dir):
                        tmp_list.extend(os.listdir(sub_dir))
                        tmp_list.sort()
                        tmp_list = [os.path.join(sub_dir, y) for y in tmp_list]

                        # strip unwanted files
                        target_list.extend([z for z in tmp_list if z.lower().endswith(TaggerUtils.FILE_TYPE)])
                        if self.tagger_config.copy_other_files:
                            copy_files = [z for z in tmp_list if not
                                          z.lower().endswith(TaggerUtils.FILE_TYPE)]

        except OSError as e:
            if e.errno == errno.EEXIST:
                raise IOError('No such directory "%s"', self.sourcedir)
            else:
                raise IOError('General IO system error "%s"' % errno[e])

        return {'target_list': target_list, 'copy_files': copy_files}

    def _get_tag_map(self):
        """ matches the old with new via TargetTagMap object. """

        tag_map = []

        # ignore files that do not match FILE_TYPE
        for position, filename in enumerate(self.files_to_tag):
            self._log.debug('track position {0}'.format(position))
            # add the found files to the tag_map list
            self._log.debug('mapping {1} --> {1} - {2}'.format(filename,
                                                               self.album.tracks[position].artist,
                                                               self.album.tracks[position].title))
            track = self.album.tracks[position]._asdict()
            track['orig_file'] = filename
            fileext = os.path.splitext(filename)[1]

            # special handling for Various Artists discs
            if self.album.artist == 'Various':
                newfile = self._value_from_tag(self.tagger_config.va_song_format,
                                               track['tracknumber'], position, fileext)
            else:
                newfile = self._value_from_tag(self.tagger_config.song_format,
                                               track['tracknumber'], position, fileext)

            track['new_file'] = self._get_clean_filename(newfile)
            tag_map.append(track)

        return tag_map

    @property
    def dest_dir_name(self):
        """ generates new album directory name """

        if self._dest_dir_name is None:
            # determine if an absolute base path was specified.
            if os.path.isabs(self.destdir):
                path_name = os.path.normpath(self.destdir)
            else:
                path_name = os.path.dirname(os.path.normpath(self.destdir))

            dest_dir = ''
            for ddir in self.tagger_config.dir_format.split('/'):
                d_dir = self._get_clean_filename(self._value_from_tag(ddir))
                if dest_dir == '':
                    dest_dir = d_dir
                else:
                    dest_dir = os.path.join(dest_dir, d_dir)

            self._dest_dir_name = os.path.join(path_name, dest_dir)

        return self._dest_dir_name

    @property
    def album_folder_name(self):
        """ returns the album as the name for the sub-dir for multi disc
        releases"""

        folder_name = '%s%s' % (self._get_clean_filename(self.album.title), self.tagger_config.disc_folder_name)

        if self.tagger_config.use_lower_filenames:
            folder_name = folder_name.lower()

        return folder_name

    @property
    def m3u_filename(self):
        """ generates the m3u file name """

        m3u = self._value_from_tag(self.tagger_config.m3u_format)
        return self._get_clean_filename(m3u)

    @property
    def nfo_filename(self):
        """ generates the nfo file name """

        nfo = self._value_from_tag(self.tagger_config.nfo_format)
        return self._get_clean_filename(nfo)

    def _get_clean_filename(self, f):
        """ Removes unwanted characters from file names """
        filename, fileext = os.path.splitext(f)

        if fileext not in TaggerUtils.FILE_TYPE and fileext not in ['.m3u', '.nfo']:
            self._log.debug('fileext: %s' % fileext)
            filename = f
            fileext = ''

        for k in self.tagger_config.char_exceptions:
            filename = filename.replace(k, self.tagger_config.char_exceptions[k])
        filename = normalize('NFKD', filename)

        cf = re.compile(r'[^-\w.\(\)_\s]')
        cf = cf.sub('', filename)
        cf = cf.replace('__', '_')
        cf = cf.replace('_-_', '-')

        return '{0}{1}'.format(cf, fileext)

    def create_nfo(self):
        """ Writes the .nfo file to disk. """

        return write_file(self.album.album_info, os.path.join(self.dest_dir_name, self.nfo_filename))

    def create_m3u(self, folder_names):
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

        m3u = '#EXTM3U\n'
        for track in self.tag_map:
            m3u += '#EXTINF:-1,%s - %s\n' % (track['artist'], track['title'])
            folder_name = folder_names[track['discnumber']]
            if folder_name is not '':
                folder_name = '%s/' % folder_name
            m3u += '%s%s\n' % (folder_name, track['new_file'])

        return write_file(m3u, os.path.join(self.dest_dir_name, self.m3u_filename))


def write_file(filecontents, filename):
    """ writes a string of data to disk """

    _log = logging.getLogger(__name__)
    if not os.path.exists(os.path.dirname(filename)):
        os.makedirs(os.path.dirname(filename))

    _log.debug('Writing file "%s" to disk' % filename)

    try:
        with open(filename, 'w') as fh:
            fh.write(filecontents)
    except IOError:
        _log.error('Unable to write file "%s"' % filename)

    return True
