# coding: utf-8
import requests
import config
import time
import json
import urllib

class OAuth(object):
	def __init__(self, oauth_type):
		self.access_token = ""
		self.expires = 0
		self.secret_key, self.app_id, self.access_token_url, self.pay_url, self.get_oauth_code_url, self.redirect_url, self.oauth_access_token_url, self.userinfo_url  = config.OAUTH_RUL[oauth_type]

	def generator_data(self):
		"""
		准备好请求data
		"""

	def get_access_token_url(self):
		url = self.access_token_url.format(self.app_id, self.secret_key)
		return url

	def return_json_data(self, json_string):
		print json_string
		return json.loads(json_string)

	def get_access_token(self):
		"""
		得到普通调用所需access_token
		根据appiid，secret_key获得access_token
		"""
		_time_now = time.time()
		if self.expires == 0 or _time_now > self.expires:
			access_token_url = self.get_access_token_url()
			response = requests.get(access_token_url)
			json_data = self.return_json_data(response.text)
			if json_data.has_key("errcode"):
				return json_data["errcode"]
			self.access_token = json_data["access_token"]
			self.expires = time.time() + json_data["expires_in"]
			return self.access_token
		return self.access_token

	def get_oauth_code_url(self):
		"""
		回调地址需要urlencode
		"""
		urlencode = urllib.urlencode({"url": self.redirect_url})
		redirect_url = urlencode.split("=", 1)[1]
		url = self.get_oauth_code_url.format(redirect_url)
		return url

	def get_oauth_access_token(self, code):
		url = self.oauth_access_token_url.format(self.app_id, self.secret_key, code)
		req = requests.get(url)
		json_data = self.return_json_data(req.text)
		if json_data.has_key("errcode"):
			return json_data["errcode"]
		access_token = json_data["access_token"]
		refresh_token = json_data["refresh_token"]
		openid = json_data["openid"]
		return access_token, openid


	def oauth(self, code):
		"""
		授权
		返回得到用户信息dict
		"""
		access_token, openid = self.get_oauth_access_token(code)
		url = self.userinfo_url.format(access_token, openid)
		req = requests.get(url)
		print req.text
		json_data = self.return_json_data(req.text)
		return json_data

	def callback(self):
		pass



class Pay(object):
	pass


try:
	weixin_oAuth
except NameError:
	weixin_oAuth = OAuth("weixin")


if __name__ == '__main__':
	oauth = OAuth("weixin")
	#oauth.get_access_token()
	oauth.get_oauth_code()
