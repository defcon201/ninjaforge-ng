'''
Library of common functions for LiveOS forge, mainly for proccessing
.liveos.zip files
'''

import sys
import zipfile
import hashlib

def proccess_index(in_data):
    '''Takes a binary string from a raw file read of the index, outputs a dictionary of key=value pairs # is the comment character'''
    index_values = {}
    # Convert to string and strip junk
    in_data = str(in_data.strip())
    in_data = in_data.lstrip("b")
    in_data = in_data.strip("\'")
    
    # Split file into lines, and strip comments
    raw_lines = in_data.split('\\n')    
    file_lines = []
    for line in raw_lines:
        li=line.strip()
        if not li.startswith("#") and li != "":
            file_lines.append(line.split("#")[0])

    # Check remaining lines for a key=value pairs, write them to index_values
    for line in file_lines:
        try:
            line = line.split("=")
        except:
            continue
        key   = line[0].strip()
        value = line[1].strip()
        value = value.strip('\"')
        index_values[key]=value
    
    #return to the user a dict with values from index file
    return index_values

def package_file_meta(in_file):
    '''Opens a .liveos.zip and returns a tupple with OS Name, Version, Partition GPG KeyID, GPG full signature, in that order'''
    index="liveos_version.conf"
    invalid_package = in_file + " is not a .liveos.zip package file"
    invalid_index = in_file + " index file contains invalid data"

    # Step 1 - Check zip file
    if zipfile.is_zipfile(in_file) != True:
        raise EOFError(invalid_package)
        return

    # Step 2 - Extract data and put in an array
    try:
        liveos_package = zipfile.ZipFile(in_file,mode='r')
        file_raw = liveos_package.read(index)
        liveos_package.close()
    # If the index cannot be read, this is not a valid file
    except:
        raise EOFError(invalid_package)

    # Step 3 - Get key=value pairs from raw data
    index_values = proccess_index(file_raw)
    try:
       output = index_values['OSNAME'],index_values['OSVERSION'],index_values['OSARCH'],index_values['PART_SIZE']
    except:
        raise EOFError(invalid_index)
    if 'CONF_KEYNAME' and 'CONF_KEYSIG' in index_values:
        output = index_values['OSNAME'],index_values['OSVERSION'],index_values['OSARCH'],index_values['PART_SIZE'],index_values['CONF_KEYNAME'],index_values['CONF_KEYSIG']
    return output
    
def package_file_md5(in_file,file_meta):
    '''Opens a .liveos.zip band returns a dictionary with the key=value pairs from the md5 hashsum file. Takes two variables. Filename of the package, and a dictionary with metadata from the index file'''
    invalid_package = in_file + " is not a .liveos.zip package file"
    invalid_md5 = in_file + " MD5 hash sum file contains invalid data"
    
    index_values = {}
    file_values  = {}

    check_hash_list = ["MAIN_HASH", "BS_HASH", "INDEX_HASH"]

    md5_sums_file="hash/md5"
    main_image_file = file_meta['OSSLUG'] +    "_"         + file_meta['OSVERSION']
    bs_image_file   = file_meta['OSSLUG'] + "_bootsector_" + file_meta['OSVERSION']

    # Step 1 - Check zip file
    if zipfile.is_zipfile(in_file) != True:
        raise EOFError(invalid_package)
        return
        
    # Step 2 - Extract data and put in an array
    try:
        liveos_package = zipfile.ZipFile(in_file,mode='r')
        file_raw = liveos_package.read(md5_sums_file)
        liveos_package.close()
    # If the MD5 file file cannot be read, it is invalid data
    except:
        raise EOFError(invalid_md5)
        
    # Step 3 - Get key=value pairs from raw data
    index_values = proccess_index(file_raw)
    
    # Step 4 - Check if keys for MD5s exist:
    if not index_values['MAIN_HASH']:
        raise EOFError(invalid_md5)
    elif not index_values['BS_HASH']:
        raise EOFError(invalid_md5)
    elif not index_values['INDEX_HASH']:
        raise EOFError(invalid_md5)
    
    # Step 5 - Return a dict() with values from the hash file
    return index_values
        
def compare_gpg_keysig_keyid(keysig,keyid):
    '''Checks if a full GPG signature matches a keyid. Takes two parameters, keysig, and keyid, and returns True/False as a bool'''
    last_bytes = keysig[-8:]
    if last_bytes == keyid:
        return True
    else:
        return False

def space_gpg_keysig(in_keysig):
    '''Take a GPG signature and put a space, every 4 characters.'''
    n = 4
    split_sig = [in_keysig[i:i+n] for i in range(0, len(in_keysig), n)]
    out_keysig = " ".join(split_sig)
    return out_keysig

def check_file_md5(in_hash,file_bytes):
    '''Check the MD5 hash sum of a file. Takes two arguments, a string with the hash, and the bytes of a file, returns a bool True/False'''
    try:
        file_hash = hashlib.md5(file_bytes).hexdigest()
    except:
        # IDK, raise something here?
        return "ERR","Hash failed"
    
    if file_hash == in_hash:
        return True
    else:
        return False
