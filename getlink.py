# -*- coding: utf-8 -*-

import ast 			#convert response string to dict
import re 			#regex
import requests		#requests.Session - cookie - get - post
import time			#sleep

from multiprocessing import Pool

import _support		#my function


__maxThread = 30			#for multithread
# 376,379,388,391,400

def main():

	link1 = 'http://anime47.com/xem-phim-one-piece-dao-hai-tac-ep-001/76748.html'
	link2 = 'http://www.phimmoi.net/phim/dao-hai-tac-665/xem-phim.html'

	link3 = 'http://tv.zing.vn/series/One-Piece-Tap-1-200'
	link4 = 'http://tv.zing.vn/video/Dao-Hai-Tac-One-Piece-Tap-601/IWZA0BWO.html'

	link5 = 'http://mp3.zing.vn/playlist/333-h4212421/IOUUBD77.html?st=6'

	link11 = 'http://www.woim.net/song/39082/arunda.html'
	# for k in lists1:
	# 	print k
	# return
	x = 4
	url = get_links(link1, -1,751,770)
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
		return _support.show_error('URL wrong!!')

	match = re.findall('(\w)', match.group(2))
	funcGetLink = 'get_link_' + ''.join(match)
	funcGetList = 'get_list_' + ''.join(match)

	if (not funcGetLink in globals()):
		return _support.show_error('Unknow domain!')

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
			if Ep and int(Ep.group(1)) in xrange(startEp, endEp + 1):
				url = filmInfo[key]
				queueUrls.append({'funcGetLink':funcGetLink,'url':url, 'quality':quality})

		return Pool(__maxThread).map(multi_run_get_links, queueUrls)
	return eval(funcGetLink)(url, quality)

############################################################################################################

def get_link_anime47(url, quality='all'):
	if not 'anime47.com/xem-phim' in url:
		print 'get_link_anime47: URL ERROR!'
		return ''

	session = requests.session()
	source = session.get(url).content

	match = re.search('\{link:"https://drive.google.com/(.*?)"', source)
	if not match:
		print 'get_link_anime47: Get info ERROR'
		return ''

	data = {'link' : 'https://drive.google.com/' + match.group(1) }
	response = session.post('http://anime47.com/player/gkphp/plugins/gkpluginsphp.php', data=data).content
	if '"link":"https' in response:
		# print response
		title = re.search('anime47.com/xem-phim-(.*?)/', url).group(1).replace('-', '_')
		response = response.replace('\\','').replace('true','True').replace('false','False')
		links = ast.literal_eval(response)['link']

		opt = {'title':title, 'quality':quality}
		return _support.filter_url(links, keyQuality='label', keyUrl='link', option=opt) 

#return [ {Ep : URL}]
def get_list_anime47(url):
	if not 'anime47.com/' in url:
		print 'get_link_anime47: URL ERROR!'
		return ''
	if not 'anime47.com/xem-phim' in url:
		source = requests.get(url).content
		match = re.search('a class="play_info" href="(.*?)"> XEM ANIME', source)
		if not match:
			print 'get_link_anime47: Get info ERROR'
			return ''
		url =  match.group(1)

	source = requests.get(url).content
	if not '<div id="servers" class="serverlist">' in source:
		print 'get_link_anime47: No list exists!'
		return ''

	match = re.search('<div id="servers" class="serverlist">(.*?)<\/div',source)
	servers = match.group(1).split('span class="server')

	ret = []
	for x in xrange(1,len(servers)):
		match = re.findall('data-episode-tap="(.*?)".*?href="(.*?)">', servers[x])
		for pair in match:
			ret.append({pair[0] : pair[1]})


	return ret

############################################################################################################


def get_link_phimmoi(url, quality='all'):
	#valid url
	if not re.search('phimmoi\.net/phim/(.+)-\d+(/.*?$)', url):
		print 'get_link_phimmoi: URL wrong!'
		return ''

	session = requests.session()
	source = session.get(url).content
	match = re.search('episodeinfo-v1\.1\.php.*?episodeid=(.*?)\&number=(.*?)\&.*?\&filmslug=phim/(.+)-\d+/.*?"', source)
	if not match:
		print 'get_link_phimmoi: URL wrong!'
		return ''

	ep = match.group(2)
	ep = '0' * (3 - len(ep)) + ep
	title = match.group(3).replace('-', '_') + '_ep' + ep
	aesKey = 'PhimMoi.Net://' + match.group(1)

	urlStream = 'http://www.phimmoi.net/' + match.group(0)
	source = session.get(urlStream).content
	print source
	match = re.search('"medias":(\[.*?\])', source)
	if not match:
		print 'get_link_phimmoi: Get Data ERROR!'
		return ''

	links = ast.literal_eval(match.group(1))
	opt = {'title':title, 'quality' : quality, 'funcDecryptUrl':'decrypt_aes_cbc', 'keyDecryptUrl':aesKey}
	urls = _support.filter_url(links, keyQuality='resolution', keyUrl='url', option=opt)
	return urls 

