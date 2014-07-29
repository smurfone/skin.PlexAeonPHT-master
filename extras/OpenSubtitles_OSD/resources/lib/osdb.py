import sys
import os
import xmlrpclib
import urllib, urllib2
import unzip
import globals
import RecursiveParser
from xml.dom import minidom  
##import sublight_utils as SublightUtils
from utilities import *

_ = sys.modules[ "__main__" ].__language__

BASE_URL_XMLRPC_DEV = u"http://dev.opensubtitles.org/xml-rpc"
BASE_URL_XMLRPC = u"http://api.opensubtitles.org/xml-rpc"
BASE_URL_SEARCH = u"http://www.opensubtitles.com/%s/search/moviename-%s/simplexml"
BASE_URL_SEARCH_ALL = u"http://www.opensubtitles.com/en/search/sublanguageid-%s/moviename-%s/simplexml"
BASE_URL_SEARCH_OFFSET = u"http://www.opensubtitles.com/en/search/sublanguageid-%s/moviename-%s/offset-40/simplexml"
BASE_URL_DOWNLOAD = u"http://dev.opensubtitles.org/%s"
BASE_URL_OSTOK = "http://app.boxee.tv/api/ostok" 

def compare_columns(a, b):
        return cmp( a["language_name"], b["language_name"] )  or cmp( b["sync"], a["sync"] ) 

class OSDBServer:
    def Create(self):
	self.subtitles_alt_list = []
	self.subtitles_list = []
	self.subtitles_hash_list = []
	self.subtitles_name_list = []
	self.subtitles_imdbid_list = []
	self.languages_list = []
	self.folderfilesinfo_list = []
	self.osdb_token = ""
	self.connected = False
	self.smbfile = False

    def connect( self, osdb_server, username, password ):
	LOG( LOG_INFO, "Connecting to server " + osdb_server + "..." )
	try:
		if osdb_server:
			self.server = xmlrpclib.Server( "http://api.opensubtitles.org/xml-rpc", verbose=0 )
#			info = self.server.ServerInfo()
#			if username:
#				LOG( LOG_INFO, "Logging in " + username + "..." )
#				login = self.server.LogIn(username, password, "en", "XBMC")
#			else:
#				LOG( LOG_INFO, "Logging in anonymously..." )
#				login = self.server.LogIn("", "", "en", "XBMC")
			LOG( LOG_INFO, "Logging in anonymously..." )
			login = self.server.LogIn("", "", "en", "XBMC/9.04.1 OpenSubtitles/1.2")
			token  = login[ "token" ]

#			socket = urllib.urlopen( BASE_URL_OSTOK )
#			result = socket.read()
#			socket.close()
#			xmldoc = minidom.parseString(result)
#			token = xmldoc.getElementsByTagName("token")[0].firstChild.data
			if token:
#			if (login["status"].find("200") > -1):
				self.connected = True
				self.osdb_token = token
#				self.osdb_token = login["token"]
				LOG( LOG_INFO, "Connected" )
				return True, ""
			else:
				self.connected = False
				error = "Login " + login["status"]
