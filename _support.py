import csv 			#save data
import os			#file
import re 			#regex
import requests		#HTTP requests
import psutil		#kill process
import base64, md5
import urllib
from Crypto.Cipher import AES

def main():
	pass

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

	return AES.new(key, AES.MODE_CBC, iv).decrypt(encypted)
#remove '\' out of URL
def decrypt_slash_url(url):
	return url.replace('\\', '')
#session = requests.session()
#return file_name_downloaded
def download_file(url, fileName='', session=''):
	if not re.search('://(www\.)?(.+)\..*?/', url):
		return show_error('download_file ERROR: URL wrong!!')

	local_filename = fileName if fileName else url.split('/')[-1]
	# NOTE the stream=True parameter
	
	r = session.get(url, stream=True) if session else requests.get(url, stream=True)

	try:
		with open(local_filename, 'wb') as f:
			for chunk in r.iter_content(chunk_size=1024): 
				if chunk: # filter out keep-alive new chunks
					f.write(chunk)
					#f.flush() commented by recommendation from J.F.Sebastian
		return local_filename
	except IOError as err:
		print format(err)
		return ''


#return url by quality (<=0:'highest' - x - else; dict{quality:url})
def filter_url(jsonData, keyQuality, keyUrl, option={}):
	#default
	if isinstance(jsonData, str):
		return get_url_by_option(jsonData, option)

	ret = {}
	if isinstance(jsonData, dict):
		if keyUrl in jsonData:
			urls = jsonData[keyUrl]
			#get type {'quality' : ' URL'}
			if (not isinstance(urls, dict)):
				return get_url_by_option(jsonData[keyUrl], option)
			else:
				jsonData = urls

		if (not isinstance(keyQuality, list)) and (not isinstance(jsonData, tuple)) \
			 and (keyQuality in jsonData):
			return get_url_by_option(jsonData[keyQuality], option)
		
		for q in keyQuality:
			if q in jsonData:
				u =  get_url_by_option(jsonData[q], option)
				if u:
					try:
						if isinstance(q, str) and re.search('\d+', q):
							q = int( re.search('\d+', q).group(0) )	
					except Exception as e:
						pass
					ret[q] = u

	#get type [{'keyQuality' :quality, 'keyUrl':URL}]
	elif (isinstance(jsonData, list)) or (isinstance(jsonData, tuple)):
		for item in jsonData:
			if isinstance(item, dict) and (keyQuality in item) and (keyUrl in item):
				q = item[keyQuality]
				try:
					if isinstance(q, str) and re.search('\d+', q):
						q = int( re.search('\d+', q).group(0) )	
				except Exception as e:
					pass
				#new title		
				newOpion = option.copy()
				if isinstance(option, dict) and ('title' in option) and option['title']:
					newOpion['title'] = option['title'] + '_[' + str(item[keyQuality]) + ']'

				u = get_url_by_option(item[keyUrl], newOpion)
				if u:
					ret[q] = u
	if not ret:
		return ''

	quality = ''
	if option and isinstance(option, dict):
		if 'quality' in option:
			quality = option['quality']

	if isinstance(quality, int):
		if quality <= 0:
			return ret[max(ret.keys())]
		elif quality in ret:
			return ret[quality]
		else:
			return ret[min(ret.keys())]

	return ret

#decrypt url
def get_url_by_option(url, option={}):
	if not ( isinstance(url, str) or isinstance(url, unicode) ):
		return url
	title = ''
	funcDecryptUrl = ''
	keyDecryptUrl = ''

	if option and isinstance(option, dict):
		if 'title' in option:
			title = option['title']
		if 'funcDecryptUrl' in option:
			funcDecryptUrl = option['funcDecryptUrl']
		if 'keyDecryptUrl' in option:
			keyDecryptUrl = option['keyDecryptUrl']

	if funcDecryptUrl and  (funcDecryptUrl in globals()):
		url = eval(funcDecryptUrl)(url, keyDecryptUrl) if keyDecryptUrl \
			else eval(funcDecryptUrl)(url)

	if title and (isinstance(title, unicode) or isinstance(title, str)) :
		title = urllib.quote_plus(title)
		match = re.search('\&title=(.*?)(&|$)', url)
		if match:
			url = url.replace(match.group(1),title)
		else:
			url += '&title=' + title

	url = ''.join( re.findall('[\w:\\\/\.?=&%-]', url) )
	return url	

# multi_kill: kill all processName
def kill_process(processName,multi_kill=True):
	for proc in psutil.process_iter():
	    if proc.name() == processName:
	        proc.kill()
	        if not multi_kill:
	        	return

#try to remove file
def remove(path):
	try:
		os.remove(path)
	except OSError as err:
		print format(err)

def show_error(errorLog):
	print errorLog
	return ''

#try to show with no error
def show_image(path):
	try:
		from PIL import Image
		img = Image.open(path).show()
	except ImportError:
		import webbrowser
		webbrowser.open(path)

#save as csv
#overwrite file
def write_file_csv(data, fileName):
	with open(fileName, 'wb') as csvfile:
		csvWriter = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
		for row in data:
			csvWriter.writerow(row)

if __name__ == '__main__':
    main()
