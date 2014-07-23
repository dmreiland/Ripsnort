import hashlib
import os
import sys

dirname = os.path.dirname(os.path.realpath( __file__ ))
sys.path.append(dirname + "/..")

import requests


__version__ = "0.1.1"


def generate_hash(s):
    s = hashlib.md5(s).hexdigest().upper()
    return "-".join([s[:8], s[8:12], s[12:16], s[16:20], s[20:]])


def get_paths(root_dir):
    file_list = []
    for root, subFolders, files in os.walk(root_dir):
        for file in files:
            f = os.path.join(root, file)
            s = os.path.getsize(f)
            f = f.replace(root_dir, '')
            if not f.startswith('/'):
                f = '/%s' % f
            file_list.append("%s:%d" % (f, s))
    return file_list


def combine_files(f):
    f.sort()
    return ":%s" % ":".join(f)


def fingerprint(path):
    p = get_paths(path)
    s = combine_files(p)
    return generate_hash(s)

def response_for_hash(hashcode):
    r = requests.get('http://discident.com/v1/' + hashcode)
    
    responseHash = r.json()
    
    if type(responseHash) is not type({}):
        responseHash = {}
    
    return responseHash

def gtin_code_from_hash(hashcode):
    
    responseHash = response_for_hash(hashcode)
    
    gtin_code = None
    
    if responseHash.has_key('gtin'):
        gtin_code = responseHash['gtin']

    return gtin_code

def disc_production_year_from_hash(hashcode):
    production_year_return = None
    
    gtin_code = gtin_code_from_hash(hashcode)
    
    if gtin_code is not None:
        r = response_for_hash(gtin_code)
        
        responseGtin = response_for_hash(gtin_code)
        
        if responseGtin.has_key('productionYear'):
            production_year_return = responseGtin['productionYear']
    
    return production_year_return

def disc_title_from_hash(hashcode):
    disc_title_return = None
    
    responseTitle = response_for_hash(hashcode)
    
    if responseTitle.has_key('title'):
        disc_title_return = responseTitle['title']

    return disc_title_return

def disc_production_year(path):
    production_year_return = disc_production_year_from_hash( fingerprint(path) )
    return production_year_return

def disc_gtin_code(path):
    gtin_code = gtin_code_from_hash( fingerprint(path) )
    return gtin_code
    
def disc_title(path):
    disc_title = disc_title_from_hash ( fingerprint(path) )
    return disc_title
    

if __name__ == "__main__":
    assert gtin_code_from_hash('3DF28C7A-3EB4-41F2-7CD8-27B691EF984D') == '00794043444623'
    assert disc_production_year_from_hash('3DF28C7A-3EB4-41F2-7CD8-27B691EF984D') == 1996
    assert disc_title_from_hash('3DF28C7A-3EB4-41F2-7CD8-27B691EF984D') == 'Long Kiss Goodnight'
