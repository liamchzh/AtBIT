#!/usr/bin/env python
# -*- coding: utf-8 -*-

import tornado.web
from tornado import gen
import tornado.database
from settings import saedb
import renren
import datetime, time
import re
import os
import md5
import douban

from tornado.httpclient import AsyncHTTPClient

class BaseHandler(tornado.web.RequestHandler):
    @property
    def db(self):
        blogdb = tornado.database.Connection(
            host = saedb["host"] + ":" + saedb["port"], database = saedb["db"],
            user = saedb["user"], password = saedb["password"])
        return blogdb

    def get_current_user(self):
        email = self.get_secure_cookie("email")
        if not email: return None
        me = self.db.get("select * from Users where email = %s", email)
        unread = self.db.get("select count(*) from `Messages` where `Messages`.toid = %s and `Messages`.read = '0'", me['userid'])['count(*)']
        me['unread'] = unread
        return me

    def execute(self, args, callback):
        books = self.db.query(args)
        return callback(books)

class IndexHandler(BaseHandler):
    def get(self):
        self.render("index.html", me=self.current_user)

class AboutHandler(BaseHandler):
    def get(self):
        self.render("about.html", me=self.current_user)

class HoleHandler(BaseHandler):
    def get(self):
        self.render("hole.html", me=self.current_user, messages=[])
    
    def post(self):
        content = self.get_argument("content")
        ipaddr = self.request.remote_ip  # 如何获取NAT的校内IP
        message = []
                
        if not self.checkIP(ipaddr):
            message = [u"请使用校内IP"]
        elif not (len(content)<120 and len(content)> 1):
            message = [u"字数超出长度限制"]
        # elif self.checkTime(ipaddr):
        #     message = [u"您刚刚发过状态，请稍后再试"]
        else:
            try:
                new_content = content + u"(发送自 http://atbit.sinaapp.com/hole )"
                renren.renren_status(new_content)
            except:
                message = [u"出错了，请稍后再试"]
            else:
                message = [u"状态发送成功"]
                self.db.execute("insert into Hole (ip, user, name, content, time) values (%s, %s, %s, %s, %s)", ipaddr, self.current_user.userid, self.current_user.name, content, datetime.datetime.now())
        self.render("hole.html", me=self.current_user, messages=message)

    # 相同IP，5分钟时间间隔
    def checkTime(self, ipaddr):
        users = self.db.query("select * from UserIP where ip = %s ", ipaddr)
        for user in users:
            if datetime.datetime.now() - user.time < datetime.timedelta(minutes=5):
                return True
        self.db.execute("insert into UserIP (ip, time) values (%s, %s)", ipaddr, datetime.datetime.now())
        return False

    def checkIP(self, ipaddr):
        return True

class SigninHandler(BaseHandler):
    def get(self):
        if not self.current_user:
            self.render("signin.html", info = {}, messages = [])
        else:
            self.redirect("/")
    
    def post(self):
        email = self.get_argument("email", "")
        pswd = self.get_argument("pswd", "")
        user_id = self.checkUser(email, pswd)
        if user_id:
            self.set_secure_cookie("email", email)
            self.redirect("/")
        else:
            info = {"email": email}
            log_info = [u"用户名或密码不正确"]
            self.render("signin.html", info = info, messages = log_info)

    def checkUser(self, email, pswd):
        user = self.db.get("select * from Users where email = %s", email)
        if user:
            password = user.password
            hashed = md5.new(pswd).hexdigest()
            if password == hashed:
                return user.userid
            else:
                return False
        else:
            return False
    
class SignoutHandler(BaseHandler):
    def get(self):
        self.clear_cookie("email")
        self.redirect("/")

