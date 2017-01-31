# -*- coding: utf-8 -*-
import re		   #regex
import requests	 #requests.Session - cookie - get - post
import time		 #sleep
import json

from models import FileInfo

from multiprocessing import Pool


__maxThread = 30			#for multithread
__cookies = {}



'''
url : url not correct to get infomation
source : requests.get(url).content has not infomation to get link, it may be host change algorithms, url wrong
response : after get enough infomation from source, and need requests one more time, most of response is json stringtify
'''
ERROR_CODE = {
	'login'		: "Wrong username or password!",
	'url' 		: "Invalid/Unsupported URL!",					
	'source' 	: "Cannot find required infomation!",
	'response'	: "Unexpected response!",
	'not found'	: "Cannot find file(s)!"
}


#Set error and return
def to_json(status='', message=''):
	return {'status' : status, 'message' : message}

#multithread get_links
def multi_run_get_links(args={}):
	if isinstance(args, dict) and ('funcGetLink' in args) and ('url' in args) and ('quality' in args):
		funcGetLink = args['funcGetLink']
		if (not funcGetLink in globals()):
			return ''
		methodGetLink = eval(funcGetLink)
		return methodGetLink(args['url'], args['quality'])

#validate url is supported 
#returnFunction: return callable function
def check_url(url, isList=False, returnFunction=False):
	if not re.search('^http(s)?://', url):
		url = 'http://' + url

	#sample: http(s)://(www.)(youtube).com/...
	###Exception tumblr
	match = re.search('://(www\.)?(.+)\..*?/', url)
	if not match: 	#Invalid
		return False

	match = re.findall('(\w)', match.group(2))
	funcName = ('get_list_' if isList else 'get_link_') + ''.join(match)

	if (not funcName in globals()):
		return False
	elif returnFunction:
		return eval(funcName)
	else:
		return True

############################################################################################################
def get_list(url):
	if not re.search('^http(s)?://', url):
		url = 'http://' + url

	funcGetList = check_url(url, isList=True, returnFunction=True)
	if not funcGetList:
		return to_json('error',ERROR_CODE['url'])
	return funcGetList(url)

# auto detect host
def get_link(url, quality='default', password=''):
	if not re.search('^http(s)?://', url):
		url = 'http://' + url

	funcGetLink = check_url(url, returnFunction=True)
	if not funcGetLink:
		return to_json('error',ERROR_CODE['url'])

	option = {'quality' : quality, 'password' : password}
	return funcGetLink(url, option)

############################################################################################################

#quality = 0|lossless => lossless
def get_link_mp3zing(url, option={}):
	#get ID
	match = re.findall('mp3\.zing\.vn/(.*?)/(.*?)/(.*?)\.html', url)
	if (not match) or ((match[0][0] != 'bai-hat') and (match[0][0] != 'video-clip')):
		return to_json(ERROR_CODE['url'] + url )

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
		return to_json('error',ERROR_CODE['response'])

	link_download = response['link_download'] if (songType == 'song') else response['source']
	fileExt = 'mp3' if (songType == 'song') else 'mp4'
	ret = {}
	for keyQuality in link_download:
		if link_download[keyQuality]:
			ret[keyQuality] = FileInfo( url=link_download[keyQuality], quality=keyQuality, 
										title=title, ext=fileExt)

	return to_json('success', get_value_by_quality(ret, option['quality']))


def get_list_mp3zing(url):
	if not re.search('mp3\.zing\.vn/(playlist)|(album)/.*?\.html', url):
		return to_json(ERROR_CODE['url'] + url)

	source = requests.get(url).content
	match = re.findall('<a class="fn-name" data-order=".*?" href="(.*?)"', source)
	if not match:
		return _support.show_error('get_list_mp3zing: no list found!')
	return match
	return [ match[x][0]for x in range(0, len(match)) ]

############################################################################################################

def get_link_tvzing(url, option={}):
	#get ID
	match = re.findall('tv\.zing\.vn/(.*?)/(.*?)/(.*?)\.html', url)
	if (not match) or (match[0][0] != 'video'):
		return to_json(ERROR_CODE['url'] + url)

	title = match[0][1]
	videoId = match[0][2]
	source = requests.get('http://api.tv.zing.vn/2.0/media/info?' \
		+ 'api_key=d04210a70026ad9323076716781c223f&media_id=' + videoId).content

	response = json.loads(source)
	if ('"message": "Invalid' in source):
		return to_json(ERROR_CODE['response'] + response['message'])

	response = response['response']
	if (not response):
		return to_json(ERROR_CODE['response'] + url)
	ret = {}
	try:
		baseObj = FileInfo(title=title, ext='mp4')
		ret[360] = baseObj.newObj(newUrl=response['file_url'], newQuality=360) #default quality

		other_url = response['other_url']
		for qlt in (480, 720, 1080):
			ret[qlt] = baseObj.newObj(newUrl=other_url['Video' + str(qlt)], newQuality=qlt)

	except Exception as e:
		pass

	return to_json('success', get_value_by_quality(ret, option['quality']))

