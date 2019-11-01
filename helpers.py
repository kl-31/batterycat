# -*- coding: utf-8 -*-
"""
Created on Thu Apr 25 05:28:51 2019

@author: KCLIANG
Helper functions for biophotobot.
"""
from sklearn.feature_extraction.text import HashingVectorizer
from sklearn.externals import joblib
import pandas as pd
import numpy as np
from unidecode import unidecode
import string
import json
from os.path import isfile,splitext,isdir,dirname
from os import environ,remove,makedirs
import tweepy
from time import sleep
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import re
import datetime
from bs4 import BeautifulSoup
import urllib
from subprocess import call
from shutil import rmtree
import patoolib
import glob
from random import choice, randint
from PyPDF2 import PdfFileReader
import fitz
import html2text
from fuzzywuzzy import fuzz
#import bitly_api
#import sys

scopes = ['https://spreadsheets.google.com/feeds',
	  'https://www.googleapis.com/auth/drive']
keyfile_dict = {
    'auth_provider_x509_cert_url': environ['GSPREAD_AUTH_PROVIDER'],
    'auth_uri': environ['GSPREAD_AUTH_URI'],
    'client_email': environ['GSPREAD_CLIENT_EMAIL'],
    'client_id': environ['GSPREAD_CLIENT_ID'],
    'client_x509_cert_url': environ['GSPREAD_CLIENT_X509'],
    'private_key': environ['GSPREAD_PRIVATE_KEY'].replace('\\n', '\n'),
    'private_key_id': environ['GSPREAD_PRIVATE_KEY_ID'],
    'project_id': environ['GSPREAD_PROJECT_ID'],
    'token_uri': environ['GSPREAD_TOKEN_URI'],
    'type': environ['GSPREAD_TYPE']
}


def get_titles_db():
	#print(keyfile_dict)
	creds = ServiceAccountCredentials.from_json_keyfile_dict(
    keyfile_dict=keyfile_dict, scopes=scopes)
	#creds = ServiceAccountCredentials.from_json_keyfile_name('client_secret.json', scope)
	client = gspread.authorize(creds)
	sh = client.open_by_key('1yKc23vjZ9AGoUaMP1ebo9q31zVj5HEq0vUq2_C5shBs')
	worksheet = sh.sheet1
	titles_list = worksheet.col_values(1)	
	titles_list = [s.strip().lower() for s in titles_list]
	return titles_list

def write_to_db(row):
	creds = ServiceAccountCredentials.from_json_keyfile_dict(
    keyfile_dict=keyfile_dict, scopes=scopes)
	#creds = ServiceAccountCredentials.from_json_keyfile_name('client_secret.json', scope)
	client = gspread.authorize(creds)
	sh = client.open_by_key('1yKc23vjZ9AGoUaMP1ebo9q31zVj5HEq0vUq2_C5shBs')
	worksheet = sh.sheet1
	worksheet.insert_row(row+[str(datetime.date.today())],1)
	sleep(1) # google api 60 write requests per 60 sec
	return


def normalize_text(s):
	s=''.join([i for i in s if not i.isdigit()]) # remove numbers
	s = s.replace('-',' ')
	s = s.replace('/',' ')
	s = s.replace('μ','u')
	s = unidecode(str(s))
	s=s.translate(s.maketrans('', '', string.punctuation)) # remove punctuation
	s = s.lower() # make lowercase
	s = s.replace('  ',' ') # remove double spaces
	return s

def strip_html(s):
		#if s[:3]=='<p>' and not s[-4:]=='</p>': # differentiate between Nature and Science abstract formats
		soup = BeautifulSoup(s,'lxml')
		#soup.p.decompose()
		s = soup.get_text() 
		return s

def pull_handles_from_twitter(accounts):
	# twitter followers
	auth = tweepy.OAuthHandler(environ['TWITTER_CONSUMER_KEY'], environ['TWITTER_CONSUMER_SECRET'])
	auth.set_access_token(environ['TWITTER_ACCESS_TOKEN'], environ['TWITTER_ACCESS_SECRET'])
	api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True,retry_count=10, retry_delay=5, retry_errors=set([503])	)
	ids = []
	names = []
	handles = []
	#accounts =  ['rita_strack','joachimgoedhart']
	for account in accounts:
		for page in tweepy.Cursor(api.followers_ids, screen_name=account).pages():
			ids.extend(page)
			sleep(5)
	for page in tweepy.Cursor(api.friends_ids, screen_name='biophotonicat').pages():
		ids.extend(page)
		sleep(5)		
			
	ids = list(set(ids)) # dedupe
	#print(len(ids))
	for chunk_i in range(0,len(ids),100):
		users_obj = api.lookup_users(ids[chunk_i:chunk_i+100])
		names.extend([unidecode(user.name) for user in users_obj])
		handles.extend(['@'+user.screen_name for user in users_obj])
		sleep(5)
	author_handles_data = dict(zip(names,handles))	
	return author_handles_data
	
