# discogstagger

## What is it

discogstagger is a console based audio meta-data tagger. Artist profile data is 
retrieved via the discogs.com API.

Simply provide the script with a destination directory name, that contains an
album consisting of either FLAC or MP3 media files and the discogs.com 
release-id. discogstaggs calls out to the discogs.com API and updates the
audio meta-data accordingly.

During the process, all album images (if present) are retrieved from the API. 
As well, a play-list (.m3u) and an information file (.nfo) are generated per
each release.

Optionally discogstagger will embed the found album art into the file meta data

## Requirements

* Mutagen 
* discogs-client 
* requests

I am also packaging/reusing the MediaFile library from the "beets" project. This
will be packaged with discogs tagger until MediaFile is split out to its own
package.

## Installation 

Fetch the repo from github
```
git clone https://github.com/jesseward/discogstagger.git
```

Install the script requirements
```
sudo pip install -r requirements.txt
```

Run through set-up script
```
sudo python setup.py install
```

## Configuration 

DiscogsTagger searches for the configuration file at the default location of
/etc/discogstagger/discogs_tagger.conf, at run-time. Or you're able to specify the config 
location with the '-c' switch.

The configuration file must be present to execute the script. The default 
settings (as shipped), should work without any modifications.

Note that you may wish to modify the following default configuration options. 
The defaults are shipped as such in attempt to be as non destructive as possible

```
# True/False : leaves a copy of the original audio files on disk, untouched after 
keep_original=True
# Embed cover art. Include album art from discogs.com in the metadata tags
embed_coverart=False
```
