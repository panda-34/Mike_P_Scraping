import time, re, csv
from itertools import count
from urllib.parse import urlsplit, parse_qs

from bs4 import BeautifulSoup
import requests

#import requests_cache
#requests_cache.install_cache(allowable_methods=('GET', 'POST'), allowable_codes=(200, 404, 500))

class Crawler:
	def __init__(self):
		self.session = requests.Session()
		self.session.headers.update((
			('User-Agent', 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.94 Safari/537.36'),
			('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8'),
			('Accept-Language', 'en-US,en;q=0.8'),
		))
		self.url = None

	def get(self, url, data=None):
		self.url = url
		for i_try in count(1):
			try:
				if data:
					resp = self.session.post(url, data=data, verify=False, timeout=30)
				else:
					resp = self.session.get(url, verify=False, timeout=30)
				if resp.status_code == 500:
					print('Server error')
					print(url)
					return None
				if resp.status_code == 404:
					return None
				resp.raise_for_status()
				return BeautifulSoup(resp.text, 'lxml')
			except requests.RequestException as e:
				print(url)
				print(e)
			time.sleep(min(2**i_try, 3600))

	def main(self):
		re_code = re.compile('\((.*?)\)$').search
		seen = set()
		with open('header.csv', newline='', encoding='utf_8_sig') as f_in, open('marketwatch.csv', 'w', newline='', encoding='utf_8_sig') as f_out:
			writer = csv.DictWriter(f_out, ('Ticker', 'Description', 'Address', 'Phone', 'Revenue', 'Employees', 'Link'))
			writer.writeheader()
			for row in csv.DictReader(f_in):
				ticker = re_code(row['About'])
				if ticker is None:
					continue
				ticker = ticker.group(1)
				code = ticker.lower()
				if code in seen:
					continue
				seen.add(code)
				row = {'Ticker': ticker}
				soup = self.get(f'https://www.marketwatch.com/investing/stock/{code}/profile')
				if soup is not None:
					el = soup.select_one('div.full')
					if el:
						row['Description'] = el.get_text('\n', strip=True).strip()
					sect = soup.find('h2', string='At a Glance')
					if sect is not None:
						sect = sect.parent
						el = sect.select_one('p.companyname')
						if el is not None:
							s = []
							for p in el.find_next_siblings('p'):
								s.append(p.get_text(strip=True))
							row['Address'] = '\n'.join(filter(None, s))
						for field in ('Phone', 'Revenue', 'Employees'):
							el = sect.find('p', class_='column', string=field)
							if el is not None:
								row[field] = el.find_next_sibling('p').string.strip()
				soup = self.get(f'https://finance.google.com/finance?q={code}')
				el = soup.select_one('a#fs-chome')
				if el is not None:
					row['Link'] = parse_qs(urlsplit(el['href']).query)['q'][0]
				writer.writerow(row)

if __name__ == '__main__':
	requests.packages.urllib3.disable_warnings()
	try:
		c = Crawler()
		c.main()
	except Exception:
		print()
		print(c.url)
		raise