#get links in series
# return [{Ep : URL}]
def get_list_tvzing(url):
	match = re.findall('(tv\.zing\.vn/)(series/)?([\w-]+)', url)
	if not match:
		return to_json(ERROR_CODE['url'] + url)

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

def get_link_woim(url, option={}):
	match = re.search('www.woim.net/song/\w+/(.*?).html', url)
	if not match:
		return to_json(ERROR_CODE['url'] + url)
	title = match.group(1)
	source = requests.get(url).content
	match = re.search('code=(.*?)"', source)
	if not match:
		return to_json(ERROR_CODE['source'] + url)
	
	response = requests.get(match.group(1)).content
	match = re.search('location="(.*?)"', response)

	if not match:
		return to_json(ERROR_CODE['response'] + url)
	return FileInfo(url=match.group(1), quality=128, title=title, ext='mp3')

def get_list_woim(url):
	if not re.search('www.woim.net/album/.*?html', url):
		return to_json(ERROR_CODE['url'] + url)

	source = requests.get(url).content

	match = re.findall('div itemprop="track".*?href="(.*?)"', source)
	if not match:
		return to_json(ERROR_CODE['source'] + url)

	return [{x: match[x]} for x in range(0, len(match))]



def get_link_dailymotion(url, option={}):
	match =  re.search('dailymotion.com/video/(.*?)(_.+)?', url)
	if not match:
		return to_json(ERROR_CODE['url'] + url)
	videoId = match.group(1)
	response = requests.get('http://www.dailymotion.com/embed/video/' + videoId).content

	match = re.search('"title":"(.*?)"', response)
	if (not match):
		return to_json(ERROR_CODE['response'] + url)
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

	return to_json('success', get_value_by_quality(ret, option['quality']))


def get_list_dailymotion(url):
	match = re.search('dailymotion.com/((playlist/\w+)|(channel/\w+)|(\w+))', url)
	if not match:
		return to_json(ERROR_CODE['url'] + url)
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

#quality only 128kbps
def  get_link_soundcloud(url, option={}):
	match = re.search('https://soundcloud.com/.*?/(.*?)')
	if (not match):
		return to_json(ERROR_CODE['url'] + url)
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

	return to_json(ERROR_CODE['response'] + url)

def get_list_soundcloud(url):
	if not ('soundcloud.com/' in url):
		return to_json(ERROR_CODE['url'] + url)

	response = requests.get(url).content
	match = re.findall('a itemprop="url" href="(.*?)"', response)
	if not match:
		return to_json(ERROR_CODE['source'] + url)

	# ret = []
	# for x in xrange(1,len(match)):
	# 	urlTrack = 'https://soundcloud.com' + match[x]
	# 	ret.append( {x : urlTrack})

	return [ {x : 'https://soundcloud.com' + match[x]} for x in range(1, len(match)) ]


# quality is not avalable :v
def get_link_tumblr(url, option={}):
	if (not 'tumblr.com/' in url):
		return to_json(ERROR_CODE['url'] + url)

	source = requests.get(url).content
	match = re.search("iframe src='(.*?)'", source)	 #NOTE: src='...' 
	if not match:
		return to_json(ERROR_CODE['source'] + url)

	source = requests.get(match.group(1)).content
	match = re.search('source src="(.*?)"', source)
	if not match:
		return to_json(ERROR_CODE['response'] + url)

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
# ext = 'mp3/mp4'
def get_link_chiasenhac(url, option={}):
	match = re.search('(.*?~.*?)~.*?$', url.split('/')[-1])
	if (not match):
		return to_json(ERROR_CODE['url'] + url)

	title = match.group(1)
	if (not '_download.html' in url):
		url = url.replace('.html', '_download.html')

	source = requests.get(url).content
	match = re.search('href="(http://data.*?/(.*?\[.*?\]\.(.*?)))"', source)
	if (not match):
		return to_json(ERROR_CODE['source'] + url)
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

	return to_json('success', get_value_by_quality(ret, option['quality']))

def get_list_chiasenhac(url):
	if (not 'chiasenhac.vn/' in url):
		return to_json(ERROR_CODE['url'] + url)

	source = requests.get(url).content
	match = re.findall('a href="(.*?)"\s+title="Download', source)
	if (not match):
		return to_json(ERROR_CODE['source'] + url)

	return [{x: match[x]} for x in range(0, len(match))]


 # quality='only 128'
