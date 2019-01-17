from bs4 import BeautifulSoup
import pandas as pd
import requests
import re
from urllib.parse import quote


def get_station_info():
	url = "http://e-service.cwb.gov.tw/HistoryDataQuery/QueryDataController.do?command=viewMain&_=1528379589863"
	html = requests.get(url)
	html_remove_end = (html.text).split("</html>")
	html = html_remove_end[0] + html_remove_end[1] + "</html>" 

	soup = BeautifulSoup(html, 'lxml')
	script_string = soup.find_all('script')[-1].string

	remove_char_list = ['\r', '\t', '\n', ' ', '	']
	for i in remove_char_list:
		script_string = script_string.replace(i, '')

	re_result = re.search('stList={.*\]}', script_string)
	exec(re_result.group(0), locals(), globals())
	st_list = stList

	st_code = list(st_list.keys())
	st_name = [i[0] for i in st_list.values()]
	st_name_en = [i[1] for i in st_list.values()]
	st_city = [i[2] for i in st_list.values()]
	station_info = pd.DataFrame({'Code':st_code,
								  'Name':st_name,
								  'Name_En':st_name_en,
								  'City': st_city})
	station_info = station_info[['Code', 'Name', 'Name_En', 'City']]
	return station_info



def get_data(station_info, time, station_name = None, station_code = None):
	url_format = "https://e-service.cwb.gov.tw/HistoryDataQuery/DayDataController.do?command=viewMain&station=%s&stname=%s&datepicker=%s"
	
	if not (station_name is None):
		st_name = get_q_st_name(station_name)
		if not (station_code is None):
			st_code = str(station_code)
		else:
			st_code = station_info[station_info.Name==station_name].Code.iloc[0]
	elif not (station_code is None):
		st_code = str(station_code)
		st_name = get_q_st_name(station_info[station_info.Code==station_code].Name.iloc[0])


	url = url_format%(st_code, st_name, time)
	result = pd.read_html(url)
	table = result[1].drop([0,1])
	table.columns = ["ObsTime", "StnPres", "SeaPres", "Temperature", "TdDewPoint",
					 "RH", "WS", "WD", "WSGust", "WDGust", "Precp", "PrecpHour",
					 "SunShine", "GloblRad", "Visb"]
	return table


def get_q_st_name(station_name):
	q_st_name = quote(station_name)
	output = q_st_name.split('%')
	output = '%25'.join(output)
	return output

def get_city_data(station_info, time, city):
	st_code_name_pair = station_info[station_info.City == city][['Code', 'Name']]
	output_table = pd.DataFrame()
	for index, row in st_code_name_pair.iterrows():
		st_result = get_data(station_info, time, row['Name'],row['Code'])
		st_result['Code'] = row['Code']
		st_result['Name'] = row['Name']
		index_rearranged = ['Code', 'Name']+list(st_result.columns)[:-2]
		st_result = st_result[index_rearranged]
		output_table = pd.concat([output_table, st_result], axis = 0)
	return output_table