import os
import inspect
import platform

import csv
import base64, md5
from Crypto.Cipher import AES
from Crypto import Random


OS_PLATFORM = platform.system()
if ('Windows' == OS_PLATFORM):
	import winreg

	



BLOCK = AES.block_size
# make sure size of key, raw for aes cipher
pad = lambda s: s + (BLOCK - len(s) % BLOCK) * chr(BLOCK - len(s) % BLOCK) 
unpad = lambda s : s[:-ord(s[len(s)-1:])]



class AESCipher:
	def __init__(self):
		pass
	@staticmethod
	def encrypt(raw, key, iv=''):
		key = pad(key)
		raw = pad(raw)
		iv = iv or Random.new().read(BLOCK)
		cipher = AES.new( key, AES.MODE_CBC, iv )
		return base64.b64encode( iv + cipher.encrypt(raw) )

	@staticmethod
	def decrypt(enc, key, iv=''):
		enc = base64.b64decode(enc)
		key = pad(key)
		iv = iv or enc[:BLOCK]
		cipher = AES.new(key, AES.MODE_CBC, iv )
		return unpad(cipher.decrypt( enc[BLOCK:] ))
		
def aes_cbc_decrypt(string, passwd):
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

def module_path(local_function):
   ''' returns the module path without the use of __file__.  Requires a function defined
   locally in the module.
   from http://stackoverflow.com/questions/729583/getting-file-path-of-imported-module'''
   return os.path.abspath(inspect.getsourcefile(local_function))

  
def get_idmExe_path():
	try:
		return regkey_value(r"HKEY_CURRENT_USER\Software\DownloadManager", "ExePath")
	except:
		return ''


def regkey_value(path, name="", start_key = None):
    if isinstance(path, str):
        path = path.split("\\")
    if start_key is None:
        start_key = getattr(winreg, path[0])
        return regkey_value(path[1:], name, start_key)
    else:
        subkey = path.pop(0)
    with winreg.OpenKey(start_key, subkey) as handle:
        assert handle
        if path:
            return regkey_value(path, name, handle)
        else:
            desc, i = None, 0
            while not desc or desc[0] != name:
                desc = winreg.EnumValue(handle, i)
                i += 1
            return desc[1]

#save as csv
#overwrite file
def write_file_csv(data, fileName):
	with open(fileName, 'wb') as csvfile:
		csvWriter = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
		for row in data:
			csvWriter.writerow(row)


def main():
	data = str([1,2, {1:'d'}])
	st = time.time()
	enc = AESCipher.encrypt(data,'key')
	print time.time() - st
	# print enc


	file = open('tmp', 'r+')
	# file.write(enc)
	st = time.time()
	encdata = file.read()
	encdata= enc

	dec = AESCipher.decrypt(encdata, 'key')
	print dec, time.time() - st
if __name__ == '__main__':
	main()
