# -*- coding: utf-8 -*-

import ast		  #convert response string to dict
import re		   #regex
import requests	 #requests.Session - cookie - get - post
import time		 #sleep
import json
import unicodedata


import base64, md5
import urllib
from Crypto.Cipher import AES

from multiprocessing import Pool

import _support	 #my function


__maxThread = 30			#for multithread
__cookies = {}
__error = ''

'''
url : url not correct to get infomation
source : requests.get(url).content has not infomation to get link, it may be host change algorithms, url wrong
response : after get enough infomation from source, and need requests one more time, most of response is json stringtify
'''
__errorCode = {
	'login'		: "Wrong username or password!",
	'url' 		: "URL invalid: ",					
	'source' 	: "Cannot find required infomation: ",
	'response'	: "Unexpected response: ",
}


def main():

	link1 = 'http://anime47.com/xem-phim-one-piece-dao-hai-tac-ep-001/76748.html'
	link2 = 'http://www.phimmoi.net/phim/dao-hai-tac-665/xem-phim.html'

	link3 = 'http://tv.zing.vn/series/One-Piece-Tap-1-200'
	link4 = 'http://tv.zing.vn/video/Dao-Hai-Tac-One-Piece-Tap-601/IWZA0BWO.html'

	link5 = 'http://mp3.zing.vn/playlist/333-h4212421/IOUUBD77.html?st=6'

	link11 = 'http://www.woim.net/song/39082/arunda.html'
	# for k in lists1:
	#   print k
	# return
	x = 4
	url = get_links(link1, -1)
	# url = get_links(link11)
	# print url 
	# # print get_link_anime47('http://anime47.com/xem-phim-one-piece-dao-hai-tac-ep-046/76793.html')
	# return
	if isinstance(url, str):
		print url
	elif  isinstance(url, dict):
		for u in url:
			print url[u]
	else:
		for u in url:
			print u


class FileInfo(object):
	def __init__(self, url=None, quality=None, title=None, ext=None):
		self.url = url
		self.quality = quality
		self.title = title
		self.ext = ext

	# def __unicode__(self):
	# 	return self.url + ' : ' + self.fileFullName

	def __str__(self):
		return self.url #+ ' : ' + unicodedata.normalize('NFKD', self.fileFullName).encode('ascii','ignore')

	@property
	def fullUrl(self):
		return self.url if re.search('^http://', self.url) else ('http://' + self.url)
	@property
	def fileName(self):
		return (str(self.title) + ' [' + str(self.quality) + ']') if self.quality else self.title

	@property
	def fileFullName(self):
		return self.fileName + '.' + self.ext

	def set_url_title(self, title=None):
		title = title or self.fileName

		if title and (isinstance(title, unicode) or isinstance(title, str)) :
			title = urllib.quote_plus(title)
			match = re.search('\&title=(.*?)(&|$)', url)
			if match:
				url = self.url.replace(match.group(1),title)
			else:
				url = self.url + '&title=' + title

		self.url = ''.join( re.findall('[\w:\\\/\.?=&%-]', url) )
		return self.url	 

	def newObj(self, newUrl=None, newQuality=None, newTitle=None, newExt=None):
		return FileInfo(url = newUrl or self.url, quality = newQuality or self.quality, \
						title = newTitle or self.title, ext = newExt or self.ext)

#Set error and return
def set_error(errorValue, returnValue=None):
	global __error
	if isinstance(__error, list):
		if errorValue:
			__error.append(errorValue)
	else:
		__error = errorValue

	# callerFunctionName = inspect.getouterframes(inspect.currentframe(), 2)[1][3]

	return returnValue

#multithread get_links
def multi_run_get_links(args={}):
	if isinstance(args, dict) and ('funcGetLink' in args) and ('url' in args) and ('quality' in args):
		funcGetLink = args['funcGetLink']
		if (not funcGetLink in globals()):
			return ''
		methodGetLink = eval(funcGetLink)
		return methodGetLink(args['url'], args['quality'])
		
