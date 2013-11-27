# -*- coding:utf-8 -*-
import urllib2
import json
import traceback 


def parse(url):
    bookinfo = {}
    if not url:
        return [u"请输入URL"], bookinfo
    while url[-1] == "/":
        url = url[:-1]
    posi = url.find("book.douban.com/subject/")
    if posi == -1:
        return
    bookid = url[posi+24:]
    apiurl = "https://api.douban.com/v2/book/"
    
    if not bookid.isdigit():
        return [u"URL错误"], bookinfo
    try:
        data = json.loads(urllib2.urlopen(apiurl+bookid).read())
        print data
    except:
        return [u"API出错，请稍后再试"], bookinfo
    keys = ["id", "title", "author","publisher", "pubdate", "isbn13", "price", "alt"]
    for key in keys:
        bookinfo[key] = data[key]
        if isinstance(bookinfo[key], list):
            bookinfo[key] = ' '.join(bookinfo[key])
    bookinfo["mpic"] = data["images"]["medium"]
    bookinfo["lpic"] = data["images"]["large"]
    bookinfo["rating"] = data["rating"]["average"]
    return "ok", bookinfo