class RegisterHandler(BaseHandler):
    def get(self):
        if not self.current_user:
            self.render("register.html", me=self.current_user, info = {}, messages = [])
        else:
            self.redirect("/")

    def post(self):
        info_keys = ["email", "pswd", "name", "qq", "phone", "campus", "notes"]
        info = {}
        for key in info_keys:
            info[key] = self.get_argument(key, "")
        infomessage = self.checkInfo(info)
        if infomessage == ["ok"]:
            if self.addUser(info):
                self.redirect("/")
            else:
                self.render("register.html", me=self.current_user, info = info, messages = [u"无法注册，请多试几次后，联系liamchzh@gmail.com"])
        else:
            self.render("register.html", me=self.current_user, info = info, messages = infomessage)


    def checkInfo(self, info):
        message = self.checkEmail(info["email"])
        if message != []:
            return message
        if not (len(info["pswd"]) >= 6 and len(info["pswd"]) <= 20):
            return [u"密码长度不符合要求"]
        if not info["name"]:
            return [u"姓名不能为空"]
        if len(info["name"]) > 10:
            return [u"姓名长度超出限制"]
        if not (info["qq"] or info["phone"]):
            return [u"QQ和手机号码至少填写一项"]
        if info["qq"]:
            if not (len(info["qq"]) >= 6 and len(info["qq"]) <= 10 and info["qq"].isdigit()):
                return [u"QQ号码不符合要求"]
        if info["phone"]:
            if not (len(info["phone"]) == 11 and info["phone"].isdigit()):
                return [u"手机号码不符合要求"]
        if not info["campus"]:
            return [u"请选择校区"]
        if info["campus"] != "BIT" and info["campus"] != "LIT":
            return [u"请不要自行修改校区"]
        return ["ok"]
        
    def checkEmail(self, email):
        exist = self.db.get("select * from Users where email = %s", email)
        if exist:
            return [u"用户名已被注册"]
        if len(email) > 20 and len(email) < 6:
            return [u"用户名长度不符合要求"]
        result = re.match("^.+\\@(\\[?)[a-zA-Z0-9\\-\\.]+\\.([a-zA-Z]{2,3}|[0-9]{1,3})(\\]?)$", email)
        if not result:
            return [u"邮箱格式不正确"]
        else:
            return []

    def addUser(self, info):
        password = md5.new(info["pswd"]).hexdigest()
        user_num = len(self.db.query("select * from Users"))
        userid = 19550224 + user_num
        try:
            self.db.execute("insert into Users (userid, email, password, name, qq, phone, campus, notes) values (%s,%s,%s,%s,%s,%s,%s,%s)",
                str(userid), info["email"], password, info["name"], info["qq"], info["phone"], info["campus"], info["notes"])
            return True
        except:
            return False

class addBookHandler(BaseHandler):
    def get(self):
        self.render("addBook.html", messages=[])

    def post(self):
        url = self.get_argument("url", "")
        status, bookinfo = douban.parse(url)
        if status != "ok":
            message = status
            self.render("addBook.html", messages = message)
        elif not bookinfo:
            message = [u"无法添加图书，请检查URL是否正确"]
            self.render("addBook.html", messages = message)
        else:
            if self.db.get("select * from Books where id = %s", bookinfo["id"]):
                self.db.execute("update Books set updatetime = %s where id = %s", datetime.datetime.now(), bookinfo["id"])
                self.redirect("/book/%s" % bookinfo["id"])
            else:
                try:
                    self.db.execute("insert into Books (id, title, author, publisher, pubdate, mpic, lpic, price, isbn13, rating, alt, time) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", bookinfo["id"], bookinfo["title"], bookinfo["author"], bookinfo["publisher"], bookinfo["pubdate"], bookinfo["mpic"], bookinfo["lpic"], bookinfo["price"], bookinfo["isbn13"], bookinfo["rating"], bookinfo["alt"],datetime.datetime.now())
                    self.redirect("/book/%s" % bookinfo["id"])
                except:
                    message = [u"暂时无法添加图书，请稍后再试"]
                    self.render("addBook.html", me=self.current_user, messages = message)


class BookHandler(BaseHandler):
    @tornado.web.asynchronous
    @gen.engine
    def get(self):
        books = yield gen.Task(self.execute, "select * from Books order by updatetime;")
        books = books[::-1]
        book1 = books[:4]
        book2 = books[4:8]
        pages = (len(books)-1)/8 + 1 # 每页显示8本书
        self.render("book.html", me=self.current_user, book1=book1, book2=book2, pages=pages)

    
        