# auto detect host
# if 0<= startEp <= endEp: return array list
def get_links(url, quality='all', startEp=1, endEp = 0):
	if not re.search('^http(s)?://', url):
		url = 'http://' + url

	match = re.search('://(www\.)?(.+)\..*?/', url)
	if not match:
		return set_error(__errorCode['url'] + url)

	match = re.findall('(\w)', match.group(2))
	funcGetLink = 'get_link_' + ''.join(match)
	funcGetList = 'get_list_' + ''.join(match)

	if (not funcGetLink in globals()):
		return set_error('Unknow domain!')

	#check get list
	if (funcGetList in globals()) and isinstance(startEp, int) \
		and isinstance(endEp, int) and (0<= startEp <= endEp):

		listsFilms = eval(funcGetList)(url)
		queueUrls = []
		for filmInfo in listsFilms:
			if not isinstance(filmInfo, dict):
				continue
			key = filmInfo.keys()[0]
			Ep = re.search('(\d+)', key)
			#check Episode in range requests
			rangeEp = range(startEp, endEp + 1)
			if Ep and int(Ep.group(1)) in rangeEp:
				rangeEp.remove(int(Ep.group(1)))	#remove avoid duplicate
				qUrl = filmInfo[key]
				queueUrls.append({'funcGetLink':funcGetLink,'url':qUrl, 'quality':quality})

		return Pool(__maxThread).map(multi_run_get_links, queueUrls)
	return eval(funcGetLink)(url, quality)

############################################################################################################

# def get_link_anime47(url, quality='all'):
# 	if not 'anime47.com/xem-phim' in url:
# 		return set_error(__errorCode[1] + url)

# 	session = requests.session()
# 	source = session.get(url).content

# 	match = re.search('\{link:"https://drive.google.com/(.*?)"', source)
# 	if not match:
# 		return set_error(__errorCode[2] + url)

# 	data = {'link' : 'https://drive.google.com/' + match.group(1) }
# 	response = session.post('http://anime47.com/player/gkphp/plugins/gkpluginsphp.php', data=data).content
# 	if '"link":"https' in response:
# 		# print response
# 		title = re.search('anime47.com/xem-phim-(.*?)/', url).group(1).replace('-', '_')
# 		response = response.replace('\\','').replace('true','True').replace('false','False')
# 		links = ast.literal_eval(response)['link']

# 		opt = {'title':title, 'quality':quality}
# 		return _support.filter_url(links, keyQuality='label', keyUrl='link', option=opt) 

# #return [ {Ep : URL}]
# def get_list_anime47(url):
# 	if not 'anime47.com/' in url:
# 		print 'get_link_anime47: URL ERROR!'
# 		return ''
# 	if not 'anime47.com/xem-phim' in url:
# 		source = requests.get(url).content
# 		match = re.search('a class="play_info" href="(.*?)"> XEM ANIME', source)
# 		if not match:
# 			print 'get_link_anime47: Get info ERROR'
# 			return ''
# 		url =  match.group(1)

# 	source = requests.get(url).content
# 	if not '<div id="servers" class="serverlist">' in source:
# 		print 'get_link_anime47: No list exists!'
# 		return ''

# 	match = re.search('<div id="servers" class="serverlist">(.*?)<\/div',source)
# 	servers = match.group(1).split('span class="server')

# 	ret = []
# 	for x in xrange(1,len(servers)):
# 		match = re.findall('data-episode-tap="(.*?)".*?href="(.*?)">', servers[x])
# 		for pair in match:
# 			ret.append({pair[0] : pair[1]})


# 	return ret

############################################################################################################


# def get_link_phimmoi(url, quality='all'):
# 	#valid url
# 	if not re.search('phimmoi\.net/phim/(.+)-\d+(/.*?$)', url):
# 		return set_error(__errorCode['url'] + url)

# 	session = requests.session()
# 	source = session.get(url).content
# 	match = re.search('episodeinfo-v1\.1\.php.*?episodeid=(.*?)\&number=(.*?)\&.*?\&filmslug=phim/(.+)-\d+/.*?"', source)
# 	if not match:
# 		set_error(__errorCode['source'] + url)

