import subprocess
from glob import glob
import os

def main(args=None):

	artists = [os.path.basename(s.rstrip("/")) for s in glob("/mnt/disk1/general/"+"*/")]

	for artist in artists:
		out = artist.replace(" ","_")
		try:
			output = subprocess.call(["gtts-cli","-l","en-uk","\"%s\"" % artist,"--output","tts/artists/%s.mp3" % out])
		except subprocess.CalledProcessError as err:
			print("Error... returncode: " + err.returncode + ", output:\n  " + err.output)

if __name__ == "__main__":

	main()
