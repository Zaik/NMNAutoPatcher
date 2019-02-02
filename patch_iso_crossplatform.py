#!/usr/bin/env python3
"""
Nordic Melee Netplay Build v1 created by Anutim
xdelta program created by Josh Macdonald
Original version of this script created by DRGN.
Cross-platform conversion by Rainer Koirikivi
Script version 2.1
"""
from __future__ import print_function
import sys
if sys.version_info[:2] <= (3, 3):
	sys.exit("python 3.3 or later is required to run this utility")

import platform
import subprocess
import shutil

indent = " "
def indent_print(*args, **kwargs):
	print(indent, *args, **kwargs)

python_executable = sys.executable

if platform.system() == 'Windows':
	is_windows = True
	xdelta_command = 'xdelta3-x86_64-3.0.10.exe'
else:
	is_windows = False
	xdelta_command = 'xdelta3'

try:
	original_iso = sys.argv[1]
except IndexError:
	indent_print("run this utility from the command line, like this:".format(sys.argv[0]))
	indent_print("")
	indent_print("{} '/path/to/Super Smash Bros Melee.iso'".format(sys.argv[0]))
	indent_print("")
	indent_print("The ISO file can be the Vanilla PAL ISO or Nordic Melee Netplay Build iso (any version, not Melee Netplay Community Build though)")
	sys.exit(1)

# Confirm existence of the relevant utilities
if not shutil.which(xdelta_command):
	if is_windows:
		indent_print("You do not have xDelta on your user path, it SHOULD have been bundled with this script")
		indent_print("Check that you're executing this script from the correct directory")
		indent_print('This utility requires "{}" to run'.format(xdelta_command))
	else:
		indent_print('Please install "{}" to run this utility'.format(xdelta_command))
	sys.exit(1)

indent_print("Now attempting to obtain the latest patchinfo file from the server")
indent_print("Starting python script...")
try:
	subprocess.check_call([
		python_executable,
		"obtain_patch_info.py",
	])
except subprocess.CalledProcessError:
	indent_print("Failed to obtain the latest patches. If you already have the patchinfo file and")
	indent_print("the xdelta files, you can continue patching to the version you already have.")
	indent_print("Would you like to continue with already existing patchinfo?")
	indent_print("(will fail if you do not have the files)")
	if input("- (y/n)").lower() in ("n", "no"):
		sys.exit(1)
indent_print("Patches succesfully obtained!")

indent_print("Now attempting to read and apply patches")

try:
	subprocess.check_call([
		python_executable,
		"read_and_apply_patch_info.py",
		original_iso,
	])
except subprocess.CalledProcessError:
	indent_print("Something went wrong while reading or applying patches")
	indent_print("This is most likely due to missing patches or incorrect checksums")
	indent_print("but check the output from the python script for more details.")
	sys.exit(1)

indent_print("Succesfull! You should now have the latest version of NMNB!")
