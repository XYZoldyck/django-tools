# coding: utf-8
import os
try:
    from urllib import urlencode, quote_plus
except ImportError:
    from urllib.parse import urlencode, quote_plus
from invoke import url_invoke, wdf_urllib, getRequest, on_thread
 
import re
import time
import xml.dom.minidom
import json
import sys
import subprocess
import utils
 
DEBUG = True

# operations
SENDMSG = 1
VERIFYUSER = 2
UPLOADMEDIA = 3
EXIT = 0
 
MAX_GROUP_NUM = 35  # 每组人数
INTERFACE_CALLING_INTERVAL = 20  # 接口调用时间间隔, 间隔太短容易出现"操作太频繁", 会被限制操作半小时左右
MAX_PROGRESS_LEN = 50

# TODO：显示在网页
QRImagePath = os.path.join(os.getcwd()+'/media', 'qrcode.jpg')

deviceId = 'e000000000000000'
 
tip = 0
uuid = ''


def responseState(func, BaseResponse):
    ErrMsg = BaseResponse['ErrMsg']
    Ret = BaseResponse['Ret']
    if DEBUG or Ret != 0:
        print('func: %s, Ret: %d, ErrMsg: %s' % (func, Ret, ErrMsg))
 
    if Ret != 0:
        return False
 
    return True
 
 
def getUUID():
    global uuid
 
    url = 'https://login.weixin.qq.com/jslogin'
    params = {
        'appid': 'wx782c26e4c19acffb',
        'fun': 'new',
        'lang': 'zh_CN',
        '_': int(time.time()),
    }
 
    request = getRequest(url=url, data=urlencode(params))
    response = wdf_urllib.urlopen(request)
    data = response.read().decode('utf-8', 'replace')
 
    # print(data)
 
    # window.QRLogin.code = 200; window.QRLogin.uuid = "oZwt_bFfRg==";
    regx = r'window.QRLogin.code = (\d+); window.QRLogin.uuid = "(\S+?)"'
    pm = re.search(regx, data)
 
    code = pm.group(1)
    uuid = pm.group(2)
 
    if code == '200':
        return True
 
    return False
 
 
def showQRImage():
    global tip
 
    url = 'https://login.weixin.qq.com/qrcode/' + uuid
    params = {
        't': 'webwx',
        '_': int(time.time()),
    }
 
    request = getRequest(url=url, data=urlencode(params))
    response = wdf_urllib.urlopen(request)
 
    tip = 1
 
    f = open(QRImagePath, 'wb')
    f.write(response.read())
    f.close()
 
    # if sys.platform.find('darwin') >= 0:
    #     subprocess.call(['open', QRImagePath])
    # elif sys.platform.find('linux') >= 0:
    #     subprocess.call(['xdg-open', QRImagePath])
    # else:
    #     os.startfile(QRImagePath)
 
    print('请使用微信扫描二维码以登录')


def syncKey(wxWeb):
    SyncKeyItems = ['%s_%s' % (item['Key'], item['Val'])
                    for item in wxWeb.syncKey['List']]
    SyncKeyStr = '|'.join(SyncKeyItems)
    return SyncKeyStr
 
 
def syncCheck(wxWeb):
    view = 'synccheck'
    query_params = {
        'skey': wxWeb.BaseRequest['Skey'],
        'sid': wxWeb.BaseRequest['Sid'],
        'uin': wxWeb.BaseRequest['Uin'],
        'deviceId': wxWeb.BaseRequest['DeviceID'],
        'synckey': syncKey(wxWeb),
        'r': int(time.time()),
    }
 
    data, data_unicode = url_invoke(wxWeb.push_uri, view, query_params)
 
    # print(data)
 
    # window.synccheck={retcode:"0",selector:"2"}
    regx = r'window.synccheck={retcode:"(\d+)",selector:"(\d+)"}'
    pm = re.search(regx, data_unicode)
 
    retcode = pm.group(1)
    selector = pm.group(2)
 
    return selector
 
 
def webwxsync(wxWeb):
    # 组织url数据
    view = 'webwxsync'
    query_params = dict(
            lang='zh_CN',
            skey=wxWeb.skey,
            sid=wxWeb.wxsid,
            pass_ticket=quote_plus(wxWeb.pass_ticket)
        )
    params = {
        'BaseRequest': wxWeb.BaseRequest,
        'SyncKey': wxWeb.syncKey,
        'rr': ~int(time.time()),
    }
    # 调用
    data, data_unicode = url_invoke(wxWeb.base_uri, view, query_params, params)
    #print(data, '########')
 
    # print(data)
 
    dic = json.loads(data_unicode)
    wxWeb.syncKey = dic['SyncKey']
 
    state = responseState('webwxsync', dic['BaseResponse'])
    return state
 

@on_thread
def heartBeatLoop(wxWeb):
    """
    与微信服务端进行心跳连接，同步skey，以及推送消息
    """
    while True:
        selector = syncCheck(wxWeb)
        if selector != '0':
            webwxsync(wxWeb)
        time.sleep(1)
 
 
