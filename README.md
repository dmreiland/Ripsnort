Ripsnort
=========
DVD/Bluray video ripper. 

Features
 - Can extract TV Episodes and Movies from discs
 - Capable of matching acronyms to media (TGTBATU -> The Good The Bad And The Ugly)
 - Notification via Email/Growl/Audio when starting and finishing
 - Automatically triggered on disc tray closed (ejects on completion too)(mac)
 - Comparison engine capable of finding imdb matches to ripped videos with > 90% accuracy


Using MakeMKV to rip discs it then uses OpenSubtitles to find a matching comparison to your ripped files subtitles. Ensuring an accurate match and cataloging your videos to your media collection.


Setup
--------------
Install MakeMkv: http://makemkv.com/</br>
Install MkvToolnix: https://www.bunkus.org/videotools/mkvtoolnix/</br>
Install VobSub2SRT: https://github.com/ruediger/VobSub2SRT</br>
Install BDSup2Sub: http://www.videohelp.com/tools/BDSup2Sub (blu-ray support only)

Edit config.ini and change the following values to match your email account and movie/tv save folder
```
    smtp_source_email = myemailaddr@gmail.com
    smtp_destination_email = myemailaddr@gmail.com
    smtp_username = myemailaddr@gmail.com
    smtp_password = mypassword
    movie_incomplete_save_path = /save_path
    movie_complete_save_path = /save_path
    tv_incomplete_save_path = /save_path
    tv_complete_save_path = /save_path

```


Autorun
--------------

(mac) Autorun: edit mac_autorun.scpt and set formatted_path to the location of ripsnort and set disk_device to the device of the dvd drive. Example settings:
```
    set formatted_path to "/Users/ryan/ripsnort"
    set disk_device to "/dev/disk2"
```
Go to 'System Preferences'->'CDs & DVDs'->'When you insert a Video DVD' and select mac_autorun.scpt


Manual Disc Ripping
--------------

Ripping disc example use, call ripsnort with the disc inserted in device /dev/disk2
```
    ./ripsnort.py /dev/disk2
```
once completed, you will receive an email

Manual Track Identification
--------------

Ripsnort can also be used to identify MKV tracks. Simply call with the file path i.e.
```
    ./ripsnort.py -i /Users/Ryan/TV/Numb3Rs - Season 6 Disc 2/title00.mkv
```

and ripsnort will proceed to compare this tracks subtitles with candidates found online. On success you will see output as such:
```
ContentMatch Show: Numb3rs
ContentMatch Season: 6
ContentMatch EpisodeNumber: 6
ContentMatch EpisodeName: Dreamland
ContentMatch Year: 2009
2014-11-21 21:29:34,051 Ripsnort complete -------
```
if you would like ripsnort to rename and move the track according to your config.ini replace ```-i``` with ```-r```

Tools used
--------------
[MakeMKV](http://www.makemkv.com)
[IMDbPY](http://imdbpy.sourceforge.net)
[OpenSubtitles.org](http://www.opensubtitles.org)
[Discident.com](http://discident.com)
[VobSub2SRT](https://github.com/ruediger/VobSub2SRT)
[Tesseract](https://code.google.com/p/tesseract-ocr/)
[BD2Sup2Sub](http://www.videohelp.com/tools/BDSup2Sub)

Donations
--------------
This project is dependant on the OpenSubtitles.org website. If this project has been useful to you please consider contributing


License
----

[BSD 3-Clause](http://www.opensource.org/licenses/BSD-3-Clause)