class PageHandler(BaseHandler):
    @tornado.web.asynchronous
    @gen.engine
    def get(self, page):
        books = yield gen.Task(self.execute, "select * from Books order by updatetime")
        books = books[::-1]
        offset = (int(page)-1)*8
        book1 = books[offset:offset+4]
        book2 = books[offset+4:offset+8]
        pages = (len(books)-1)/8 + 1 # 每页显示8本书
        self.render("page.html", me=self.current_user, book1=book1, book2=book2, pages=pages, this=int(page))
        
class ViewbookHandler(BaseHandler):
    @tornado.web.asynchronous
    @gen.engine
    def get(self, id):
        book = yield gen.Task(self.execute, "select * from Books where id = %s " % id)
        buy = False
        sell = False
        collected = False
        if self.current_user:
            email = self.current_user.get("email", "")
            if self.db.get("select * from Buyers where id = %s and email= %s and active = '1'", id, email):
                buy = True
            if self.db.get("select * from Sellers where id = %s and email= %s and active = '1'", id, email):
                sell = True
            if self.db.get("select * from Collections where id = %s and email= %s and active = '1'", id, email):
                collected = True
        buyers = self.db.query("select u.userid, u.name, u.phone, u.qq, u.campus, b.time from Users AS u, Buyers AS b where b.id = %s AND active='1' AND u.email = b.email", id)
        sellers = self.db.query("select u.userid, u.name, u.phone, u.qq, u.campus, s.time, s.price, s.des from Users AS u, Sellers AS s where s.id = %s AND active='1' AND u.email = s.email", id)
        self.render("viewbook.html", me=self.current_user, book=book[0], buy=buy, sell=sell, collected=collected, buyers=buyers, sellers=sellers)
        
class SearchHandler(BaseHandler):
    def get(self):
        self.render("search.html", me=self.current_user, content="", book1=[], book2=[], book3=[], book4=[])
        
    def post(self):
        content = self.get_argument("search", "")
        split_content = content.split(' ')
        if len(split_content) == 2:
            sql = "select * from Books where title like '%%" + split_content[0] + "%%' and author like '%%" + split_content[1] + "%%'"
        else:
            sql = "select * from Books where title like '%%" + content + "%%' or author like '%%" + content + "%%'"
        books = self.db.query(sql)
        books = books[::-1]
        book1 = books[0:4]
        book2 = books[4:8]
        book3 = books[8:12]
        book4 = books[12:16]
        self.render("search.html", me=self.current_user, content=content, book1=book1, book2=book2, book3=book3, book4=book4)
        
class BuyHandler(BaseHandler):
    def get(self, id):
        if not self.current_user:
            self.redirect("/book/%s" % id)
        else:
            email = self.current_user.get("email", "")
            # 判断是否已经存在buyers表中
            if self.db.get("select * from Buyers where id = %s and email= %s and active = '0'", id, email):
                self.db.execute("update Buyers set active = '1' where id = %s and email= %s", id, email)
                self.db.execute("update Books set updatetime = %s where id = %s", datetime.datetime.now(), id)
                self.redirect("/book/%s" % id)
            else:
                self.db.execute("insert into Buyers (email, id, time, active) values (%s, %s, %s, '1')", email, id, datetime.datetime.now())
                self.db.execute("update Books set updatetime = %s where id = %s", datetime.datetime.now(), id)
                self.redirect("/book/%s" % id)
            
