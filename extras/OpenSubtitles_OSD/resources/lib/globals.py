from xmlrpclib import Server,Transport
from httplib import HTTP
import locale
import os
from urlparse import urlparse
from types import UnicodeType
import re
import struct
import base64
import pickle
##import imdb
import urllib

#TESTS
defaultavi = "" 
disable_osdb = True
debugmode = True
use_threads = True
check_update = True
doing_login = False

#CONFIGS
videos_ext = ["avi","mpg","mpeg","wmv","divx","mkv","ogm","asf", "mov", "rm", "vob", "dv", "3ivx"]
subs_ext = ["srt","sub","txt","ssa","tmp"]
videos_wildcards = "All videos|*.avi;*.mpg;*.mpeg;*.wmv;*.asf;*.divx;*.mov;*.m2p;*.moov;*.omf;*.qt;*.rm;*.vob;*.dat;*.dv;*.3ivx;*.mkv;*.ogm|ALL files (*.*)|*.*"
    
##LOCAL_ENCODING = locale.getpreferredencoding(do_setlocale=False);
##if not LOCAL_ENCODING or LOCAL_ENCODING == "ANSI_X3.4-1968":
LOCAL_ENCODING = 'latin1'

version = ""
date_released = ""


update_address = ""


preferences_list = {}
sublanguages = {}
update_list = {}

##imdbserver = imdb.IMDb()

#GLOBAL NEEDED(don't change)
cookiefile = "conf/.cookie"
sourcefolder = ""
app_parameteres = ""

param_function = ""
param_files = []


osdb_token = ""
logged_as = ""
user_has_uploaded = False
xmlrpc_server = ""
proxy_address = None
text_log = False

subdownloader_pointer = None

class GtkTransport (Transport):
    user_agent = "Subdownloader " + version 
    
class ProxiedTransport(Transport):
    user_agent = "Subdownloader " + version 
    def set_proxy(self, proxy):
        self.proxy = proxy
    def make_connection(self, host):
        self.realhost = host
	h = HTTP(self.proxy)
	return h
    def send_request(self, connection, handler, request_body):
        connection.putrequest("POST", 'http://%s%s' % (self.realhost, handler))
    def send_host(self, connection, host):
        connection.putheader('Host', self.realhost)
	
def MakeOSLink(pagelink,sid=True):
    if preferences_list["server_osdb"].endswith("/"):
	serverosdb = preferences_list["server_osdb"][:-1]
    else:
	serverosdb = preferences_list["server_osdb"]
	
    parsed = urlparse(serverosdb)
    internallink = ""
    sidlink = ""
    if pagelink:
	internallink = "/" + pagelink
    if sid and logged_as:
	sidlink = "/sid-" + osdb_token
    link = parsed[0] + "://" + parsed[1] + internallink + sidlink
    return link 

def CleanString(s):
    garbage = ['_',' ','.',',','(',')']
    for char in garbage:
	s = s.replace(char,'')
    return s

def CleanTagsFile(texto):
    p = re.compile( '<.*?>')
    return p.sub('',texto)

def DeleteExtension(file):
    lastpointposition = file.rfind(".")
    return file[:lastpointposition]
		
def GetFpsAndTimeMs(path):
    fps = ""
    time_ms = ""
    try: 
	    avi_info = parse(path)
	    if avi_info.video[0].fps > 0:
		   fps = avi_info.video[0].fps

	    if avi_info.length > 0:
		    time_ms = avi_info.length * 1000
		    
	    return fps,time_ms 
    except:
	   return fps,time_ms 
	    

    
def Log(message):
    string_message = str(message)
    subdownloader_pointer.log_memory.append(string_message)
        
    if text_log:
	try:
	    for line in subdownloader_pointer.log_memory:
		text_log.AppendText("\n" + line)
	except:
	    pass
	
	subdownloader_pointer.log_memory = []
    
    
