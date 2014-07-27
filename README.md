Ripsnort
=========

DVD/Bluray video ripper. uses MakeMKV to rip. IMDb to rename and Email to notify

Notes
-------------

• Currently only supports Mac


Setup
--------------
Config: edit settings.ini and change the following values to match your email address and movie/tv save folder
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

Autorun: edit mac_autorun.scpt and set formatted_path to the location of ripsnort and set disk_device to the device of the dvd drive. Example settings:
```
    set formatted_path to "/Users/ryan/ripsnort"
    set disk_device to "/dev/disk2"
```
Go to 'System Preferences'->'CDs & DVDs'->'When you insert a Video DVD' and select mac_autorun.scpt


Running
--------------

Example use, call autorip with the disc inserted in device /dev/disk2
```
    ./autorip.py /dev/disk2
```
once completed, you will receive an email


License
----

[BSD 3-Clause](http://www.opensource.org/licenses/BSD-3-Clause)