# 	ep = match.group(2)
# 	ep = '0' * (3 - len(ep)) + ep
# 	title = match.group(3).replace('-', '_') + '_ep' + ep
# 	aesKey = 'PhimMoi.Net://' + match.group(1)

# 	urlStream = 'http://www.phimmoi.net/' + match.group(0)
# 	response = session.get(urlStream).content

# 	match = re.search('"medias":(\[.*?\])', response)
# 	if not match:
# 		set_error(__errorCode['response'] + url + '\r\n' + response)

# 	medias = json.loads(match.group(1))
# 	ret = {}
# 	for info in medias:
# 		filmInfo = FileInfo(url = info['url'], title = title, \
# 							quality = info['resolution'], ext = info['type'])
# 		if not re.search('http:(.*?)\.(.*?)\.(.*?)', filmInfo.url):
# 			filmInfo.url = decrypt_aes_cbc(filmInfo.url, aesKey)

# 		ret[filmInfo.quality] = filmInfo
# 	return set_error(None, get_value_by_quality(ret, quality)) 

# #return [ {Ep : URL}]
# def get_list_phimmoi(url):  
# 	if not re.search('phimmoi\.net/phim/(.+)-\d+(/.*?$)', url):
# 		return set_error(__errorCode['url'] + url)

# 	if url[-1] == '/':
# 		url += 'xem-phim.html'
# 	source = requests.get(url).content
# 	match = re.findall('<li class="episode"><a(.*)>', source)
# 	if not match:
# 		return set_error(__errorCode['source'] + url)

# 	isPhimBo = '<ul class="server-list">' in source
# 	ret = []

# 	for anchor in match:
# 		key = re.search('backuporder="(.*?)"', anchor).group(1) if isPhimBo \
# 			else re.search('number="(.*?)"', anchor).group(1)
# 		ret.append({key : 'http://www.phimmoi.net/' + re.search('href="(.*?)"', anchor).group(1) })

# 	return set_error(None, ret)

############################################################################################################

#quality = 0|lossless => lossless
def get_link_mp3zing(url, quality=''):
	#get ID
	match = re.findall('mp3\.zing\.vn/(.*?)/(.*?)/(.*?)\.html', url)
	if (not match) or ((match[0][0] != 'bai-hat') and (match[0][0] != 'video-clip')):
		return set_error(__errorCode['url'] + url )

	if (match[0][0] == 'bai-hat'):
		songType = 'song'
	elif (match[0][0] == 'video-clip'):
		songType = 'video'

	title = match[0][1]
	songId = match[0][2]
	response = requests.get('http://api.mp3.zing.vn/api/mobile/' + songType
			+ '/get' + songType + 'info?requestdata={"id":"' + songId + '"}').content

	response = json.loads(response)
	if (not title):
		return set_error(__errorCode['response'] + url)

	link_download = response['link_download'] if (songType == 'song') else response['source']
	fileExt = 'mp3' if (songType == 'song') else 'mp4'
	ret = {}
	for keyQuality in link_download:
		if link_download[keyQuality]:
			ret[keyQuality] = FileInfo( url=link_download[keyQuality], quality=keyQuality, \
										title=title, ext=fileExt)

	return set_error(None, get_value_by_quality(ret, quality))


def get_list_mp3zing(url):
	if not re.search('mp3\.zing\.vn/(playlist)|(album)/.*?\.html', url):
		return set_error(__errorCode['url'] + url)

	source = requests.get(url).content
	match = re.findall('<a class="fn-name" data-order="(.*?)" href="(.*?)"', source)
	if not match:
		return _support.show_error('get_list_mp3zing: no list found!')

	return [ {match[x][0]: match[x][1]} for x in range(0, len(match)) ]

############################################################################################################

