from sunlight.errors import LegislationError

import xml.dom.minidom as domdom
from hashlib import sha1 as sha

import operator
import re

def get_text(x):
	"""
	Get the text from a minidom node or from each of its child nodes.
	Return appended version.

	Recurses on x.
	"""
	if hasattr(x, 'wholeText'):
		# TEXT NODE
		return x.wholeText

	if hasattr(x, 'childNodes'):
		# OTHER NODE WITH CHILDREN
		return reduce(operator.__add__, map(get_text, x.childNodes), '')

	# I DON'T KNOW WHAT KIND OF NODE THIS IS
	return ''

def strip_text(s):
	"""
	From a string s, only keep around A-z and make everything lowercase.
	"""
	return reduce(operator.__add__, [ss for ss in s if ss.isalpha()], '').lower()
	
def get_sha_of_text(x):
	"""
	Returns the hexdigest of the sha1 hash of get_text(x)
	"""
	text = get_text(x)
	text = strip_text(text)
	shatext = sha(text.encode('utf-8'))
	return shatext.hexdigest()

def make_printable(s):
	"""
	Removes newlines and carriage returns from s
	Turns tabs to 4 spaces.
	"""
	# Would use s.translate, but that doesn't work with unicode strings
	return re.sub('[\n\r]', '', s).replace('\t', '    ')

def paragraphs_to_sha(f, keep_paragraphs=False):
	"""
	Takes as input a file handle which is a piece of legislative xml and returns
	a list of lists containing shaed versions of paragraphs.

	Methodology
	-----------
	Takes the paragraph tags and first:
		1. Strips out all subtags
		2. Only keeps [A-z]
		3. Makes all lowercase

	Returns
	-------
	List of lists where the sublists are:
		bill_id, paragraph_id, sha_of_manipulated_paragraph[, paragraph if keep_paragraphs]

	Raises
	------
	If f is a malformed xml file will raise an
		xml.parsers.expat.ExpatError

	If f doesn't have certain tags (e.g., a title), raises
		sunlight.errors.LegislationError
	"""

	tree = domdom.parse(f)
	bill_name = tree.getElementsByTagName("dc:title")
	if len(bill_name) == 0:
		raise LegislationError("%s doesn't have a title tag" % f.name)
	elif len(bill_name) > 1:
		raise LegislationError("%s has more than one title tag" % f.name)

	bill_name = bill_name[0].firstChild.wholeText	

	# Bill names are structured as
	# 	number_of_congress type_of_bill number_of_bill subtype_of_bill: full_name_of_bill
	#	e.g. 112 HR 7 HR: American Energy and Infrasturcture Jobs Act of 2012
	# But sometimes there are errors......
	bill_id = bill_name.split(':')[0]

	paragraphs = tree.getElementsByTagName("paragraph")
	if keep_paragraphs:
		paragraphs = [ (bill_id, 
						p.attributes['id'].value.lower(), 
						get_sha_of_text(p),
						make_printable(get_text(p))) for p in paragraphs ]
	else:
		paragraphs = [ (bill_id, 
						p.attributes['id'].value.lower(), 
						get_sha_of_text(p)) for p in paragraphs ]
	return paragraphs

def paragraphs_with_shas(f, shas):
	"""
	Takes input a file f and returns the text of the paragraphs in f which
	match one of the shas in shas.
	"""
	tree = domdom.parse(f)
	paragraphs = tree.getElementsByTagName("paragraph")
	return [ (get_sha_of_text(p), 
				make_printable(get_text(p))) 
					for p in paragraphs if get_sha_of_text(p) in shas ]