def waitForLogin(wxWeb):
    """
    等待用户扫描二维码确认登陆
    得到各类uri
    """
    url = 'https://login.weixin.qq.com/cgi-bin/mmwebwx-bin/login?tip=%s&uuid=%s&_=%s' % (
        wxWeb.tip, uuid, int(time.time()))
 
    request = getRequest(url=url)
    response = wdf_urllib.urlopen(request)
    data = response.read().decode('utf-8', 'replace')
 
    # window.code=500;
    regx = r'window.code=(\d+);'
    pm = re.search(regx, data)
 
    code = pm.group(1)
 
    if code == '201':  # 已扫描
        print('成功扫描,请在手机上点击确认以登录')
        wxWeb.tip = 0
    elif code == '200':  # 已登录
        print('正在登录...')
        regx = r'window.redirect_uri="(\S+?)";'
        pm = re.search(regx, data)
        redirect_uri = pm.group(1) + '&fun=new'
        base_uri = redirect_uri[:redirect_uri.rfind('/')]
 
        # push_uri与base_uri对应关系(排名分先后)(就是这么奇葩..)
        services = [
            ('wx2.qq.com', 'webpush2.weixin.qq.com'),
            ('qq.com', 'webpush.weixin.qq.com'),
            ('web1.wechat.com', 'webpush1.wechat.com'),
            ('web2.wechat.com', 'webpush2.wechat.com'),
            ('wechat.com', 'webpush.wechat.com'),
            ('web1.wechatapp.com', 'webpush1.wechatapp.com'),
        ]
        push_uri = base_uri
        for (searchUrl, pushUrl) in services:
            if base_uri.find(searchUrl) >= 0:
                push_uri = 'https://%s/cgi-bin/mmwebwx-bin' % pushUrl
                break

        wxWeb.base_uri = base_uri
        wxWeb.push_uri = push_uri
        wxWeb.redirect_uri = redirect_uri
        if sys.platform.find('darwin') >= 0:  # for OSX with Preview
            os.system("osascript -e 'quit app \"Preview\"'")
    elif code == '408':  # 超时
        pass
    # elif code == '400' or code == '500':
 
    return code
 
 
def login(wxWeb):
    """
    登陆，获得调用接口凭证
    """
    request = getRequest(url=wxWeb.redirect_uri)
    response = wdf_urllib.urlopen(request)

    cookie = response.headers.get("set-cookie")
    data_ticket = cookie[cookie.find("webwx_data_ticket"):].split(";")[0].split("=", 1)[1]

    print(data_ticket, "data ticket..")

    data = response.read().decode('utf-8', 'replace')
 
    print(data)
 
    doc = xml.dom.minidom.parseString(data)
    root = doc.documentElement
 
    for node in root.childNodes:
        if node.nodeName == 'skey':
            skey = node.childNodes[0].data
        elif node.nodeName == 'wxsid':
            wxsid = node.childNodes[0].data
        elif node.nodeName == 'wxuin':
            wxuin = node.childNodes[0].data
        elif node.nodeName == 'pass_ticket':
            pass_ticket = node.childNodes[0].data

    # print('skey: %s, wxsid: %s, wxuin: %s, pass_ticket: %s' % (skey, wxsid,
    # wxuin, pass_ticket))
 
    if not all((skey, wxsid, wxuin, pass_ticket)):
        return False
 
    BaseRequest = {
        'Uin': int(wxuin),
        'Sid': wxsid,
        'Skey': skey,
        'DeviceID': deviceId,
    }
 
    wxWeb.BaseRequest = BaseRequest
    wxWeb.data_ticket = data_ticket
    wxWeb.pass_ticket = pass_ticket
    return True

def webwxinit(wxWeb):
    """
    微信登陆初始化
    获取联系人信息，得到当前用户信息
    """
    # 组织请求url及数据
    view = 'webwxinit'
    query_params = dict(pass_ticket=wxWeb.pass_ticket, skey=wxWeb.skey, r=int(time.time()))    
    params = {
        'BaseRequest': wxWeb.BaseRequest
    }

    # 调用
    data, data_unicode = url_invoke(wxWeb.base_uri, view, query_params, params)
 
    if DEBUG:
        f = open(os.path.join(os.getcwd(), 'webwxinit.json'), 'wb')
        f.write(data)
        f.close()
        
    # 转换json
    dic = json.loads(data_unicode)

    state = responseState('webwxinit', dic['BaseResponse'])

    wxWeb.My = dic['User']
    wxWeb.syncKey = dic['SyncKey']
    wxWeb.ContactList = dic['ContactList']
    return state

def show_qrcode(wxWeb):
    if not getUUID():
        print('获取uuid失败')
        return
 
    print('正在获取二维码图片...')
    showQRImage()
    time.sleep(1)

def init_login(wxWeb):
    while waitForLogin(wxWeb) != '200':
        pass
 
    os.remove(QRImagePath)
 
    if not login(wxWeb):
        print('登录失败')
        return
 
    print(dir(wxWeb), '========')
    if not webwxinit(wxWeb):
        print('初始化失败')
        return

    
    print('开启心跳线程')
    heartBeatLoop(wxWeb)



