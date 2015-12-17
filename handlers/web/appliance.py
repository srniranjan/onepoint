import webapp2
from handlers.web import WebRequestHandler
from auth import login_required
from model.store import Store
from model.appliance import Appliance
import json
import logging

class AppliancesPage(WebRequestHandler):
    @login_required
    def get(self):
        email = self.session['email']
        role = self.session['role']
        store = Store.all().filter(role + ' =', email).get()
        appliances = []
        for appliance in Appliance.all().filter('store =', store).fetch(100):
            appliances.append(appliance)
        path = 'appliances.html'
        appliance_tabs = ['starred', 'newest', 'oldest']
        appliances_dict = {}
        for tab in appliance_tabs:
            rows = []
            curr_row = []
            for idx,appliance in enumerate(appliances):
                print idx
                if idx != 0 and idx % 3 == 0:
                    print("Inside if..")
                    rows.append(curr_row)
                    curr_row = []
                curr_row.append(appliance)
            if len(curr_row) > 0:
                rows.append(curr_row)
            appliances_dict[tab] = rows
            print rows
        template_values = {'appliances':appliances_dict}
        self.write(self.get_rendered_html(path, template_values), 200)

class ApplianceDetailsPage(WebRequestHandler):
    def get(self):
        path = 'appliance_details.html'
        details = [
            {
                'name':'MANUFACTURER',
                'value':'Frymaster'
            },
            {
                'name':'MODEL',
                'value':'FM102'
            },
            {
                'name':'SERIAL NUMBER',
                'value':'EGY674489GHTY76'
            },
            {
                'name':'LAST REPAIR DATE',
                'value':'7/2/2015'
            },
            {
                'name':'INSTALLED ON',
                'value':'6/1/2010'
            },
            {
                'name':'WARRANTY',
                'value':'Expired 6/1/2013'
            }
        ]
        template_values = {'details':details}
        self.write(self.get_rendered_html(path, template_values), 200)

app = webapp2.WSGIApplication(
    [
        ('/appliance/list', AppliancesPage)
    ]
)