import time, random, csv
from itertools import count, cycle, product
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
import html2text

DEBUG = False
if DEBUG:
	#from collections import Counter
	import requests_cache
	from scrape_utils import DbCacheOptimized

class DummyWith:
	def __enter__(self):
		return
	def __exit__(self, *args):
		return

class Crawler:
	def __init__(self):
		self.base_url = 'https://seekingalpha.com/'
		self.session = requests_cache.CachedSession(backend=DbCacheOptimized()) if DEBUG else requests.Session()
		self.session.headers.update((
			('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8'),
			('Accept-Language', 'en-US,en;q=0.9'),
		))
		self.url = None
		agents = '''
Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.0; Trident/5.0;  Trident/5.0)
Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0;  Trident/5.0)
Mozilla/5.0 (Windows NT 6.1; Trident/7.0; rv:11.0) like Gecko
Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko
Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko
Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; Touch; rv:11.0) like Gecko
Mozilla/5.0 (iPad; CPU OS 11_1_2 like Mac OS X) AppleWebKit/604.3.5 (KHTML, like Gecko) Version/11.0 Mobile/15B202 Safari/604.1
Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_3) AppleWebKit/600.5.17 (KHTML, like Gecko) Version/8.0.5 Safari/600.5.17
Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/603.3.8 (KHTML, like Gecko) Version/10.1.2 Safari/603.3.8
Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/604.3.5 (KHTML, like Gecko) Version/11.0.1 Safari/604.3.5
Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/604.4.7 (KHTML, like Gecko) Version/11.0.2 Safari/604.4.7
Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_5) AppleWebKit/603.2.4 (KHTML, like Gecko) Version/10.1.1 Safari/603.2.4
Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/603.3.8 (KHTML, like Gecko) Version/10.1.2 Safari/603.3.8
Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/604.3.5 (KHTML, like Gecko) Version/11.0.1 Safari/604.3.5
Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/604.4.7 (KHTML, like Gecko) Version/11.0.2 Safari/604.4.7
Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Safari/604.1.38
Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_1) AppleWebKit/604.3.5 (KHTML, like Gecko) Version/11.0.1 Safari/604.3.5
Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_2) AppleWebKit/604.4.7 (KHTML, like Gecko) Version/11.0.2 Safari/604.4.7
Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/62.0.3202.94 Chrome/62.0.3202.94 Safari/537.36
Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.79 Safari/537.36 Edge/14.14393
Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36 Edge/15.15063
Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36 Edge/16.16299
Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.89 Safari/537.36 OPR/49.0.2725.47
'''.strip().splitlines()
		oss = '''
Windows NT 5.1
Windows NT 5.1; WOW64
Windows NT 5.1; Win64; x64
Windows NT 6.1
Windows NT 6.1; WOW64
Windows NT 6.1; Win64; x64
Windows NT 6.2
Windows NT 6.2; WOW64
Windows NT 6.2; Win64; x64
Windows NT 6.3
Windows NT 6.3; WOW64
Windows NT 6.3; Win64; x64
Windows NT 10.0
Windows NT 10.0; WOW64
Windows NT 10.0; Win64; x64
X11; Linux i686
X11; Linux i686 on x86_64
X11; Linux x86_64
X11; Fedora; Linux i686
X11; Fedora; Linux i686 on x86_64
X11; Fedora; Linux x86_64
X11; Ubuntu; Linux i686
X11; Ubuntu; Linux i686 on x86_64
X11; Ubuntu; Linux x86_64
'''.strip().splitlines()
		macoss = '''
Macintosh; Intel Mac OS X 10.8
Macintosh; Intel Mac OS X 10.9
Macintosh; Intel Mac OS X 10.10
Macintosh; Intel Mac OS X 10.11
Macintosh; Intel Mac OS X 10.12
Macintosh; Intel Mac OS X 10.13
'''.strip().splitlines()
		browsers = ['%.1f' % x for x in range(45, 59)]
		agents.extend(f'Mozilla/5.0 ({os}; rv:{browser}) Gecko/20100101 Firefox/{browser}' for os, browser in product(oss+macoss, browsers))
		macoss = '''
Macintosh; Intel Mac OS X 10_10_3
Macintosh; Intel Mac OS X 10_10_5
Macintosh; Intel Mac OS X 10_11_6
Macintosh; Intel Mac OS X 10_12_5
Macintosh; Intel Mac OS X 10_12_6
Macintosh; Intel Mac OS X 10_13_0
Macintosh; Intel Mac OS X 10_13_1
Macintosh; Intel Mac OS X 10_13_2
'''.strip().splitlines()
		browsers = '''
51.0.2704.79
51.0.2704.106
52.0.2743.116
58.0.3029.110
61.0.3163.100
62.0.3202.62
62.0.3202.75
62.0.3202.89
62.0.3202.94
63.0.3239.84
63.0.3239.108
'''.strip().splitlines()
		agents.extend(f'Mozilla/5.0 ({os}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{browser} Safari/537.36' for os, browser in product(oss+macoss, browsers))
