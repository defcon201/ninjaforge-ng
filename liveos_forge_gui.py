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

options = {
    "valid_package" : False,
    "valid_target"  : False
}

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
    options.update({"valid_package":False})
    
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
        package_index = package_file_meta(filename)
    except EOFError:
        update_ui_invalid_package("Can't parse .liveos.zip index, invalid package")
        options.update({"valid_package":False})
        return

    # Update the valid package flag if we didn't return errors with the
    # package
    # window.button_start.setEnabled(True) # This needs to go later, 
    
    os_name   = package_index[0]
    os_ver    = package_index[1]
    os_arch   = package_index[2]
    part_size = package_index[3]
    key_sig   = package_index[4]
    
    # Load OS Name, Version, Parition Size, and System Archecture into window
    window.editbox_os_name.setText(os_name)
    window.editbox_os_version.setText(os_ver)
    window.editbox_os_size.setText(part_size)
    window.editbox_os_arch.setText(os_arch)
    
    # Check GPG key against index
    if key_sig != None:
        window.editbox_gpg_sig.setPlainText( space_gpg_keysig(key_sig) )

        try:
            gpg_index_valid = check_gpg_index(key_sig,filename)
        except EOFError:
            update_ui_invalid_package("Invalid GPG Keyring, not loading")
            options.update({"valid_package":False})
            return
        
        if gpg_index_valid == True:
            # Update the valid package flag if we didn't return errors with the
            # package
            # window.button_start.setEnabled(True) # This needs to go later, 
            options.update({"valid_package":True})
            window.editbox_forge_action.appendPlainText("* Package Loaded" )
        else:
            window.editbox_forge_action.appendPlainText("* FAIL. Package GPG key doesn't match index")
            options.update({"valid_package":False})
    else:
        # Update the valid package flag if we didn't return errors with the
        # package
        # window.button_start.setEnabled(True) # This needs to go later, 
        options.update({"valid_package":True})
        window.editbox_forge_action.appendPlainText("* Package Loaded" )


def window_drop(contents):
   print("Drop Event")
   print(contents)
   
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
    
    #window.forge_main_widget.(drop_open)
    
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()