#				error = _( 653 )
				LOG( LOG_ERROR, error )
				return False, error
		else:
			self.connected = False
			error = _( 730 )
			LOG( LOG_ERROR, error )
			return False, error
	except Exception, e:
		error = _( 731 ) % ( _( 732 ), str ( e ) )
		LOG( LOG_ERROR, error )
		return False, error


    def disconnect( self ):
	try:
		if ( self.osdb_token ) and ( self.connected ):
			LOG( LOG_INFO, "Disconnecting from server..." )
			logout = self.server.LogOut(self.osdb_token)
			self.connected = False
			LOG( LOG_DEBUG, logout )
			LOG( LOG_INFO, "Disconnected" )
			return True, ""
		else:
			error = _( 737 )
			LOG( LOG_ERROR, error )
			return False, error
	except Exception, e:
		error = _( 731 ) % ( _( 733 ), str ( e ) )
		LOG( LOG_ERROR, error )
		return False, error


    def getlanguages( self ):
	try:
		if self.connected:
			LOG( LOG_INFO, "Retrieve subtitle languages..." )
			languages = self.server.GetSubLanguages()
			##LOG( LOG_INFO, str(languages) )
			LOG( LOG_INFO, "Retrieved subtitle languages" )      
			self.languages_list = []
			if languages["data"]:
				for item in languages["data"]:
					self.languages_list.append( {"language_name":item["LanguageName"], "language":item["SubLanguageID"], "flag_image":"flags/" + item["ISO639"] + ".gif"} )
			##LOG( LOG_INFO, str(self.languages_list) )
			return True, ""
		else:
			error = _( 737 )
			LOG( LOG_ERROR, error )
			return False, error
	except Exception, e:
		error = _( 731 ) % ( _( 734 ), str ( e ) )
		LOG( LOG_ERROR, error )
		return False, error

    def getfolderfilesinfo( self, folder ):
	recursivefiles = []
	hashedfiles_list = []
	hashes_list = []
	self.folderfilesinfo_list = []
	try:
		if ( self.connected ) and ( os.path.isdir( folder ) ):
			parser = RecursiveParser.RecursiveParser()
			recursivefiles = parser.getRecursiveFileList(folder, globals.videos_ext)
			for item in recursivefiles:
				filename = globals.EncodeLocale(os.path.basename(item))
				filenameurl = (item) #Corrects the accent characters.
				if not os.path.exists(item):
					error = _( 738 ) % ( item, )
					LOG( LOG_ERROR, error )
					return False, error
				else:
					hash = globals.hashFile(item)
					if hash == "IOError" or hash == "SizeError":
						error = _( 739 ) % ( item, hash, )
						LOG( LOG_ERROR, error )
						return False, errors
					else:
						hashedfiles_list.append( {'filename':item, 'hash':hash} )
						hashes_list.append( hash )
			if hashedfiles_list:
				hashes = self.server.CheckMovieHash(self.osdb_token, hashes_list)
				for item in hashes_list:
					for file in hashedfiles_list:
						if file["hash"] == item:
							f = file["filename"]				
					if hashes["data"][item]:
						movie = hashes["data"][item]
						self.folderfilesinfo_list.append( {'filename':f, 'moviename':movie['MovieName'], 'imdbid':movie['MovieImdbID']} )
						
	except Exception, e:
		error = _( 731 ) % ( _( 735 ), str ( e ) ) 
		LOG( LOG_ERROR, error )
		return False, error
		
    def mergesubtitles( self ):
        self.subtitles_list = []
        if( len ( self.subtitles_hash_list ) > 0 ):
            for item in self.subtitles_hash_list:
			    if item["format"].find( "srt" ) == 0:
			        self.subtitles_list.append( item )
			    if item["format"].find( "sub" ) == 0:
			        self.subtitles_list.append( item )
        if( len ( self.subtitles_name_list ) > 0 ):
            for item in self.subtitles_name_list:
			    if item["format"].find( "srt" ) == 0:
			        self.subtitles_list.append( item )
			    if item["format"].find( "sub" ) == 0:
			        self.subtitles_list.append( item )