def get_link_tvzing(url, quality=''):
	#get ID
	match = re.findall('tv\.zing\.vn/(.*?)/(.*?)/(.*?)\.html', url)
	if (not match) or (match[0][0] != 'video'):
		return set_error(__errorCode['url'] + url)

	title = match[0][1]
	videoId = match[0][2]
	source = requests.get('http://api.tv.zing.vn/2.0/media/info?' \
		+ 'api_key=d04210a70026ad9323076716781c223f&media_id=' + videoId).content

	response = json.loads(source)
	if ('"message": "Invalid' in source):
		return set_error(__errorCode['response'] + response['message'])

	response = response['response']
	if (not response):
		return set_error(__errorCode['response'] + url)
	ret = {}
	try:
		baseObj = FileInfo(title=title, ext='mp4')
		ret[360] = baseObj.newObj(newUrl=response['file_url'], newQuality=360) #default quality

		other_url = response['other_url']
		for qlt in (480, 720, 1080):
			ret[qlt] = baseObj.newObj(newUrl=other_url['Video' + str(qlt)], newQuality=qlt)

	except Exception as e:
		pass

	return set_error(None, get_value_by_quality(ret, quality))

#get links in series
# return [{Ep : URL}]
def get_list_tvzing(url):
	match = re.findall('(tv\.zing\.vn/)(series/)?([\w-]+)', url)
	if not match:
		return set_error(__errorCode['url'] + url)

	url = 'http://' + match[0][0] + 'series/' + match[0][2] + '?p=' #?p= page
	ret = [] 
	for page in xrange(1, 20):
		source = requests.get(url + str(page)).content
		if ('Nội dung trang bạn yêu cầu đã bị khóa hoặc bị xóa khỏi hệ thống' in source):
			break
		match = re.findall('<a class="thumb" itemprop="url" href="(/video/.*?-Tap-(\d+).*?)(/.*?)"', source)
		if not match:
			break
		for href in match:
			ret.append( {href[1]:'http://tv.zing.vn' +href[0] + href[2]} )

	return ret


############################################################################################################

def get_link_woim(url, quality=''):
	match = re.search('www.woim.net/song/\w+/(.*?).html', url)
	if not match:
		return set_error(__errorCode['url'] + url)
	title = match.group(1)
	source = requests.get(url).content
	match = re.search('code=(.*?)"', source)
	if not match:
		return set_error(__errorCode['source'] + url)
	
	response = requests.get(match.group(1)).content
	match = re.search('location="(.*?)"', response)

	if not match:
		return set_error(__errorCode['response'] + url)
	return FileInfo(url=match.group(1), quality=128, title=title, ext='mp3')

def get_list_woim(url):
	if not re.search('www.woim.net/album/.*?html', url):
		return set_error(__errorCode['url'] + url)

	source = requests.get(url).content

	match = re.findall('div itemprop="track".*?href="(.*?)"', source)
	if not match:
		return set_error(__errorCode['source'] + url)

	return [{x: match[x]} for x in range(0, len(match))]



def get_link_dailymotion(url, quality=''):
	match =  re.search('dailymotion.com/video/(.*?)(_.+)?', url)
	if not match:
		return set_error(__errorCode['url'] + url)
	videoId = match.group(1)
	response = requests.get('http://www.dailymotion.com/embed/video/' + videoId).content

	match = re.search('"title":"(.*?)"', response)
	if (not match):
		return set_error(__errorCode['response'] + url)
	else:
		title = match.group(1)
	ret = {}
	try:
		data = json.loads(re.search('"qualities":(\{.*?\}\]\})').group(1))
		baseObj = FileInfo(title=title, ext='mp4')
		for key in data:
			keyQuality = int(key)
			qUrl = data[key][1]['url']
			ret[keyQuality] = baseObj.newObj(newUrl=qUrl, quality=keyQuality)
	except Exception as e:
		pass

	return set_error(None, get_value_by_quality(ret, quality))


