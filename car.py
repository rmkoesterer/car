from contextlib import contextmanager
import evdev
import time
import mpd
import subprocess
import sys
from select import select
import os.path

HOST, PORT = 'localhost', 6600
SKIPSIZE = 1
TTSDIR="/home/pi/tts"
VALIDKEYCODES = ["KEY_D","KEY_PLAYPAUSE","KEY_STOPCD","KEY_B","KEY_F","KEY_PREVIOUSSONG","KEY_LEFT","KEY_NEXTSONG","KEY_RIGHT","KEY_UP","KEY_DOWN","KEY_PAGEDOWN","KEY_PAGEUP","KEY_HOME","KEY_F3","KEY_F4","KEY_F6"]
VALIDSEARCHKEYS = ["KEY_1","KEY_2","KEY_3","KEY_4","KEY_5","KEY_6","KEY_7","KEY_8","KEY_9","KEY_0"]
TX = [('abc','2'),('def','3'),('ghi','4'),('jkl','5'),('mno','6'),('pqrs','7'),('tuv','8'),('wxyz','9')]
TXMAP = {c:v for k,v in TX for c in k}
client = mpd.MPDClient()

# A mapping of file descriptors (integers) to InputDevice instances.
remotes = map(evdev.InputDevice, ('/dev/input/event0', '/dev/input/event1', '/dev/input/event2'))
remotes = {dev.fd: dev for dev in remotes}

@contextmanager
def connection():
	try:
		client.connect(HOST, PORT)
		yield
	finally:
		client.close()
		client.disconnect()

def exec_mpd(cmd):
	with connection():
		try:
			x = eval("%s" % cmd)
		except Exception, err:
			print err
			x = None
	return x

def list_all():
	with connection():
		try:
			x = client.listall()
		except mpd.CommandError:
			return None
		else:
			return x

def status():
	return exec_mpd("client.status()")

def stats():
	return exec_mpd("client.stats()")

def speak(list):
	try:
		output = subprocess.call(["mpg123","--gapless"] + [os.path.join(TTSDIR,s + ".mp3") for s in list])
	except subprocess.CalledProcessError as e:
		print("Error... returncode: " + e.returncode + ", output:\n  " + e.output)

def info():
	s = status()
	if s is not None:
		exec_mpd("client.pause(1)")
		if s['state'] == 'stop':
			speak(["current_state_stop"])
		elif s['state'] == 'play':
			speak(["current_state_play"])
			exec_mpd("client.pause(0)")
		else: # s['state'] == 'pause'
			speak(["current_state_pause"])
	else:
		print "unable to get info"

def toggleplay():
	s = status()
	if s['state'] == 'stop':
		exec_mpd("client.play()")
	elif s['state'] == 'pause':
		exec_mpd("client.pause(0)")
	else: # s == 'play'
		exec_mpd("client.pause(1)")

def togglerandom():
	s = status()
	exec_mpd("client.pause(1)")
	if s['random'] == '0':
		exec_mpd("client.random(1)")
		speak(["random_on"])
		if s['consume'] == '0':
			exec_mpd("client.consume(1)")
	else: # s['random'] == '1'
		exec_mpd("client.random(0)")
		speak(["random_off"])
		if s['consume'] == '1':
			exec_mpd("client.consume(0)")
	if s['state'] == 'play':
		toggleplay()

def togglerepeat():
	s = status()
	exec_mpd("client.pause(1)")
	if s['repeat'] == '0':
		exec_mpd("client.repeat(1)")
		speak(["repeat_on"])
	else: # s['repeat'] == '1'
		exec_mpd("client.repeat(0)")
		speak(["repeat_off"])
	if s['state'] == 'play':
		toggleplay()

def pause():
	exec_mpd("client.pause(1)")

def stop():
	exec_mpd("client.stop()")

def skipforward(seconds):
	exec_mpd("client.seekcur('+%s')" % str(seconds))

def skipbackward(seconds):
	exec_mpd("client.seekcur('-%s')" % str(seconds))

def next():
	exec_mpd("client.next()")

def previous():
	exec_mpd("client.previous()")

def home():
	exec_mpd("client.seek(0, 0)")

def clear():
	exec_mpd("client.clear()")

def show():
	exec_mpd("client.playlist()")

def previous_album():
	s = exec_mpd("client.currentsong()")
	pl = exec_mpd("client.playlistinfo()")
	pl_albums = sorted(list(set([x['album'] for x in pl if x['artist'] == s['artist']])))
	if len(pl_albums) > 1:
		idx = pl_albums.index(s['album'])
		if idx > 0:
			pl_previous = sorted(list(set([x['pos'] for x in pl if x['album'] == pl_albums[idx - 1]])))
			exec_mpd("client.seek(%s, 0)" % pl_previous[0])

def next_album():
	s = exec_mpd("client.currentsong()")
	pl = exec_mpd("client.playlistinfo()")
	pl_albums = sorted(list(set([x['album'] for x in pl if x['artist'] == s['artist']])))
	if len(pl_albums) > 1:
		idx = pl_albums.index(s['album'])
		if idx < len(pl_albums) - 1:
			pl_next = sorted(list(set([x['pos'] for x in pl if x['album'] == pl_albums[idx + 1]])))
			exec_mpd("client.seek(%s, 0)" % pl_next[0])

