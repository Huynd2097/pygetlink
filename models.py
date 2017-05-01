import urllib
import re


AUDIO_EXTENTIONS = ['mp3', 'm4a', 'flac', 'wav']
VIDEO_EXTENTIONS = ['mp4', 'm4v', 'flv', 'webm', 'avi', '3gp']

class FileInfo(object):
	def __init__(self, url='', quality='', title='', ext=''):
		# Make sure url valid
		self.__url = url if re.search('^http(s)?://', url) else ('http://' + url)
		self.__quality = quality
		self.__title = title or 'Untitled'
		# Get ext of file in url
		ext = ext or self.__url.split('.')[-1]
		# ext = tar.gz
		self.__ext = ext if len(ext) <= 6 else ''

	def __str__(self):
		return self.__url + '   ' + self.fileName

	def to_tuple(self):
		return [self.__url, self.fileName, self.__ext]

	@property
	def url(self):
		return self.__url 

	@property
	def quality(self):
		return self.__quality 

	@property
	def title(self):
		return self.__title

	@property
	def ext(self):
		return self.__ext

	@property
	def fileName(self):
		# Remove duplicate ext
		file_name = self.__title
		ext = '.' + self.__ext
		if (file_name.endswith(ext)):
			file_name = file_name.replace(ext, '')
			
		quality = str(self.__quality)
		try:
			int(self.__quality)
			if (self.__ext in AUDIO_EXTENTIONS):
				quality +='kbps' 
			elif (self.__ext in VIDEO_EXTENTIONS):
				quality += 'p'
		except Exception as e:
			pass

		if quality:
			file_name += '-' + quality
		file_name += ext

		return file_name

	def set_url_title(self, title=None):
		title = title or self.__fileName

		if title and (isinstance(title, unicode) or isinstance(title, str)):
			# urlencode title
			title = urllib.quote_plus(title)

			# Replace existed title with new title or append new title
			match = re.search('\&title=(.*?)(&|$)', url)
			if match:
				url = self.__url.replace(match.group(1),title)
			else:
				url = self.__url + '&title=' + title

		# Get all legal character
		self.__url = ''.join( re.findall('[\w:\\\/\.?=&%-]', url) )
		return self.__url	 

	def newObj(self, newUrl=None, newQuality=None, newTitle=None, newExt=None):
		return FileInfo(url = newUrl or self.__url, quality = newQuality or self.__quality, \
						title = newTitle or self.__title, ext = newExt or self.__ext)




# # auto detect host
# # if 0<= startEp <= endEp: return array list
# def get_link(url, quality='default', password=''):
# 	if not re.search('^http(s)?://', url):
# 		url = 'http://' + url

# 	match = re.search('://(www\.)?(.+)\..*?/', url)
# 	if not match:
# 		return to_json(ERROR_CODE['url'] + url)

# 	match = re.findall('(\w)', match.group(2))
# 	funcGetLink = 'get_link_' + ''.join(match)
# 	funcGetList = 'get_list_' + ''.join(match)

# 	if (not funcGetLink in globals()):
# 		return to_json('error','Unsupported site!')

# 	#check get list
# 	if (funcGetList in globals()) and isinstance(startEp, int) \
# 		and isinstance(endEp, int) and (0<= startEp <= endEp):

# 		listsFilms = eval(funcGetList)(url)
# 		queueUrls = []
# 		for filmInfo in listsFilms:
# 			if not isinstance(filmInfo, dict):
# 				continue
# 			key = filmInfo.keys()[0]
# 			Ep = re.search('(\d+)', key).group(1) if (not isinstance(key, int)) else key
# 			#check Episode in range requests
# 			rangeEp = range(startEp, endEp + 1)
# 			if Ep in rangeEp:
# 				rangeEp.remove(Ep)	#remove avoid duplicate
# 				qUrl = filmInfo[key]
# 				queueUrls.append({'funcGetLink':funcGetLink,'url':qUrl, 'quality':quality})

# 		return Pool(__maxThread).map(multi_run_get_links, queueUrls)
# 	return eval(funcGetLink)(url, quality)
