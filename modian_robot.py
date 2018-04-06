#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import requests
import time
import hashlib
import urllib.parse

def md5(str):
    hl = hashlib.md5()
    hl.update(str.encode(encoding='utf-8'))
    return hl.hexdigest()

class Robot(object):

    def __init__(self, host, port, receivers):
        self.host = host
        self.port = port
        self.receivers = receivers

    def run(self, interval):
        while True:
            time.sleep(interval)
            for receiver in self.receivers:
                messages = receiver.get_messages()
                if messages:
                    self.send(receiver.qqs, messages)

    def send(self, qqs, messages):
        for msg in messages:
            print(msg)
            for qq in qqs:
                self.send_group_msg(qq, msg)

    def send_group_msg(self, qq, message):
        # send to coolq http server
        url = 'http://' + host + ':' + port + '/send_group_msg'
        data = {
            'group_id': qq, 
            'message': message
        }
        try:
            response = requests.post(url, data=data)
            response = response.json()
            if response['retcode'] != '0':
                print("消息发送失败: " + qq)
        except:
            print("send_group_msg api error: " + qq)


class Receiver(object):

    def __init__(self, qqs, main_project, other_projects, template):
        self.qqs = qqs
        self.main_project = main_project
        self.other_projects = other_projects
        self.template = template

    def get_messages(self):
        if self.main_project.update(is_get_rankings=True):
            for project in self.other_projects:
                project.update(is_get_rankings=False)
            return self.template(self.main_project, self.other_projects)
        return None


class Project(object):
    
    def __init__(self, id):
        self.id = id
        self.detail = self.get_detail()
        print(self.detail)
        self.new_orders = []
        self.user_money = {}
        self.user_days ={}

    def update(self, is_get_rankings):
        detail = self.get_detail()
        print(detail['already_raised'])
        if detail and detail['already_raised'] > self.detail['already_raised']:
            if is_get_rankings:
                diff = round(detail['already_raised'] - self.detail['already_raised'], 2)
                self.new_orders = self.get_new_orders(diff)
                self.user_money = self.get_user_money()
                self.user_days = self.get_user_days()
            self.detail = detail
            return True
        else:
            return False

    def get_detail(self):
        url = 'https://wds.modian.com/api/project/detail'
        params = {
            'pro_id': self.id
        }
        return self.post_api(url, params)[0]

    def get_orders(self, page=1):
        url = 'https://wds.modian.com/api/project/orders'
        params = {
            'page': page,
            'pro_id': self.id
        }
        return self.post_api(url, params)

    def get_new_orders(self, diff):
        new_orders = []
        amount = 0
        page = 1
        while amount < diff:
            orders = self.get_orders(page)
            for order in orders:
                amount += order['backer_money']
                if amount <= diff:
                    new_orders.append(order)
                else:
                    return new_orders
            page += 1
        return new_orders

    def get_rankings(self, type, page=1):
        url = 'https://wds.modian.com/api/project/rankings'
        params = {
            'page': page,
            'pro_id': self.id,
            'type': type
        }
        return self.post_api(url, params)

    def get_user_rankings(self, type, pages=5):
        user_rankings = {}
        for p in range(1, pages):
            rankings = self.get_rankings(type, p)
            if rankings == None:
                break
            for ranking in rankings:
                user = ranking['nickname']
                user_rankings[user] = ranking
        return user_rankings

    def get_user_money(self):
        return self.get_user_rankings(type=1)

    def get_user_days(self):
        return self.get_user_rankings(type=2)

    def sign(self, params):
        url_str = urllib.parse.urlencode(params) + '&p=das41aq6'
        md5_str = md5(url_str)
        return md5_str[5:21]

    def post_api(self, url, params):
        data = params.copy()
        data['sign'] = self.sign(params)
        try:
            headers={'Accepat':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8','Accept-Language':'en-US,en;q=0.8,zh-CN;q=0.6,zh;q=0.4','User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36'}
            response = requests.post(url, headers=headers, data=data, timeout=10)
            response = response.json()
            if response['status'] == '0':
                return response['data']
            else:
                return None
        except:
            print("api error: " + url)
            return None
