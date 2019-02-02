import sys
try:
	from dulwich import porcelain
	from dulwich.repo import Repo
	use_dulwich = True
except ImportError:
	use_dulwich = False

indent = " "
def indent_print(*args, **kwargs):
	print(indent, *args, **kwargs)

indent_print("Obtaining 'patch_info.csv', 'version_info.csv' and xdelta files...")

repo_url = "git://github.com/Anutim/NordicMeleeBuild.git"
repo_dir = "patchAndVersionFiles"

if use_dulwich:
	try:
		repo = Repo(repo_dir)
		config = repo.get_config()
		porcelain.pull(repo_dir, repo_url)
	except Exception as e1:
		try:
			porcelain.clone(repo_url, repo_dir)
		except Exception as e2:
			indent_print("Failed to clone or pull remote repo using git.")
			indent_print("Check that you're connected to the internet.")
			indent_print("Exception dump:")
			indent_print("Pull failed:", repr(e1))
			indent_print("Clone failed:", repr(e2))
			sys.exit(1)
else:
	import os
	import shutil
	import subprocess
	if not shutil.which('git'):
		indent_print(
			'Install either the "dulwich" python package or the '
			'"git" tool to run this utility'
		)
		sys.exit(1)
	indent_print(
		'Using "git" since the "dulwich" python package is not installed'
	)
	if os.path.exists(repo_dir):
		subprocess.check_output([
			'git',
			'pull',
			repo_url,
		], cwd=repo_dir)
	else:
		subprocess.check_output([
			'git',
			'clone',
			repo_url,
			repo_dir,
		])
