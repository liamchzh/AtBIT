import tornado.wsgi
import sae
import tornado.web

from urls import urls
from settings import settings

#app = tornado.wsgi.WSGIApplication(urls, **settings)
#application = sae.create_wsgi_app(app)

application = tornado.web.Application(urls, **settings)
