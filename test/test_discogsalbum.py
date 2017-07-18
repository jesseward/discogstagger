import pytest
import mock

from discogstagger.discogsalbum import DiscogsAlbum
from discogstagger.discogswrapper import DiscogsWrapper


@pytest.fixture(scope='module')
def discogs_album():

    with open('responses/40522.json', 'rb') as fh:
        b = fh.read()

    with mock.patch('discogstagger.discogswrapper.DiscogsWrapper.is_authenticated', new_callable=mock.PropertyMock) as mock_authenticated:
        mock_authenticated.return_value = False

        with mock.patch('discogstagger.discogswrapper.DiscogsWrapper._get_request_token') as mock_token:
            mock_token.return_value = True
            with mock.patch('discogs_client.fetchers.RequestsFetcher') as mock_discogs_request_fetcher:

                dw = DiscogsWrapper()
                mock_discogs_request_fetcher.return_value = b, 200
                da = DiscogsAlbum(dw.discogs, 40522, '&', '&')
    return da


def test_discogs_release_properties(discogs_album):
    assert discogs_album.releaseid == 40522
    assert discogs_album.url == 'http://www.discogs.com/release/40522'
    assert discogs_album.catno == '12DEF006'
    assert discogs_album.label == 'Definitive Recordings'
    assert discogs_album.title == 'House For All'
    assert discogs_album.year == '1993'
    assert discogs_album.master_id == 206510
    assert discogs_album.genre == 'Electronic'
    assert discogs_album.genres == 'Electronic'
    assert discogs_album.style == 'House'
    assert discogs_album.country == 'Canada'
    assert discogs_album.artist == 'Blunted Dummies'
    assert discogs_album.note == '"House For All (Original Mix)" was originally released on the [r=183558]  '
    assert discogs_album.disctotal == 1
    assert discogs_album.is_compilation is False


def test_discogs_release_tracks(discogs_album):
    track_one = discogs_album.tracks[0]
    assert len(discogs_album.tracks) == 5
    assert track_one.tracknumber == 1
    assert track_one.discsubtitle is None
    assert track_one.sortartist == track_one.artist
    assert track_one.title == 'House For All (Original Mix)'


def test_discogs_release_str(discogs_album):
    with open('responses/40522.txt') as fh:
        str_rep = fh.read()
    assert str(discogs_album) == str_rep
    assert discogs_album.album_info == str_rep


def test_discogsalbum_clean_name():
    assert DiscogsAlbum.clean_name('Aphex Twin, The') == 'The Aphex Twin'
