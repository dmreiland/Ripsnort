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
Install MakeMkv: http://makemkv.com/

Install MkvToolnix: https://www.bunkus.org/videotools/mkvtoolnix/

Install VobSub2SRT: https://github.com/ruediger/VobSub2SRT

Edit settings.ini and change the following values to match your email account and movie/tv save folder
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


Manual execution
--------------

Example use, call autorip with the disc inserted in device /dev/disk2
```
    ./autorip.py /dev/disk2
```
once completed, you will receive an email


Tools used
--------------
 - MakeMKV
 - IMDbPY
 - OpenSubtitles.org
 - Discident.com
 - VobSub2SRT
 - Tesseract


Donations
--------------
If this project has helped you please consider becoming a VIP member to the not-for-profit OpenSubtitles.org website


License
----

[BSD 3-Clause](http://www.opensource.org/licenses/BSD-3-Clause)
