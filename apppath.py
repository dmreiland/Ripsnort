#!/usr/bin/env python
# -*- coding: utf-8 -*-


import os
import platform
import subprocess


def pathForBinary(binApp):
    cmdargs = ['which',binApp]
    cmd = subprocess.Popen(cmdargs,stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    cmd.wait()
    response = cmd.communicate()
    path = response[0].strip()
    
    if not os.path.exists(path):
        path = None
    
    return path


def mkvinfo():
    path = pathForBinary('mkvinfo')
    
    if not path:
        platformName = platform.system().lower().strip()

        if platformName == 'darwin':
            path = '/Applications/Mkvtoolnix.app/Contents/MacOS/mkvinfo'
    
            if not os.path.exists(path):
                path = None

    return path


def mkvmerge():
    path = pathForBinary('mkvmerge')
    
    if not path:
        platformName = platform.system().lower().strip()

        if platformName == 'darwin':
            path = '/Applications/Mkvtoolnix.app/Contents/MacOS/mkvmerge'
    
            if not os.path.exists(path):
                path = None

    return path


def mkvextract():
    path = pathForBinary('mkvextract')
    
    if not path:
        platformName = platform.system().lower().strip()

        if platformName == 'darwin':
            path = '/Applications/Mkvtoolnix.app/Contents/MacOS/mkvextract'
    
            if not os.path.exists(path):
                path = None

    return path


def makemkvcon():
    path = pathForBinary('makemkvcon')
    
    if not path:
        platformName = platform.system().lower().strip()

        if platformName == 'darwin':
            path = '/Applications/MakeMKV.app/Contents/MacOS/makemkvcon'
    
            if not os.path.exists(path):
                path = None

    return path


def vobsub2srt():
    path = pathForBinary('vobsub2srt')
    return path


def checkDependancies():
    errReason = ''

    if mkvinfo() == None:
        errReason += 'mkvinfo is not installed. Please install Mkvtoolnix (https://www.bunkus.org/videotools/mkvtoolnix)\n'

    if mkvmerge() == None:
        errReason += 'mkvmerge is not installed. Please install Mkvtoolnix (https://www.bunkus.org/videotools/mkvtoolnix)\n'

    if mkvextract() == None:
        errReason += 'mkvextract is not installed. Please install Mkvtoolnix (https://www.bunkus.org/videotools/mkvtoolnix)\n'

    if makemkvcon() == None:
        errReason += 'makemkvcon is not installed. Please install MakeMkv (http://makemkv.com)\n'

    if vobsub2srt() == None:
        errReason += """vobsub2srt is not installed. Please install vobsub2srt (https://github.com/ruediger/VobSub2SRT)
MacOSX instructions:
  sudo chown -R $(whoami) /usr/local/lib/
  brew install --all-languages tesseract
  brew install --HEAD https://github.com/ruediger/VobSub2SRT/raw/master/packaging/vobsub2srt.rb
"""

    if len(errReason) == 0:
        errReason = None
        
    return errReason
        

if __name__ == "__main__":
    assert makemkvcon() != None
    assert mkvextract() != None
    assert mkvinfo() != None
    
    platformName = platform.system().lower().strip()

    if platformName == 'darwin' or platformName == 'linux':
        assert pathForBinary('bash') != None