##		if DEBUG:
##			self.agents_use = Counter()
##			for agent in agents:
##				self.agents_use[agent] = 0
##			with open('agents_use.csv', newline='') as f:
##				for agent, cnt in csv.reader(f):
##					self.agents_use[agent] = int(cnt)
		random.shuffle(agents)
		self.agents = cycle(agents)

	def next_agent(self):
		self.session.headers['User-Agent'] = next(self.agents)
		self.session.cookies.clear()

	def get(self, url):
		self.url = url = urljoin(self.base_url, url)
		for i_try in count(1):
			try:
				self.next_agent()
				resp = self.session.get(url, verify=False, timeout=60)
				if resp.status_code == 404:
					print('\nNot found')
					print(url)
					return None
				resp.raise_for_status()
				if not (DEBUG and resp.from_cache):
##					if DEBUG:
##						self.agents_use[self.session.headers['User-Agent']] += 1
					print(' ', i_try, sep='', end='', flush=True)
					#time.sleep(random.uniform(11, 19))
				return BeautifulSoup(resp.text, 'html.parser')
			except Exception as e:
				if i_try > 10:
					print()
					print(e)
				time.sleep(min(2**i_try, 3600))#random.uniform(10, 18)+

	def main(self):
		seen = set()
		h2t = html2text.HTML2Text()
		h2t.unicode_snob = True
		h2t.ignore_images = True
		h2t.ignore_links = True
		h2t.ignore_emphasis = True
		h2t.single_line_break = True
		h2t.body_width = 0

		with open('seekingalpha.csv', 'w', newline='', encoding='utf_8_sig') as f:
			writer = csv.writer(f)
			writer.writerow(('URL', 'Title', 'Date', 'About', 'Text Length', 'Text'))
			main_url = 'https://seekingalpha.com/earnings/earnings-call-transcripts'
			for page_no in count(1):
				print('page', page_no, end='')
				old_time = time.time()
				with self.session.cache if DEBUG else DummyWith():
					main_soup = self.get(main_url)
					for item in main_soup.find('ul', class_='sa-base-article-list')('li', recursive=False):
						url = urljoin(self.base_url, item.a['href'])
						if url in seen:
							continue
						seen.add(url)
						soup = self.get(url)
						if soup is None:
							continue
						soup = soup.find('div', id='content-rail')
						text = []
						for p in soup.find('div', id='a-body').children:
							if p.name == 'p' and p.find('strong', string='Copyright policy: '):
								break
							text.append(str(p))
						text = h2t.handle(''.join(text))
						soup = soup.find('div', id='a-hd')
						about = soup.find('span', string='About:')
						writer.writerow((
							url,
							soup.find('h1', itemprop='headline').get_text(strip=True),
							soup.find('time', itemprop='datePublished')['content'],
							about and about.find_next_sibling('span').get_text(strip=True),
							len(text),
							text
						))
				a = main_soup.find('a', string='Next Page')
				if not a:
					break
				main_url = a['href']
				print(' %ds' % (time.time() - old_time))

if __name__ == '__main__':
	requests.packages.urllib3.disable_warnings()
	try:
		c = Crawler()
		c.main()
	except Exception:
		print()
		print(c.url)
		raise
##	finally:
##		if DEBUG:
##			with open('agents_use.csv', 'w', newline='') as f:
##				csv.writer(f).writerows(c.agents_use.items())