#return [ {Ep : URL}]
def get_list_phimmoi(url):	
	if not re.search('phimmoi\.net/phim/(.+)-\d+(/.*?$)', url):
		print 'get_link_phimmoi: URL wrong!'
		return ''
	if url[-1] == '/':
		url += 'xem-phim.html'

	source = requests.get(url).content
	match = re.findall('<li class="episode"><a(.*)>', source)
	if not match:
		return _support.show_error('get_link_phimmoi: Cant get list films')

	isPhimBo = '<ul class="server-list">' in source
	ret = []

	for anchor in match:
		key = re.search('backuporder="(.*?)"', anchor).group(1) if isPhimBo \
			else re.search('number="(.*?)"', anchor).group(1)
		ret.append({key : 'http://www.phimmoi.net/' + re.search('href="(.*?)"', anchor).group(1) })

	return ret

############################################################################################################

#quality = 0|lossless => lossless
def get_link_mp3zing(url, quality=''):
	#get ID
	match = re.findall('mp3\.zing\.vn/(.*?)/(.*?)/(.*?)\.html', url)
	if (not match) or ((match[0][0] != 'bai-hat') and (match[0][0] != 'video-clip')):
		return _support.show_error('get_link_mp3zing: invalid URL!')

	if (match[0][0] == 'bai-hat'):
		songType = 'song'
	elif (match[0][0] == 'video-clip'):
		songType = 'video'

	songId = match[0][2]
	source = requests.get('http://api.mp3.zing.vn/api/mobile/' + songType
			+ '/get' + songType + 'info?requestdata={"id":"' + songId + '"}').content

	response = ast.literal_eval(source.replace('true','True').replace('false','False'))

	if (songType == 'song'):
		keyQuality = ['3GP','128','320','500','lossless']
		keyUrl = 'link_download'
	else:
	 	keyQuality = ['360','480','720','1080']
		keyUrl = 'source'

	opt = {'quality' : quality, 'funcDecryptUrl' : 'decrypt_slash_url'} 

	return _support.filter_url(response, keyQuality=keyQuality, keyUrl=keyUrl, option=opt)


def get_list_mp3zing(url):
	if not re.search('mp3\.zing\.vn/(playlist)|(album)/.*?\.html', url):
		return _support.show_error('get_list_mp3zing: invalid URL!')

	source = requests.get(url).content
	match = re.findall('<a class="fn-name" data-order="(.*?)" href="(.*?)"', source)
	if not match:
		return _support.show_error('get_list_mp3zing: no list found!')

	ret = []
	for item in match:
		ret.append( {item[0] : item[1]})
	return ret

############################################################################################################

def get_link_tvzing(url, quality=''):
	#get ID
	match = re.findall('tv\.zing\.vn/(.*?)/(.*?)/(.*?)\.html', url)
	if (not match) or (match[0][0] != 'video'):
		return _support.show_error('get_link_tvzing: invalid URL!')

	videoId = match[0][2]
	source = requests.get('http://api.tv.zing.vn/2.0/media/info?' \
		+ 'api_key=d04210a70026ad9323076716781c223f&media_id=' + videoId).content

	response = ast.literal_eval(source.replace('true','True').replace('false','False'))
	if ('"message": "Invalid' in source):
		return _support.show_error('get_link_tvzing: ' + response['message'])

	response = response['response']
	url360p = response['file_url']
	if (quality == 360):
		return url360p
 	keyQuality = ['Video3GP','Video480','Video720','Video1080']
	keyUrl = 'other_url'
	opt = {'quality' : quality} 

	ret = _support.filter_url(response, keyQuality=keyQuality, keyUrl=keyUrl, option=opt)
	if isinstance(ret, dict):
		ret[360] = url360p
		if (3 in ret):
			ret['3GP'] = ret.pop(3)

	return ret
