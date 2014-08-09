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


if __name__ == "__main__":
    assert makemkvcon() != None
    assert mkvextract() != None
    assert mkvinfo() != None
    
    platformName = platform.system().lower().strip()

    if platformName == 'darwin' or platformName == 'linux':
        assert pathForBinary('bash') != None