def get_list_dailymotion(url):
	match = re.search('dailymotion.com/((playlist/\w+)|(channel/\w+)|(\w+))', url)
	if not match:
		return set_error(__errorCode['url'] + url)
	apiUrl = 'https://api.' + match.group(0) + '/videos?limit=100&page=' # + page
	if not (('/playlist/' in url) or ('/channel/' in apiUrl)):
		apiUrl = apiUrl.replace('dailymotion.com/','dailymotion.com/user/')
		

	ret = []
	for page in xrange(1,100):
		response = requests.get(apiUrl + str(page)).content
		response = json.loads(response)
		if 'error' in response:
			break
		for video in response['list']:
			ret.append( {len(ret) + 1 : 'http://www.dailymotion.com/video/' + video['id']})
		if not response['has_more']:
			break

	return ret


def  get_link_soundcloud(url, quality='only 128kbps'):
	match = re.search('https://soundcloud.com/.*?/(.*?)')
	if (not match):
		return set_error(__errorCode['url'] + url)
	retObj = FileInfo(url=None, quality=128, title=match.group(1), ext='mp3')

	try:
		# =============== solution #1 ===============
		response = requests.get('http://keepvid.com/?url=' + url).content
		match = re.search('href="(https://api.soundcloud.com/.*?)"', response)
		if match:
			return retObj.newObj(newUrl=match.group(1))

 	except Exception as e:
 		pass
	# =============== solution #2 ===============
	listClientIDs = ['fDoItMDbsbZz8dY16ZzARCZmzgHBPotA', 'f3d0bb2d98c2cc1b42cdaff035033de0']
	resolveUrl = 'https://api.soundcloud.com/resolve?url={TRACK_URL}' \
					+ '&_status_code_map%5B302%5D=200&_status_format=json&client_id={CLIENT_ID}'

	for clientID in listClientIDs:
	  apiUrl = resolveUrl.replace('{TRACK_URL}', url).replace('{CLIENT_ID}', clientID)
	  responseApi = requests.get(apiUrl).content
	  if '"location":' in responseApi:
		   responseTrack = requests.get(json.loads(responseApi)['location']).content
		   return retObj.newObj(newUrl=(json.loads(responseTrack)['stream_url'] + '?client_id=' + clientID))

	return set_error(__errorCode['response'] + url)

def get_list_soundcloud(url):
	if not ('soundcloud.com/' in url):
		return set_error(__errorCode['url'] + url)

	response = requests.get(url).content
	match = re.findall('a itemprop="url" href="(.*?)"', response)
	if not match:
		return set_error(__errorCode['source'] + url)

	# ret = []
	# for x in xrange(1,len(match)):
	# 	urlTrack = 'https://soundcloud.com' + match[x]
	# 	ret.append( {x : urlTrack})

	return [ {x : 'https://soundcloud.com' + match[x]} for x in range(1, len(match)) ]


# quality is not avalable :v
def get_link_tumblr(url, quality='unidentify quality'):
	if (not 'tumblr.com/' in url):
		return set_error(__errorCode['url'] + url)

	source = requests.get(url).content
	match = re.search("iframe src='(.*?)'", source)	 #NOTE: src='...' 
	if not match:
		return set_error(__errorCode['source'] + url)

	source = requests.get(match.group(1)).content
	match = re.search('source src="(.*?)"', source)
	if not match:
		return set_error(__errorCode['response'] + url)

	return FileInfo(url=match.group(1), ext='mp4')

def login_chiasenhac():
	loginUrl = 'http://chiasenhac.vn/login.php'
	if ('chiasenhac' in __cookies):
		if ('logout=true' in requests.get(loginUrl, cookies=__cookies['chiasenhac']).content):
			return True

	for i in xrange(1,9):
		data = {'username'	: 'huan' + str(i) + 'hoang' + str(i+1),
				'password'	: '123456',
				'redirect'	: '',
				'login'		: 'Đăng nhập'
				}
		response = requests.post(loginUrl, data=data)
		if ('logout=true' in response.content):
			__cookies['chiasenhac'] = response.cookies
			return True

	return False