def get_link_nhaccuatui(url, option={}):
	if (not 'nhaccuatui.com/' in url):
		return to_json(ERROR_CODE['url'] + url)

	source = requests.get(url).content
	match = re.search('player.peConfig.xmlURL = "(.*?)"', source)
	if (not match):
		return to_json(ERROR_CODE['source'] + url)

	response = requests.get(match.group(1)).content

	matchQuality = re.search('download="(\d+)"', source)
	matchInfo = re.search('<info>\s*<\!\[CDATA\[(.*?)\]', response)
	matchUrl = re.search('<location>\s*<\!\[CDATA\[(.*?)\]', response)
	# matchUrl320 = re.search('<locationHQ>\s+<\!\[CDATA\[(.*?)\]', response)
	if (not matchInfo) or (not matchUrl):
		return to_json(ERROR_CODE['response'] + url)
	title = re.search('nhaccuatui.com/.+/(.*?)\..+\.html', matchInfo.group(1)).group(1)
	urlDl = matchUrl.group(1)
	qualityDl = int(matchQuality.group(1))

	return FileInfo(url=urlDl, quality=qualityDl, title=title, ext=urlDl.split('.')[-1])

def get_list_nhaccuatui(url):
	if (not 'nhaccuatui.com/' in url):
		return to_json(ERROR_CODE['url'] + url)

	source = requests.get(url).content
	match = re.findall('downloadPlaylist.*?"(.*?\.html)')
	if (not match):
		return to_json(ERROR_CODE['source'] + url)

	return [{x: match[x]} for x in range(0, len(match))]

# quality='apk thi quality de lam gi :v'
def get_link_playgoogle(url, option={}):
	match = re.search('play.google.com.*?details\?id=(.*?)$', url)
	if (not match):
		return to_json(ERROR_CODE['url'] + url)

	source = requests.get('http://apkleecher.com/download/?dl=' + match.group(1)).content

	matchUrl = re.search('location.href="(.*?)"', source)
	matchTitle = re.search('<title>Downloading (.*?)<\/title>', source)
	if (not matchUrl) or (not matchTitle):
		return to_json(ERROR_CODE['source'] + url)

	return FileInfo(url=('http://apkleecher.com/'+matchUrl.group(1)), title=matchTitle.group(1), ext='apk')

# quality='[pending] normal/max speed'
def get_link_fshare(url, option={}):
	if (not 'fshare.vn/' in url):
		return to_json(ERROR_CODE['url'] + url)
	pwd = option['password']

	source = requests.get(url)
	try:
		fs_csrf = re.search("fs_csrf:'(.*?)'", source.content).group(1)
		linkcode = re.search('linkcode="(.*?)"', source.content).group(1)
		data = {
			'fs_csrf' : fs_csrf,
			'DownloadForm[pwd]' : pwd,
			'DownloadForm[linkcode]' : linkcode,
			'ajax' : 'download-form',
			'undefined' : 'undefined',
		}
		response = requests.post('https://www.fshare.vn/download/get', data=data, cookies=source.cookies).content
		response = json.loads(response)
		if (not 'url' in response):
			return to_json(ERROR_CODE['response'] + url)
		return FileInfo(url=response['url'])

	except Exception as e:
		return to_json(ERROR_CODE['source'] + url)

# quality='Unknow'
def get_link_drivegoogle(url, option={}):
	match = re.search('d\W(\w{28})', url) #get ID file ( ?id=ID || /d/ID)
	if (not match):
		return to_json(ERROR_CODE['url'] + url)
	urlConfirm = 'http://docs.google.com/uc?export=download&id=' + match.group(1)
	session = requests.session()
	response = session.get(urlConfirm, stream=True)
	#get get confirm token
	for key, value in response.cookies.items():
		if key.startswith('download_warning'):
			urlStream = urlConfirm.replace('?export=download', '?export=download&confirm=' + value)
			response = session.get(urlStream, stream=True)
			# print response.content
			break

	return to_json('success', FileInfo(url=response.url))
