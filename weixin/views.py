# coding: utf-8
from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from oauth import weixin_oAuth
from tools import wx_utils
from tools.wxweb import WXWeb
import os
import thread
import time
import json
import sys

reload(sys)
sys.setdefaultencoding('utf-8')

# Create your views here.

def response_code(req):
    """
    1.微信回调携带code参数
    2.根据回调code拿到授权access_token
    3.根据access_token,openid获得用户基本信息
    4.添加用户到数据库
    5.登陆成功跳转到首页
    """
    if req.GET.get("nsukey"):
        return HttpResponse("login success")
    code = req.GET.get("code")
    userinfo = weixin_oAuth.oauth(code)    
    print userinfo
    return HttpResponse("success login")

d_wx = {}

def to_qrcode(req):
	wx_utils.show_qrcode(1)
	return render(req, 'qrcode.html')

def to_weixin(req):
    if d_wx:
        wxWeb = d_wx.values()[0]
    else:
        wxWeb = WXWeb()
        wx_utils.init_login(wxWeb)
        print wxWeb.base_uri, '-----'
        d_wx[wxWeb.UserName] = wxWeb

    MemberList = wxWeb.webwxgetcontact()
    MemberCount = len(MemberList)

    return render(req, "weixin.html", {"count": MemberCount, "member_list": MemberList, "base_uri": wxWeb.base_uri, "contact_list": wxWeb.ContactList, "UserName": wxWeb.UserName})


@csrf_exempt
def do_something(req):
    print dir(req), '----'
    do_type = req.GET.get('do_type')
    initial = req.GET.get("initial")
    wxWeb = d_wx[initial]
    if req.method == 'POST':
        arg = json.loads(req.POST.get("f"))
        members = arg.get("members")
        message = arg.get("message")
        if do_type == u'1':
            # 发送消息，指定
            wxWeb.sendMsg(members, message)
            return HttpResponse("success")
        elif do_type == u'2':
            def get_members(groups):
                member_list = []
                for x in groups:
                    for c in wxWeb.ContactList:
                        if x == c['UserName']:
                            member_list += c['MemberList']
                return member_list

            member_list = get_members(members)
            print member_list,'-----', len(member_list)
            # 发送群组请求好友
            wxWeb.verifyUser(member_list, message)
            return HttpResponse("group ok")
        elif do_type == u'3':
            pass
        else:
            return HttpResponse("invalid type...")








