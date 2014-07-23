Ripsnort
=========

DVD/Bluray video ripper. uses MakeMKV to rip. IMDb to rename and Email to notify

Notes
-------------

• Currently only supports Mac


Setup
--------------
edit settings.ini and change the following values
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
