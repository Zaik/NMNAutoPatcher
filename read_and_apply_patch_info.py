#This utility does 4 things:
# Reads the patch_info.csv file to obtain information about which versions should exist, what their xdelta files are and what the resulting md5 hash should be
# Verifies the existance of each patch
# Obtains the version of your current ISO either by md5 hash or by user input
# Applies the xdelta patches to obtain the latest version
import sys
import csv
import subprocess
import os
import platform
import hashlib

has_cert_utils = False

repo_dir = "patchAndVersionFiles"

indent = " "
def indent_print(*args, **kwargs):
	print(indent, *args, **kwargs)

def file_md5(file_path):
	# Stack Overflow Driven Programming: https://stackoverflow.com/questions/3431825/generating-an-md5-checksum-of-a-file
	hash_md5 = hashlib.md5()
	with open(file_path, 'rb') as f:
		for chunk in iter(lambda: f.read(4096), b""):
			hash_md5.update(chunk)
	return hash_md5.hexdigest()

if platform.system() == 'Windows':
	is_windows = True
	xdelta_command = 'xdelta3-x86_64-3.0.10.exe'
else:
	is_windows = False
	xdelta_command = 'xdelta3'

if len(sys.argv) < 2:
	indent_print("This utility requires at least one argument (the file that is the source for the patches)")
	indent_print("Exiting...")
	sys.exit(1)
orig_file = sys.argv[1]

if len(sys.argv) > 2:
	if len(sys.argv) > 3:
		indent_print("This utility script takes at most 2 arguments, ignoring extra arguments...")
	arg = sys.argv[2]
	if arg == "true":
		has_cert_utils = True

#format: (<patch_file>, <from_version>, <to_version>)
xdelta_patch_set = set()
#format:  <md5> : (<version_name>, <latest>:bool)
md5_version_map = {}

set_of_versions = set()
latest_version = None

#obtain version info
indent_print("Reading versioninfo.csv...")
with open(os.path.join(repo_dir, 'version_info.csv'),'rt') as csvfile:
	reader = csv.DictReader(csvfile)
	for row in reader:
		md5_version_map[row['md5']] = (row['version'], row['latest'] == 'latest')
		set_of_versions.add(row['version'])
		if row['latest'] == 'latest':
			latest_version = row['version']
if latest_version == None:
	indent_print("WARNING: No version is marked as latest. You can still specify the target version manually")
indent_print("Done")
indent_print("Obtained info about the following versions:")
for key in md5_version_map:
	ver, latest = md5_version_map[key]
	indent_print(ver + (" (latest)" if latest else ""))
indent_print("Reading patchinfo.csv")
with open(os.path.join(repo_dir, 'patch_info.csv'),'rt') as csvfile:
	reader = csv.DictReader(csvfile)
	for row in reader:
		xdelta_patch_set.add((os.path.join(repo_dir, row['patchinfo']), row['fromversion'], row['toversion']))
indent_print("Done")
todelete = []
indent_print("Verifying existence of patch files...")
for file, fversion, tversion in xdelta_patch_set:
	try:
		open(file,'r')
	except:
		indent_print("WARNING: " + file + " was declared as an xdelta patch but was not found, continuing...")
		todelete.append((file, fversion, tversion))
indent_print("Done")
if todelete != []:
	indent_print("WARNING: Some patches could not be found, the patcher will try to bring you to the latest version anyway but there might not be a path from your current ISO to the latest version with existing patches")
	for tuple in todelete:
		xdelta_patch_set.remove(tuple)

current_version = None

indent_print("Determining original ISO version...")
#determine version of current ISO
if is_windows:
	# TODO: this is actually not necessary since we can just use python md5 for windows too
	if has_cert_utils:
		#obtain md5 of ISO to automatically determine version
		try:
			hash = subprocess.check_output(" ".join(["CertUtil", "-hashfile", "\"" + orig_file + "\"", "\"MD5\""]), shell = True)
			hash = hash.split(b'\n')[1]
			hash = hash.decode('utf-8')
			hash = ''.join([ch for ch in hash if ch.isalnum()])
		except subprocess.CalledProcessError as E:
			indent_print("Error in checking hash: " + str(E) + "\n" + str(E.output))
			hash = None
		if hash not in md5_version_map:
			indent_print("WARNING: Your ISOs md5 does not match any known versions, you can specify the version manually but this is NOT recommended when the md5 does not match")
		else:
			current_version = md5_version_map[hash][0]
	else:
		indent_print("'CertUtil' program is not available")
