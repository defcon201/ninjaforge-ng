'''
Library of common functions for LiveOS forge, mainly for proccessing
.liveos.zip files
'''
forge_lib_meta = {
  'name'    : "Ninja Forge",
  'version' : "0.0.0"
}
import sys
import shutil
import zipfile
import hashlib
import gnupg
import tempfile
import subprocess
import json

def slugify(in_text):
    '''return a slug. Remove spaces, and lowercase'''
    out_text = in_text.strip()
    out_text = out_text.lower()
    out_text = out_text.replace(" ","")
    
    return out_text
    
def byte2str(in_string):
    '''convert bytes into string'''
    output = str(in_string.strip())
    output = output.lstrip("b")
    output = output.strip("\'")
    return output

def os_supported():
    '''Check if current Operating System is supported. There are OS specific calls in Forge'''
    supported_list = ['linux', 'win', 'freebsd', 'darwin']

    output = False
    for item in supported_list:
        if item in sys.platform:
            output = True
            break
    return output

def proccess_index(in_data):
    '''Takes a binary string from a raw file read of the index, outputs a dictionary of key=value pairs # is the comment character'''
    index_values = {}
    # Convert to string and strip junk
    in_data = byte2str(in_data)
    
    # Split file into lines, and strip comments
    raw_lines  = in_data.split('\\n')    
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
    '''Opens a .liveos.zip and returns a tupple with OS Name, Version, CPU Arch, Partition Size, GPG signature, Format Version, in that order'''
    index           = "liveos_version.conf"
    invalid_package = in_file + " is not a .liveos.zip package file"
    invalid_index   = in_file + " index file contains invalid data"

    # Step 1 - Check zip file
    if zipfile.is_zipfile(in_file) != True:
        raise EOFError(invalid_package)

    # Step 2 - Extract data and put in an array
    try:
        liveos_package = zipfile.ZipFile(in_file,mode='r')
        file_raw       = liveos_package.read(index)
        liveos_package.close()
    # If the index cannot be read, this is not a valid file
    except:
        raise EOFError(invalid_package)

    # Step 3 - Get key=value pairs from raw data
    index_values = proccess_index(file_raw)
    #Generate slug from name. lowercase and remove spaces
    index_values['OSSLUG'] = slugify( index_values['OSNAME'] )
    if 'CONF_KEYSIG' not in index_values:
        index_values['CONF_KEYSIG'] = None
    
    wanted_str   = ['OSNAME', 'OSSLUG', 'OSVERSION','OSARCH','PART_SIZE', 'CONF_KEYSIG']
    wanted_float = ['FORMAT_VER']
    wanted_int   = []
    output       = {}
    try:
        for item in wanted_str:
            output[item] = str(index_values[item])
        for item in wanted_float:
            output[item] = float(index_values[item])
        for item in wanted_int:
            output[item] = int(index_values[item])
    except:
        raise EOFError(invalid_index)

    return output
    
def check_manifest(in_file,options=[]):
    '''Check .liveos.zip package to ensure files are present as per spec. Options should be a list of strings. valid options are gpg and md5'''

    # Step 1 - Get Meta from package and set filenames
    file_meta       = package_file_meta(in_file)
    index           = "liveos_version.conf"
    main_image_file = file_meta['OSSLUG'] + "_" + file_meta['OSVERSION'] + ".img"
    if file_meta['FORMAT_VER'] >= 3:
        bootsector_file = file_meta['OSSLUG']  + "_bootsector_" + file_meta['OSVERSION'] + ".img"
        gpg_keyring     = "gpg/package_key.gpg"
    else:
        bootsector_file = "ninjabootsector" + file_meta['OSVERSION'] + ".img"
        gpg_keyring     = "gpg/ninja_pubring.gpg"


    # Step 2 - get list of files
    liveos_package = zipfile.ZipFile(in_file,mode='r')
    file_list      = liveos_package.namelist()
    liveos_package.close()
    
    # Check base files.
    if index not in file_list:
        return False
    if main_image_file not in file_list:
        return False
    if bootsector_file not in file_list:
        return False
    
    # Check MD5 hashsum file
    if "md5" in options:
        if "hash/md5" not in file_list:
            return False
            
    # Check GPG signatures
    if "gpg" in options:
        index_sig      = "gpg/" + index + ".sig"
        main_image_sig = "gpg/" + main_image_file + ".sig"
        bootsector_sig = "gpg/" + bootsector_file + ".sig"
        if gpg_keyring not in file_list:
            return False
        if index_sig not in file_list:
            return False
        if main_image_sig not in file_list:
            return False
        if bootsector_sig not in file_list:
            return False
    # If nothing fails, return True
    return True
    
