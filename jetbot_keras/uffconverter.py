import os
from pathlib import Path
import subprocess

def convert_to_uff(fpath):
	pb_path = Path('%s/%s.pb' % (fpath.parent.as_posix(), fpath.stem))
	uff_path = Path('%s/%s.uff' % (fpath.parent.as_posix(), fpath.stem))
	print("Converting .pb file to .uff file, \"%s\" >> \"%s\"" % (pb_path, uff_path))
	subprocess.run(["convert-to-uff", "--output=%s" % uff_path, pb_path])
	if os.path.exists(uff_path) and os.path.isfile(uff_path):
		print("Conversion of .pb to .uff file succeeded")
		return True
	else:
		print("Conversion of .pb to .uff file failed")
		return False
