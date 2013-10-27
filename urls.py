#!/usr/bin/env python
# -*- coding: utf-8 -*-

import atbit

urls = [
    (r"/", atbit.IndexHandler),
    (r"/hole", atbit.HoleHandler),
    (r"/about", atbit.AboutHandler),
    (r"/signin", atbit.SigninHandler),
    (r"/signout", atbit.SignoutHandler),
    (r"/register", atbit.RegisterHandler),
    (r"/book/add", atbit.addBookHandler),
    (r"/book", atbit.BookHandler),
    (r"/book/page/(\d+)", atbit.PageHandler),
    (r"/book/(\d+)", atbit.ViewbookHandler),
    (r"/search", atbit.SearchHandler),
    (r"/book/buy/(\d+)", atbit.BuyHandler),
    (r"/book/sell", atbit.SellHandler),
    (r"/book/notbuy/(\d+)", atbit.NotbuyHandler),
    (r"/book/notsell/(\d+)", atbit.NotsellHandler),
    (r"/user/(\d+)", atbit.ViewuserHandler),
    (r"/book/collect/(\d+)", atbit.CollectHandler),
    (r"/book/notcollect/(\d+)", atbit.NotcollectHandler),
    (r"/me", atbit.MypageHandler),
    (r"/inbox", atbit.InboxHandler),
    (r"/message/(\d+)", atbit.MessageHandler),
    (r"/.*", atbit.PageNotFound), 
]

