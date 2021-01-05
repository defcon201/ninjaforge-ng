#!/usr/bin/env python3

forge_gui_meta = {
  'name'    : "Ninja Forge",
  'version' : "0.0.0"
}

ninjaforge_about='''
This is the GUI Version of Ninja Forge.

Ninja Forge reads from .liveos.zip packages and burns them to USB sticks
orother media. It can also check GPG signatures and hashesas part of the
spec to ensure the integrity of the data.

The format, and this package where started by the Ninja OS team to
address the shortcommings in existing distribution models for USB stick
live OSes.

The format is a zip file containing an image of a partition of a fixed
size, and a image of the bootloader, prefrably one pulled form a working
live sytem as a clone. This works with existing Ninja OS Clone and Forge
Framework. This will eventually replace existing Clone and Forge with
updated python scripts.

USAGE
=====
Open the package liveos.zip package using the open button or shortcut.

If the package is not a valid package, this will throw an error. If a
GPG Signature is specified in the metadata, then it will check for a
keyring. If one is not found, or it doesn't contain specificly one key
matching the signature in the metadata, it will throw an error. It
will also check for the presence of a hash sum file, if enabled and
throw an error if not found. Other than this, it will do a basic
manifest check of the zip file to ensure the expected files are present.
If not, it will throw an error, and you will be unable to procede.

Once a valid package is loaded, select a target and options and press
start. Action will depend on options checked.

Target
------

If "Format" is selected in the options, pick a block device, and use the
entire device. If it is NOT selected. Pick an existing parition of a
block device. See Below

Options:
--------
Format - This will parition the USB stick. The first partition will be
Parition Size as displayed on the column on the left, and the second,
the remainder of the drive.

Write to Media - Write images to media. If this is unchecked, the tool
can be used to format the drive, or simply just check the validity of
package without writing.

Check GPG Sig - Checks GPG signatures of package. uses internal keyring,
checked against "GPG Signature". Please verify that this signature
matches that known to be of the author of the OS in question.

Check Hash Sum - At current, checks stored MD5 sum hashes of shipped
files to verify they are uncorrupted. This is used as an alternative
to GPG, that can check against transmission/storage issues, but NOT
security threats.

Start Button
-------------
Will do the actions checked, starting with hash and GPG checks.


TIP - Uncheck "Format" and "Write to Media" to verify the intergrity of
the package. Nothing will be written.
'''
ninjaforge_about = ninjaforge_about.strip()

from ninjaforge_common import *
#from PySide2.QtUiTools import QUiLoader
#from PySide2.QtWidgets import QApplication, QFileDialog
#from PySide2.QtCore import QFile, QCryptographicHash

from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QFileDialog
from PyQt5.QtCore import QCryptographicHash

# Keep track if the current selections are valid. starts with False,
# and must be validated by checks, otherwise start will not run.
package_checks = {
    "valid_package" : False,
    "valid_target"  : False
}

# kept concurent with the target combo box
target_list = []

def drop_open(filename):
    '''Open a package that is dropped in the window'''
    print("drag and drop " + filename)

def clear_action():
    '''unload the loaded file, clear file display'''
    window.editbox_os_name.setText('')
    window.editbox_os_version.setText('')
    window.editbox_os_size.setText('')
    window.editbox_os_arch.setText('')
    window.editbox_input_file.setText('')
    window.editbox_gpg_sig.setPlainText('')
    window.editbox_forge_action.setPlainText('')
    # Reset valid package flag
    package_checks.update({"valid_package":False})
    
def update_ui_invalid_package(Error_Message):
    '''An invalid file was selected as a package, update the UI'''
    window.editbox_os_name.setText('*Invalid*')
    window.editbox_os_version.setText('*Invalid*')
    window.editbox_os_size.setText('*Invalid*')
    window.editbox_os_arch.setText('*Invalid*')
    window.editbox_gpg_sig.setPlainText('*Invalid*')
    window.editbox_forge_action.setPlainText("* Invalid Package: " + Error_Message)

def file_open_dialog():
    ''' Open file dialog and ask for a file to load'''
    filename = QFileDialog.getOpenFileName(None,"Open .liveos.zip Package File",'',"LiveOS Packages (*.liveos.zip)")
    if filename[1] == 'LiveOS Packages (*.liveos.zip)':
        filename = filename[0]
        window.editbox_input_file.setText(filename)
    else:
        update_ui_invalid_package('Not a .liveos.zip')
        return
        
    file_open(filename)

        
