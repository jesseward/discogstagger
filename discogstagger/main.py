#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import imghdr
import os
import errno
import shutil
import sys

import logging

from logging.config import fileConfig
from six.moves import configparser

import click

from discogstagger.taggerutils import TaggerUtils
from discogstagger.discogsalbum import DiscogsAlbum
from discogstagger.discogswrapper import DiscogsWrapper
from mediafile import MediaFile

click.disable_unicode_literals_warning = True


def mkdir_p(path):
    """Wrapper around os.makedirs. Silently suppresses errno.EEXIST as long as the
    destination path is a directory.

    :param path: target directories to create."""

    try:
        os.makedirs(path)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


class TaggerConfig():
    def __init__(self, source_dir, dest_dir, conf_file):
        self.config = configparser.RawConfigParser()
        self.config.read(conf_file)
        self.source_dir = source_dir
        self.dest_dir = dest_dir

        self._release_tags = None

    def _config_override(self, section, config_key, method='get'):
        """Performs a look-up against any release level overrides providing by the user.
        Instead of first pulling the config value from the global config, we check for
        the presence of an local value and return that if present.

        :param section: configparser section name
        :param config_key: configparser key name
        :param method: configparser lookup method (getboolean, get)"""
        cfg = getattr(self.config, method)
        config_value = cfg(section, config_key)

        if config_key in self.release_tags:
            config_value = self.relase_tags[config_key]

        return config_value

    @property
    def char_exceptions(self):
        exceptions = self.config._sections['character_exceptions']

        KEYS = {
            "{space}": " ",
        }

        try:
            del exceptions["__name__"]
        except KeyError:
            pass

        for k in KEYS:
            try:
                exceptions[KEYS[k]] = exceptions.pop(k)
            except KeyError:
                pass

        return exceptions

    @property
    def copy_other_files(self):
        return self.config.getboolean('options', 'copy_other_files')

    @property
    def dir_format_batch(self):
        return 'dir'

    @property
    def disc_folder_name(self):
        return self._config_override('file-formatting', 'discs')

    @property
    def dir_format(self):
        return self._config_override('file-formatting', 'dir')

    @property
    def embed_coverart(self):
        return self.config.getboolean('options', 'embed_coverart')

    @property
    def encoder_tag(self):
        return self._config_override('tags', 'encoder')

    @property
    def first_image_name(self):
        return 'folder.jpg'

    @property
    def group_name(self):
        return self._config_override('options', 'group')

    @property
    def id_tag(self):
        return self.config.get('batch', 'id_tag')

    @property
    def id_file(self):
        return self.config.get('batch', 'id_file')

    @property
    def images_format(self):
        return self._config_override('file-formatting', 'images')

    @property
    def keep_tags(self):
        return self._config_override('options', 'keep_tags')

    @property
    def keep_original(self):
        return self.config.getboolean('options', 'keep_original')

    @property
    def m3u_format(self):
        return self.config.get('file-formatting', 'm3u')

    @property
    def nfo_format(self):
        return self.config.get('file-formatting', 'nfo')

    @property
    def release_tags(self):
        """Allows overriding of global config for individual releases."""

        if self._release_tags is None:
            my_tags = {}
            if os.path.exists(os.path.join(self.source_dir, self.id_file)):
                with open(os.path.join(self.source_dir, self.id_file)) as tag_file:
                    for line in tag_file:
                        name, var = line.partition('=')[::2]
                        my_tags[name.strip()] = var
            self._release_tags = my_tags
        return self._release_tags

    @property
    def song_format(self):
        return self._config_override('file-formatting', 'song')

    @property
    def split_artists(self):
        return self._config_override('options', 'split_artists').strip('"')

    @property
    def split_discs(self):
        return self._config_override('options', 'split_discs', method='getboolean')

    @property
    def split_discs_extension(self):
        if self.split_discs:
            return self._config_override('options', 'split_discs_extension').strip('"')
        return None

    @property
    def split_discs_folder(self):
        return self._config_override('options', 'split_discs_folder', method='getboolean')

    @property
    def split_genres_and_styles(self):
        return self._config_override('options', 'split_genres_and_styles').strip('"')

    @property
    def use_lower_filenames(self):
        return self.config.getboolean('options', 'use_lower_filenames')

    @property
    def use_folder_jpg(self):
        return self.config.getboolean('options', 'use_folder_jpg')

    @property
    def use_style(self):
        return self._config_override('options', 'use_style', method='getboolean')

    @property
    def va_song_format(self):
        return self._config_override('file-formatting', 'va_song')

    @property
    def write_m3u(self):
        return self.config.getboolean('options', 'write_m3u')

    @property
    def write_nfo(self):
        return self.config.getboolean('options', 'write_nfo')