class SellHandler(BaseHandler):
    """
    def get(self, id):
        if not self.current_user:
            self.redirect("/book/%s" % id)
        else:
            email = self.current_user.get("email", "")
            if self.db.get("select * from Sellers where id = %s and email= %s and active = '0'", id, email):
                self.db.execute("update Sellers set active = '1' where id = %s and email = %s", id, email)
                self.db.execute("update Books set updatetime = %s where id = %s", datetime.datetime.now(), id)
                self.redirect("/book/%s" % id)
            else:
                self.db.execute("insert into Sellers (email, id, time, active) values (%s, %s, %s, '1')", email, id, datetime.datetime.now())
                self.db.execute("update Books set updatetime = %s where id = %s", datetime.datetime.now(), id)
                self.redirect("/book/%s" % id)
    """

    def post(self):
        book_id = self.get_argument("book_id", "")
        price = self.get_argument("price", "")
        des = self.get_argument("des", "")
        price = price[0:2]
        des = des[0:10]
        if not price: price = "--"
        if not des: des = "None"

        if not self.current_user:
            self.redirect("/book/%s" % book_id)
        else:
            email = self.current_user.get("email", "")
            if self.db.get("select * from Sellers where id = %s and email= %s and active = '0'", book_id, email):
                self.db.execute("update Sellers set active = '1', price = %s, des = %s, time = %s where id = %s and email = %s",price, des, datetime.datetime.now(), book_id, email)
                self.db.execute("update Books set updatetime = %s where id = %s", datetime.datetime.now(), book_id)
                self.redirect("/book/%s" % book_id)
            else:
                self.db.execute("insert into Sellers (email, id, price, des, time, active) values (%s, %s, %s, %s, %s, '1')", email, book_id, price, des, datetime.datetime.now())
                self.db.execute("update Books set updatetime = %s where id = %s", datetime.datetime.now(), book_id)
                self.redirect("/book/%s" % book_id)




class CollectHandler(BaseHandler):
    def get(self, id):
        if not self.current_user:
            self.redirect("/book/%s" % id)
        else:
            email = self.current_user.get("email", "")
            if self.db.get("select * from Collections where id = %s and email= %s and active = '0'", id, email):
                self.db.execute("update Collections set active = '1' where id = %s and email= %s", id, email)
                self.redirect("/book/%s" % id)
            else:
                self.db.execute("insert into Collections (email, id, time, active) values (%s, %s, %s, '1')", email, id, datetime.datetime.now())
                self.redirect("/book/%s" % id)

class NotbuyHandler(BaseHandler):
    def get(self, id):
        if not self.current_user:
            self.redirect("/book/%s" % id)
        else:
            email = self.current_user.get("email", "")
            if self.db.get("select * from Buyers where id = %s and email= %s and active = '1'", id, email):
                self.db.execute("update Buyers set active = '0' where id = %s and email= %s", id, email)
                self.redirect("/book/%s" % id)
            else:
                self.redirect("/book/%s" % id)
                
class NotsellHandler(BaseHandler):
    def get(self, id):
        if not self.current_user:
            self.redirect("/book/%s" % id)
        else:
            email = self.current_user.get("email", "")
            if self.db.get("select * from Sellers where id = %s and email= %s and active = '1'", id, email):
                self.db.execute("update Sellers set active = '0' where id = %s and email= %s", id, email)
                self.redirect("/book/%s" % id)
            else:
                self.redirect("/book/%s" % id)
                
class NotcollectHandler(BaseHandler):
    def get(self, id):
        if not self.current_user:
            self.redirect("/book/%s" % id)
        else:
            email = self.current_user.get("email", "")
            if self.db.get("select * from Collections where id = %s and email= %s and active = '1'", id, email):
                self.db.execute("update Collections set active = '0' where id = %s and email= %s", id, email)
                self.redirect("/book/%s" % id)
            else:
                self.redirect("/book/%s" % id)

class ViewuserHandler(BaseHandler):
    def get(self, userid):
        try:
            user = self.db.get("select userid, email, name, phone, qq, campus, notes from Users where userid = %s", userid)
            email = user["email"]
        except:
            self.render("404.html", me=self.current_user)
        buybooks = self.db.query("select Books.id, title, author, time, alt from Buyers inner join Books on Buyers.id = Books.id where Buyers.active = '1' AND Buyers.email = %s", email)
        sellbooks = self.db.query("select Books.id, title, author, time, alt from Sellers inner join Books on Sellers.id = Books.id where Sellers.active = '1' AND Sellers.email = %s", email)
        collectbooks = self.db.query("select Books.id, title, author, time, alt from Collections inner join Books on Collections.id = Books.id where Collections.active = '1' AND Collections.email = %s", email)
        self.render("user.html", me=self.current_user, user=user, buybooks=buybooks, sellbooks=sellbooks, collectbooks=collectbooks)

        
