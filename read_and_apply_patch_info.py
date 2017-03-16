#This utility does 4 things:
# Reads the patch_info.csv file to obtain information about which versions should exist, what their xdelta files are and what the resulting md5 hash should be
# Verifies the existance of each patch
# Obtains the version of your current ISO either by md5 hash or by user input
# Applies the xdelta patches to obtain the latest version
import sys
import csv
import subprocess
import os

has_cert_utils = False

if len(sys.argv) < 2:
	print "This utility requires at least one argument (the file that is the source for the patches)"
	print "Exiting..."
	sys.exit(1)
orig_file = sys.argv[1]

if len(sys.argv) > 2:
	if len(sys.argv) > 3:
		print "This utility script takes at most 2 arguments, ignoring extra arguments..."
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
print "Reading versioninfo.csv..."
with open('versioninfo.csv','rb') as csvfile:
	reader = csv.DictReader(csvfile)
	for row in reader:
		md5_version_map[row['md5']] = (row['version'], row['latest'] == 'latest')
		set_of_versions.add(row['version'])
		if row['latest'] == 'latest':
			latest_version = row['version']
if latest_version == None:
	print "WARNING: No version is marked as latest. You can still specify the target version manually"
print "Done"
print "Obtained info about the following versions:"
for key in md5_version_map:
	ver, latest = md5_version_map[key]
	print ver + (" (latest)" if latest else "")
print "Reading patchinfo.csv"
with open('patchinfo.csv','rb') as csvfile:
	reader = csv.DictReader(csvfile)
	for row in reader:
		xdelta_patch_set.add((row['patchfile'], row['fromversion'], row['toversion']))
print "Done"
todelete = []
print "Verifying existence of patch files..."
for file, fversion, tversion in xdelta_patch_set:
	try:
		open(file,'r')
	except:
		print "WARNING: " + file + " was declared as an xdelta patch but was not found, continuing..."
		todelete.append((file, fversion, tversion))
print "Done"
if todelete != []:
	print "WARNING: Some patches could not be found, the patcher will try to bring you to the latest version anyway but there might not be a path from your current ISO to the latest version with existing patches"
	for tuple in todelete:
		xdelta_patch_set.remove(tuple)

current_version = None

print "Determining original ISO version..."
#determine version of current ISO
if has_cert_utils:
	#obtain md5 of ISO to automatically determine version
	try:
		hash = subprocess.check_output(" ".join(["CertUtil", "-hashfile", orig_file, "\"MD5\""]), shell = True)
		hash = hash.split('\n')[1]
	except subprocess.CalledProcessError as E:
		print "Error in checking hash: " + str(E) + "\n" + str(E.output)
		hash = None
	if hash not in md5_version_map:
		print "WARNING: Your ISOs md5 does not match any known versions, you can specify the version manually but this is NOT recommended when the md5 does not match"
	else:
		current_version = md5_version_map[hash]
else:
	print "'CertUtil' program is not available"

if current_version == None:
	print "Do you want to specify current version manually?"
	responded = False
	response = raw_input("(y/n):").lower()
	while (response != 'y' and response != 'n'):
		response = raw_input("Please respond 'y' or 'n' (y/n):")
	if response == 'n':
		print "Exiting due to unable to determine original ISO version"
		sys.exit(1)
	response = raw_input("Input name of version (or 'EXIT' to exit):")
	if response == 'exit':
		print "Exiting due to unable to determine original ISO version"
		sys.exit(1)
	while not response in set_of_versions:
		response = raw_input("Incorrect version specifier, retry or type 'EXIT' to exit:")
		if response == 'exit':
			print "Exiting due to unable to determine original ISO version"
			sys.exit(1)
	current_version = response
print "Done"

print "Determining update path"
version_patch_map = {}
for patch, from_v, to_v in xdelta_patch_set:
	if from_v in version_patch_map:
		version_patch_map['from_v'].add((to_v, patch))
	else:
		version_patch_map['from_v'] = set([(to_v, patch)])
		
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
				search_stack.push((to_v, path + [to_v], patches + [patch]))

if len(viable_paths) == 0:
	print "ERROR: Could not find a patch path from your current version to the latest version\nExiting..."
	sys.exit(1)

viable_paths.sort(key = len)
patch_path = viable_paths[0]
print "Done"

print "Merging patches..."
merged_delta_name = "\"merged_deltas_for_" + latest_version + "\""
subprocess.check_call("xdelta3-x86_64-3.0.10.exe " + " ".join(["-m " + patch for patch in patch_path[:-1]) + " " + patch_path[-1] + " " + merged_delta_name)
print "Done"

print "Applying merged patch..."
output_file = "NordicMeleeNetplayBuildv{0}.iso".format(latest_version)
subprocess.check_call("xdelta3-x86_64-3.0.10.exe -d -s {0} {1} {2}".format(orig_file, merged_delta_name, output_file))
print "Done"
if not has_cert_utils:
	print "WARNING: CertUtils is not available, cannot verify integrity of generated file"
else:
	print "Verifying integrity of generated file"
	try:
		hash = subprocess.check_output(" ".join(["CertUtil", "-hashfile", output_file, "\"MD5\""]), shell = True)
		hash = hash.split('\n')[1]
	except subprocess.CalledProcessError as E:
		print "Error in checking hash: " + str(E) + "\n" + str(E.output)
		hash = None
	if hash is not None:
		if hash not in md5_version_map or md5_version_map[hash] != latest_version:
			print "WARNING: The hash of the generated file does not match the expected hash. Most likely it is not correct"
			sys.exit(1)
		else:
			print "Verified!"
print "Patching complete, exiting python script"