#get links in series
# return [{Ep : URL}]
def get_list_tvzing(url):
	match = re.findall('(tv\.zing\.vn/)(series/)?([\w-]+)', url)
	if not match:
		return _support.show_error('get_list_tvzing: invalid URL!')

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
	if not re.search('www.woim.net/song/.*?html', url):
		return ''

	source = requests.get(url).content
	match = re.search('code=(.*?)"', source)
	if not match:
		return ''
	
	response = requests.get(match.group(1)).content
	match = re.search('location="(.*?)"', response)

	if not match:
		return ''
	return match.group(1)

def get_list_woim(url):
	if not re.search('www.woim.net/album/.*?html', url):
		return ''

	source = requests.get(url).content

	match = re.findall('div itemprop="track".*?href="(.*?)"', source)
	if not match:
		return ''
		
	ret = []
	for x in xrange(0, len(match)):
		ret.append( {x+1 : match[x]})
	return ret



def get_link_dailymotion(url, quality=''):
	match =  re.search('dailymotion.com/video/(.*?)_.+', url)
	if not match:
		return ''
	videoId = match.group(1)
	source = requests.get('http://www.dailymotion.com/embed/video/' + videoId).content

	keyQuality = [240, 480, 720, 1080]
	ret = {}
	for qualityStream in keyQuality:
		match = re.search(str(qualityStream)+'"\},\{"type":"video.*?url":"(.*?)"', source)
		if match:
			urlStream = match.group(1).replace('\\', '')
			ret[qualityStream] = urlStream

	if not ret:
		return ''

	if isinstance(quality, int):
		if quality <= 0:
			return ret[max(ret.keys())]
		elif quality in ret:
			return ret[quality]
		else:
			return ret[min(ret.keys())]

	return ret


def get_list_dailymotion(url):
	match = re.search('dailymotion.com/((playlist/\w+)|(channel/\w+)|(\w+))', url)
	if not match:
		return ''
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


def  get_link_soundcloud(url, quality=''):
	if not ('soundcloud.com/' in url):
		return ''

	# =============== solution #1 ===============
	response = requests.get('http://keepvid.com/?url=' + url).content
	match = re.search('href="(https://api.soundcloud.com/.*?)"', response)
	if not match:
		return ''

	return match.group(1)
 
	# =============== solution #2 ===============
	# listClientIDs = ['fDoItMDbsbZz8dY16ZzARCZmzgHBPotA', 'f3d0bb2d98c2cc1b42cdaff035033de0']
	# resolveUrl = 'https://api.soundcloud.com/resolve?url={TRACK_URL}&_status_code_map%5B302%5D=200&_status_format=json&client_id={CLIENT_ID}'

	# for clientID in listClientIDs:
	# 	apiUrl = resolveUrl.replace('{TRACK_URL}', url).replace('{CLIENT_ID}', clientID)
	# 	responseApi = requests.get(apiUrl).content
	# 	if '"location":' in responseApi:
	# 		responseTrack = requests.get(json.loads(responseApi)['location']).content
	# 		return json.loads(responseTrack)['stream_url'] + '?client_id=' + clientID
	# return ''

def get_list_soundcloud(url):
	if not ('soundcloud.com/' in url):
		return ''

	response = requests.get(url).content
	match = re.findall('a itemprop="url" href="(.*?)"', response)
	if not match:
		return ''

	ret = []
	for x in xrange(1,len(match)):
		urlTrack = 'https://soundcloud.com' + match[x]
		ret.append( {x : urlTrack})

	return ret


# quality is not avalable :v
def get_link_tumblr(url, quality=''):
	if (not 'tumblr.com/' in url):
		return ''

	source = requests.get(url).content
	match = re.search("iframe src='(.*?)'", source) 	#NOTE: src='...' 
	if not match:
		return ''

	source = requests.get(match.group(1)).content
	match = re.search('source src="(.*?)"', source)
	if not match:
		return ''

	return match.group(1)

































	




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
	#mode = else: return array [Episode, Language, Link360p, Link480p, Link720p, Link1080p, LinkHighestResolution]
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
			print 'get_link_phimmoi: Something Wrong!\r\nFileName:', matchInfo[0][2], '\r\nURL:', url, '\r\nResponse:', response, '\r\n'
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
		# 	try:		
		# 		index = int(threadName)
		# 	except:
		# 		pass
		# 	else:
		# 		if 0 <= index < len(self.__result):
		# 			self.__result[index] = ret

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