def get_link_chiasenhac(url, quality='mp3/mp4'):
	match = re.search('(.*?~.*?)~.*?$', url.split('/')[-1])
	if (not match):
		return set_error(__errorCode['url'] + url)

	title = match.group(1)
	if (not '_download.html' in url):
		url = url.replace('.html', '_download.html')

	source = requests.get(url).content
	match = re.search('href="(http://data.*?/(.*?\[.*?\]\.(.*?)))"', source)
	if (not match):
		return set_error(__errorCode['source'] + url)
	baseStreamUrl = match.group(1)
	tagQuality = '/' + match.group(2).split('/')[-2] + '/' 	
	baseFileName = match.group(2).split('/')[-1]
	fileType = 'video' if (match.group(3) == 'mp4') else 'audio'

	data = {
		'Link Download 1':{'tag':'/128/','video':{'quality':360,'ext':'mp4'},'audio':{'quality':128,'ext':'mp3'}},
		'Link Download 3':{'tag':'/320/','video':{'quality':480,'ext':'mp4'},'audio':{'quality':320,'ext':'mp3'}},
		'Link Download 5':{'tag':'/m4a/','video':{'quality':720,'ext':'mp4'},'audio':{'quality':500,'ext':'m4a'}},
		'Link Download 6':{'tag':'/flac/','video':{'quality':1080,'ext':'mp4'},'audio':{'quality':'lossless','ext':'flac'}},
		'Mobile Download':{'tag':'/32/','video':{'quality':180,'ext':'mp4'},'audio':{'quality':128,'ext':'m4a'}},
	}

	ret = {}
	for link in data:
		if (link in source):
			tagSong = data[link]['tag']
			linkData = data[link][fileType]
			baseObj = FileInfo(title=title, quality=linkData['quality'], ext=linkData['ext'])
			baseObj.url = baseStreamUrl.replace(tagQuality, tagSong).replace(baseFileName, baseObj.fileFullName)
			ret[baseObj.quality] = baseObj

	return set_error(None, get_value_by_quality(ret, quality))

def get_list_chiasenhac(url):
	if (not 'chiasenhac.vn/' in url):
		return set_error(__errorCode['url'] + url)

	source = requests.get(url).content
	match = re.findall('a href="(.*?)"\s+title="Download', source)
	if (not match):
		return set_error(__errorCode['source'] + url)

	return [{x: match[x]} for x in range(0, len(match))]


 
def get_link_nhaccuatui(url, quality='only 128'):
	if (not 'nhaccuatui.com/' in url):
		return set_error(__errorCode['url'] + url)

	source = requests.get(url).content
	match = re.search('player.peConfig.xmlURL = "(.*?)"', source)
	if (not match):
		return set_error(__errorCode['source'] + url)

	response = requests.get(match.group(1)).content

	matchQuality = re.search('download="(\d+)"', source)
	matchInfo = re.search('<info>\s*<\!\[CDATA\[(.*?)\]', response)
	matchUrl = re.search('<location>\s*<\!\[CDATA\[(.*?)\]', response)
	# matchUrl320 = re.search('<locationHQ>\s+<\!\[CDATA\[(.*?)\]', response)
	if (not matchInfo) or (not matchUrl):
		return set_error(__errorCode['response'] + url)
	title = re.search('nhaccuatui.com/.+/(.*?)\..+\.html', matchInfo.group(1)).group(1)
	urlDl = matchUrl.group(1)
	qualityDl = int(matchQuality.group(1))
	baseObj = FileInfo(url=urlDl, quality=qualityDl, title=title, ext=urlDl.split('.')[-1])
	if (isinstance(quality, int)):
		return baseObj
	else:
		return {baseObj.quality : baseObj}

def get_list_nhaccuatui(url):
	if (not 'nhaccuatui.com/' in url):
		return set_error(__errorCode['url'] + url)

	source = requests.get(url).content
	match = re.findall('downloadPlaylist.*?"(.*?\.html)')
	if (not match):
		return set_error(__errorCode['source'] + url)

	return [{x: match[x]} for x in range(0, len(match))]