def hashFile(name):
      try: 
                 
                longlongformat = 'q'  # long long 
                bytesize = struct.calcsize(longlongformat) 
                    
                f = open(name, "rb") 
                    
                filesize = os.path.getsize(name) 
                hash = filesize 
                    
                if filesize < 65536 * 2: 
                       return "SizeError" 
                 
                for x in range(65536/bytesize): 
                        buffer = f.read(bytesize) 
                        (l_value,)= struct.unpack(longlongformat, buffer)  
                        hash += l_value 
                        hash = hash & 0xFFFFFFFFFFFFFFFF #to remain as 64bit number  
                         
    
                f.seek(max(0,filesize-65536),0) 
                for x in range(65536/bytesize): 
                        buffer = f.read(bytesize) 
                        (l_value,)= struct.unpack(longlongformat, buffer)  
                        hash += l_value 
                        hash = hash & 0xFFFFFFFFFFFFFFFF 
                 
                f.close() 
                returnedhash =  "%016x" % hash 
                return returnedhash 
    
      except(IOError): 
                return "IOError"



def EncodeLocale(phrase):
    #if not isinstance(phrase, UnicodeType):
    phrase = unicode(phrase.encode("iso-8859-1","replace"))
    return phrase

def ConvertLang_xxx2xx(str):
    return sublanguages["languages_id_xxx"][str][0]
def ConvertLang_xxx2name(str):
    return sublanguages["languages_id_xxx"][str][1]
def ConvertLang_xx2name(str):
    return sublanguages["languages_id_xxx"][sublanguages["languages_xx2xxx"][str]][1]
def ConvertLang_xx2xxx(str):
    return sublanguages["languages_xx2xxx"][str]
def ConvertLang_name2xxx(str):
    return sublanguages["languages_name2xxx"][str]
def ConvertLang_name2xx(str):
    return sublanguages["languages_id_xxx"][sublanguages["languages_name2xxx"][str]][0]
    
def DownloadNewTranslations(lang_app_xx):
	try:
	    mo_translation_coded = xmlrpc_server.GetTranslation(osdb_token, lang_app_xx, "mo" )["data"]
	    po_translation_coded = xmlrpc_server.GetTranslation(osdb_token, lang_app_xx, "po" )["data"]
	    po_translation = base64.decodestring(po_translation_coded)
	    mo_translation = base64.decodestring(mo_translation_coded)
	    if not os.path.exists(os.path.join(sourcefolder,"locale",lang_app_xx)):
		os.mkdir(os.path.join(sourcefolder,"locale",lang_app_xx))
		os.mkdir(os.path.join(sourcefolder,"locale",lang_app_xx,"LC_MESSAGES"))
			      
	    mofile = file(os.path.join(sourcefolder,"locale",lang_app_xx,"LC_MESSAGES","subdownloader.mo"),'wb')
	    mofile.write(mo_translation)
	    mofile.close()
	    pofile = file(os.path.join(sourcefolder,"locale",lang_app_xx,"LC_MESSAGES","subdownloader.po"),'wb')
	    pofile.write(po_translation)
	    pofile.close()
	    #current_translations_dates[lang_app_xx] = new_translations_dates[lang_app_xx]
	    #pickle.dump(current_translations_dates,file(os.path.join(sourcefolder,"conf/.translations"),"wb"))
	    return True
	except:
	    return False
    
def getAddress(file):
	filename = EncodeLocale(os.path.basename(file))
	filenameurl = (filename) #Corrects the accent characters.
	
	if not os.path.exists(file):
		return "NotFoundError"
	else:
		hash = hashFile(file)
		if hash == "IOError" or hash== "SizeError":
			return hash
		
		#We keep going if there was no error.
		
		videofilesize = os.path.getsize(file)
		linkhtml_index =  "search/moviebytesize-"+str(videofilesize)+"/moviehash-"+hash
		videofilename = filename
		pathvideofilename = file
		videohash = hash
		return {"hash":hash, "filename":filename, "pathvideofilename":file, "filesize":str(videofilesize)
			, "linkhtml_index":linkhtml_index}


