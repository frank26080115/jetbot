import os
from pathlib import Path
import subprocess

def convert_to_uff(fpath):
	fpath = Path(fpath)
	pb_path = Path('%s/%s.pb' % (fpath.parent.as_posix(), fpath.stem))
	uff_path = Path('%s/%s.uff' % (fpath.parent.as_posix(), fpath.stem))
	print("Converting .pb file to .uff file, \"%s\" >> \"%s\"" % (pb_path, uff_path))

	#subprocess.run(["convert-to-uff", "--output=%s" % str(uff_path), str(pb_path)])
	import uff
	uff.from_tensorflow_frozen_model(str(pb_path), output_filename=str(uff_path))

	if os.path.exists(uff_path) and os.path.isfile(uff_path):
		print("Conversion of .pb to .uff file succeeded")
		return True
	else:
		print("Conversion of .pb to .uff file failed")
		return False
