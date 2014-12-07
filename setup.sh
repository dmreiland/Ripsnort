#!/bin/bash


SCRIPTDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd)"


function linux_install_mkvtoolnix {
    
    echo ''
    echo '** Installing MKVTOOLNIX **'
    echo ''
    
    sudo apt-get install -y mkvtoolnix

}


function mac_install_mkvtoolnix {

    echo ''
    echo '** Installing MKVTOOLNIX **'
    echo ''
    
    pushd /Applications

    sudo unzip $SCRIPTDIR/setup/mac/MKVToolNix.zip
    
    sudo chmod +x Mkvtoolnix.app/Contents/MacOS/mkvinfo
    sudo chmod +x Mkvtoolnix.app/Contents/MacOS/mkvmerge
    sudo chmod +x Mkvtoolnix.app/Contents/MacOS/mkvextract
    sudo chmod +x Mkvtoolnix.app/Contents/MacOS/mkvpropedit
    sudo chmod +x Mkvtoolnix.app/Contents/MacOS/mmg
    sudo chmod +x Mkvtoolnix.app/Contents/MacOS/Mkvmmg
    
    popd

}
 

function linux_install_makemkv {
    
    echo ''
    echo '** Installing MAKEMKV **'
    echo ''

    VER="$1"
    TMPDIR=`mktemp -d`

    # Install prerequisites
    sudo apt-get install build-essential pkg-config libc6-dev libssl-dev libexpat1-dev libavcodec-dev libgl1-mesa-dev libqt4-dev
 
    # Install this version of MakeMKV
    pushd $TMPDIR
 
    for PKG in bin oss; do
        PKGDIR="makemkv-$PKG-$VER"
        PKGFILE="$PKGDIR.tar.gz"
 
        wget "http://www.makemkv.com/download/$PKGFILE"
        tar xzf $PKGFILE
 
        pushd $PKGDIR
        # pre-1.8.6 version
        if [ -e "./makefile.linux" ]; then
            make -f makefile.linux
            sudo make -f makefile.linux install
 
        # post-1.8.6 version
        else
            if [ -e "./configure" ]; then
                ./configure
            fi
            make
            sudo make install
        fi
 
        popd
    done

    popd

    # Remove temporary directory
    if [ -e "$TMPDIR" ]; then rm -rf $TMPDIR; fi

}


function mac_install_makemkv {

    echo ''
    echo '** Installing MAKEMKV **'
    echo ''

    TMPDIR=`mktemp -d`

    # Install this version of MakeMKV
    pushd $TMPDIR

    curl -o makemkv.dmg http://www.makemkv.com/download/makemkv_v1.9.0_osx.dmg
    
    hdiutil mount makemkv.dmg
    
    sudo cp -rf /Volumes/makemkv*/MakeMKV.app /Applications
    
    rm makemkv.dmg
    
    popd

    # Remove temporary directory
    if [ -e "$TMPDIR" ]; then rm -rf $TMPDIR; fi

}


function linux_install_vobsub2srt {
    
    echo ''
    echo '** Installing VOBSUB2SRT **'
    echo ''

    TMPDIR=`mktemp -d`

    # Install this version of MakeMKV
    pushd $TMPDIR

    sudo apt-get install -y libtiff5-dev libtesseract-dev tesseract-ocr-eng build-essential cmake pkg-config
    
    processorType = $(uname -m)
    
    debLink = ''
    
    if [[ $processorType == 'x86_64' ]]; then
        #64 bit
        debLink = 'https://launchpad.net/~ruediger-c-plusplus/+archive/ubuntu/vobsub2srt/+files/vobsub2srt_1.0pre6-31-g1c782e5-ppa1_amd64.deb'
    else
        #32 bit
        debLink = 'https://launchpad.net/~ruediger-c-plusplus/+archive/ubuntu/vobsub2srt/+files/vobsub2srt_1.0pre6-31-g1c782e5-ppa1_i386.deb'
    fi
    
    wget $debLink -O vobsub2srt.deb
    
    sudo dpkg -i vobsub2srt.deb
    
    popd
    
    # Remove temporary directory
    if [ -e "$TMPDIR" ]; then rm -rf $TMPDIR; fi

}


function mac_install_vobsub2srt {
    
    echo ''
    echo '** Installing VOBSUB2SRT **'
    echo ''
    
    which brew > /dev/null
    
    if [[ $? -eq 1 ]]; then
        echo 'Homebrew is not install. Please install this first: http://brew.sh'
        exit 1
    fi
    
    brew install --all-languages tesseract
    
    if [[ $? -ne 0 ]]; then
        echo 'Tesseract install failed'
        exit 1
    fi
    
    brew install --HEAD https://github.com/ruediger/VobSub2SRT/raw/master/packaging/vobsub2srt.rb
    
    if [[ $? -ne 0 ]]; then
        echo 'VobSub2SRT install failed'
        exit 1
    fi

}


function linux_install_bdsup2sub {

    echo ''
    echo '** Installing BDSUP2SUB **'
    echo ''
    
    cd /usr/local/bin

    sudo wget http://www.videohelp.com/download/BDSup2Sub512.jar -O BDSup2Sub
    sudo chmod +x /usr/local/bin/BDSup2Sub
    
}


function mac_install_bdsup2sub {

    echo ''
    echo '** Installing BDSUP2SUB **'
    echo ''

    pushd /Applications
    
    sudo unzip $SCRIPTDIR/setup/mac/BDSup2Sub.zip
    
    popd
    
    # Remove temporary directory
    if [ -e "$TMPDIR" ]; then rm -rf $TMPDIR; fi

}


## START ##


# Collect sudo credentials
sudo -v

os_name=$(uname)


#Install MKVToolnix
if [[ $os_name == 'Linux' ]]; then
    which mkvinfo > /dev/null

    if [ $? -ne 0 ]; then
        linux_install_mkvtoolinx
    fi

elif [[ $os_name == 'Darwin' ]]; then
    if [[ ! -f /Applications/Mkvtoolnix.app/Contents/MacOS/mkvinfo ]]; then
        mac_install_mkvtoolnix
    fi

fi


#Install MakeMKV
if [[ $os_name == 'Linux' ]]; then
    which makemkvcon > /dev/null

    if [ $? -ne 0 ]; then
        linux_install_makemkv 1.9.0
    fi

elif [[ $os_name == 'Darwin' ]]; then
    if [[ ! -f /Applications/MakeMKV.app/Contents/MacOS/makemkvcon ]]; then
        mac_install_makemkv 1.9.0
    fi

fi


#Install VobSub2SRT
which vobsub2srt > /dev/null

if [ $? -ne 0 ]; then
    if [[ $os_name == 'Linux' ]]; then
        linux_install_vobsub2srt
    elif [[ $os_name == 'Darwin' ]]; then
        mac_install_makemkv
    fi
fi


#Install BDSup2Sub
if [[ $os_name == 'Linux' ]]; then
    which makemkvcon

    if [ $? -ne 0 ]; then
        linux_install_bdsup2sub
    fi

elif [[ $os_name == 'Darwin' ]]; then
    if [[ ! -f /Applications/BDSup2Sub.app/Contents/MacOS/JavaApplicationStub ]]; then
        mac_install_bdsup2sub
    fi

fi


echo ''
echo '** Setup complete **'
echo ''
