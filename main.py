from __future__ import division
import itertools
from operator import itemgetter, attrgetter
import echonest.remix.audio as audio
import easygui as eg
import sys
import subprocess
from multiprocessing import Process


majorscaletemp = [0, 2, 4, 5, 7, 9, 11]
minorscaletemp = [0, 2, 3, 5, 6, 8, 11]

majortriadtemp = [0, 4, 5]
minortriadtemp = [0, 3, 5]

notedict = {0 : "C", 1 : "Db", 2 : "D", 3 : "Eb", 4 : "E", 5 : "F", 6 : "F#", 7 : "G", 8 : "Ab", 9 : "A", 10 : "Bb", 11 : "B"}

class Note:
	def __init__(self, value = 0, confidence = 0):
		#0 = C
		self.value = value
		self.confidence = confidence

class Chord:
	def __init__(self, notes = [], clength = 0, mode = 0):
		self.notes = notes
		self.clength = clength
		self.mode = mode

	def notelist(self):
		notelist = []
		for note in self.notes:
			notelist.append(note.value)
		return notelist

class Song:
	def __init__(self, chords = []):
		self.chords = chords

def generatechord(chord = Chord(), offset = 0, root = 0, mode = 0):
	#function to generate chord
	bigoffset = 12
	#generate first note of chord based on root + offset, then generate the others based on similar math
	chord.notes[0].value = abs((root + offset)) 
	if chord.notes[0].value > 11:
		chord.notes[0].value = chord.notes[0].value - bigoffset

	if mode == 1:
		chord.notes[1].value = abs((chord.notes[0].value + 4))
		if chord.notes[1].value > 11:
			chord.notes[1].value = chord.notes[1].value - bigoffset

	if mode == 0:
		chord.notes[1].value = abs((chord.notes[0].value + 3))
		if chord.notes[1].value > 11:
			chord.notes[1].value = chord.notes[1].value - bigoffset

	chord.notes[2].value = abs((chord.notes[0].value + 7))
	if chord.notes[2].value > 11:
			chord.notes[2].value = chord.notes[2].value - bigoffset

	chord.mode = mode
	chord.clength = 3

	return chord


def parsechords(song = Song(), chunks = [], minconfidence = 0):
	#parse song chords and see what fits to key/chords
	chord = Chord()
	chord = generatechord(chord, 7, song.chords[0].notes[0].value, 1)

	nstring = "chord: "
	for x in chord.notelist():
		nstring = nstring + str(notedict[x]) + " "
	print nstring

	for chunk in chunks:

		pitchconf = chunk.mean_pitches()

		noteavgconf = sum(pitchconf) / 12
		minconf = noteavgconf * minconfidence

		for i in range(len(pitchconf)):
			pitch = pitchconf[i]
			note = Note(i, pitchconf[i])


		"""max_indexes = []
		max_pitches = sorted(pitchconf, key=)
		print set(max_pitches)
		for pitch in max_pitches:
			#pitch = pitchconf[i]
			max_indexes.append(max_pitches.index(pitch))


		cnoteset = set(chord.notelist())
		print set(max_indexes)
		print set(chord.notelist())
		if cnoteset.issubset(set(max_indexes)):
			filtered_chunks.append(chunk)"""

def organizechord(chord = Chord()):
	#ordering chord notes through note value math
	counter = 0
	ordered = 0
	while counter < 4:
		#finding if major 3rd interval

		if abs(chord.notes[0].value - chord.notes[1].value) == 4 or abs(chord.notes[0].value - chord.notes[1].value) == 8:
			if abs(chord.notes[1].value - chord.notes[2].value) == 3 or abs(chord.notes[1].value - chord.notes[2].value) == 9:
				chord.mode = 1
				ordered = 1
				counter = 4
		#finding if minor 3rd interval
		if abs(chord.notes[0].value - chord.notes[1].value) == 3 or abs(chord.notes[0].value - chord.notes[1].value) == 9:
			if abs(chord.notes[1].value - chord.notes[2].value) == 4 or abs(chord.notes[1].value - chord.notes[2].value) == 8:
				chord.mode = 0
				ordered = 1
				counter = 4
		#reordering
		else:
			chord.notes = [chord.notes[2], chord.notes[0], chord.notes[1]]
			counter += 1
	print chord.notelist()
	if ordered == 1:
		return chord
	else:
		print "Found root chord is not a valid triad"
		return

