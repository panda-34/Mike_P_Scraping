import time, csv
from itertools import count
from contextlib import contextmanager
from urllib.parse import urljoin
import lxml.html

import requests

DEBUG = False
if DEBUG:
	import datetime as dt
	import requests_cache

class Progress:
	def __init__(self):
		self.printed = 0
	def print(self, current, total):
		to_print = round(current / total * 80) - self.printed
		if to_print:
			print('.' * to_print, end='', flush=True)
			self.printed += to_print
		return current < total

def get_text(s):
	return s and lxml.html.document_fromstring(s).text_content()

class Crawler:
	def __init__(self):
		self.session = requests_cache.CachedSession(allowable_methods=('GET', 'POST')) if DEBUG else requests.Session()
		self.session.headers.update((
			('User-Agent', 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.94 Safari/537.36'),
			('Accept', 'application/json, text/plain, */*'),
			('Accept-Language', 'en-US,en;q=0.8'),
		))
		self.url = None
		self.base_url = 'http://ieeexplore.ieee.org/'

	@contextmanager
	def exc_handler(self, i_try):
		try:
			if i_try == 0 or not DEBUG:
				yield
			else:
				old_value = self.session._cache_expire_after
				self.session._cache_expire_after = dt.timedelta(seconds=1)
				try:
					yield
				finally:
					self.session._cache_expire_after = old_value
		except Exception as e:
			print()
			print(self.url)
			print(e)

	def get(self, url, data=None):
		self.url = data or url
		for i_try in count():
			with self.exc_handler(i_try):
				if data is not None:
					resp = self.session.post(url, json=data)
					resp.raise_for_status()
					if i_try > 0 and not resp.content:
						print()
						print(data)
						print('Empty response')
						return None
					return resp.json()
				else:
					resp = self.session.get(url)
					resp.raise_for_status()
					return resp
			time.sleep(min(2**i_try, 3600))

	def main(self):
		for file_name, content_type in (('Conference Publications', '4291944822'),):#, ('Journals & Magazines', '4291944246'), ('Early Access Articles', '4291944245')):
			with open(file_name + '.csv', 'w', newline='', encoding='utf_8_sig') as f:
				writer = csv.writer(f)
				writer.writerow(('Title', 'Year', 'Published In', 'Publisher', 'Authors', 'Abstract', 'Link'))
				req_data = {'refinements': [content_type], 'sortType': 'desc_p_Publication_Year', 'rowsPerPage': '100'}
				url = f'http://ieeexplore.ieee.org/search/searchresult.jsp?refinements={content_type}&sortType=desc_p_Publication_Year&rowsPerPage=100'
				self.get(url)
				self.session.headers['Referer'] = url
				print()
				print(file_name)
				progress = Progress()
				for page_no in count(1):
					if page_no > 1:
						req_data['pageNumber'] = str(page_no)
					js = self.get('http://ieeexplore.ieee.org/rest/search', req_data)
					if js is None:
						continue
					page_len = len(js['records'])
					if page_len != 100:
						print(f'\npage {page_no}: {page_len} records')
					for row in js['records']:
						year = row['publicationYear']
						if int(year) < 2013:
							break
						url = row.get('documentLink', '')
						url = url and urljoin(self.base_url, url)
						published_in = row['displayPublicationTitle']
						s = []
						for k in ('volume', 'issue'):
							v = row.get(k)
							if v:
								s.append(f'{k.capitalize()}: {v}')
						if s:
							published_in += ' (%s)' % ', '.join(s)
						writer.writerow(map(get_text, (
							row.get('title'),
							year,
							published_in,
							row['publisher'],
							'; '.join(x.get('preferredName') or '' for x in row.get('authors', ())),
							row.get('abstract'),
							url
						)))
					else:
						if progress.print(js['endRecord'], js['totalRecords']):
							continue
					break

if __name__ == '__main__':
	requests.packages.urllib3.disable_warnings()
	try:
		c = Crawler()
		c.main()
	except Exception:
		print()
		print(c.url)
		raise