def get_author_handles(raw_author_list,journal,author_handles_data):

	
	handles_all = ''
	if journal == 'Biorxiv Biophys/Bioeng' or journal == 'Science' or journal == 'Science Advances':
		#paper_id = urllib.parse.urlparse(raw_author_list).path.split('/')[-1]
		#paper_path = 'https://www.biorxiv.org/content/10.1101/' + paper_id + '.full'
		soup = BeautifulSoup(urllib.request.urlopen(raw_author_list).read(),'lxml')
		authors_raw = soup.find_all('meta',{'class':'DC.Contributor'})	
		author_list = [x['content'] for x in authors_raw]
		
		#raw_author_list_split=raw_author_list[0]['name'].split(', ')
		#author_list = []
#		for i in range(0,len(raw_author_list_split),2):
#			author_list.append(raw_author_list_split[i+1].replace('.','')+' '+raw_author_list_split[i])	
#		# names are given in initials and last name. need to change format of twitter names.
#		for key in author_handles_data.keys():
#			lastname = str(key).split(' ')[-1]
#			if len(str(key).split(' ')) > 1:
#				initials = ' '.join([s[0] for s in str(key).split(' ')[:-1]])
#			else:
#				initials = ''
#			name = initials + ' ' + lastname
#			author_handles_data[name] = author_handles_data.pop(key)
	elif journal == "Arxiv Optics":
		h = html2text.HTML2Text()
		h.ignore_links = True	
		author_list = h.handle(raw_author_list[0]['name'])
		author_list = (author_list).replace('\n',' ').split(', ')
	elif journal == "Journal of Biophotonics":
		if 'name' in raw_author_list[0]:
			author_list=raw_author_list[0]['name'].replace('\n','').split(', ')
		else:
			author_list = []
	elif journal == "PNAS Engineering":
		author_list=raw_author_list[0]['name'].split(', ')
	else: 
		#journal == 'Nature Photonics' or journal == 'Nature Methods' or journal == 'Nature' or journal == 'Nature Communications' or journal == "Light: Science and Applications" or journal == 'Nature BME':
		author_list = [s['name'] for s in raw_author_list]

	for handle_query in author_handles_data.keys():
		for author in author_list:
			if fuzz.ratio(normalize_text(author),normalize_text(handle_query)) > 90:
				handles_all = handles_all + author_handles_data[handle_query] + ' '
				#print(author+' matched with ' +handle_query)
				break
	return handles_all
	
def scrape_image(raw, journal):
	if raw == '':
		return False
	
	if isdir('./data/'):
		rmtree('./data/')
		
	if journal == 'Journal of The Electrochemical Society':
		makedirs('./data/',exist_ok=True)
		raw=raw.replace('/cgi','')
		raw=raw.replace('/short','')
		raw=raw.replace('?rss=1','.figures-only')
		soup = BeautifulSoup(urllib.request.urlopen(raw).read(),'lxml')
		links_raw = soup.find_all('a',{'class':'in-nw'})		
		links=[dirname(raw)+'/'+x['href'].replace('expansion.html','large.jpg') for x in links_raw]
		if len(links)>0:
			pic_raw = choice(links)
		else:
			return False
		#this section is required for JPS and probably others
		opener = urllib.request.build_opener()
		opener.addheaders = [('User-agent', 'Mozilla/5.0')]
		urllib.request.install_opener(opener)	
		urllib.request.urlretrieve(pic_raw,'./data/pic_raw'+'.jpg')
		call(['convert','-density','300','-define', 'trim:percent-background=2%','-trim','+repage','-background', 'white', '-alpha', 'remove', '-alpha', 'off','./data/pic_raw.jpg','./data/tweet_pic.png'])
		
		#print(raw)
