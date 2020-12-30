#!/usr/bin/env python
forge_cli_meta = {
  'name'    : "Ninja Forge",
  'version' : "0.0.0"
}
ninjaforge_about='''
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

MD5 checks are not intended to provide security, only integrity
against data corruption. It is for if GPG signatures are not available,
or for unofficial clones from ninja_clone.

GPG signature checking checks detached GPG signatures against a
key distributed with the package, and checks the signature of that key
against that of the metadata index. If they don't match, the check fails

Targets: If you are partitioning the drive with --format, use the entire
drive, i.e. /dev/sdX. If you are NOT using this option, use the parition
i.e. /dev/sdXN, i.e. /dev/sdd vs /dev/sdd1
'''
ninjaforge_about = ninjaforge_about.strip()

import argparse

def main():
    parser = argparse.ArgumentParser(description=ninjaforge_about)
    parser.add_argument("target", nargs="", help="Partition/Drive to burn with Ninja OS or other Live OS")
    
    parser_checks = parser.add_argument_group("Checks","Methods to Verify Package Integrity")
    parser_checks.add_argument("-g","--gpg"  ,help="Check GPG Signatures",action="store_true",default=True)
    parser_checks.add_argument("-a","--hash" ,help="Check MD5 Hash signatures",action="store_true",default=False)
    
    parser_write  = parser.add_argument_group("Write Options", "Options for USB Stick Burning")
    parser_write.add_argument("-w","--write" ,help="Write to the USB stick. enabled by default. Disable if just checking package",default=True)
    parser_write.add_argument("-f","--format",help="Parition the USB stick. If this option is not checked, target a partition")

    parser_source = parser.add_argument_group("Source", ".liveos.zip package options")
    parser_source.add_argument('-k','--package' ,help=".liveos.zip package file to burn.",type=str,nargs=1)

if __name__ == "__main__":
    main()
