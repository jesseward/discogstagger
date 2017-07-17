# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import pytest

from discogstagger.taggerutils import TaggerUtils


@pytest.fixture(scope='module')
def tagger_object(discogs_album, discogs_cfg):
    return TaggerUtils(discogs_album, discogs_cfg)


def test_tagger_attributes(tagger_object):
    assert tagger_object.sourcedir == 'responses/40522'
    assert tagger_object.destdir == 'responses/out'
    assert len(tagger_object.files_to_tag) == 5
    assert tagger_object.m3u_filename == '00-Blunted_Dummies-House_For_All.m3u'
    assert tagger_object.nfo_filename == '00-Blunted_Dummies-House_For_All.nfo'
    assert tagger_object.album_folder_name == 'House_For_All-CD'
    assert tagger_object.dest_dir_name == 'responses/Blunted_Dummies-House_For_All-(12DEF006)-1993-jW'


def test_tagger_value_from_tag_format(tagger_object):
    assert tagger_object._value_from_tag_format('%ALBTITLE%-%ALBARTIST%') == 'House For All-Blunted Dummies'


def test_tagger_get_clean_filename(tagger_object):
    assert tagger_object._get_clean_filename('Th!s%Is^^Ü+ TĚsŤ__') == 'ThsIsU_and_TEsT_'