def get_link_playgoogle(url, quality='apk thi quality de lam gi :v'):
	match = re.search('play.google.com.*?details\?id=(.*?)$', url)
	if (not match):
		return set_error(__errorCode['url'] + url)

	source = requests.get('http://apkleecher.com/download/?dl=' + match.group(1)).content

	matchUrl = re.search('location.href="(.*?)"', source)
	matchTitle = re.search('<title>Downloading (.*?)<\/title>', source)
	if (not matchUrl) or (not matchTitle):
		return set_error(__errorCode['source'] + url)

	return FileInfo(url=('http://apkleecher.com/'+matchUrl.group(1)), title=matchTitle.group(1), ext='apk')


















def decrypt_aes_cbc(string, passwd):
	#declaire
	keySize = 256
	keyLen = int(keySize / 8)
	blockLen = 16
	#get str, key, iv for aes
	data = base64.b64decode(string)
	salt = data[8:16]
	encypted = data[16:]

	rounds = 3
	if 128 == keySize:
		rounds = 2
	tmpHash = str(passwd) + str(salt)
	md5_hash = [''] * rounds

	for i in xrange(0,len(md5_hash)):
		md5_hash[i] = md5.new(md5_hash[i-1] + tmpHash).digest()
		# print ''.join(md5_hash)

	hashResult = ''.join(md5_hash)
	key = hashResult[0: keyLen]
	iv = hashResult[keyLen: keyLen + blockLen]
	try:
		return AES.new(key, AES.MODE_CBC, iv).decrypt(encypted)
	except:
		return string
		
#remove '\' out of URL
def url_remove_chars(url, chars=''):
	for c in chars:
		url = url.replace(c, '')
	return url



def get_value_by_quality(urls, quality='all'):
	if urls and (not isinstance(urls, dict)):
		return urls

	if quality in urls:
		return urls[quality]
		
	if isinstance(quality, int):
		keys = urls.keys()
		keys.sort()

		if quality <= 0:
			return urls[keys[-1]] #max quality
		for keyQuality in reversed(p):
			if (keyQuality < quality):
				return urls[keyQuality]		#max quality that less than argv quality
		return urls[keys[0]]	#min quality

	return urls
	



















	