#		makedirs('./data/',exist_ok=True)
#		soup = BeautifulSoup(raw,'lxml')
#		if len(soup.find_all('img', src=True))==0:
#			return False
#		link = soup.find_all('img', src=True)[0]['src']
#		extension = splitext(urllib.parse.urlparse(link).path)[-1]
#		urllib.request.urlretrieve(link,'./data/tweet_pic'+extension)
#		call(['convert','-density','300','-define', 'trim:percent-background=2%','-trim','+repage','-background', 'white', '-alpha', 'remove', '-alpha', 'off','./data/tweet_pic'+extension,'./data/tweet_pic.png'])

	elif journal in ['Journal of Power Sources','Electrochimica Acta','Journal of Electroanalytical Chemistry','Energy Storage Materials','Advanced Energy Materials','ACS Energy Letters','Batteries & Supercaps','Nano Energy']:
		makedirs('./data/',exist_ok=True)
		soup = BeautifulSoup(raw,'lxml')
		links_raw = soup.find_all('img')		
		links = [x['src'] for x in links_raw]
		if len(links) == 0:
			return False
		else:
			pic_raw = choice(links)
		
			#this section is required for JPS and probably others
			opener = urllib.request.build_opener()
			opener.addheaders = [('User-agent', 'Mozilla/5.0')]
			urllib.request.install_opener(opener)		
			
			urllib.request.urlretrieve(pic_raw,'./data/pic_raw'+'.jpg')
			call(['convert','-density','300','-define', 'trim:percent-background=2%','-trim','+repage','-background', 'white', '-alpha', 'remove', '-alpha', 'off','./data/pic_raw.jpg','./data/tweet_pic.png'])

	elif journal in ['Energy & Environment Science','JMCA']:
		makedirs('./data/',exist_ok=True)
		if 'GA?' in raw.summary:
			print('EES: graphical abstract available')
			soup = BeautifulSoup(raw.summary,'lxml')
			links_raw = soup.find_all('img')
			for link in links_raw:
				if 'GA?' in link['src']:
					pic_raw = 'http://pubs.rsc.org'+link['src']
		else:
			print('EES: graphical abstract unavailable, trying to pull pdf')
			link = raw.title_detail.base.lower()
			link = link.replace('articlelanding','articlepdf')
			try:
				#this section is required for JPS and probably others
				opener = urllib.request.build_opener()
				opener.addheaders = [('User-agent', 'Mozilla/5.0')]
				urllib.request.install_opener(opener)	
				urllib.request.urlretrieve(link,'./data/paper.pdf')
				doc = fitz.open('./data/paper.pdf')
				img_pgs = []
				for i in range(1,len(doc)):
					if len(doc.getPageImageList(i)) > 0:
						img_pgs.append(str(i)) # pages with images
				if len(img_pgs) > 0:
					pg_choice = choice(img_pgs)
					call(['convert','-density','150','-define', 'trim:percent-background=2%','-trim','+repage','-background', 'white', '-alpha', 'remove', '-alpha', 'off','./data/paper.pdf['+ pg_choice+']','./data/tweet_pic.png'])
					print('Page %s saved as image.' % pg_choice)
				else:
					return False				
				
			except PermissionError or FileNotFoundError:
				print('pdf pull denied, sorry no image')
				return False

	elif journal == "Joule":
		makedirs('./data/',exist_ok=True)
		#paper_id = urllib.parse.urlparse(raw).path.split('/')[-1]
		#paper_path = 'https://www.biorxiv.org/content/10.1101/' + paper_id + '.full'
		opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor()) # site requires cookie processing
		soup = BeautifulSoup(opener.open(raw).read(),'lxml')
		links_raw = soup.find_all('a',{'class':'download-links__download-Hi-res'})
		if len(links_raw) == 0:
			return False
		else:
			links = []
			for link in links_raw:
				links.append('http://'+link['href'][2:])
			pic_raw = choice(links)
			urllib.request.urlretrieve(pic_raw,'./data/pic_raw'+'.jpg')
			call(['convert','-density','300','-define', 'trim:percent-background=2%','-trim','+repage','-background', 'white', '-alpha', 'remove', '-alpha', 'off','./data/pic_raw.jpg','./data/tweet_pic.png'])

		
	elif journal == "Arxiv Optics":
		makedirs('./data/',exist_ok=True)
		urllib.request.urlretrieve(raw.replace('abs','e-print'),'source')
		if isdir('./data/'):
			rmtree('./data/')
		makedirs('./data/',exist_ok=True)
		try:	
			patoolib.extract_archive("source", outdir="./data/")
		except:
			print('Arxiv: eprint not a zip file, so probably PDF.')
			doc = fitz.open('source')
			img_pgs = []
			for i in range(len(doc)):
				if len(doc.getPageImageList(i)) > 0:
					img_pgs.append(str(i)) # pages with images
			if len(img_pgs) > 0:
				pg_choice = choice(img_pgs)
				call(['convert','-density','150','-define', 'trim:percent-background=2%','-trim','+repage','-background', 'white', '-alpha', 'remove', '-alpha', 'off','./source['+ pg_choice+']','./data/tweet_pic.png'])
				print('Page %s saved as image.' % pg_choice)
			else:
				return False
			
			#return False	
	#	if glob.glob('./data/' + '**/*.tex', recursive=True) !=[]:
		files = glob.glob('./data/' + '**/*.png', recursive=True)
		if files != []:
			picraw = choice(files)
			call(['convert','-density','300','-define', 'trim:percent-background=2%','-trim','+repage','-background', 'white', '-alpha', 'remove', '-alpha', 'off', picraw+'[0]','./data/tweet_pic.png'])
			return True
		else:
			otherfiles = glob.glob('./data/' + '**/*.pdf', recursive=True) + glob.glob('./data/' + '**/*.eps', recursive=True) + glob.glob('./data/' + '**/*.ps', recursive=True)
			if otherfiles != []:
				picraw = choice(otherfiles)
				call(['convert','-density','300','-define', 'trim:percent-background=2%','-trim','+repage','-background', 'white', '-alpha', 'remove', '-alpha', 'off', picraw+'[0]','./data/tweet_pic.png'])
				return True
			else:
				return False		
	
	if isfile('./data/tweet_pic.png'):
		return True
	else:
		return False

