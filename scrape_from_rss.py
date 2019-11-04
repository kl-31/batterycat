import feedparser
import csv
#import string
from unidecode import unidecode
import json
from os.path import isfile
import helpers
import datetime
import re

if isfile('feed_info.txt'):
	feed_info = json.load(open("feed_info.txt"))
else:
	feed_info = {
			'jes': 
				{'name':'Journal of The Electrochemical Society', 
				 'path': 'http://jes.ecsdl.org/cgi/collection/rss?journal_coll_id=A',
				 'etag':''},
			 'jps':
				 {'name': 'Journal of Power Sources',
				'path': 'http://rss.sciencedirect.com/publication/science/03787753',
				  'etag': ''},
			  'ea':
				  {'name':'Electrochimica Acta',
				   'path': 'http://rss.sciencedirect.com/publication/science/00134686',
				   'etag': ''},
			'jec':
				{'name': 'Journal of Electroanalytical Chemistry',
					 'path': 'http://rss.sciencedirect.com/publication/science/15726657',
					 'etag': ''},
				'nenergy':
					{'name': 'Nature Energy',
					  'path': 'http://feeds.nature.com/nenergy/rss/current',
					  'etag': ''},
				'ees':
					{'name': 'Energy & Environment Science',
					  'path': 'http://feeds.rsc.org/rss/ee',
					  'etag': ''},
				'joule':
					{'name': 'Joule',
						'path': 'http://www.cell.com/joule/inpress.rss',
						'etag': ''},
				'esm':
					{'name': 'Energy Storage Materials',
						  'path': 'http://rss.sciencedirect.com/publication/science/24058297',
						  'etag': ''},
					'aem':
					{'name': 'Advanced Energy Materials',
						  'path': 'https://onlinelibrary.wiley.com/feed/16146840/most-recent',
						  'etag': ''},
					'acs':
					{'name': 'ACS Energy Letters',
						  'path': 'http://feeds.feedburner.com/acs/aelccp',
						  'etag': ''},
					  'bs':
					{'name': 'Batteries & Supercaps',
						  'path': 'https://onlinelibrary.wiley.com/feed/25666223/most-recent',
						  'etag': ''},
					  'jestor':
					{'name': 'Journal of Energy Storage', #this journal has no scrapable image
						  'path': 'http://rss.sciencedirect.com/publication/science/2352152X',
						  'etag': ''},					
					  'chemrxiv':
					{'name': 'ChemRxiv',
						  'path': 'https://chemrxiv.org/rss/portal_category/chemrxiv/1948',
						  'etag': ''},					
					  'nanoenergy':
					{'name': 'Nano Energy',
						  'path': 'http://rss.sciencedirect.com/publication/science/22112855',
						  'etag': ''},
					  'jmca':
					{'name': 'JMCA',
						  'path': 'http://feeds.rsc.org/rss/ta',
						  'etag': ''},
					  'chemistry':
					{'name': 'Chemistry of Materials',
						  'path': 'http://feeds.feedburner.com/acs/cmatex',
						  'etag': ''},
					  'acsami':
					{'name': 'ACS Applied Materials',
						  'path': 'http://feeds.feedburner.com/acs/aamick',
						  'etag': ''}									
					}

written = 0
posted = 0
titles_list = helpers.get_titles_db()
#twit_handles = helpers.pull_handles_from_twitter(['rita_strack','joachimgoedhart'])

#with open('batterycat_rss_proba_samples.csv', mode='w') as data_file:
#	writer = csv.writer(data_file, delimiter=',')
for feed in feed_info.keys():	
	print(feed)
	feed_name = feed_info[feed]['name']
	feed_path = feed_info[feed]['path']
	feed_rss = feedparser.parse(feed_path)
	for i in range(len(feed_rss.entries)):
		entry = feed_rss.entries[i]
		if feed_name == 'Journal of The Electrochemical Society': # for each journal, there is a raw source/link from which image can be pulled.
			image_raw = entry.link
			if 'authors' in entry:
				authors_raw = entry.authors
			elif 'author' in entry:
				authors_raw = entry.author
			else:
				authors_raw = ''
		elif feed_name in ['Journal of Power Sources','Electrochimica Acta','Journal of Electroanalytical Chemistry','Energy Storage Materials',
					 'ACS Energy Letters','Nano Energy','Chemistry of Materials','ACS Applied Materials']:
			image_raw = entry.summary
			if 'authors' in entry:
				authors_raw = entry.authors
			elif 'author' in entry:
				authors_raw = entry.author
			else:
				authors_raw = ''
		elif feed_name in ['Energy & Environment Science', 'JMCA']: 
			image_raw = entry
			if 'authors' in entry:
				authors_raw = entry.authors
			elif 'author' in entry:
				authors_raw = entry.author
			else:
				authors_raw = ''
		elif feed_name == 'Joule':
			image_raw = entry.link
			if 'authors' in entry:
				authors_raw = entry.authors
			elif 'author' in entry:
				authors_raw = entry.author
			else:
				authors_raw = ''
		elif feed_name in ['Advanced Energy Materials','Batteries & Supercaps']:
			image_raw = entry.content[0].value
			authors_raw = entry.link # scrape authors from html
		else:
			image_raw = ''
			if 'authors' in entry:
				authors_raw = entry.authors
			elif 'author' in entry:
				authors_raw = entry.author
			else:
				authors_raw = ''
		abstract = unidecode(entry.summary.replace('\n',' '))
		row = [[unidecode(entry.title), entry.link, feed_name, abstract ]] 
		if re.sub(r'\[[^\[\]]*\]','',str(row[0][0])).strip().lower() not in titles_list:  # remove [text]
			proba_out = helpers.compute_proba(row)
				#print(proba_out)
			helpers.write_to_db(proba_out)
			#writer.writerow(proba_out)
			written = written + 1
#			if feed_name == 'Biomedical Optics Express' or feed_name == 'Journal of Biophotonics':
#				#handles = helpers.get_author_handles(authors_raw,feed_name,twit_handles)
#				if helpers.tweet_post('%s %s #biophotonics #biomedicaloptics' % (entry.title, entry.link),helpers.scrape_image(image_raw,feed_name)):
#						posted = posted + 1			
			if proba_out[-1] >=0.5:
				#handles = helpers.get_author_handles(authors_raw,feed_name,twit_handles)
				if helpers.tweet_post('%s (relevance: %.0f%%) %s #battchat #batterytwitter' % (proba_out[0], proba_out[-1]* 100,entry.link),helpers.scrape_image(image_raw,feed_name)):
						posted = posted + 1

				
		if posted >=23: # 22 hours elapsed  
		   break
	if posted >=23: # 22 hours elapsed  
		break
print('%d rows written.' % written)
print('%d tweets posted.' % posted)

#while datetime.datetime.today().weekday()==5 or datetime.datetime.today().weekday()==6:
if posted < 23:
	helpers.retweet_old(23-posted)
