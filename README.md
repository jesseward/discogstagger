# discogstagger

## What is it

discogstagger is a console based audio meta-data tagger. Artist profile data is 
retrieved via the discogs.com API.

Simply provide the script with a destination directory name, that contains an
album consisting of either FLAC or MP3 media files and the discogs.com 
release-id. discogstaggs calls out to the discogs.com API and updates the
audio meta-data accordingly.

If no release-id is given, the application checks, if a file "id.txt" exists
(the name of this file can be configured in the configuration) and if this file
contains a specific property (id_tag). If both is true the release-id from this
file is used. This is useful for batch processing.

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

## Examples

```
$ discogs_tagger.py -s Nine\ Inch\ Nails\ Pretty\ Hate\ Machine -r 145796
INFO:requests.packages.urllib3.connectionpool:Starting new HTTP connection (1): api.discogs.com
INFO:discogstagger.discogsalbum:Fetching Nine Inch Nails - Pretty Hate Machine (145796)
INFO:root:Tagging album 'Nine Inch Nails - Pretty Hate Machine'
INFO:root:Creating destination directory 'Nine_Inch_Nails-Pretty_Hate_Machine-(TVT_2610-2)-1989-jW'
INFO:root:Downloading and storing images
INFO:__main__:Writing file Nine_Inch_Nails-Pretty_Hate_Machine-(TVT_2610-2)-1989-jW/01-Nine_Inch_Nails-Head_Like_A_Hole.flac
INFO:__main__:Embedding album art.
INFO:__main__:Writing file Nine_Inch_Nails-Pretty_Hate_Machine-(TVT_2610-2)-1989-jW/02-Nine_Inch_Nails-Terrible_Lie.flac
INFO:__main__:Embedding album art.
INFO:__main__:Writing file Nine_Inch_Nails-Pretty_Hate_Machine-(TVT_2610-2)-1989-jW/03-Nine_Inch_Nails-Down_In_It.flac
INFO:__main__:Embedding album art.
INFO:__main__:Writing file Nine_Inch_Nails-Pretty_Hate_Machine-(TVT_2610-2)-1989-jW/04-Nine_Inch_Nails-Sanctified.flac
INFO:__main__:Embedding album art.
INFO:__main__:Writing file Nine_Inch_Nails-Pretty_Hate_Machine-(TVT_2610-2)-1989-jW/05-Nine_Inch_Nails-Something_I_Can_Never_Have.flac
INFO:__main__:Embedding album art.
INFO:__main__:Writing file Nine_Inch_Nails-Pretty_Hate_Machine-(TVT_2610-2)-1989-jW/06-Nine_Inch_Nails-Kinda_I_Want_To.flac
INFO:__main__:Embedding album art.
INFO:__main__:Writing file Nine_Inch_Nails-Pretty_Hate_Machine-(TVT_2610-2)-1989-jW/07-Nine_Inch_Nails-Sin.flac
INFO:__main__:Embedding album art.
INFO:__main__:Writing file Nine_Inch_Nails-Pretty_Hate_Machine-(TVT_2610-2)-1989-jW/08-Nine_Inch_Nails-Thats_What_I_Get.flac
INFO:__main__:Embedding album art.
INFO:__main__:Writing file Nine_Inch_Nails-Pretty_Hate_Machine-(TVT_2610-2)-1989-jW/09-Nine_Inch_Nails-The_Only_Time.flac
INFO:__main__:Embedding album art.
INFO:__main__:Writing file Nine_Inch_Nails-Pretty_Hate_Machine-(TVT_2610-2)-1989-jW/10-Nine_Inch_Nails-Ringfinger.flac
INFO:__main__:Embedding album art.
INFO:root:Generating .nfo file
INFO:root:Generating .m3u file
INFO:root:Tagging complete.
```
