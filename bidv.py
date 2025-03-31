
import hashlib
import json
import base64
import random
import string
import base64
import json
import os
import hashlib
import time
import uuid
import base64
from datetime import datetime
import re
from lxml import html
import urllib.parse
from bypass_ssl_v3 import get_legacy_session
from urllib.parse import quote
import requests

# requests = get_legacy_session()
class BIDV:
    def __init__(self, username, password, account_number):
        # setting proxy
        with open('proxies.txt', 'r') as file:
            proxy_list = [line.strip() for line in file if line.strip()]
        proxy_list = proxy_list if proxy_list else None
        self.proxy_list = proxy_list
        if self.proxy_list:
            self.proxy_info = random.choice(self.proxy_list)
            proxy_host, proxy_port, username_proxy, password_proxy = self.proxy_info.split(':')
            self.proxies = {
                'http': f'http://{username_proxy}:{password_proxy}@{proxy_host}:{proxy_port}',
            }
        else:
            self.proxies = None

        self.session = get_legacy_session()
        self.is_login = False
        self.file = f'data/{username}.txt'
        self.balance = None
        self.dse_pageId = 0
        self.cookie = ''
        self.token = ''
        self.transactions = []
        self.url = {
            "get_balance": "https://www.bidv.vn/iBank/MainEB.html?transaction=PaymentAccount&method=getMain&_ACTION_MODE=search",
            "getCaptcha": "https://www.bidv.vn/iBank/getCaptcha.html",
            "login": "https://www.bidv.vn/iBank/MainEB.html",
            "getHistories": "https://www.bidv.vn/iBank/MainEB.html?transaction=eBankBackend",
        }

        self.retry_login = 0
        self.retry_captcha = 0
        self.retry_balance = 0
        self.retry_transactions = 0
        if not os.path.exists(self.file):
            self.username = username
            self.password = password
            self.account_number = account_number
            self.cookie = None
            self.save_data()
        else:
            self.parse_data()
            self.username = username
            self.password = password
            self.account_number = account_number

    def save_data(self):
        data = {
            'username': self.username,
            'password': self.password,
            'account_number': self.account_number,
            'cookie': getattr(self, 'cookie', ''),
            'token': getattr(self, 'token', '')
        }
        with open(self.file, 'w') as f:
            json.dump(data, f)

    def parse_data(self):
        with open(self.file, 'r') as f:
            data = json.load(f)
        self.username = data.get('username', '')
        self.password = data.get('password', '')
        self.account_number = data.get('account_number', '')
        self.cookie = data.get('cookie', '')
        self.token = data.get('token', '')
        
    
    def curlGet(self, url):
        # print('curlGet')
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9',
            'Cache-Control': 'max-age=0',
            'Connection': 'keep-alive',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': 'https://www.bidv.vn/iBank/MainEB.html',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 Edg/126.0.0.0',
            'sec-ch-ua': '"Not/A)Brand";v="8", "Chromium";v="126", "Microsoft Edge";v="126"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"'
        }
        # if self.token:
        #     headers['Token'] = self.token

        response = self.session.get(url, headers=headers, allow_redirects=True, proxies=self.proxies)
        try:
            return response.json()
        except:
            response = response.text
            dse_pageId = self.extract_dse_pageId(response)
            if dse_pageId:
                self.dse_pageId = dse_pageId
            # else:
            #     print('error_page',url)
            return response
        return result
    
    def curlPost(self, url, data ,headers = None):
        # print('curlPost')
        if not headers:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0',
                'Accept': '*/*',
                'Accept-Language': 'vi-VN,vi;q=0.8,en-US;q=0.5,en;q=0.3',
                'Accept-Encoding': 'gzip, deflate, br, zstd',
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'RESULT_TYPE': 'JSON',
                'X-Requested-With': 'XMLHttpRequest',
                'Origin': 'https://www.bidv.vn',
                'Connection': 'keep-alive',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-origin',
                'Priority': 'u=0'
            }
            # if self.token:
            #     headers['Token'] = self.token

        response = self.session.post(url, headers=headers, data=data, proxies=self.proxies)
        try:
            return response.json()
        except:
            response = response.text
            dse_pageId = self.extract_dse_pageId(response)
            if dse_pageId:
                self.dse_pageId = dse_pageId
            # else:
            #     print('error_page',url)
            return response
        return result

    def extract_dse_pageId(self,html_content):
        pattern = r'dse_pageId=(\d+)&'
        match = re.search(pattern, html_content)
        return match.group(1) if match else None
    
    def extract_by_pattern(self,html_content,pattern):
        match = re.search(pattern, html_content)
        return match.group(1) if match else None
    
    def identifyCaptcha(self, image):
        payload = {
            'image': image,
            'model': 'bidv_biz'
        }
        headers = {
            'Content-Type':'application/json'
        }
        response = requests.post("http://localhost:19952/captcha/v1", data=json.dumps(payload), headers=headers)
        if response is not None:
            return response.json()
        else:
            return {}

    def solveCaptcha(self):
        url = self.url['getCaptcha']
        for _ in range(3):  # 最多重试三次
            response = self.session.post(url)
            base64_captcha_img = response.text

            result = self.identifyCaptcha(base64_captcha_img)
            
            if 'message' in result and result['message']:
                if len(result['message']) == 6:
                    captcha_value = result['message']
                    return {"status": True, "captcha": captcha_value}
                else:
                    continue  # 重试
            else:
                return {"status": False, "msg": "Error solving captcha", "data": result}

        return {"status": False, "msg": "Error solving captcha", "data": "captcha retry over three times"}
    
    def doLogin(self):
        # self.session = get_legacy_session()
        response = self.curlGet(self.url['login'])

        # 获取当前会话的 cookies
        cookies_jar = self.session.cookies
        # 将 cookies 转换为字典
        cookies_dict = requests.utils.dict_from_cookiejar(cookies_jar)
        # 将字典转换为字符串（格式：key=value; key=value; ...）
        self.cookie = '; '.join([f'{key}={value}' for key, value in cookies_dict.items()])

        _token_login = self.extract_by_pattern(response,r'<input type="hidden" name="_token_login" value="(.*)" />')
        solveCaptcha = self.solveCaptcha()
        if not solveCaptcha["status"]:
                    return solveCaptcha
        captcha_text = solveCaptcha["captcha"]
        payload = 'username='+quote(self.username)+'&password='+quote(self.password)+'&captcha='+quote(captcha_text)+'&transaction=User&method=Login&_token_login='+_token_login
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/png,image/svg+xml,*/*;q=0.8',
            'Accept-Language': 'vi-VN,vi;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': 'null',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Priority': 'u=0, i'
        }
        self.retry_login += 1
        response = self.curlPost(self.url['login'],payload,headers)

        if 'url += arrayPathName[1] +\'/MainEB.html\';' in response:
            response = self.curlGet(self.url['login'])
            if 'Số cif doanh nghiệp:' in response:
                self.retry_login = 0
                self.is_login = True
                self.token = self.extract_by_pattern(response,r'var tokenVar = tokenVar \|\| \'(.*)\';')
                self.save_data()
                return {
                    'code': 200,
                    'success': True,
                    'message': 'Đăng nhập thành công',
                    'data':{
                        'token':self.token
                    }
                }
            else:
                print('get login url fail')
                return {
                    'code': 520,
                    'success': False,
                    'message': "Unknown Error!"
                }
        elif 'Đăng nhập không thành công.' in response:
                return {
                            'code': 404,
                            'success': False,
                            'message': 'Tài khoản không tồn tại hoặc không hợp lệ.',
                            }
        elif 'Tên đăng nhập hoặc mật khẩu không chính xác.' in response:
                return {
                            'code': 444,
                            'success': False,
                            'message': 'Tài khoản hoặc mật khẩu không đúng',
                            }
        elif 'Captcha không chính xác' in response:
                if self.retry_login < 3:
                    self.doLogin()
                else:
                    return {
                        'code': 422,
                        'success': False,
                        'message': 'Mã Tiếp tục không hợp lệ',
                        }
        elif 'Tài khoản của quý khách đã bị khóa' in response:
                return {
                    'code': 449,
                    'success': False,
                    'message': 'Blocked account!'                    
                    }
        else:
            print('do login Unknown Error!')
            return {
                    'code': 520,
                    'success': False,
                    'message': "Unknown Error!"
            }

    def get_balance(self, need_login = False):
        if need_login:
            login = self.doLogin()
            if not login['success']:
                return login

        payload = "keyWord=&currencyDefault=VND&hostUnit=Y&memberUnits=0&take=100&skip=0&page=1&pageSize=100"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'vi-VN,vi;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Cookie': self.cookie,
            'Token': self.token,
            'RESULT_TYPE': 'JSON_GRID',
            'X-Requested-With': 'XMLHttpRequest',
            'Origin': 'https://www.bidv.vn',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin'
        }
        self.retry_balance += 1
        response = self.curlPost(self.url['get_balance'],payload,headers)
        # session time out 或查询中错误
        error_messages = [
            'Bạn đã hết phiên làm việc! Vui lòng đăng nhập lại.',
            'Có lỗi trong quá trình vấn tin tài khoản, xin vui lòng thử lại !'
        ]
        # ensure_ascii=False 直接输出原始的 Unicode 字符
        print('balance response: ' + json.dumps(response, ensure_ascii=False, indent=4))
        if 'errorCode' in response and  response['errorCode'] == 0 and 'responseData' in response:
            for account in response['responseData']['rows']:
                if self.account_number == account['accountNo']:
                    self.retry_balance = 0
                    amount = float(account['availableBalance'].replace(',',''))
                    if amount < 0:
                        return {'code':448,'success': False, 'message': 'Blocked account with negative balances!',
                                'data': {
                                    'balance':amount
                                }
                                }
                    else:
                        return {'code':200,'success': True, 'message': 'Thành công',
                                'data':{
                                    'account_number':self.account_number,
                                    'balance':amount
                        }}
            return {'code':404,'success': False, 'message': 'account_number not found!'} 
        elif 'errorCode' in response and  response['errorCode'] == 1 and 'responseData' in response and any(errMsg in response['responseData']['objOut']['responseData'] for errMsg in error_messages):
            if self.retry_balance < 3:
                # session time out 或查询中错误 重新登入
                print('get_balance 重新登入')
                self.is_login = False
                return self.get_balance(True)
            else:
                print('balance 查询失败次数过多(retry_balance: ' + self.retry_balance + ') return Unknown Error')
                return {'code':520 ,'success': False, 'message': 'Unknown Error!'} 
        else: 
            print('get balance Unknown Error!')
            return {'code':520 ,'success': False, 'message': 'Unknown Error!'} 
    
    def get_transactions_by_page(self,page,limit,postingOrder,postingDate,nextRunBal,account_number):
        
        payload = "SERVICESID=ONLACCINQ&subsvc=getTransactionHistoryOnline&accountNo="+account_number+"&nextRunBal="+quote(nextRunBal)+"&postingOrder="+quote(postingOrder)+"&postingDate="+quote(postingDate)+"&currency=VND&fileIndicator="
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0',
            'Accept': '*/*',
            'Accept-Language': 'vi-VN,vi;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Cookie':self.cookie,
            'Token': self.token,
            'RESULT_TYPE': 'JSON',
            'X-Requested-With': 'XMLHttpRequest',
            'Origin': 'https://www.bidv.vn',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'Priority': 'u=0'
        }

        response = self.curlPost(self.url['getHistories'],payload,headers)
        if 'status' in response and  response['status'] == "0" and 'data' in response and "items" in response['data']:
            transaction_history = response['data']['items']


        if len(transaction_history) < 100:
            if transaction_history:
                self.transactions += transaction_history
        elif page*100 < limit:
            if transaction_history:
                self.transactions += transaction_history
            page=page+1
            nextRunBal = transaction_history[-1]['nextRunBal']
            postingOrder = transaction_history[-1]['postingOrder']
            postingDate = transaction_history[-1]['postingDate']
            return self.get_transactions_by_page(page,limit,postingOrder,postingDate,nextRunBal,account_number)
        else:
            if transaction_history:
                self.transactions += transaction_history[:limit - (page-1)*100]
        return True

    def getHistories(self, account_number='',limit = 100, need_login = False):
        if need_login:
            login = self.doLogin()
            if not login['success']:
                return login
        self.transactions = []

        payload = "SERVICESID=ONLACCINQ&subsvc=getTransactionHistoryOnline&accountNo="+account_number+"&currency=VND"    

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'vi-VN,vi;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Cookie':self.cookie,
            'Token': self.token,
            'RESULT_TYPE': 'JSON_GRID',
            'X-Requested-With': 'XMLHttpRequest',
            'Origin': 'https://www.bidv.vn',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin'
        }
        self.retry_transactions += 1
        response = self.curlPost(self.url['getHistories'], payload,headers)

        # session time out 或查询中错误
        error_messages = [
            'Bạn đã hết phiên làm việc! Vui lòng đăng nhập lại.',
            'Có lỗi trong quá trình vấn tin tài khoản, xin vui lòng thử lại !'
        ]

        if 'status' in response and response['status'] == "0" and 'data' in response and "items" in response['data']:
            self.transactions = response['data']['items']
            nextRunBal = response['data']['items'][-1]['nextRunBal']
            postingOrder = response['data']['items'][-1]['postingOrder']
            postingDate = response['data']['items'][-1]['postingDate']
           
            if limit > 100:
                self.get_transactions_by_page(2,limit,postingOrder,postingDate,nextRunBal,account_number)
            
            crediTransactionstList = list(filter(self.getFiterTransactionData, self.transactions))
            result = list(map(self.removeKeys, crediTransactionstList))
            self.retry_transactions = 0
            return {'code':200,'success': True, 'message': 'Thành công',
                    'data':{
                        'transactions':result,
            }}
        elif 'errorCode' in response and  response['errorCode'] == 1 and 'responseData' in response and any(errMsg in response['responseData']['objOut']['responseData'] for errMsg in error_messages):
            if self.retry_transactions < 3:
                # session time out 或查询中错误 重新登入
                print('getHistories 重新登入')
                self.is_login = False
                return self. getHistories(self.account_number, 100, True)
            else:
                print('histories 查询失败次数过多(retry_transactions: ' + self.retry_transactions + ') return Unknown Error')
                return {'code':520 ,'success': False, 'message': 'Unknown Error!'} 
        else:
            # ensure_ascii=False 直接输出原始的 Unicode 字符
            print('histories response: ' + json.dumps(response, ensure_ascii=False, indent=4))
            return  {
                    "success": False,
                    "code": 503,
                    "message": "Service Unavailable!"
                }

    def getFiterTransactionData(self, transaction):
        # 只抓收款资料
        return transaction['dorc'] == 'C'

    def removeKeys(self, transaction):
        removeList = ['postingOrder','id']
        amountKeys = ['amount','creditAmount','debitAmount']
        # 移除每次查询都会改变的资料及去掉金额的逗号
        return {
            k: (v.replace(',', '') if k in amountKeys else v)  # 去掉 amountKeys 所有的逗号
            for k, v in transaction.items() if k not in removeList
        }
        
