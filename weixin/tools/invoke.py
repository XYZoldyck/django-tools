# coding: utf-8
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

import ssl
import json


ssl._create_default_https_context = ssl._create_unverified_context
 
opener = wdf_urllib.build_opener(
    wdf_urllib.HTTPCookieProcessor(CookieJar()))
opener.addheaders = [
    ('User-agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.125 Safari/537.36'),
    ]
wdf_urllib.install_opener(opener)

def getRequest(url, data=None):
    try:
        data = data.encode('utf-8')
    except:
        pass
    finally:
        return wdf_urllib.Request(url=url, data=data)


def url_invoke(base_uri, view, query_params, params=None, headers=None, ensure_ascii=True, media=False):
    _query_params = urlencode(query_params)
    url = base_uri + \
        '/{}?{}'.format(view, _query_params)
    data = None
    _headers = dict(ContentType='application/json; charset=UTF-8')
    if params:
    	data = params if media else json.dumps(params, ensure_ascii=ensure_ascii)

    if headers:
    	if media:
    		_headers = headers
    	else:
        	_headers.update(headers)

    request = getRequest(url=url, data=data)
    for key, value in _headers.iteritems():
        request.add_header(key, value)
    response = wdf_urllib.urlopen(request)
    data_str = response.read()
    data_unicode = data_str.decode('utf-8', 'replace')
    return data_str, data_unicode


from concurrent import futures

MAX_WORKERS = 16
executor = futures.ThreadPoolExecutor(max_workers=MAX_WORKERS)

#逻辑层的多线程封装,使用的是concurrent库
#开发者无需关注线程,关注逻辑开发即可
def on_thread(func):
    def _deco_params(*args, **kwargs):
          executor.submit(func, *args, **kwargs)
    return _deco_params