class MypageHandler(BaseHandler):
    def get(self):
        if not self.current_user:
            self.redirect("/signin")
        else:
            email = self.current_user.get("email", "")
            myself = self.db.get("select * from Users where email=%s", email)
            buybooks = self.db.query("select Books.id, title, author, time, alt from Buyers inner join Books on Buyers.id = Books.id where Buyers.active = '1' AND Buyers.email = %s", email)
            sellbooks = self.db.query("select Books.id, title, author, time, alt from Sellers inner join Books on Sellers.id = Books.id where Sellers.active = '1' AND Sellers.email = %s", email)
            collectbooks = self.db.query("select Books.id, title, author, time, alt from Collections inner join Books on Collections.id = Books.id where Collections.active = '1' AND Collections.email = %s", email)
            self.render("me.html", me=self.current_user, myself=myself, buybooks=buybooks, sellbooks=sellbooks, collectbooks=collectbooks)
            
class RequestHandler(tornado.web.RequestHandler):
    def write_error(self, status_code, **kwargs):
        if status_code == 404:
            self.render('404.html')
        elif status_code == 500:
            self.render('500.html')
        else:
            super(RequestHandler, self).write_error(status_code, **kwargs)
           
class PageNotFound(BaseHandler):
    def get(self):
        self.render('404.html', me=self.current_user)


class InboxHandler(BaseHandler):
    def get(self):
        if not self.current_user:
            self.redirect("/signin")
        else:
            my_id = self.current_user.get("userid", "")
            all_messages = self.db.query("select * from Messages where fromid = %s or toid = %s", my_id, my_id)
            # 时间倒序，最新的在前面
            all_messages = all_messages[::-1]
            id_list = []
            messages_list = []
            for m in all_messages:
                read = True
                if m["fromid"] != my_id:
                    other_id = m["fromid"]
                    tome = True
                    if m['read'] == '0':
                        read = False
                else:
                    other_id = m["toid"]
                    tome = False
                if other_id not in id_list:
                    id_list.append(other_id)
                    other_name = self.db.get("select * from Users where userid = %s", other_id)["name"]
                    messages_list.append({"id": other_id, "name": other_name, "content": m["content"], "time": m["time"], "tome": tome, "read": read})
                    print messages_list
            self.render("inbox.html", me=self.current_user, messages=messages_list)

    def post(self):
        if not self.current_user:
            self.redirect("/signin")
        from_id = self.current_user.get("userid", "")
        to_id = self.get_argument("to_user", "")
        url = self.get_argument("redirect_url", "")
        content = self.get_argument("content", "")
        if not content or from_id == to_id:
            self.redirect("%s" % url)
        else:
            self.db.execute("insert into Messages (fromid, toid, content, time) values (%s, %s, %s, %s)", from_id, to_id, content, datetime.datetime.now())
            self.redirect("%s" % url)


class MessageHandler(BaseHandler):
    def get(self, other_id):
        if not self.current_user:
            self.redirect("/signin")
        else:
            my_id = self.current_user.get("userid", "")
            all_messages = self.db.query("select * from Messages where (fromid = %s and toid = %s) or (fromid = %s and toid = %s)", my_id, other_id, other_id, my_id)
            self.db.execute("UPDATE `Messages` SET  `read` =  '1' WHERE  `Messages`.`fromid` = %s AND `Messages`.`toid` = %s AND `Messages`.`read` =  '0' ", other_id, my_id)
            all_messages = all_messages[::-1]
            other_name = self.db.get("select * from Users where userid = %s", other_id)["name"]
            other = {"id": other_id, "name": other_name}
            messages_list = []
            for m in all_messages:
                if m["fromid"] != my_id:
                    tome = True
                else:
                    tome = False
                messages_list.append({"content": m["content"], "time": m["time"], "tome": tome })
            self.render("message.html", me=self.current_user, other=other, messages=messages_list)

