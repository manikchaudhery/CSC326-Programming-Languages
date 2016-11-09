#http://stackoverflow.com/questions/18479838/authentication-using-google-and-facebook-very-slow
#http://stackoverflow.com/questions/16746545/google-api-client-is-really-slow-when-building-the-drive-v2-api
#http://stackoverflow.com/questions/2720014/upgrading-all-packages-with-pip
#http://www.whatisseolearning.com/wp-content/uploads/2015/11/se23.jpg

from bottle import get, post, route, run, request, static_file, SimpleTemplate, template, redirect
import operator

#------------------------------------------------------------------------------------------------------------
					#-- Using beaker for sessions
import bottle
from beaker.middleware import SessionMiddleware
session_opts = {
    'session.type': 'file',
    'session.cookie_expires': 300,
    'session.data_dir': './data',
    'session.auto': True
}
app = SessionMiddleware(bottle.app(), session_opts)

#------------------------------------------------------------------------------------------------------------

'''My global nested dictionary to keep track of users and all words 
	to their occurances. Use like this:
		globalUserWordList['shafaaf'] = {}
		globalUserWordList['shafaaf']['key'] = 'value'
'''
globalUserWordList = {}

'''My global nested dictionary to keep track of users and list of most recent words
'''
globalUserRecentSearch = {}

#------------------------------------------------------------------------------------------------------------
								#My routes
@get('/')
def sendIndexPage():
	session = request.environ.get('beaker.session')
	#checking if user is logged in, set him up
	if 'email' in session:
		email = session['email']
		picture = session['picture']
		fullName = session['name']
		loggedIn = 1
		#make new dictionary of search history words for user if first time
		if email not in globalUserWordList:
			globalUserWordList[email] = {}		
		#make new list (use like stack) of recent search words for user if first time
		if email not in globalUserRecentSearch:
			globalUserRecentSearch[email] = []	

	else:
		loggedIn = 0		
	
	#keywords is name of input field in search box
	keywords = request.query.keywords

	#if no keywords passed in from form, them return normal home page
	if not keywords:
		if loggedIn == 1:
			return template('index', loggedIn = loggedIn, email = email, 
				picture = picture, fullName = fullName)
		else:
			return template('index', loggedIn = loggedIn)

	#Else show results of query
	else:

		#first making current search stats, not historical

	    keywordList = keywords.strip()
	    #This puts keywords into array
	    keywordList = keywordList.lower().split()
	    #currentWordList is a dict used for only this current search search
	    currentWordList = {}
	    for word in keywordList:
			if word in currentWordList:
				currentWordList[word]  = currentWordList[word] + 1;
			else:
			    currentWordList[word] = 1;    
	    print "main.py: currentWordList is ", currentWordList

	    #Removing duplicates from keywordList and put in list to maintain order
	    seen = []
	    for word in keywordList:
		    if word not in seen:
			    seen.append(word)

	    print "main.py: User typed keywordList is ", keywordList
	    print "main.py: seen is ", seen

	    #if user is not logged in, no need for search history
	    if loggedIn == 0:
	    	return template('results', loggedIn = loggedIn, currentWordList = currentWordList, 
		    seen = seen, keywordList = keywordList, keywords = keywords)

	    #user logged in so need search history for that specific user
	    else:

	    #making search history for loggedin user
		for word in keywordList:
			if word in globalUserWordList[email]:
				globalUserWordList[email][word] = globalUserWordList[email][word] + 1
			else:
				globalUserWordList[email][word] = 1

	    print "main.py: globalUserWordList is ", globalUserWordList
	    print "server.py: globalUserWordList[email] is ", globalUserWordList[email]

	    globalWordList = globalUserWordList[email]		

	    #Making reverse sorted list of tuples from globalWordList's value i.e word count
	    topWordList = sorted(globalWordList.items(), key=operator.itemgetter(1), reverse=True)
	    print "main.py: My topWordList is ",topWordList
	    print "main.py: topWordList has length ", len(topWordList)
	    
	    #Only get top 5
	    #TO DO... change this to 20 later...
	    if len(topWordList) > 20:
		    myLength = 20
	    else:
		    myLength = len(topWordList)
	    
	    top20List = topWordList[:myLength]
	    print "main.py: top20List is ", top20List

	    #making most recent words for loggedin user
	    for word in keywordList:
			if word in globalUserRecentSearch[email]:
				globalUserRecentSearch[email].remove(word);
				globalUserRecentSearch[email].insert(0, word)
			else:
				globalUserRecentSearch[email].insert(0, word)		

	    return template('results', loggedIn = loggedIn, email = email, 
	    	picture = picture, fullName = fullName, currentWordList = currentWordList, 
	    		seen = seen, top20List=top20List, keywordList = keywordList, 
	    			keywords = keywords, mostRecentlySearched = globalUserRecentSearch[email][:10])