else:
	hash = file_md5(orig_file)
	if hash not in md5_version_map:
		indent_print("WARNING: Your ISOs md5 does not match any known versions, you can specify the version manually but this is NOT recommended when the md5 does not match")
	else:
		current_version = md5_version_map[hash][0]



if current_version == None:
	indent_print("Do you want to specify current version manually?")
	responded = False
	response = input("(y/n):").lower()
	while (response != 'y' and response != 'n'):
		response = input("Please respond 'y' or 'n' (y/n):")
	if response == 'n':
		indent_print("Exiting due to unable to determine original ISO version")
		sys.exit(1)
	response = input("Input name of version (or 'EXIT' to exit):")
	if response == 'exit':
		indent_print("Exiting due to unable to determine original ISO version")
		sys.exit(1)
	while not response in set_of_versions:
		response = input("Incorrect version specifier, retry or type 'EXIT' to exit:")
		if response == 'exit':
			indent_print("Exiting due to unable to determine original ISO version")
			sys.exit(1)
	current_version = response
indent_print("Done")

if current_version == latest_version:
	indent_print("You are already at the latest version, no patching needed!\nExiting")
	sys.exit(0)

indent_print("Your current version is: " + current_version)

indent_print("Determining update path")

version_patch_map = {}
for patch, from_v, to_v in xdelta_patch_set:
	if from_v in version_patch_map:
		version_patch_map[from_v].add((to_v, patch))
	else:
		version_patch_map[from_v] = set([(to_v, patch)])
		
search_stack = [(current_version, [], [])]
viable_paths = []

while search_stack:
	(search_ver, path, patches) = search_stack.pop()
	if search_ver not in path:
		if search_ver == latest_version:
			viable_paths.append(patches)
		else:
			if search_ver not in version_patch_map:
				continue
			for (to_v, patch) in version_patch_map[search_ver]:
				search_stack.append((to_v, path + [search_ver], patches + [patch]))

if len(viable_paths) == 0:
	indent_print("ERROR: Could not find a patch path from your current version to the latest version\nExiting...")
	sys.exit(1)

viable_paths.sort(key = len)
patch_path = viable_paths[0]
indent_print("Done")

source_file = orig_file

indent_print("Patching...")
for index, patch in enumerate(patch_path):
	if patch is patch_path[-1]:
		output_file = "NordicMeleeNetplayBuildv{0}.iso".format(latest_version)
	else:
		output_file = "NordicMeleeNetplayBuild_temp{}.iso".format(index)
	indent_print("Applying {}".format(patch))
	subprocess.check_call([
		xdelta_command,
		'-f',
		'-d',
		'-s',
		source_file,
		patch,
		output_file,
	])
	if index != 0:
		indent_print("Removing previous temporary file")
		os.remove(source_file)
	source_file = output_file
indent_print("Done")

if is_windows:
	if not has_cert_utils:
		indent_print("WARNING: CertUtils is not available, cannot verify integrity of generated file")
	else:
		indent_print("Verifying integrity of generated file")
		try:
			hash = subprocess.check_output(" ".join(["CertUtil", "-hashfile", output_file, "\"MD5\""]), shell = True)
			hash = hash.split(b'\n')[1]
			hash = hash.decode('utf-8')
			hash = ''.join([ch for ch in hash if ch.isalnum()])
		except subprocess.CalledProcessError as E:
			indent_print("Error in checking hash: " + str(E) + "\n") + str(E.output)
			hash = None
		if hash is not None:
			if hash not in md5_version_map or md5_version_map[hash][0] != latest_version:
				indent_print("WARNING: The hash of the generated file does not match the expected hash. Most likely it is not correct")
				sys.exit(1)
			else:
				indent_print("Verified!")
else:
	indent_print("Verifying integrity of generated file")
	hash = file_md5(output_file)
	if hash not in md5_version_map or md5_version_map[hash][0] != latest_version:
		indent_print("WARNING: The hash of the generated file does not match the expected hash. Most likely it is not correct")
		sys.exit(1)
	else:
		indent_print("Verified!")

indent_print("Patching complete, exiting python script")
