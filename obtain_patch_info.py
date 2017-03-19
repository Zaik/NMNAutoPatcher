from dulwich import porcelain
from dulwich.repo import Repo
import sys

indent = " "
def indent_print(*args, **kwargs):
	print(indent, *args, **kwargs)

indent_print("Obtaining 'patch_info.csv', 'version_info.csv' and xdelta files...")

repo_url = "git://github.com/Anutim/NordicMeleeBuild.git"
repo_dir = "patchAndVersionFiles"

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