def default_config():
    """Provides a default configuration file location."""
    return os.path.expanduser('~/.config/discogstagger/discogs_tagger.conf')


def init_logging(conf):
    fileConfig(conf)
    return logging.getLogger(__name__)


@click.command()
@click.option('-c', '--conf', default=default_config(), help='The discogstagger configuration file.')
@click.option('-d', '--destination', help='The (base) directory to copy the tagged files to')
@click.option('-r', '--releaseid', help='The discogs.com release id of the target album')
@click.option('-s', '--source', help='The directory that you wish to tag', type=click.Path(exists=True))
def tagger(conf, destination, releaseid, source):

    _log = init_logging(conf)
    if not destination:
        destination = source

    cfg = TaggerConfig(source, destination, conf)

    if cfg.id_tag in cfg.release_tags:
        release_id = cfg.release_tags[cfg.id_tag].strip()

    if releaseid:
        release_id = releaseid

    if not releaseid:
        click.echo('Please specify the discogs.com releaseid ("-r")')
        sys.exit(1)

    _log.info('Attempting to tag files from target destination={0}'.format(destination))

    discogs_release = DiscogsAlbum(DiscogsWrapper().discogs, release_id, cfg.split_artists, cfg.split_genres_and_styles)
    release = TaggerUtils(discogs_release, cfg)

    # ensure we were able to map the release appropriately.
    if not release.tag_map:
        _log.fatal("Unable to map available audio files to the number of tracks in the Discogs release '{0}'. Exiting".format(
                   release_id))
        sys.exit(1)

    artist = cfg.split_artists.join(release.album.artists)
    artist = release.album.clean_name(artist)

    _log.info("Tagging album '{0} - {1}'".format(artist, release.album.title))

    dest_dir_name = release.dest_dir_name

    if os.path.exists(dest_dir_name):
        _log.fatal('Destination directory already exists. directory={0}. Aborting operation'.format(dest_dir_name))
        sys.exit(1)
    else:
        _log.info("Creating destination directory '{0}'".format(dest_dir_name))
        mkdir_p(dest_dir_name)

    _log.info("Downloading and storing images")
    release.album.get_images(dest_dir_name, cfg.images_format, cfg.first_image_name)

    disc_names = dict()
    folder_names = dict()
    if release.album.disctotal > 1 and cfg.split_discs_folder:
        _log.debug("Creating disc structure")
        for i in range(1, release.album.disctotal + 1):
            folder_name = "%s%.d" % (release.album_folder_name, i)
            disc_dir_name = os.path.join(dest_dir_name, folder_name)
            mkdir_p(disc_dir_name)
    # This is duplicate, remove one of the following statements
            disc_names[i] = disc_dir_name
            folder_names[i] = folder_name
    else:
        folder_names[1] = ""

    for track in release.tag_map:
        # copy old file into new location
        if release.album.disctotal > 1 and cfg.split_discs_folder:
            target_folder = disc_names[int(track['discnumber'])]
        else:
            target_folder = dest_dir_name

        _log.debug("Source file {0}".format(os.path.join(source, track['orig_file'])))
        _log.info("Writing file {0}".format(os.path.join(target_folder, track['new_file'])))
        _log.debug("metadata -> {0:2d} {1} - {2}".format(track['tracknumber'], track['artist'], track['title']))
        _log.debug("----------> {0}".format(track['new_file']))

        shutil.copyfile(track['orig_file'], os.path.join(target_folder, track['new_file']))

        # load metadata information
        metadata = MediaFile(os.path.join(target_folder, track['new_file']))

        # read already existing (and still wanted) properties
        keep_tags = {}
        if cfg.keep_tags:
            for name in cfg.keep_tags.split(","):
                try:
                    getattr(metadata, name)
                except AttributeError:
                    _log.warn('Unable to keep_tag. tag={0}'.format(name))
                    continue
                keep_tags[name] = getattr(metadata, name)

        # remove current metadata
        metadata.delete()

        # set album metadata
        metadata.album = release.album.title

        if cfg.split_discs_folder and release.album.disctotal > 1:
            # the fileext should be stored on the album/track as well
            fileext = os.path.splitext(track['orig_file'])[1]
            disc_title_extension = release._value_from_tag_format(cfg.split_discs_extension,
                                                                  track['tracknumber'],
                                                                  track['position'] - 1, fileext)
            metadata.album = "{0}{1}".format(metadata.album, disc_title_extension)

        metadata.composer = artist
        metadata.albumartist = artist
        metadata.albumartist_sort = release.album.sort_artist
        metadata.label = release.album.label
        metadata.year = release.album.year
        metadata.country = release.album.country
        metadata.url = release.album.url
        # add styles to the grouping tag (right now, we can just use one)
        metadata.grouping = release.album.styles

        # adding two as there is no standard. discogstagger pre v1
        # used (TXXX desc="Catalog #")
        # mediafile uses TXXX desc="CATALOGNUMBER"
        metadata.catalognum = release.album.catno
        metadata.catalognumber = release.album.catno

        # use the correct genre field, on config use the first style
        genre = release.album.genres
        if cfg.use_style:
            genre = release.album.style

        metadata.genre = genre
        metadata.discogs_id = release_id

        if release.album.disctotal and release.album.disctotal > 1 and track['discnumber']:
            _log.debug("writing disctotal and discnumber")
            metadata.disc = track['discnumber']
            metadata.disctotal = release.album.disctotal

        if release.album.is_compilation:
            metadata.comp = True

        metadata.comments = release.album.note

        # encoder
        if cfg.encoder_tag is not None:
            metadata.encoder = cfg.encoder_tag

        #    if track.discsubtotal:
        #        metadata.discsubtotal = track.discsubtotal

        # set track metadata
        metadata.title = track['title']
        metadata.artist = track['artist']
        metadata.artist_sort = track['sortartist']
        metadata.track = track['tracknumber']

        # the following value will be wrong, if the disc has a name or is a multi
        # disc release --> fix it
        metadata.tracktotal = release.album.tracktotal_on_disc(track['discnumber'])

        # it does not make sense to store this in the "common" configuration, but only in the
        # id.txt. we use a special naming convention --> most probably we should reuse the
        # configuration parser for this one as well, no?
        for name, value in list(cfg.release_tags.items()):
            if name.startswith("tag:"):
                name = name.split(":")
                name = name[1]
                setattr(metadata, name, value)

        first_image_name = cfg.first_image_name
        # this should be done in a cleaner way to avoid multiple images in different
        # folders (use the dest_dir again....)
        if cfg.embed_coverart and os.path.exists(os.path.join(dest_dir_name,
                                                 first_image_name)):
            imgdata = open(os.path.join(dest_dir_name,
                           first_image_name), 'rb').read()
            imgtype = imghdr.what(None, imgdata)

            if imgtype in ("jpeg", "png"):
                _log.debug("Embedding album art.")
                metadata.art = imgdata

        if keep_tags is not None:
            for name in keep_tags:
                setattr(metadata, name, keep_tags[name])

        metadata.save()

    # start supplementary actions

    if cfg.write_nfo:
        _log.info("Generating .nfo file")
        release.create_nfo()

    # adopt for multi disc support
    if cfg.write_m3u:
        _log.info("Generating .m3u file")
        release.create_m3u(folder_names)

    # copy "other files" on request
    if cfg.copy_other_files and len(release.copy_files) > 0:
        _log.info("copying files from source directory")
        copy_files = release.copy_files
        dir_list = os.listdir(source)
        _log.debug("start_dir: {0}".format(source))
        _log.debug("dir list: {0}".format(dir_list))
        file_list = [os.path.join(source, x) for x in dir_list if not x.lower().endswith(TaggerUtils.FILE_TYPE) and
                     os.path.isfile(os.path.join(source, x))]
        copy_files.extend(file_list)

        for fname in copy_files:
            if not fname.endswith(".m3u"):
                _log.debug("source: {0}".format(fname))
                _log.debug("target: {0}".format(os.path.join(dest_dir_name, os.path.basename(fname))))
                shutil.copyfile(fname, os.path.join(dest_dir_name, os.path.basename(fname)))

    # remove source directory, if configured as such.
    if not cfg.keep_original:
        _log.info("Deleting source directory '{0}'".format(source))
        shutil.rmtree(source)

    _log.info("Tagging complete.")


if __name__ == '__main__':
    tagger()