def file_open(filename):
    ''' Open .liveos.zip file. Takes on argument, file path as string'''
    clear_action()
    window.editbox_input_file.setText(filename)

    # Throw an error if invalid metadata is given
    try:
        file_meta = package_file_meta(filename)
    except EOFError:
        update_ui_invalid_package("Can't parse .liveos.zip index, invalid package")
        package_checks.update({"valid_package":False})
        return

    # Load OS Name, Version, Parition Size, and System Archecture into window
    window.editbox_os_name.setText(file_meta['OSNAME'])
    window.editbox_os_version.setText(file_meta['OSVERSION'])
    window.editbox_os_size.setText(file_meta['PART_SIZE'])
    window.editbox_os_arch.setText(file_meta['OSARCH'])
    
    # Check GPG key against index
    if file_meta['CONF_KEYSIG'] != None:
        window.editbox_gpg_sig.setPlainText( space_gpg_keysig(file_meta['CONF_KEYSIG']) )

        try:
            gpg_index_valid = check_gpg_index(file_meta['CONF_KEYSIG'],filename,file_meta['FORMAT_VER'])
        except EOFError:
            window.editbox_forge_action.appendPlainText("* FAIL: Invalid GPG Keyring")
            package_checks.update({"valid_package":False})
            return
        
        if gpg_index_valid == True:
            # Update the valid package flag if we didn't return errors with the
            # package
            # window.button_start.setEnabled(True) # This needs to go later, 
            package_checks.update({"valid_package":True})
            window.editbox_forge_action.appendPlainText("* Package Loaded" )
        else:
            window.editbox_forge_action.appendPlainText("* FAIL: Package GPG key doesn't match index")
            package_checks.update({"valid_package":False})
    else:
        # Update the valid package flag if we didn't return errors with the
        # package
        # window.button_start.setEnabled(True) # This needs to go later, 
        package_checks.update({"valid_package":True})
        window.editbox_forge_action.appendPlainText("* Package Loaded" )


def window_drop(contents):
   '''DEBUG function, remove before going live'''
   print("Drop Event")
   print(contents)
   
def check_md5_sums(file_name,file_meta,file_hashes):
    '''check .liveos.zip hash sums, main image, boot sector, and package image'''
    check_hash_list   = ["MAIN_HASH", "BS_HASH", "INDEX_HASH"]
    main_image_file   = file_meta['OSSLUG'] +    "_"         + file_meta['OSVERSION']
    if file_meta['FORMAT_VER'] >= 3:
        bs_image_file = file_meta['OSSLUG'] + "_bootsector_" + file_meta['OSVERSION']
    else:
        bs_image_file = ninjabootsector + file_meta['OSVERSION'] + ".img"
    
def populate_options():
    '''This takes all the options set in the GUI and populates the options dict'''
    options = {'check_gpg': False, 'check_md5':False, 'format':False, 'write':False, 'in_file':None, 'target_select':None }

    # Start by getting checkbox options
    if window.checkbox_verify_gpg.checkState():
        options['check_gpg'] = True
    if window.checkbox_verify_hash.checkState():
        options['check_md5'] = True
    if window.checkbox_format.checkState():
        options['format']    = True
    if window.checkbox_write_to_media.checkState():
        options['write']     = True
        
    # package file and target
    options['in_file']        = window.editbox_input_file.text()
    options['target_select']  = window.combobox_drive_selection.currentIndex()
    
    return options

def action_reload():
    '''This is what happens when the you hit the reload button'''

    settings = populate_options()
    file_open(settings['in_file'])

def populate_target_box():
    '''Function for loading/reloading target combo box'''
    option = None

    # If "format" is checked, select drives, if not, select partitions
    if window.checkbox_format.checkState():
        option = "drive"
    else:
        option = "partition"

    # Clear list at start
    window.combobox_drive_selection.clear()
    # Get list of drives
    target_list = get_drive_list(option)
    line = ""
    for item in target_list:
        line = "\t".join(item)
        window.combobox_drive_selection.addItem(line)
   
def action_start():
    '''This is what happens when you hit the Start button'''

    # Step 1 - check to see if we have a valid package. If not, Stop.
    if package_checks['valid_package'] != True:
        window.editbox_forge_action.appendPlainText("* No Valid Package Loaded!")
        return

    # Step 2 - Check settings
    settings = populate_options()
    
    # Step 3 - Manifest Check. Ensure all files are present
    check_opts = []
    if settings["check_gpg"] == True:
        check_opts.append("gpg")
    if settings["check_md5"] == True:
        check_opts.append("md5")
    manifest_ok = check_manifest(settings['in_file'],check_opts)
    if manifest_ok != True:
        window.editbox_forge_action.appendPlainText("* Files are missing from package, Stopping!")
        return
        
    print(settings) #DEBUG
    
def open_about_window():
    '''opens the about window'''
    about_window.label_name.setText(forge_gui_meta["name"])
    about_window.label_version.setText(forge_gui_meta["version"])
    about_window.editbox_about.setPlainText(ninjaforge_about)
    about_window.show()

def main():
    
    app = QApplication(sys.argv)

    # Main Window
    global window
    window = uic.loadUi("ninjaforge_qt5.ui")
    
    # About Window
    global about_window
    about_window = uic.loadUi("ninjaforge_about.ui")
    
    #button presses
    window.action_Open.triggered.connect(file_open_dialog)
    window.action_Reload_Package.triggered.connect(action_reload)
    window.action_Refresh_Drives.triggered.connect(populate_target_box)
    window.action_Clear.triggered.connect(clear_action)
    window.action_About.triggered.connect(open_about_window)
    window.action_Start.triggered.connect(action_start)
    # When the format checkbox is clicked, refresh
    window.checkbox_format.clicked.connect(populate_target_box)
    
    #window.forge_main_widget.(drop_open) #TODO: figure out Qt5 drop Mechanics
    
    #Initial population of drive selection:
    populate_target_box()
    
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
