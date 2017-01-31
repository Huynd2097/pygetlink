import urllib
import re


AUDIO_EXTENTIONS = ['mp3', 'm4a', 'flac', 'wav']
VIDEO_EXTENTIONS = ['mp4', 'm4v', 'flv', 'webm', 'avi', '3gp']

class FileInfo(object):
	def __init__(self, url='', quality='', title='', ext=''):
		#make sure url valid
		self._url = url if re.search('^http(s)?://', url) else ('http://' + url)
		self._quality = quality
		self._title = title or (self._url.split('/')[-1] if ('/' in self._url) else '')
		self._ext = ext or (self._url.split('.')[-1] if ('.' in self._url) else '')		

	def __str__(self):
		return self._url 

	def to_tuple(self):
		return [self._url, self.fileName, self._ext]

	@property
	def url(self):
		return self._url 
	@property
	def fileName(self):
		quality = str(self._quality)
		try:
			int(self._quality)
			if (self._ext in AUDIO_EXTENTIONS):
				quality +='kbps' 
			elif (self._ext in VIDEO_EXTENTIONS):
				quality += 'p'
		except Exception as e:
			pass
		return ((self._title + '['+quality+']') if self._quality else self._title) + '.' + self._ext

	def set_url_title(self, title=None):
		title = title or self._fileName

		if title and (isinstance(title, unicode) or isinstance(title, str)) :
			title = urllib.quote_plus(title)
			match = re.search('\&title=(.*?)(&|$)', url)
			if match:
				url = self._url.replace(match.group(1),title)
			else:
				url = self._url + '&title=' + title

		self._url = ''.join( re.findall('[\w:\\\/\.?=&%-]', url) )
		return self._url	 

	def newObj(self, newUrl=None, newQuality=None, newTitle=None, newExt=None):
		return FileInfo(url = newUrl or self._url, quality = newQuality or self._quality, \
						title = newTitle or self._title, ext = newExt or self._ext)




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