def findroot(chunks = [], minconfidence = 0):
	#find and return root chord given array of chunks
	chordarray = []
	root = Chord(clength = 3)

	for chunk in chunks:
		pitchconf = chunk.mean_pitches()

		noteavgconf = sum(pitchconf) / 12
		#print "average note conf: " + str(noteavgconf)
		minconf = noteavgconf * minconfidence
		#print "minimum note conf: " + str(minconf)
		chord = Chord(clength = 3)

		for i in range(len(pitchconf)):
			note = Note(i, pitchconf[i])
			#pitch = actual pitch confidence value
			#i = pitch value on note scale
			if note.confidence > minconf:
				if not chord.notes:
					chord.notes.append(note)
				else:
					validinterval = 0
					for x in chord.notes:
						#iterate through existing notes making sure all the intervals are correct
						if abs((x.value) - (note.value)) > 2:
							validinterval += 1
							#print "list: " + str(len(chord.notes))
					#print "validinterval: " + str(validinterval)
					if validinterval == len(chord.notes):
						chord.notes.append(note)
		if len(chord.notes) == chord.clength:
			chordarray.append(chord)
			#print "chord valid"
		#else:
			#print "chord not valid"

	#gets rid of duplicate array entries, checks if they are all the same
	if chordarray[0] == chordarray[1]:
		root = chordarray[0]

	root = organizechord(root)

	pstring = "root: "
	for i in root.notes:
		pstring = pstring + str(notedict[i.value]) + " "
	print pstring

	return root

def loadsong(filename = ""):
	audiofile = audio.LocalAudioFile(filename)
	rootstr = ""
	pkey = ""
	pmode = ""
	#beats, tatums, or segments?
	chunks = audiofile.analysis.__getattribute__("tatums")
	pkey = audiofile.analysis.__getattribute__("key")
	pmode = audiofile.analysis.__getattribute__("mode")
	minconfidence = 1.5

	#loudness = chunk.mean_loudness()
	#filtered_chunks.append(chunk)

	#find key of song/root chord
	thissong.chords.append(findroot(chunks, minconfidence))

	for i in thissong.chords[0].notes:
		rootstr = rootstr + str(notedict[i.value]) + " "
	if thissong.chords[0].mode == 1:
		rootstr = rootstr + "(Major)"
	elif thissong.chords[0].mode == 0:
		rootstr = rootstr + "(Minor)"
	parsechords(thissong, chunks, minconfidence)

	#file output code
	#out = audio.getpieces(audiofile, filtered_chunks)
	#out.encode("out.mp3")

	#audio_file = "out.mp3"
	#subprocess.call(["afplay", filename])

	return [rootstr, pkey, pmode]

filtered_chunks = []
thissong = Song()

while 1:
	title = "EchoNest API song key analyzer"
	reply = eg.enterbox("Type song filename", title)
	if reply:
		response = loadsong(reply)
		if response:
			subprocess.Popen(["afplay", reply])
			eg.textbox("Results ", title, "Calculated Root chord: " + response[0] + "\n" + " EchoNext Calculated Root Note and confidence: " + str(response[1]) + "\n" + " EchoNext Calculated Mode and confidence: " + str(response[2]) + "\n")
	else:
		sys.exit(0)
	
#music.play()

#------------

#notes
#track load --> find pitches for keys from song parts --> draw keyboard and link sounds to keys
#possiblity: noise-filled sections for drum machine?

#audionode to send notes to keyboard?