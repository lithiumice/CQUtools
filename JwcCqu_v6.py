import requests
import re
from hashlib import md5
import asyncio
import json
import threading
import traceback
import lxml.html
import queue
import urllib.parse
from .JwcCqu import *


def ChromeHeaders2Dict(chrome_headers_str: str) -> dict:
    """

    :param chrome_headers_str:
    :return: dict
    """
    if not chrome_headers_str:
        return {}

    headers = {}
    item_list = chrome_headers_str.splitlines(keepends=False)
    for item in item_list:
        item_str = item.strip()
        if not item_str:
            continue
        if item_str.startswith(':'):
            continue
        key_value_pair = item_str.split(':')
        if len(key_value_pair) < 2:
            continue
        key = key_value_pair[0]
        value = ':'.join(key_value_pair[1:])
        headers[key] = value.strip()
    return headers


class JwcCqu(object):
    '''
    :param:None
    readme:
    this program is only useful for CQU's student & submit classes
    this version can only select main subject not include second subject
    and it can only select one teacher at the same time
    :return:None
    '''

    def __init__(self):
        self.schoolcode = "10611"
        self.usr_name = CONFIG['usr_name']
        self.passwd = CONFIG['passwd']

        self.intersted_list = intersted_list
        self.teacher_list = teacher_list

        self.host='202.202.1.41'
        self.change_value_list = {}
        self.selspecial = ''
        self.submit_data = {}
        self.header = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate', 'Accept-Language': 'zh-CN,zh;q=0.9', 'Connection': 'keep-alive',
            'Cookie': 'ASP.NET_SessionId=o110mu55hhaf4c55ycksgdul; safedog-flow-item=D756AFDF590DF04FA386EF2FF303E6D6',
            'Host': '202.202.1.41', 'Referer': 'http://202.202.1.41/SYS/Main_banner.aspx',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36'}
        print('init finished')

    def login(self):
        state_url = f'http://{self.host}/_data/index_login.aspx'
        state_page = requests.get(state_url, headers=self.header).content.decode('gb2312')
        login_tree = lxml.html.fromstring(state_page)
        viewstate = login_tree.xpath('//input[@name="__VIEWSTATE"]/@value')[0]
        self.view_generator = login_tree.xpath('//input[@name="__VIEWSTATEGENERATOR"]/@value')[0]

        crack_code = md5(self.usr_name.encode() + md5(self.passwd.encode()).hexdigest()[
                                                  :30].upper().encode() + self.schoolcode.encode()).hexdigest()[
                     :30].upper()
        form_data = {
            '__VIEWSTATE': viewstate,
            '__VIEWSTATEGENERATOR': self.view_generator,
            'Sel_Type': 'STU',
            'txt_dsdsdsdjkjkjc': self.usr_name,
            'txt_dsdfdfgfouyy': '',
            'txt_ysdsdsdskgf': '',
            'pcInfo': '',
            'typeName': '',
            'aerererdsdxcxdfgfg': '',
            'efdfdfuuyyuuckjg': crack_code}
        login_reponse = requests.post(state_url, form_data, headers=self.header)
        if login_reponse.status_code is not 200:
            print('Error while login with return code {}'.format(login_reponse.status_code))
        else:
            print('Login successfully.')

    def get_selspecail(self):
        url = 'http://202.202.1.41/WSXK/Private/List_WSXK_NJZY.aspx?id=0&xklb=2&xn=2018&xq=1'
        res = requests.get(url, headers=self.header).text
        self.selspecial = re.findall('option value=(.*?) selected', res)[0]

    def get_real_list(self):
        sl_data = {
            'sel_lx': '0',
            'SelSpeciality': self.selspecial,
            'Submit': '%BC%EC%CB%F7',
            # mean url decode gb2312 to 检索
            'kclbmc': 'Nothing'
        }
        self.real_list = requests.post('http://202.202.1.41/wsxk/stu_btx_rpt.aspx', data=sl_data,
                                       headers=self.header).content.decode('gb2312')
        self.list_tree = lxml.html.fromstring(self.real_list)

    def parse_list_for_info(self):

        self.mcount = self.list_tree.xpath('//*[@id="mcount"]/@value')[0]
        self.field_tree = self.list_tree.xpath('//*[@id="oTable"]/tr')

    def find_intersted_one(self):
        classes_info = [x.xpath('td/input/@value') for x in
                        self.field_tree][1:-2]
        detail_list = [x.xpath('td/a/@value') for x in self.field_tree][1:-2]
        # its number is equal to info
        for (i, classes) in enumerate(classes_info):
            for intersted in self.intersted_list:
                if intersted in classes[1]:
                    self.change_value_list[i] = detail_list[i][1]

    def open_all_windows(self):
        for (i, j) in list(self.change_value_list.items()):
            self.open_selected_one(i, j)
            print(f'current threading {threading.currentThread()}')

    def open_selected_one(self, value, idx):
        url = f"http://{host}/wsxk/stu_xszx_skbj.aspx?lx=BX&id=" + str(idx) + "&skbjval=" + ''
        open_window = requests.get(url, headers=self.header).content.decode('gb2312')
        open_tree = lxml.html.fromstring(open_window)

        find_teacher_list = open_tree.xpath('//input[contains(@id,"rad_")]/@value')

        for one_teacher_found in find_teacher_list:
            for teacher in self.teacher_list:
                if teacher in one_teacher_found:
                    long_idx = one_teacher_found.split('@')[2]
                    self.submit_data[value] = long_idx

    def parse_submut_data(self):
        strid = 'TTT'
        form_data = {}
        for (x, y) in list(self.submit_data.items()):
            chkkc: str = 'chkKC' + str(x)
            chkkc_value = self.list_tree.xpath(f'//input[@id="{chkkc}"]/@value')[0]
            form_data['chkKC' + str(x)] = chkkc_value
            form_data['chkSKBJ' + str(x)] = str(y)
            strid += ',' + str(y) + '#' + str(chkkc_value)

        form_data['mcount'] = self.mcount
        # form_data['sel_lx'] = '0'
        form_data['sel_xq'] = '%'
        form_data['SelSpeciality'] = self.selspecial
        form_data['kclb3'] = '%'
        form_data['chk_kyme'] = '0'
        form_data['id'] = strid
        form_data['yxsjct'] = '0'
        form_data['txt_yzm'] = ''

        self.form_data = urllib.parse.urlencode(form_data, encoding='gb2312')

    def submit_all(self):
        submit_url = 'http://202.202.1.41/wsxk/stu_btx_rpt.aspx?func=1&'
        resault = requests.post(submit_url + self.form_data, headers=self.header)
        print('the resault of respones : {}'.format(resault.content.decode('gb2312')))
        if resault.status_code is not '200':
            print(f'can not post data with status code: {resault.status_code}.')
        else:
            print(f'submit success.')

    def run(self):
        self.login()
        self.get_selspecail()
        self.get_real_list()
        self.parse_list_for_info()
        self.find_intersted_one()
        self.open_all_windows()

        # loop = asyncio.get_event_loop()
        # loop.run_until_complete(self.open_all_windows())
        # loop.close()

        self.parse_submut_data()
        self.submit_all()


if __name__ == '__main__':

    try:
        handler = JwcCqu()
        handler.run()
    except:
        # print(traceback.StackSummary)
        pass
    finally:
        print('all done.')