def get_drive_list(option):
    '''Get list of drives that are usable. option is either drive or partition. returns a tupple of device,size,[label]'''
    out_list   = []

    if 'win' in sys.platform:
        list_drives        = subprocess.Popen('wmic logicaldisk get name,description', shell=True, stdout=subprocess.PIPE)
        list_drives_o, err = list_drives.communicate()
        list_drives_o      = list_drives_o.split('\n')
        drive_list         = "" #TODO: FIGURE OUT HOW THIS VARIABLE WORKS IN WINDOWS
        raise EnvironmentError("windoze not supported yet: TODO: FIGURE THIS SHIT OUT!")

    elif 'linux' in sys.platform:
        list_drives_cmd  = "lsblk -J -o +LABEL" # -J is for JSON. We can then snarf it later
        list_drives      = subprocess.Popen(list_drives_cmd, shell=True, stdout=subprocess.PIPE)
        drive_table, err = list_drives.communicate()
        drive_table      = byte2str(drive_table)
        drive_table      = drive_table.replace('\\n','\n')
        drive_table      = json.loads(drive_table)
        # Drive table is a python dict{} lookup table of all drive and
        # partition information from lsblk
        
    elif 'freebsd' in sys.platform:
        raise EnvironmentError("FreeBSD is not supported yet: TODO: FIGURE THIS SHIT OUT")
    elif 'darwin' in sys.platform:
        raise EnvironmentError("Apple Darwin(OSX/IPhone) is not supported yet: TODO FIGURE THIS SHIT OUT")
    else:
       raise EnvironmentError(sys.platform + ": OS Not supported!(support is not planned)")
        
    # Parse though the drive_table object. We are looking for not mounted
    # partitions, that have no child objects, i.e. RAID, lvm, or crypto
    # This should help prevent nuking system partitions. Drive checks
    # ALL partitions on the disk. They all have to be unmounted. partition
    # only checks invidual partitions.
    if option == "drive":
        parts_check = {}
        for drive in drive_table['blockdevices']:
            parts_check = set()
            for part in drive['children']:
                if 'children' in part.keys():
                    break
                parts_check.add(part['mountpoint'])
            if parts_check != { None }:
                continue
            out_list.append( ("/dev/" + drive['name'],drive['size']) )
    elif option == "partition":
        for drive in drive_table['blockdevices']:
            for part in drive['children']:
                if 'children' in part.keys():
                    break
                if part['mountpoint'] == None:
                    if part['label'] == None:
                        part['label'] = ""
                    out_list.append( ("/dev/" + part['name'],part['size'],part['label']) )
    else:
        raise KeyError('Option must be either drive or partition')
        
    return out_list

def package_file_md5(in_file):
    '''Opens a .liveos.zip band returns a dictionary with the key=value pairs from the md5 hashsum file. Takes two variables. Filename of the package, and a dictionary with metadata from the index file'''
    md5_sums_file   = "hash/md5"
    invalid_package = in_file + " is not a .liveos.zip package file"
    invalid_md5     = in_file + " MD5 hash sum file contains invalid data"
    
    index_values    = {}
    file_values     = {}

    # Step 1 - Check zip file
    if zipfile.is_zipfile(in_file) != True:
        raise EOFError(invalid_package)
        
    # Step 2 - Extract data and put in an array
    try:
        liveos_package = zipfile.ZipFile(in_file,mode='r')
        file_raw       = liveos_package.read(md5_sums_file)
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


def space_gpg_keysig(in_keysig):
    '''Take a GPG signature and put a space, every 4 characters.'''
    n = 4
    split_sig  = [in_keysig[i:i+n] for i in range(0, len(in_keysig), n)]
    out_keysig = " ".join(split_sig)
    return out_keysig

def check_gpg_index(key_sig,file_name,format_ver):
    '''Checks if GPG Signature in index file matches keyring, returns True/False'''
    if format_ver >= 3:
        index       = "gpg/package_key.gpg"
    else:
        index       = "gpg/ninja_pubring.gpg"
    temp_dir        = tempfile.mkdtemp()
    temp_index      = temp_dir + "/" + index
    invalid_package = file_name + " is not a .liveos.zip package file"
    invalid_keyring = file_name + " GPG keyring file contains invalid data"
    # Step 1 - Check zip file
    if zipfile.is_zipfile(file_name) != True:
        raise EOFError(invalid_package)

    # Step 2 - Extract keyring file. There is no way to load this data
    # directly into a buffer.
    try:
        liveos_package = zipfile.ZipFile(file_name,mode='r')
        liveos_package.extract(index,path=temp_dir)
    # If the index cannot be read, this is not a valid file
    except:
        raise EOFError(invalid_package)
    
    # Step 3 - keyring data from the keyring file and then close it.
    try:
        gpg     = gnupg.GPG(keyring=temp_index)
    except:
        shutil.rmtree(temp_dir)
        raise EOFError(invalid_keyring)
    # Get the keyring from the file
    keyring = gpg.list_keys()
    
    liveos_package.close()
    shutil.rmtree(temp_dir)
    ## Step 4 - check to make sure keyring data matches index.
    # There should only be ONE key. If not, fail
    if len(keyring) != 1:
        return False
    # get fingerprint of first key. check against key from index file
    if keyring[0]['fingerprint'] != key_sig:
        return False
    else:
        return True

def check_file_buffer_md5(in_hash,file_bytes):
    '''Check the MD5 hash sum of a file in a buffer. Takes two arguments, the known hash, and file buffer object. Returns True/False'''
    try:
        file_hash = hashlib.md5(file_bytes).hexdigest()
    except:
        # IDK, raise something here?
        return "ERR","Hash failed"
    
    if file_hash == in_hash:
        return True
    else:
        return False
                
def check_file_name_md5(in_hash,file_name):
    '''Check the MD5 hash of a file, read from the disk. Two arguments, in hash, and file name. Returns True/False'''
    block_size = 4096 # 4k
    percent = 0.0
    out_md5 = hashlib.md5()
    f = open(file_name,"rb")
    for byte_block in iter(lambda: f.read(block_size),b""):
        out_md5.update(byte_block)

    if out_md5 == in_hash:
        return True
    else:
        return False
