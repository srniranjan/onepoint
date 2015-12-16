import webapp2
import urllib2
import json
from model.member import Member
from handlers.web.web_request_handler import WebRequestHandler

class CreateStorePage(WebRequestHandler):
    def get(self):
        path = 'create_store.html'
        template_values = {}
        self.write(self.get_rendered_html(path, template_values), 200)

app = webapp2.WSGIApplication([
    ('/data_creation/create_store', CreateStorePage)
])