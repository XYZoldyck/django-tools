# coding: utf-8
import os

try:
    from urllib import urlencode, quote_plus
except ImportError:
    from urllib.parse import urlencode, quote_plus
try:
    import urllib2 as wdf_urllib
    from cookielib import CookieJar
except ImportError:
    import urllib.request as wdf_urllib
    from http.cookiejar import CookieJar
 
import time
import json
import utils
import hashlib
import random


from poster.encode import multipart_encode
from poster.streaminghttp import register_openers
from wx_utils import getRequest, responseState
from invoke import url_invoke, on_thread
 
DEBUG = True

# operations

class WXWeb(object):
    def __init__(self):
        """
        微信Web
        @param: data_ticket 微信上传资源所需凭证
        @param: BaseRequest 调用接口基本凭证
        @param: my 登录用户后的信息
        @param: skey 调用接口基本凭证skey
        @oaran: wxsid 调用接口基本凭证wxsid
        @param: wxuin 调用接口基本凭证wxuin
        @param: pass_ticket query string url 接口所需凭证
        @param: syncKey 微信每次交互，同步key
        """
        self.data_ticket = ''
        self.BaseRequest = ''
        self.My = ''
        self.skey = ''
        self.wxsid = ''
        self.wxuin = ''
        self.pass_ticket = ''
        self.syncKey = ''
    
        self.tip = 1
        self.base_uri = ''
        self.push_uri = ''
        self.redirect_uri = ''
        self.upload_uri = 'https://file.wx.qq.com/cgi-bin/mmwebwx-bin'

        self.ContactList = []

        # 文件流分隔符
        self.boundary = "----WebKitFormBoundary{}".format(utils.generate_token(16))

    def __setattr__(self, key, value):
        self.__dict__[key] = value
        if key == "BaseRequest" and isinstance(value, dict):
            self.wxuin = value.get('Uin')
            self.wxsid = value.get('Sid')
            self.skey = value.get('Skey')

    @property
    def UserName(self):
        return self.My['UserName']

    def webwxgetcontact(self):
        # 组织url数据结构
        view = 'webwxgetcontact'
        query_params = dict(pass_ticket=self.pass_ticket, skey=self.skey, r=int(time.time()))    
        params = {
            'BaseRequest': self.BaseRequest
        }
        # 调用
        data, data_unicode = url_invoke(self.base_uri, view, query_params, params)

        if DEBUG:
            f = open(os.path.join(os.getcwd(), 'webwxgetcontact.json'), 'wb')
            f.write(data)
            f.close()
     
        dic = json.loads(data_unicode)
        MemberList = dic['MemberList']
     
        # 倒序遍历,不然删除的时候出问题..
        SpecialUsers = ["newsapp", "fmessage", "filehelper", "weibo", "qqmail", "tmessage", "qmessage", "qqsync", "floatbottle", "lbsapp", "shakeapp", "medianote", "qqfriend", "readerapp", "blogapp", "facebookapp", "masssendapp",
                        "meishiapp", "feedsapp", "voip", "blogappweixin", "weixin", "brandsessionholder", "weixinreminder", "wxid_novlwrv3lqwv11", "gh_22b87fa7cb3c", "officialaccounts", "notification_messages", "wxitil", "userexperience_alarm"]

        temp_list =[]
        for i in range(len(MemberList) - 1, -1, -1):
            Member = MemberList[i]
            if Member['VerifyFlag'] & 8 != 0:  # 公众号/服务号
                MemberList.remove(Member)
            elif Member['UserName'] in SpecialUsers:  # 特殊账号
                MemberList.remove(Member)
            elif Member['UserName'] == self.My['UserName']:  # 自己
                MemberList.remove(Member)
        return MemberList


    #@on_thread
    def sendMsg(self, member_list, message):
        """
        发送消息
        """
        # 发送好友
        for member in member_list:
            self.do_send_msg(member, message)
            r = random.randint(2, 5)
            time.sleep(r)

    def do_send_msg(self, toUserName, message):
    	# 组织url数据
        _now_time = int(time.time())
        msg = dict(
                ClientMsgId=_now_time,
                Content=message,
                FromUserName=self.My["UserName"],
                LocalID=_now_time,
                ToUserName=toUserName,
                Type=1
            )
        print msg, 'msg'
    	view = 'webwxsendmsg'
    	query_params = dict(lang='zh_CN', pass_ticket=self.pass_ticket)
        params = {
            'BaseRequest': self.BaseRequest,
            'Msg': msg,
            'Scene': 0,
        }
        
        # 调用
        data, data_unicode = url_invoke(self.base_uri, view, query_params, params=params, ensure_ascii=False)
        print data, 'data'
        dic = json.loads(data_unicode)

    def webwxUploadMedia(self, toUserName, upload_media=None):
        """
        上传文件
        """
        # 注册流句柄 wdf_urllib.bind()
        print("开始上传!")
        register_openers()
        # TODO: 参数化
        path = "/Users/admin/Desktop/timg.jpeg"
        view = 'webwxuploadmedia'
        w = open(path, "rb")
        filemd5 = hashlib.md5()
        f = w.read()
        filemd5.update(f)
        w.seek(0)
        md5 = filemd5.hexdigest()
        size = os.path.getsize(path)
        
        t = (("uploadmediarequest", json.dumps({"UploadType": 2, "BaseRequest": self.BaseRequest, "ClientMediaId": int(time.time()), "TotalLen": size, "StartPos": 0, "DataLen": size, "MediaType": 4, 
            "FromUserName": self.My["UserName"], "ToUserName": toUserName, "FileMd5": md5})), ("webwx_data_ticket", self.data_ticket), ("pass_ticket", self.pass_ticket), ("filename", w))

        datagen, headers = multipart_encode(t, boundary=self.boundary)
        query_params = dict(f='json')
       
        data, data_unicode = url_invoke(self.upload_uri, view, query_params, params=datagen, headers=headers, media=True)
        w.close()

        if DEBUG:
            f = open(os.path.join(os.getcwd(), 'uploadmedia.json'), 'wb')
            f.write(data)
            f.close()
        dic = json.loads(data_unicode)
        return dic, toUserName

    def sendMedia(self, media_dic, toUserName):
        """
        发送文件
        """
    	# 组织url结构
        view = 'webwxsendmsgimg'
        query_params = {
        	"fun": "async",
        	"f": "json",
        	"lang": "zh_CN",
        	"pass_ticket": self.pass_ticket
        }
        _now_time = int(time.time())
        msg = dict(
                ClientMsgId=_now_time,
                FromUserName=self.My["UserName"],
                LocalID=_now_time,
                MediaId=media_dic['MediaId'],
                ToUserName=toUserName,
                Type=3,
            )
        params = {
            'BaseRequest': self.BaseRequest,
            'Msg': msg,
            'Scene': 0,
        }

        # 请求
        data, data_unicode = url_invoke(self.base_uri, view, query_params, params)
        dic = json.loads(data_unicode)

    #@on_thread
    def verifyUser(self, UserList, verify_info):
        """
        同时发送多个添加好友
        """
        # 组织url结构
        print("开始请求添加群组里好友")
        def generate_user(uList):
            _u_list = []
            for user in uList:
                d = {"Value": user["UserName"], "VerifyUserTicket": ""}
                _u_list.append(d)
            return _u_list

        _u_list = generate_user(UserList)

        view = 'webwxverifyuser'
        query_params = dict(r=int(time.time()), pass_ticket=self.pass_ticket)
        for u in _u_list:
            params = {
                "BaseRequest": self.BaseRequest,
                "Opcode": 2,
                "SceneList": [33],
                "SceneListCount": 1,
                "VerifyContent": verify_info,
                "VerifyUserList": u,
                "VerifyUserTicket": "",
                "VerifyUserListSize": 1,
                "skey": self.skey
            }
            # 调用
            data, data_unicode = url_invoke(self.base_uri, view, query_params, params, ensure_ascii=False)
            print data, 'dattttt'
            dic = json.loads(data_unicode)
            r = random.randint(2, 5)
            time.sleep(r)