##        if( len ( self.subtitles_imdbid_list ) > 0 ):
##            for item in self.subtitles_imdbid_list:
##			    if item["format"].find( "srt" ) == 0:
##			        self.subtitles_list.append( item )
##			    if item["format"].find( "sub" ) == 0:
##			        self.subtitles_list.append( item )
	
        if ( len ( self.subtitles_alt_list ) > 0 ):
             for item in self.subtitles_alt_list:
			    if item["format"].find( "srt" ) == 0:
			        self.subtitles_list.append( item )
			    if item["format"].find( "sub" ) == 0:
			        self.subtitles_list.append( item )

        if( len ( self.subtitles_list ) > 0 ):
            self.subtitles_list = sorted(self.subtitles_list, compare_columns)
        
    def searchsubtitles( self, file, hash, size, lang1,lang2 ):
	self.subtitles_hash_list = []
        self.allow_exception = False
	
	try:
		if ( self.osdb_token ) and ( self.connected ):
			
			##filename = globals.EncodeLocale( os.path.basename( file ) )
			##filename = filename.encode('iso-8859-1', 'replace')
			##LOG( LOG_INFO, "Searching subtitles by hash for " + file )
			filename = os.path.basename( file )
			
			if lang1 == "all" or lang2 == "all":	
				language = "all"
			else:
				if lang1 == lang2:
					language = lang1
				else:
					language = lang1 + "," + lang2

			videofilesize = size
			linkhtml_index =  "search/moviebytesize-"+str( videofilesize )+"/moviehash-"+hash
			videofilename = filename
			pathvideofilename = file
			videohash = hash
			hashresult = {"hash":hash, "filename":filename, "pathvideofilename":file, "filesize":str( videofilesize ), "linkhtml_index":linkhtml_index}
			searchlist = []
			searchlist.append({'sublanguageid':language,'moviehash':hashresult["hash"],'moviebytesize':str( hashresult["filesize"] ) })
			##LOG( LOG_INFO, "Searchlist " + searchlist )
			search = self.server.SearchSubtitles( self.osdb_token, searchlist )
			##LOG( LOG_INFO, "Searching subtitles by hash for " + searchlist )

			if search["data"]:
				for item in search["data"]:
					if item["ISO639"]:
						flag_image = item["ISO639"] + ".png"
					else:								
						flag_image = "-.png"
					self.subtitles_hash_list.append({'filename':item["SubFileName"],'link':item["ZipDownloadLink"],"language_name":item["LanguageName"],"language_flag":flag_image,"language_id":item["SubLanguageID"],"ID":item["IDSubtitle"],"rating":str( int( item["SubRating"][0] ) ),"format":item["SubFormat"],"sync":True})
				self.subtitles_list.append( self.subtitles_hash_list )

				message =  str( len ( self.subtitles_hash_list )  ) + " subtitles found"
				LOG( LOG_INFO, message )
				return True, message
			else: 
				message = "No subtitles found"
				LOG( LOG_INFO, message )
				return True, message
	except Exception, e:
		error = _( 731 ) % ( _( 736 ), str ( e ) ) 
		LOG( LOG_ERROR, error )
		return False, "Greska"



    def searchsubtitlesbyimdbid( self, imdbid, language="all" ):
	self.subtitles_imdbid_list = []
        self.allow_exception = False
	
	try:
		if ( self.osdb_token ) and ( self.connected ):
			LOG( LOG_INFO, "Searching subtitles by imdbid for " + imdbid )
			
			#We try and check if the file is from an smb share
			if file.find( "//" ) == 0:
				error = _( 740 )
				LOG( LOG_ERROR, error )
				return False, error

			filename = globals.EncodeLocale( os.path.basename( file ) )
			filenameurl = ( filename ) #Corrects the accent characters.
			
			if not os.path.exists( file ):
				error = _( 738 ) % ( file, )
				LOG( LOG_ERROR, error )
				return False, error
			else:
				hash = globals.hashFile( file )
				if hash == "IOError" or hash== "SizeError":
					error = _( 739 ) % ( file, hash, )
					LOG( LOG_ERROR, error )
					return False, error		
				#We keep going if there was no error.
				videofilesize = os.path.getsize( file )
				linkhtml_index =  "search/moviebytesize-"+str( videofilesize )+"/moviehash-"+hash
				videofilename = filename
				pathvideofilename = file
				videohash = hash
				hashresult = {"hash":hash, "filename":filename, "pathvideofilename":file, "filesize":str( videofilesize )
						, "linkhtml_index":linkhtml_index}
				searchlist = []
				searchlist.append({'sublanguageid':language,'moviehash':hashresult["hash"],'moviebytesize':str( hashresult["filesize"] ) })
				search = self.server.SearchSubtitles( self.osdb_token, searchlist )
				if search["data"]:
					for item in search["data"]:
						if item["ISO639"]:
							flag_image =  item["ISO639"] + ".png"
						else:	
							flag_image = "-.png"
						self.subtitles_imdbid_list.append({'filename':item["SubFileName"],'link':item["ZipDownloadLink"],"language_name":item["LanguageName"],"language_flag":flag_image,"language_id":item["SubLanguageID"],"ID":item["IDSubtitle"],"rating":str( int( item["SubRating"][0] ) ),"format":item["SubFormat"],"sync":True})
					self.subtitles_list.append ( self.subtitles_imdbid_list )

					message =  str( len ( self.subtitles_hash_list )  ) + " subtitles found"
					LOG( LOG_INFO, message )
					return True, message
				else: 
					message = "No subtitles found"
					LOG( LOG_INFO, message )
					return True, message
	except Exception, e:
		error = _( 731 ) % ( _( 736 ), str ( e ) ) 
		LOG( LOG_ERROR, error )
		return False, error

    def searchsubtitlesbyname_alt( self, name, lang2, lang1 ):
	self.subtitles_alt_list = []
        self.allow_exception = False
        search_url = ""
	try:
		LOG( LOG_INFO, "Searching subtitles by name for " + name )
		if lang1 == lang2 :
			search_url = BASE_URL_SEARCH_OFFSET % ( lang2, name )
			##search_url = BASE_URL_SEARCH_ALL % ( lang2, os.path.basename( name ) )
		else:
			search_url = BASE_URL_SEARCH_ALL % ( lang2,  name )
		search_url.replace( " ", "+" )
		LOG( LOG_INFO, search_url )

		socket = urllib.urlopen( search_url )
		result = socket.read()
		socket.close()
		xmldoc = minidom.parseString(result)

		subtitles_alt = xmldoc.getElementsByTagName("subtitle")

		if subtitles_alt:
			url_base = xmldoc.childNodes[0].childNodes[1].firstChild.data
			for subtitle in subtitles_alt:
				filename = ""
				movie = ""
				lang_name = ""
				subtitle_id = ""
				lang_id = ""
				flag_image = ""
				link = ""
				if subtitle.getElementsByTagName("releasename")[0].firstChild:
					filename = subtitle.getElementsByTagName("releasename")[0].firstChild.data
				if subtitle.getElementsByTagName("format")[0].firstChild:
					format = subtitle.getElementsByTagName("format")[0].firstChild.data
					filename = filename + "." +  format
				if subtitle.getElementsByTagName("movie")[0].firstChild:
					movie = subtitle.getElementsByTagName("movie")[0].firstChild.data
				if subtitle.getElementsByTagName("language")[0].firstChild:
					lang_name = subtitle.getElementsByTagName("language")[0].firstChild.data
				if subtitle.getElementsByTagName("idsubtitle")[0].firstChild:
					subtitle_id = subtitle.getElementsByTagName("idsubtitle")[0].firstChild.data
				if subtitle.getElementsByTagName("iso639")[0].firstChild:
					lang_id = subtitle.getElementsByTagName("iso639")[0].firstChild.data
					flag_image = lang_id + ".png"
				if subtitle.getElementsByTagName("download")[0].firstChild:
					link = subtitle.getElementsByTagName("download")[0].firstChild.data
					link = url_base + link
				if subtitle.getElementsByTagName("subrating")[0].firstChild:
					rating = subtitle.getElementsByTagName("subrating")[0].firstChild.data
				
					
				self.subtitles_alt_list.append({'filename':filename,'link':link,'language_name':lang_name,'language_id':lang_id,'language_flag':flag_image,'movie':movie,"ID":subtitle_id,"rating":str( int( rating[0] ) ),"format":format,"sync":False})
			self.subtitles_list.append ( self.subtitles_alt_list )

			message =  str( len ( self.subtitles_hash_list )  ) + " subtitles found"
			LOG( LOG_INFO, message )
			return True, message
		else: 
			message = "No subtitles found"
			LOG( LOG_INFO, message )
			return True, message

	except Exception, e:
		error = _( 743 ) % ( search_url, str ( e ) ) 
		LOG( LOG_ERROR, error )
		return False, error

    def searchsubtitlesbyname( self, name, lang1 ):
	self.subtitles_name_list = []
        self.allow_exception = False
	search_url = ""
	
	try:
		LOG( LOG_INFO, "Searching subtitles by name for " + name )
		search_url = BASE_URL_SEARCH_ALL % ( lang1, os.path.basename( name ), )

		search_url.replace( " ", "+" )
		LOG( LOG_INFO, search_url )

		socket = urllib.urlopen( search_url )
		result = socket.read()
		socket.close()
		xmldoc = minidom.parseString(result)

		subtitles = xmldoc.getElementsByTagName("subtitle")

		if subtitles:
			url_base = xmldoc.childNodes[0].childNodes[1].firstChild.data
			for subtitle in subtitles:
				filename = ""
				movie = ""
				lang_name = ""
				subtitle_id = ""
				lang_id = ""
				flag_image = ""
				link = ""
				if subtitle.getElementsByTagName("releasename")[0].firstChild:
					filename = subtitle.getElementsByTagName("releasename")[0].firstChild.data
				if subtitle.getElementsByTagName("format")[0].firstChild:
					format = subtitle.getElementsByTagName("format")[0].firstChild.data
					filename = filename + "." +  format
				if subtitle.getElementsByTagName("movie")[0].firstChild:
					movie = subtitle.getElementsByTagName("movie")[0].firstChild.data
				if subtitle.getElementsByTagName("language")[0].firstChild:
					lang_name = subtitle.getElementsByTagName("language")[0].firstChild.data
				if subtitle.getElementsByTagName("idsubtitle")[0].firstChild:
					subtitle_id = subtitle.getElementsByTagName("idsubtitle")[0].firstChild.data
				if subtitle.getElementsByTagName("iso639")[0].firstChild:
					lang_id = subtitle.getElementsByTagName("iso639")[0].firstChild.data
					flag_image = lang_id + ".png"
				if subtitle.getElementsByTagName("download")[0].firstChild:
					link = subtitle.getElementsByTagName("download")[0].firstChild.data
					link = url_base + link
				if subtitle.getElementsByTagName("subrating")[0].firstChild:
					rating = subtitle.getElementsByTagName("subrating")[0].firstChild.data
				
					
				self.subtitles_name_list.append({'filename':filename,'link':link,'language_name':lang_name,'language_id':lang_id,'language_flag':flag_image,'movie':movie,"ID":subtitle_id,"rating":str( int( rating[0] ) ),"format":format,"sync":False})
			self.subtitles_list.append ( self.subtitles_name_list )

			message =  str( len ( self.subtitles_hash_list )  ) + " subtitles found"
			LOG( LOG_INFO, message )
			return True, message
		else: 
			message = "No subtitles found"
			LOG( LOG_INFO, message )
			return True, message

	except Exception, e:
		error = _( 743 ) % ( search_url, str ( e ) ) 
		LOG( LOG_ERROR, error )
		return False, error



