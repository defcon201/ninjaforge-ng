#!/usr/bin/env python3
liveos_forge_about='''LiveOS Forge
--------------
This is an app that reads from .liveos.zip packages and burns them to
USB sticks or other media. It can also check GPG signatures and hashes
as part of the spec to ensure the integrity of the data.

The format, and this package where started by the Ninja OS team to
address the shortcommings in existing distribution models for USB stick
live OSes.

The format is a zip file containing an image of a partition of a fixed
size, and a image of the bootloader, prefrably one pulled form a working
live sytem as a clone. This works with existing Ninja OS Clone and Forge
Framework. This will eventually replace existing Clone and Forge with
updated python scripts.

This is the GUI version. There will be a match CLI version in the future
'''
from liveos_common import *
import sys
from PySide2.QtUiTools import QUiLoader
from PySide2.QtWidgets import QApplication, QFileDialog
from PySide2.QtCore import QFile, QCryptographicHash

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

    check_hash_list = ["MAIN_HASH", "BS_HASH", "INDEX_HASH"]

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
    
def action_start():
    '''This is what happens when you hit the Start button'''

    # Step 1, check to see if we have a valid package. If not, Stop.
    if package_checks['valid_package'] != True:
        window.editbox_forge_action.appendPlainText("* No Valid Package Loaded!")
        return

    # Step 2 - Check settings
    settings = populate_options()

    print(settings) #DEBUG

def open_about_window():
    '''opens the about window'''
    about_window.show()

def main():
    
    app = QApplication(sys.argv)

    ui_file = QFile("liveos_forge_qt5.ui")
    ui_file.open(QFile.ReadOnly)

    loader = QUiLoader()
    global window
    window = loader.load(ui_file)
    ui_file.close()
    
    about_ui_file = QFile("liveos_forge_about.ui")
    about_ui_file.open(QFile.ReadOnly)
    loader = QUiLoader()
    global about_window
    about_window = loader.load(about_ui_file)
    about_ui_file.close()
    about_window.editbox_about.setPlainText(liveos_forge_about)
    
    #button presses
    window.action_Open.triggered.connect(file_open_dialog)
    window.action_Clear.triggered.connect(clear_action)
    window.action_About.triggered.connect(open_about_window)
    window.action_start.triggered.connect(action_start)
    #window.forge_main_widget.(drop_open)
    
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()

