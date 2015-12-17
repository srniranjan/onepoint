import webapp2
from handlers.web import WebRequestHandler
from auth import login_required
from model.provider import Provider
from util.util import convert_to_grid_format
import json
import logging

class ProvidersPage(WebRequestHandler):
    def load_manager_view(self):
        providers = [provider for provider in Provider.all().fetch(100)]
        providers_dict = convert_to_grid_format(providers, ['starred'])
        path = 'providers.html'
        template_values = {'providers':providers_dict,'count':len(providers)}
        self.write(self.get_rendered_html(path, template_values), 200)

    @login_required
    def get(self):
        role = self.session['role']
        if role == 'owner' or role == 'manager':
            self.load_manager_view()

class ProviderDetailsPage(WebRequestHandler):
    @login_required
    def get(self):
        path = 'provider_details.html'
        provider = Provider.get_by_id(long(self['id']))
        template_values = {'details':provider.template_format,'name':provider.name}
        self.write(self.get_rendered_html(path, template_values), 200)

app = webapp2.WSGIApplication(
    [
        ('/provider/list', ProvidersPage),
        ('/provider/details',ProviderDetailsPage)
    ]
)