#get file url in folder
# https://www.googleapis.com/drive/v2/files?q=%270B6UqbP7Q2QG7QWRhN2xzbzQwbFU%27+in+parents&key=
def get_list_drivegoogle(url):
	match = re.search('drive.google.com/.*?/folders/(\w+)', url) #get id folder
	if (not match):
		return to_json(ERROR_CODE['url'] + url)
	folderId = match.group(1)
	apiUrl = 'https://www.googleapis.com/drive/v2/files'
	params = {
		'orderBy' 	: 'title', #sort by name, A comma-separated list of sort keys. Valid keys are 'createdDate', 'folder', 'lastViewedByMeDate', 'modifiedByMeDate', 'modifiedDate', 'quotaBytesUsed', 'recency', 'sharedWithMeDate', 'starred', and 'title'. Each key sorts ascending by default, but may be reversed with the 'desc' modifier. Example usage: ?orderBy=folder,modifiedDate desc,title. Please note that there is a current limitation for users with approximately one million files in which the requested sort order is ignored.
		'key' 		: 'AIzaSyA5ksKoRxexg8faABQjpN9EBn7swh2gSe4',
		'maxResults': '1000', #max
		'pageToken'	: '',
		'q' 		: "'" + folderId + "' in parents",
	}
	countFile = 0
	ret = []
	while 1:
		response = json.loads( requests.get(apiUrl, params=params).content )
		if ('error' in response):
			return to_json(ERROR_CODE['response'] + '(response error: ' + response['error']['errors']['message']
							+ '), url: ' + url )

		if (not 'items' in response):
			return to_json(ERROR_CODE['response'] + url)

		for itemInfo in response['items']:
			countFile += 1
			ret.append(itemInfo['webContentLink'])
	
		if ('nextPageToken' in response):
			params['pageToken'] = response['nextPageToken']
		else:
			return ret









#remove '\' out of URL
def url_remove_chars(url, chars=''):
	for c in chars:
		url = url.replace(c, '')
	return url


#default return minimum
def get_value_by_quality(urls, quality='default'):
	if (not urls) and (not isinstance(urls, dict)):
		return urls

	if quality in urls:
		return urls[quality]

	keys = urls.keys()
	keys.sort()
	if quality in ('max', 'maximum', 'highest', -1):
		return urls[keys[-1]] #max quality
	elif quality in ('min', 'minimum', 'lowest'):
		return urls[keys[0]] #min quality

	#try: '128kpbs' => 128
	try:
		quality = int( re.findall('\d+', quality)[0] )
		for keyQuality in reversed(keys):
			if (keyQuality <= quality):
				return urls[keyQuality]		#max quality that less than argv quality
	except Exception as e:
		pass
	return urls[keys[0]]	#min quality = default

	



















	




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




############################################################################################################

# def get_link_anime47(url, quality='all'):
# 	if not 'anime47.com/xem-phim' in url:
# 		return to_json(ERROR_CODE[1] + url)

# 	session = requests.session()
# 	source = session.get(url).content

# 	match = re.search('\{link:"https://drive.google.com/(.*?)"', source)
# 	if not match:
# 		return to_json(ERROR_CODE[2] + url)

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
# 		return to_json(ERROR_CODE['url'] + url)

# 	session = requests.session()
# 	source = session.get(url).content
# 	match = re.search('episodeinfo-v1\.1\.php.*?episodeid=(.*?)\&number=(.*?)\&.*?\&filmslug=phim/(.+)-\d+/.*?"', source)
# 	if not match:
# 		to_json(ERROR_CODE['source'] + url)

# 	ep = match.group(2)
# 	ep = '0' * (3 - len(ep)) + ep
# 	title = match.group(3).replace('-', '_') + '_ep' + ep
# 	aesKey = 'PhimMoi.Net://' + match.group(1)

# 	urlStream = 'http://www.phimmoi.net/' + match.group(0)
# 	response = session.get(urlStream).content

# 	match = re.search('"medias":(\[.*?\])', response)
# 	if not match:
# 		to_json(ERROR_CODE['response'] + url + '\r\n' + response)

# 	medias = json.loads(match.group(1))
# 	ret = {}
# 	for info in medias:
# 		filmInfo = FileInfo(url = info['url'], title = title, \
# 							quality = info['resolution'], ext = info['type'])
# 		if not re.search('http:(.*?)\.(.*?)\.(.*?)', filmInfo.url):
# 			filmInfo.url = decrypt_aes_cbc(filmInfo.url, aesKey)

# 		ret[filmInfo.quality] = filmInfo
# 	return to_json(None, get_value_by_quality(ret, quality)) 

# #return [ {Ep : URL}]
# def get_list_phimmoi(url):  
# 	if not re.search('phimmoi\.net/phim/(.+)-\d+(/.*?$)', url):
# 		return to_json(ERROR_CODE['url'] + url)

# 	if url[-1] == '/':
# 		url += 'xem-phim.html'
# 	source = requests.get(url).content
# 	match = re.findall('<li class="episode"><a(.*)>', source)
# 	if not match:
# 		return to_json(ERROR_CODE['source'] + url)

# 	isPhimBo = '<ul class="server-list">' in source
# 	ret = []

# 	for anchor in match:
# 		key = re.search('backuporder="(.*?)"', anchor).group(1) if isPhimBo \
# 			else re.search('number="(.*?)"', anchor).group(1)
# 		ret.append({key : 'http://www.phimmoi.net/' + re.search('href="(.*?)"', anchor).group(1) })

# 	return to_json(None, ret)