def compute_proba(titles):
	vectorizer = HashingVectorizer(ngram_range=(1, 3))
	
	titles = pd.DataFrame(titles,columns=['title','link','journal_name','abstract'])
	titles['abstract'] = [re.sub(r'^(.*?)<br\/>','',str(s)) for s in titles['abstract']] # remove all text up to and including <br\>
	titles['title'] = [re.sub(r'\[[^\[\]]*\]','',str(s)).strip() for s in titles['title']] # remove all text within [] brackets
	titles['abstract'] = [re.sub(r'\[[^\[\]]*\]','',str(s)) for s in titles['abstract']] # remove all text within [] brackets
	titles['abstract'] = [strip_html(s) for s in titles['abstract']]
	titles['text'] = [normalize_text(re.sub(r'\([^()]*\)', '', str(s))) for s in titles['title']+' '+titles['abstract']] 
	X_test = vectorizer.fit_transform(titles['text'])
	clf = joblib.load('new_trained_model.pkl')
	
	pred = clf.predict_proba(X_test)
	#arr = np.empty((np.size(titles,0),4),dtype=object)
	arr = [None] * 5
	arr[0] = titles['title'][0]
	arr[1] = titles['link'][0]
	arr[2] = titles['journal_name'][0]
	arr[3] = titles['abstract'][0]
	arr[4] = float(pred[:,1])
	return arr
	

def tweet_post(line,image_flag):
	auth = tweepy.OAuthHandler(environ['TWITTER_CONSUMER_KEY'], environ['TWITTER_CONSUMER_SECRET'])
	auth.set_access_token(environ['TWITTER_ACCESS_TOKEN'], environ['TWITTER_ACCESS_SECRET'])
	api = tweepy.API(auth,retry_count=10, retry_delay=5, retry_errors=set([503]))	
	try:
		if image_flag == False:
			api.update_status(line)
			sleep(30*60) 
			return True
		else:
			try:
				api.update_with_media('./data/tweet_pic.png',line)
			except:
				api.update_status(line)
			sleep(30*60) 
			return True
	except tweepy.TweepError as e:
		print(e.args[0][0]['message'])
		return False

#def shorten_link(link):
#	b = bitly_api.Connection(API_USER, API_KEY)
#	response = b.shorten(link)
#	return response['url']
		
def retweet_old(number):
	auth = tweepy.OAuthHandler(environ['TWITTER_CONSUMER_KEY'], environ['TWITTER_CONSUMER_SECRET'])
	auth.set_access_token(environ['TWITTER_ACCESS_TOKEN'], environ['TWITTER_ACCESS_SECRET'])
	api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True,retry_count=10, retry_delay=15, retry_errors=set([503]))
	tweets = []
	# retweeting tweets
	tweets = api.user_timeline(count = 200)
	
	for i in range(number):
		while 1:
			tweet = choice(tweets)
			if tweet.retweeted == False:
				break
		try:
			api.retweet(tweet.id)
			sleep(30*60)	
		except:
			pass
	return 	
	