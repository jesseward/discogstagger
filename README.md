# discogstagger

## What is it

discogstagger is a console based audio meta-data tagger for FLAC, Ogg and MP3 audio files. Album, artist and track data profile is retrieved via the discogs.com API and then saved to the related metadata fields in the audio container.

To tag an album, provide the script with a target directory name (-s), that contains an album consisting of supported media files as well as the discogs.com release-id (-r). discogstagger calls out to the discogs.com API and updates the audio meta-data accordingly.

If no release-id is given the application checks if a file "id.txt" exists (the name of this file can be configured in the configuration) and if this file contains a specific property (id_tag). If both is true the release-id from this file is used. This is useful for batch processing.

During the process, all album images (if present) are retrieved from the API.  As well, a play-list (.m3u) and an information file (.nfo) are generated per each release.

Optionally discogstagger will embed the found album art into the file meta data

## Requirements

* Mutagen 
* discogs-client 
* requests
* Mediafile
* OAuth

I am also packaging/reusing the MediaFile library from the "beets" project. This will be packaged with discogs tagger until MediaFile is split out to its own package.

## Installation 

Fetch the repo from github
```
git clone https://github.com/jesseward/discogstagger.git
```
Create a virtual environment for your installations
```
python3 -m venv ~/.virtualenvs/discogstagger
source ~/.virtualenvs/discogstagger/bin/activate
```

Run the setuptools installation.
```
python setup.py install
```

Optionally you can install the developer requirements, if you plan on running the test suite or making changes to the tool
```
pip install -r dev_requirements.txt
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
$ discogs-tagger --help
Usage: discogs-tagger [OPTIONS]

Options:
  -c, --conf TEXT         The discogstagger configuration file.
  -d, --destination TEXT  The (base) directory to copy the tagged files to
  -r, --releaseid TEXT    The discogs.com release id of the target album
  -s, --source PATH       The directory that you wish to tag
  --help                  Show this message and exit.
```

## Examples

The following tags the directory "Pepe_Bradock-Deep_Burnt" with discogs release id '204' (http://www.discogs.com/release/204)

```
$ discogs-tagger -s Pepe_Bradock-Deep_Burnt -r 204
2017-07-17 04:36:30,686 discogstagger.main INFO     Attempting to tag files from target destination=Pepe_Bradock-Deep_Burnt
2017-07-17 04:36:31,044 discogstagger.discogsalbum INFO     Fetching discogs release. artist=Pépé Bradock & The Grand Brûlé's Choir, title=Burning, id=204
2017-07-17 04:36:31,047 discogstagger.main INFO     Tagging album 'Pépé Bradock & The Grand Brûlé's Choir - Burning'
2017-07-17 04:36:31,047 discogstagger.main INFO     Creating destination directory 'Pepe_Bradock_and_The_Grand_Brules_Choir-Burning-(KIF_S_A_08)-1999-jW'
2017-07-17 04:36:31,048 discogstagger.main INFO     Downloading and storing images
2017-07-17 04:36:33,966 discogstagger.main INFO     Writing file Pepe_Bradock_and_The_Grand_Brules_Choir-Burning-(KIF_S_A_08)-1999-jW/01-Pepe_Bradock_and_The_Grand_Brules_Choir-Burning_Hot.mp3
2017-07-17 04:36:34,011 discogstagger.main INFO     Writing file Pepe_Bradock_and_The_Grand_Brules_Choir-Burning-(KIF_S_A_08)-1999-jW/02-Pepe_Bradock_and_The_Grand_Brules_Choir-The_Right_Way.mp3
2017-07-17 04:36:34,032 discogstagger.main INFO     Writing file Pepe_Bradock_and_The_Grand_Brules_Choir-Burning-(KIF_S_A_08)-1999-jW/03-Pepe_Bradock_and_The_Grand_Brules_Choir-Deep_Burnt.mp3
2017-07-17 04:36:34,054 discogstagger.main INFO     Generating .nfo file
2017-07-17 04:36:34,056 discogstagger.main INFO     Generating .m3u file
2017-07-17 04:36:34,056 discogstagger.main INFO     Tagging complete.
```
