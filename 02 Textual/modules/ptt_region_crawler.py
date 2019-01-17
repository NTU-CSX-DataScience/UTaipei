from bs4 import BeautifulSoup
import pandas as pd
import requests
import re
import time

def get_post_num(region, date, verbose=True, init_index=None, return_index=False):
	date_timestamp = pd.Timestamp(date)
	max_index = get_max_index(region)

	if init_index is None:
		i = max_index
		current_year = pd.Timestamp.today().year
	else:
		i = init_index
		current_year = get_page_year(region, init_index)

	if verbose == True:
		print_target_info(region, date)
	
	target_post_num = 0
	is_year_crossed = False
	
	while i > 0:
		posts_soup = get_posts_soup(region, i)
		(first_post_timestamp, last_post_timestamp) = get_first_last_timestamp(posts_soup, current_year)
		page_info = (i, max_index, first_post_timestamp, last_post_timestamp)

		(posts_soup, is_year_crossed) = solve_special_case(posts_soup, page_info)
		year_info = get_page_year_info(posts_soup, current_year, is_year_crossed)
		(first_post_timestamp, last_post_timestamp) = get_first_last_timestamp(posts_soup, year_info[0])
		
		if verbose == True:
			print_current_stage(region, i, year_info)

		if date_timestamp < first_post_timestamp:
			pass
		elif date_timestamp == first_post_timestamp:
			target_post_num += count_post(posts_soup, date_timestamp, year_info)
		else:
			target_post_num += count_post(posts_soup, date_timestamp, year_info)
			break

		i -= 1
		if is_year_crossed:
			current_year -= 1
			is_year_crossed = False			

	if return_index == True:
		return (target_post_num, i)
	else:	
		return target_post_num



### Auxiliary functions ###

# general function in return of BeautifulSoup object
def get_soup(url, n_try=10, wait=10): 
	for i in range(n_try):
		try:
			page = requests.get(url)
			soup = BeautifulSoup(page.text, 'lxml')
			return soup
		except Exception as e:
			incident = e
			time.sleep(wait)
			continue
	print(repr(e))
	return None

# get BeautifulSoup object for ptt pages
def get_page_soup(site, index = ''): 
	url_format = "https://www.ptt.cc/bbs/%s/index%s.html"
	page_url = url_format%(site, str(index))
	soup = get_soup(page_url)
	return soup

# get BeautifulSoup object for ptt posts in the ptt page
def get_posts_soup(site, index): 
	posts_soup = get_page_soup(site, index).find_all('div', {'class':'r-ent'})
	return posts_soup

# get the maximum index for the ptt block
def get_max_index(site, n_try = 10, wait = 10): 
	for i in range(n_try):
		try:
			previous_page_url = get_page_soup(site).find('a', string='‹ 上頁')['href']
			pattern = re.compile('\d+')
			max_index = int(pattern.search(previous_page_url).group(0))+1
			return max_index
		except Exception as e:
			incident = e
			time.sleep(wait)
			continue
	print(repr(incident))
	return None


def get_ymd(year, date):
	return str(year) +'/'+ date

def get_timestamp(year=None, date=None, ymd=None):
	if ymd is None:
		return pd.Timestamp(get_ymd(year, date))
	else:
		return pd.Timestamp(ymd)

def get_page_year(site, index, n_try=10, wait=10):
	soup_correctly_fetched = False
	for i in range(n_try):
		try:
			posts_soup = get_posts_soup(site, index)
			_ = (e for e in posts_soup)
			soup_correctly_fetched = True
			break
		except Exception as e:
			incident = e
			time.sleep(wait)
			continue

	if soup_correctly_fetched:
		for post in posts_soup[::-1]:
			try:
				post_url = 'https://www.ptt.cc' + post.find('a')['href']
				post_soup = get_soup(post_url)
				article_metalines = post_soup.find('div', {'id':'main-content'}).find_all('div', {'class':'article-metaline'})
				post_year_string = article_metalines[2].find('span', {'class':'article-meta-value'}).string
				year = int(post_year_string.split(' ')[-1])
			except Exception as e:
				continue
			else:
				return year
	else:
		print(repr(incident))
	
	return None


### Internal functions ###  Not recommended to use them alone.

def get_first_last_timestamp(posts_soup, year):
	first_post_date = get_post_date(posts_soup[0])
	last_post_date = get_post_date(posts_soup[-1])
	
	if isinstance(year, int):
		return (get_timestamp(year, first_post_date), get_timestamp(year, last_post_date))
	if isinstance(year, tuple):
		return (get_timestamp(year[0], first_post_date), get_timestamp(year[1], last_post_date))

def solve_special_case(posts_soup, page_info):
	(current_index, max_index, first_timestamp, last_timestamp) = page_info
	if check_year_crossed(first_timestamp, last_timestamp) == True:
		if check_latest_page(current_index, max_index) == True:
			crossed_index = get_page_cross_index(posts_soup)
			posts_soup = posts_soup[:crossed_index]
			is_year_crossed = False
		else:
			is_year_crossed = True
	else:
		is_year_crossed = False

	return (posts_soup, is_year_crossed)

def get_page_year_info(posts_soup, current_year, is_year_crossed):
	if not is_year_crossed:
		return (current_year, None)
	else:
		last_year = current_year -1
		years = (last_year, current_year)
		return (years, get_page_cross_index(posts_soup))

def print_target_info(region, date):
	print("\n[[ %s, %s ]]"%(region, str(date)))
	print("=====")

def print_current_stage(region, index, year_info):
	url_format = "https://www.ptt.cc/bbs/%s/index%s.html"
	print("Crawling| %s | %s |:>> %s"%(region, str(index), url_format%(region, str(index))))
	print("     ...| year_info", year_info)


def count_post(posts_soup, target_time, year_info):
	(year, crossed_index) = year_info

	if crossed_index is None:
		date_list = [get_timestamp(year, get_post_date(i)) for i in posts_soup] 
	else:
		early_year_date_list = [get_timestamp(year[0], get_post_date(i)) for i in posts_soup[:crossed_index]]
		latter_year_date_list = [get_timestamp(year[1], get_post_date(i)) for i in posts_soup[crossed_index:]]
		date_list = early_year_date_list + latter_year_date_list
	
	return date_list.count(target_time)

def check_latest_page(current_index, max_index):
	if current_index == max_index:
		return True
	else: 
		return False

def check_year_crossed(first_timestamp, last_timestamp):
	if first_timestamp > last_timestamp:
		return True
	else:
		return False

def get_page_cross_index(posts_soup):
	test_year = 2018
	date_list = [get_timestamp(test_year, get_post_date(i)) for i in posts_soup]
	for i in range(len(date_list)-1):
		if date_list[i] > date_list[i+1]:
			return i+1
	return None

def get_post_date(post_soup):
	post_meta = post_soup.find('div', {'class':'meta'})
	post_date = post_meta.find('div', {'class':'date'}).string.strip()
	return post_date