def previous_artist():
	s = exec_mpd("client.currentsong()")
	pl = exec_mpd("client.playlistinfo()")
	pl_artists = sorted(list(set([x['artist'] for x in pl])))
	if len(pl_artists) > 1:
		idx = pl_artists.index(s['artist'])
		if idx > 0:
			pl_previous = sorted(list(set([x['pos'] for x in pl if x['artist'] == pl_artists[idx - 1]])))
			exec_mpd("client.seek(%s, 0)" % pl_previous[0])

def next_artist():
	s = exec_mpd("client.currentsong()")
	pl = exec_mpd("client.playlistinfo()")
	pl_artists = sorted(list(set([x['artist'] for x in pl])))
	if len(pl_artists) > 1:
		idx = pl_artists.index(s['artist'])
		if idx < len(pl_artists)-1:
			pl_next = sorted(list(set([x['pos'] for x in pl if x['artist'] == pl_artists[idx + 1]])))
			exec_mpd("client.seek(%s, 0)" % pl_next[0])

def listen_mode():
	while True:
		r, w, x = select(remotes, [], [])
		for fd in r:
			for event in remotes[fd].read():
				if event.type == evdev.ecodes.EV_KEY:
					keyevent = evdev.KeyEvent(event)
					print keyevent.keycode
					if keyevent.keycode in VALIDKEYCODES:
						if keyevent.keycode == "KEY_D" and keyevent.keystate == 1: # info key
							info()
						elif keyevent.keycode == "KEY_PLAYPAUSE" and keyevent.keystate == 1: # play/pause key
							toggleplay()
						elif keyevent.keycode == "KEY_F3" and keyevent.keystate == 1: # red key
							togglerandom()
						elif keyevent.keycode == "KEY_F6" and keyevent.keystate == 1: # blue key
							togglerepeat()
						elif keyevent.keycode == "KEY_STOPCD" and keyevent.keystate == 1: # stop key
							stop()
						elif keyevent.keycode == "KEY_B" and keyevent.keystate in [1,2]: # rw key
							skipbackward(SKIPSIZE)
						elif keyevent.keycode == "KEY_F" and keyevent.keystate in [1,2]: # ff key
							skipforward(SKIPSIZE)
						elif keyevent.keycode in ["KEY_PREVIOUSSONG","KEY_LEFT"] and keyevent.keystate == 1: # previous key
							previous()
						elif keyevent.keycode in ["KEY_NEXTSONG","KEY_RIGHT"] and keyevent.keystate == 1: # next key
							next()
						elif keyevent.keycode == "KEY_UP" and keyevent.keystate == 1: # up key
							next_album()
						elif keyevent.keycode == "KEY_DOWN" and keyevent.keystate == 1: # down key
							previous_album()
						elif keyevent.keycode == "KEY_PAGEDOWN" and keyevent.keystate == 1: # ch- key
							previous_artist()
						elif keyevent.keycode == "KEY_PAGEUP" and keyevent.keystate == 1: # ch+ key
							next_artist()
						elif keyevent.keycode == "KEY_HOME" and keyevent.keystate == 1: # home key
							home()
						elif keyevent.keycode == "KEY_F4" and keyevent.keystate == 1:
							return

def search_mode(uids):
	pause()
	selected = sorted(uids.values())
	if len(selected) == 1:
		speak(["no_other_artists_found"])
		toggleplay()
		return
	speak(["search_mode","search_mode_prompt"])
	UID=""
	while len(selected) > 1:
		r, w, x = select(remotes, [], [])
		for fd in r:
			for event in remotes[fd].read():
				if event.type == evdev.ecodes.EV_KEY:
					keyevent = evdev.KeyEvent(event)
					print keyevent.keycode
					if keyevent.keycode in VALIDSEARCHKEYS:
						if keyevent.keystate == 1:
							keynum = keyevent.keycode.split("_")[1]
							speak([keynum])
							UID = UID + keynum
					elif keyevent.keycode == "KEY_ENTER":
						speak(["clearing_playlist"])
						clear()
						if len(selected) <= 10:
							speak(["adding_artists"] + ["artists/" + x.replace(' ','_') for x in selected])
						else:
							speak(["adding_more_than_10_artists"])
						for a in selected:
							exec_mpd("client.findadd('artist','%s')" % a)
						toggleplay()
						return
					elif keyevent.keycode == "KEY_BACKSPACE":
						speak(["returning to current playlist"])
						toggleplay()
						return
					selected = sorted([uids[k] for k in uids.keys() if k.startswith(UID)])
	if len(selected) > 0:
		speak(["clearing_playlist"])
		clear()
		speak(["adding_artist","artists/" + selected[0].replace(' ','_')])
		exec_mpd("client.findadd('artist','%s')" % selected[0])
	else:
		speak(["artist_not_found"])
	toggleplay()
	return

def get_uid(s):
	word = s.replace(' ','').lower()
	return "".join(TXMAP.get(c,c) for c in word)

def main(args=None):

	for remote in remotes:
		print "found input device " + remotes[remote].__fspath__() + "\n  name: " + remotes[remote].name + "\n  phys: " + remotes[remote].phys

	dbfull = list_all()
	dbdirs = [a['directory'] for a in dbfull if 'directory' in a]
	dbartists = [a for a in dbdirs if not '/' in a]
	uids = {get_uid(w): w for w in dbartists}

	while True:
		listen_mode()
		search_mode(uids)

	stop()

if __name__ == "__main__":

	main()
