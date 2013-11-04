# discogstagger

## What is it

discogstagger is a console based audio meta-data tagger for FLAC, Ogg and MP3 audio files. Album, artist and track data profile is retrieved via the discogs.com API and then saved to the related metadata fields in the audio container.

To tag an album, provide the script with a target directory name (-s), that contains an album consisting of supported media files as well as the discogs.com release-id (-r). discogstagger calls out to the discogs.com API and updates the audio meta-data accordingly.

If no release-id is given, the application checks, if a file "id.txt" exists (the name of this file can be configured in the configuration) and if this file contains a specific property (id_tag). If both is true the release-id from this
file is used. This is useful for batch processing.

During the process, all album images (if present) are retrieved from the API.  As well, a play-list (.m3u) and an information file (.nfo) are generated per each release.

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

DiscogsTagger searches for the configuration file at the default location of ~/.config/discogstagger/discogs_tagger.conf, at run-time. Or you're able to specify the config location with the '-c' switch.

The configuration file must be present to execute the script. The default settings (as shipped), should work without any modifications.

Note that you may wish to modify the following default configuration options. The defaults are shipped as such in attempt to be as non destructive as possible

```
# True/False : leaves a copy of the original audio files on disk, untouched after 
keep_original=True
# Embed cover art. Include album art from discogs.com in the metadata tags
embed_coverart=False
```

To specify genre in your tags, review the use_style option. With use_style set to True, you're instructing discogstagger to pull the "Style" field. The style field is typically more genre specific than the discogs "Genre" field. In the example below (40522) 
with use_style=True, the genre field is tagged as "House".

```
Use Discogs "style" elements instead of the genre as the genre Meta-Tag in files (True)
Example http://www.discogs.com/Blunted-Dummies-House-For-All/release/40522
Style = House
Genre = Electronic
use_style=True
```

To keep already existing tags, you can include these tags in the configuration as well.  Usually Rippers (e.g. RubyRipper) do include the freedb_id, which could be kept using the following configuration. The list of all tags could be taken from the file 
discogstagger/ext/mediafile.py.

```
# Keep the following tags
keep_tags=freedb_id
```

Furthermore you can use lowercase directory and filenames using the following configuration:

```
# Use lowercase filenames
use_lower_filenames=True
```

For batch-mode tagging, it is not necessary anymore to provide the release-id via the '-r' parameter on the commandline. The same is possible by using a file (by default: id.txt) with the key/value pair 'discogs_id'. This can be configured in the configuration via the following parameters as well:

```
[batch]
# if no release id is given, the application checks if a file with the
# name id_file (in this case id.txt) is in the source directory,
# if it is there the id_tag is checked (discogs_id) and assigned to the
# release id
id_file=id.txt
id_tag=discogs_id
```

Please note, that right now there is no error-handling, if there is no '-r' parameter
and no id.txt file. The program will then just exit with an error message.

The command line takes the following parameters:

```
Usage: discogs_tagger.py [options]

Options:
  -h, --help            show this help message and exit
  -r RELEASEID, --releaseid=RELEASEID
                        The discogs.com release id of the target album
  -s SDIR, --source=SDIR
                        The directory that you wish to tag
  -d DESTDIR, --destination=DESTDIR
                        The (base) directory to copy the tagged files to
  -c CONFFILE, --conf=CONFFILE
                        The discogstagger configuration file.
```

## Examples

The following tags the directory "Beatles_The-Revolver" with discogs release id '4250662' (http://www.discogs.com/release/4250662)

```
$ discogs_tagger.py -s Beatles_The-Revolver -r 4250662
INFO:__main__:Using destination directory: Beatles_The-Revolver
INFO:requests.packages.urllib3.connectionpool:Starting new HTTP connection (1): api.discogs.com
INFO:discogstagger.discogsalbum:Fetching The Beatles - Revolver (4250662)
INFO:__main__:Tagging album 'The Beatles - Revolver'
INFO:__main__:Creating destination directory 'The_Beatles-Revolver-(PCS_7009)-1966-jW'
INFO:__main__:Downloading and storing images
INFO:__main__:Writing file The_Beatles-Revolver-(PCS_7009)-1966-jW/01-The_Beatles-Taxman.mp3
INFO:__main__:Writing file The_Beatles-Revolver-(PCS_7009)-1966-jW/02-The_Beatles-Eleanor_Rigby.mp3
INFO:__main__:Writing file The_Beatles-Revolver-(PCS_7009)-1966-jW/03-The_Beatles-Im_Only_Sleeping.mp3
INFO:__main__:Writing file The_Beatles-Revolver-(PCS_7009)-1966-jW/04-The_Beatles-Love_You_To.mp3
INFO:__main__:Writing file The_Beatles-Revolver-(PCS_7009)-1966-jW/05-The_Beatles-Here_There_And_Everywhere.mp3
INFO:__main__:Writing file The_Beatles-Revolver-(PCS_7009)-1966-jW/06-The_Beatles-Yellow_Submarine.mp3
INFO:__main__:Writing file The_Beatles-Revolver-(PCS_7009)-1966-jW/07-The_Beatles-She_Said_She_Said.mp3
INFO:__main__:Writing file The_Beatles-Revolver-(PCS_7009)-1966-jW/08-The_Beatles-Good_Day_Sunshine.mp3
INFO:__main__:Writing file The_Beatles-Revolver-(PCS_7009)-1966-jW/09-The_Beatles-And_Your_Bird_Can_Sing.mp3
INFO:__main__:Writing file The_Beatles-Revolver-(PCS_7009)-1966-jW/10-The_Beatles-For_No_One.mp3
INFO:__main__:Writing file The_Beatles-Revolver-(PCS_7009)-1966-jW/11-The_Beatles-Dr_Robert.mp3
INFO:__main__:Writing file The_Beatles-Revolver-(PCS_7009)-1966-jW/12-The_Beatles-I_Want_To_Tell_You.mp3
INFO:__main__:Writing file The_Beatles-Revolver-(PCS_7009)-1966-jW/13-The_Beatles-Got_To_Get_You_Into_My_Life.mp3
INFO:__main__:Writing file The_Beatles-Revolver-(PCS_7009)-1966-jW/14-The_Beatles-Tomorrow_Never_Knows.mp3
INFO:__main__:Generating .nfo file
INFO:__main__:Generating .m3u file
INFO:__main__:Tagging complete.
```
