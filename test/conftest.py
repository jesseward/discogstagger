import pytest
import mock

from discogstagger.discogsalbum import DiscogsAlbum
from discogstagger.discogswrapper import DiscogsWrapper
from discogstagger.main import TaggerConfig


@pytest.fixture(scope='session')
def discogs_cfg():

    return TaggerConfig('responses/40522', 'responses/out', 'responses/discogs_tagger.conf')


@pytest.fixture(scope='session')
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