class Phimmoi(object):
	"""docstring for Phimmoi"""
	__maxThread = 50
	
	def __init__(self, url):
		match = re.search('phimmoi\.net/phim/(.+)-\d+(/.*?$)', url)
		if not match:
			print 'get_link_phimmoi: URL wrong!'
			return

		self.name = match.group(1).replace('-', '_')

		self.__url = url
		self.__listsFilms = []
		self.__result = []
		self.__cookies = {}
		self.__countThread = 0

	#error : return ''
	#mode2: return LinkHighestResolution
	#mode = 360/480/720/1080 return Link_Mode_Resolution (Mode <= mode)
	def get_link(self, id, mode=''):
		if not self.__listsFilms:
			if not self.getlist_films():
				return ''

		if isinstance(id, int):
			if 0 <= id < len(self.__listsFilms):
				url = self.__listsFilms[id]
			else:
				print 'get_link_phimmoi: index out of range (', id , ')'
				return ''
		elif 'phimmoi.net/phim/' in id:
			url = id 
		else:
			print 'get_link_phimmoi: URL wrong!'
			return ''
	

		cookies = self.__cookies
		subSrc = requests.get(url, cookies=cookies).content
		matchInfo = re.findall("var get_linkToken='(.+)';\nvar fileId='(.+)';\nvar fileName='(.+)';", subSrc)
		
		if not matchInfo:
			print 'get_link_phimmoi: This url has been expired, Invalid or private!'
			return ''

		time.sleep(5)
		data = {'fileId': matchInfo[0][1], 'fileName': matchInfo[0][2], 'get_linkToken': matchInfo[0][0] }
		response = requests.post('http://www.phimmoi.net/download.php', data=data, cookies=cookies).content
		
		#check status
		if not '"videoStatus":"ok"' in response:
			print 'get_link_phimmoi: Something Wrong!\r\nFileName:', matchInfo[0][2], \
					'\r\nURL:', url, '\r\nResponse:', response, '\r\n'
			return ''

		links = ast.literal_eval(response.replace('\\', ''))['links']

		if mode == 'highest':
			ret = links[-1]['url']
		elif isinstance(mode, int) and mode >= 360:
			for link in reversed(links):
				if link['resolution'] <= mode:
					ret = link['url']
					break
		else:
			#else, return array
			ret = [''] * 7
			match = re.search('PhimMoi.Net---Tap\.(.*?)-',response)
			if match:
				ret[0] = match.group(1) 
			ret[1] = 'Vietsub' if '-Vietsub-' in response else 'ThuyetMinh'

			for link in links:
				resolution = link['resolution']
				url = link['url']

				index = 2
				if resolution >= 1080:
					index = 5
				elif resolution >= 720:
					index = 4
				elif resolution >= 480:
					index = 3	   

				ret[index] = url
				#highest resolution
				ret[6] = url
		threadName = threading.currentThread().name
		#getall_links: multithread
		# if threadName != 'MainThread':	
		#   try:		
		#	   index = int(threadName)
		#   except:
		#	   pass
		#   else:
		#	   if 0 <= index < len(self.__result):
		#		   self.__result[index] = ret

		return ret

	#mode: see get_link
	def getall_links(self, mode='arrar'):
		if not self.__listsFilms:
			if not self.getlist_films():
				return ''

		episodes = self.__listsFilms if self.__listsFilms else self.getlist_films()
		if not episodes:
			return ''

		self.__result = [''] * ( len(episodes) + 1 )
		if not mode == 'highest' and not isinstance(mode, int):
			self.__result[0] = [''] * 7
			# self.__result[0][0] = 'Server' if '<th>Server<' in source else 'Episode'
			self.__result[0][0] = 'Episode'
			self.__result[0][1] = 'Language'
			self.__result[0][2] = '360'
			self.__result[0][3] = '480'
			self.__result[0][4] = '720'
			self.__result[0][5] = '1080'		
		
		for x in xrange(0,len(episodes)):
			#check max thread
			while threading.activeCount() >= self.__maxThread:
				time.sleep(0.1)

			threading.Thread(target=self.get_link, name=x+1, args=(episodes[x],mode,)).start()

		return self.__result
	#return and set self.__listsFilms = list all film in page download  
	def getlist_films(self):
		session = requests.session()

		match = re.search('phimmoi\.net/phim/(.+)(/.*?$)', self.__url)
		if not match:
			print 'get_link_phimmoi: URL wrong!'
			return ''
		urlDownloadList = 'http://www.phimmoi.net/phim/' + match.group(1) + '/download.html'
		source = session.get(urlDownloadList).content
		session.headers.update({'referer': urlDownloadList})

		#get token
		match = re.search("fx.token='(.*?)'",source)
		if not match:
			print 'get_link_phimmoi: URL ERROR!'
			return ''
		token = match.group(1)

		#get capchar
		match = re.search('verify-image.php\?verifyId=download&d=(.*?)"',source)
		if not match:
			print 'get_link_phimmoi: URL Capchar ERROR!'
			return ''
		capcharURL = 'http://www.phimmoi.net/' + match.group(0)
		
		capcharPath = 'capchar.jpeg'
		while 1:
			capcharPath = _support.download_file(capcharURL, capcharPath, session)
			if not capcharPath:
				print 'get_link_phimmoi: Download image capchar ERROR'
				return ''

			#show capchar
			_support.show_image(capcharPath)
			capchar = raw_input('Enter capchar: ')  

			#close image show window
			_support.kill_process('display')
			
			#get list
			urlDownloadList += '?_fxAjax=1&_fxResponseType=JSON&_fxToken=' + token

			data = {'download[verify]=':str(capchar)}
			source = session.post(urlDownloadList, data=data).content
			episodes = re.findall('href=."(.*?)" rel=', source)
			if not episodes:
				print 'get_link_phimmoi: Capchar Wrong!'
			else:
				for x in xrange(0,len(episodes)):
					episodes[x] = 'http://www.phimmoi.net/' + episodes[x].replace('\\', '')

				_support.remove(capcharPath)
			
				self.__cookies = session.cookies
				self.__listsFilms = episodes
				return episodes



if __name__ == '__main__':
	main()