#------------------------------------------------------------------------------------------------------------
							#------------Serving staic files from static folder---------
@route('/<filename:path>')
def send_static(filename):
    return static_file(filename, root='static/')
    
#------------------------------------------------------------------------------------------------------------
									#------------Google Login---------

@get('/googleLogin')
def googleLogin():
	from oauth2client import client

	#follow - https://developers.google.com/api-client-library/python/guide/aaa_oauth

	print "Server: googleLogin"
	flow = client.flow_from_clientsecrets("client_secrets.json", scope='https://www.googleapis.com/auth/plus.me https://www.googleapis.com/auth/userinfo.email', redirect_uri='http://localhost:8080/redirect')
	# .45.183.165:8080/redirect must end with a public top-level domai
	# redirect_uri='http://localhost:8080/redirect'

	#Redirect the user to Google's OAuth 2.0 server

	#Generate a URL to request access from Google's OAuth 2.0 server
	uri = flow.step1_get_authorize_url()

	#Redirect the user to auth_uri
	redirect(str(uri))

#------------------------------------------------------------------------------------------------------------
								#------------Google redirect page---------
@get('/redirect')
def redirect_page():
	'''A one-time code will be attached to the query string when the 
		browser is redirected to the redirect_uri.'''	
	
	#if allowed access
	code = request.query.get('code','')
	print "code is ", code	

	#if not allowed access, TODO: Make error page
	#code = request.query.get('error','')
	#print "error is ", code	

	from oauth2client.client import OAuth2WebServerFlow
	flow = OAuth2WebServerFlow(client_id='599698187223-j3u1h35rnc4h80qd51st3mnqghkbf32o.apps.googleusercontent.com',
                           client_secret='WR6_bPmNcJ3WlKkMxvNyF8p7',
                           scope='https://www.googleapis.com/auth/plus.me https://www.googleapis.com/auth/userinfo.email',
                           redirect_uri= 'http://localhost:8080/redirect')

	'''The step2_exchange() function of the Flow class exchanges an 
		authorization code for a Credentials object'''
	print "flow is ", flow	
	credentials = flow.step2_exchange(code)
	print "credentials is ", credentials	


	'''A Credentials object holds refresh and access tokens that authorize access 
		to a single user's data. These objects are applied to httplib2.Http objects 
		to authorize access. They only need to be applied once and can be stored. '''
	token = credentials.id_token['sub']

	''' Use the authorize() function of the Credentials class to apply necessary 
		credential headers to all requests made by an httplib2.Http instance:'''
	import httplib2
	http = httplib2.Http(cache=".cache")
	http = credentials.authorize(http)

	# Once an httplib2.Http object has been authorized, it is typically passed to the build function:
	# get user email: from handout
	from apiclient.discovery import build
	users_service = build('oauth2', 'v2', http=http)
	user_document = users_service.userinfo().get().execute()
	user_email = user_document['email']
	#print 'user_document is ', user_document
	#print 'user_email is ', user_email

	#now save session
	session = request.environ.get('beaker.session')
	session['email'] = user_document['email']
	session['picture'] = user_document['picture']
	session['name'] = user_document['name']
	session.save()
	print "/redirect: session is ", session

	#Redirect the user to home page
	redirect(str("/"))

#------------------------------------------------------------------------------------------------------------
							#logout
@get('/logout')
def logout():
	session = request.environ.get('beaker.session')
	session.delete()
	redirect(str("/"))


#------------------------------------------------------------------------------------------------------------

run(app=app, host='0.0.0.0', port=8080, debug=True, reloader=True)

#------------------------------------------------------------------------------------------------------------
