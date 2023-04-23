#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jan  3 14:20:18 2022

@author: loickreseski
"""

import requests
import json
import pandas as pd
from bs4 import BeautifulSoup as bs
import re
from datetime import timedelta, date, datetime
import pytz
import time
from bs4 import BeautifulSoup
import re





def ads_search(index = 0):
    url = 'https://www.rightmove.co.uk/property-for-sale/find.html?minBedrooms=2&keywords=&sortType=2&viewType=LIST&maxDaysSinceAdded=14&mustHave=garden%2Cparking&channel=BUY&index={}&maxPrice=550000&radius=0.0&locationIdentifier=USERDEFINEDAREA%5E%7B%22polylines%22%3A%22o%7EvyHbtZnlGpVui%40mqFjt%40y%7BDlp%40e_%40mtAecJlpByv%40kl%40euCcgBzi%40k%5Ck%7CGiHoaAw%7DAlT%7EJt%60Hu%7DFrt%40kd%40vcM%7ER%7CpCjxDrzI%22%7D'.format(str(index))
    response = requests.get(url)
    text = response.text
    text = text.replace(';', '')
    pattern = r'window\.jsonModel\s*=\s*(.*?)(;|\n)'
    match = re.search(pattern, text)
    if match:
        json_string = match.group(1).rstrip('</script>')
        print(json_string)
        json_object = json.loads(json_string.replace(';', ':'))
        return json_object
    else:
        print('JSON data not found on page')
        return False
    

def full_list_df(ads_data):
    df = pd.DataFrame()
    resultCount = ads_data['resultCount']
    resultCount = resultCount.replace(',','')
    for i in range (0, int(resultCount), 24):
        ads_data_page = ads_search(index=i)
        if ads_data_page is not False:
            df_page = pd.json_normalize(ads_data_page['properties'])
            df= pd.concat([df, df_page], ignore_index = True, axis = 0)
        else:
            break
    df['listingUpdate.listingUpdateDate'] = pd.to_datetime(df['listingUpdate.listingUpdateDate'])
    df['url'] = "https://www.rightmove.co.uk/properties/" + df["id"].astype(str)
    df = df[["url", "summary", "displayAddress", "propertySubType", "price.amount","bedrooms", "bathrooms", "displaySize", "keywords", "keywordMatchType", "customer.contactTelephone", "initialListingDay", "addedOrReduced", "listingUpdate.listingUpdateDate"]]
    print(df.head(3))

    return df

def process_and_sort_df(df):
    df['listingUpdate.listingUpdateDay'] = pd.to_datetime(df['listingUpdate.listingUpdateDate']).dt.date
    df['listingUpdate.listingUpdateDate']=df['listingUpdate.listingUpdateDate'].dt.tz_localize(None)
    df['initialListingDay'] =  pd.to_datetime(df['firstVisibleDate']).dt.date
    df['requestDayTimestamp'] = pd.to_datetime(datetime.now().strftime('%Y-%m-%d'))
    df = df.sort_values(["listingUpdate.listingUpdateDay","price.amount", "keywordMatchType"], ascending = (False, True, True))
    return df

def get_detailled_information(listing_id):
    url = 'https://www.rightmove.co.uk/properties/{}#/?channel=RES_BUY'.format(str(listing_id))
    response = requests.get(url)
    text = response.text
    text = text.replace(';', '')
    pattern = r'window\.PAGE_MODEL\s*=\s*(.*?)(;|\n)'
    match = re.search(pattern, text)
    if match:
        json_string = match.group(1).rstrip('</script>')
        print(json_string)
        json_object = json.loads(json_string.replace(';', ':'))
        return json_object
    else:
        print('JSON data not found on page')
        return False




df = pd.read_excel('rm_listing.xlsx')
while True:
    try:
        print(datetime.now())
        ads_data = ads_search()
        print(ads_data)
        df_request = full_list_df(ads_data)
        df_request = process_and_sort_df(df_request)
        df = pd.concat([df_request, df], ignore_index = True, axis = 0)
        df = df.drop_duplicates(subset=['url','requestDayTimestamp'])
        df = process_and_sort_df(df)
        df.to_excel('rm_listing.xlsx', index=False)
        time.sleep(60)
    except:
        raise
        print('Error in the process')
        time.sleep(10)
    



