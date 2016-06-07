# coding: utf-8

OAUTH_RUL = {
	"weibo": ("secret_key", "appid", "access_token_url", "pay_url"),
	"weixin": ("d2419b4cd189f76c840e69e28f613d4a", "wx74cda484a2ba4fc2", "https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={}&secret={}", "pay_url", "https://open.weixin.qq.com/connect/oauth2/authorize?appid=wx74cda484a2ba4fc2&redirect_uri={}&response_type=code&scope=snsapi_userinfo&state=STATE#wechat_redirect", "http://139.129.59.198:8881/response", "https://api.weixin.qq.com/sns/oauth2/access_token?appid={}&secret={}&code={}&grant_type=authorization_code", "https://api.weixin.qq.com/sns/userinfo?access_token={}&openid={}&lang=zh_CN")
}
