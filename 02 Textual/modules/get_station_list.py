import pandas as pd
from bs4 import BeautifulSoup
import requests
import re

url = "http://e-service.cwb.gov.tw/HistoryDataQuery/QueryDataController.do?command=viewMain&_=1528379589863"
html = requests.get(url)
html_remove_end = html.split("</html>")
html = html_remove_end[0] + html_remove_end[1] + "</html>" 

soup = BeautifulSoup(html, 'lxml')
script_string = soup.find_all('script')[-1].string

remove_char_list = ['\r', '\t', '\n', ' ', '	']
for i in remove_char_list:
	script_string = script_string.replace(i, '')

re_result = re.search('stList={.*\]}', script_string)
exec(re_result)
st_list = stList

st_code = list(st_list.keys())
st_name = [i[0] for i in st_list.values()]
st_name_en = [i[1] for i in st_list.values()]
st_city = [i[2] for i in st_list.values()]
station_info = pd.DataFrame({'Code':st_code,
							  'Name':st_name,
							  'Name_En':st_name_en,
							  'City': st_city})
