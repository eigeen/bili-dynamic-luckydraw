#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import re
import sqlite3
import time

import requests

from ..globals import *


# 获取时间
def now_time(type=0):  # Type0 FullTime  Type1 InFileName
    if type == 0:
        t = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    elif type == 1:
        t = time.strftime("%Y%m%d-%H%M%S", time.localtime())
    else:
        t = None
    return t


# 爬虫核心
class Scraper(object):
    def __init__(self, dyn_id):
        self.time = now_time(type=1)
        self.dynamic_id = dyn_id

    def scrape(self):
        count = 0
        offset = 0
        total_num = -1
        conn = sqlite3.connect(db_path_)
        cursor = conn.cursor()
        dynamic_api = "https://api.live.bilibili.com/dynamic_repost/v1/dynamic_repost/view_repost"
        header = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) \
                        AppleWebKit/537.36 (KHTML, like Gecko) \
                        Chrome/89.0.4386.0 Safari/537.36 Edg/89.0.767.0',
            'd': '1',
            'origin': 'https://space.bilibili.com',
            'referer': 'https://space.bilibili.com/',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site'
        }

        self.time = now_time(type=1)
        while offset < total_num or total_num == -1:  # 数据获取
            # try:
            param = {'dynamic_id': self.dynamic_id, 'offset': offset}
            response = requests.get(dynamic_api, headers=header, params=param, timeout=10)
            resp_json = json.loads(response.text)
            if total_num == -1:  # 初始化
                total_num = resp_json['data']['total_count']
                print("总转发人数：" + str(total_num))
                # up_name = resp_json['data']['comments'][0]['detail']['desc']['origin'][
                #     'user_profile']['info']['uname']
                up_name = "Unknown"

                # 数据库初始化
                cursor.execute('''CREATE TABLE Reposts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                        uid INT NOT NULL,
                        user_name TEXT NOT NULL,
                        comment TEXT NOT NULL,
                        timestamp INT NOT NULL
                    )''')
                cursor.execute('''CREATE TABLE RepostHeaders (
                        time INT NOT NULL,
                        up_name TEXT NOT NULL,
                        dynamic_id INT NOT NULL,
                        total_count INT NOT NULL
                    )''')
                cursor.execute('''INSERT INTO RepostHeaders (time, up_name, dynamic_id, total_count) 
                    VALUES ('{}', '{}', '{}', '{}')'''.format(self.time, up_name, self.dynamic_id, total_num))

            # except Exception:
            #     print("出现错误，程序中断")
            #     print(response.text[:200])
            #     return

            for tmp_num in range(0, 20):  # 数据写入数据库
                # try:
                if count < total_num:
                    count += 1
                    uid = resp_json['data']['comments'][tmp_num]['uid']
                    user_name = resp_json['data']['comments'][tmp_num]['uname']
                    comment = resp_json['data']['comments'][tmp_num]['comment']
                    card = resp_json['data']['comments'][tmp_num]['detail']['card']
                    timestamp = re.findall(r"timestamp.*?(\d+)", card)[0]
                    cursor.execute('''INSERT INTO Reposts 
                        VALUES(NULL, '{}', '{}', '{}', '{}')'''.format(uid, user_name, comment, timestamp))
                else:
                    break
            # except:
            #     print("Error when collecting data.")
            #     return
            offset += 20
        conn.commit()
        conn.close()
