from google.appengine.ext import db
from util.mandrill import send_mandrill_email
from model.appliance import Appliance
from model.store import Store
from model.member import Member
from model.provider import Provider

work_order_states = ["CREATED", ["ESTIMATED", "REJECTED"], ["APPROVED", "DISAPPROVED"], "PROVIDER_CHECKED_IN", "COMPLETED"]
separator = '~~##'

class WorkOrderHistory(db.Model):
	time = db.DateTimeProperty(auto_now=True)
	details = db.StringProperty(indexed=False)

class WorkOrder(db.Model):
    appliance = db.StringProperty(indexed=True)
    provider = db.StringProperty(indexed=True)
    history = db.ListProperty(long)
    curr_state = db.StringProperty(indexed=True)

    @property
    def id(self):
        return self.key().id()
    @property
    def appliance_obj(self):
        return Appliance.get_by_id(long(self.appliance))
    @property
    def provider_obj(self):
        return Provider.get_by_id(long(self.provider))
    @property
    def store(self):
        return self.appliance_obj.store
    @property
    def provider_user(self):
        return self.provider_obj.owner
    @property
    def owner_user(self):
        return Member.get_by_key_name(self.store.owner)
    @property
    def manager_user(self):
        return Member.get_by_key_name(self.store.manager)
    @property
    def action_url(self):
        if self.curr_state == 'CREATED':
            return [('ESTIMATE','')]
        elif self.curr_state == 'ESTIMATED':
            return [('APPROVE','approval:1'), ('DISAPPROVE','approval:0')]
        elif self.curr_state == 'APPROVED':
            return [('CHECK IN PROVIDER','')]
        elif self.curr_state == 'PROVIDER_CHECKED_IN':
            return [('COMPLETE','')]
        return None

    def create_wo_history(self, details):
        woh = WorkOrderHistory()
        if details:
            woh.details = details
        woh.put()
        self.history.append(woh.key().id())
        return woh

    def send_wo_created_email(self, wo_id, remarks, priority):
        estimation_link = "http://onepointapp.appspot.com/work_order/provide_estimate?work_order='+str(wo_id)+'"
        template_content = [
            {'name':'work_order_id','content':self.key().id()},
            {'name':'store_address','content':self.store.address},
            {'name':'store_name','content':self.store.name},
            {'name':'store_manager_name','content':self.manager_user.name},
            {'name':'store_manager_phone','content':self.manager_user.phone},
            {'name':'store_address','content':self.store.address},
            {'name':'appliance_name','content':self.appliance_obj.name},
            {'name':'manufacturer','content':self.appliance_obj.manufacturer},
            {'name':'model','content':self.appliance_obj.model},
            {'name':'serial_num','content':self.appliance_obj.serial_num},
            {'name':'warranty','content':self.appliance_obj.warranty},
            {'name':'appliance_status','content':remarks},
            {'name':'service_type','content':priority},
            {'name':'provider_name','content':self.provider_obj.name},
            {'name':'accept_link','content':'<a class="mcnButton " title="ACCEPT" href="' + estimation_link + '" target="_blank" style="font-weight: bold;letter-spacing: normal;line-height: 100%;text-align: center;text-decoration: none;color: #FFFFFF;">ACCEPT</a>'},
            {'name':'reject_link','content':'<a class="mcnButton " title="REJECT" href="' + estimation_link + '" target="_blank" style="font-weight: bold;letter-spacing: normal;line-height: 100%;text-align: center;text-decoration: none;color: #FFFFFF;">REJECT</a>'},
        ]
        to = [{'email':self.provider_user.key().name(),'name':self.provider_user.name,'type':'to'},
              {'email':self.owner_user.key().name(),'name':self.owner_user.name,'type':'cc'},
              {'email':self.manager_user.key().name(),'name':self.provider_user.name,'type':'cc'}]
        send_mandrill_email('work-order-created', template_content, to)

    def send_wo_approval_email(self, estimate, wo_id):
        appliance = Appliance.get_by_id(long(self.appliance))
        store = appliance.store
        provider = Provider.get_by_id(long(self.provider))
        provider_user = provider.owner
        owner = Member.get_by_key_name(store.owner)
        manager = Member.get_by_key_name(store.manager)
        template_content = [
            {'name':'owner_name','content':owner.name},
            {'name':'appliance_type','content':appliance.manufacturer+':'+appliance.model},
            {'name':'estimate','content':estimate},
            {'name':'provider_name','content':provider.name},
            {'name':'approval_link','content':'<a href="http://onepointapp.appspot.com/work_order/list?work_order='+str(wo_id)+'">here</a>'},
            {'name':'disapproval_link','content':'<a href="http://onepointapp.appspot.com/work_order/list?work_order='+str(wo_id)+'">here</a>'}
        ]
        to = [{'email':owner.key().name(),'name':owner.name,'type':'to'}]
        send_mandrill_email('approve-work-order', template_content, to)

    def send_wo_disapproved_email(self, wo_id):
        appliance = Appliance.get_by_id(long(self.appliance))
        store = appliance.store
        provider = Provider.get_by_id(long(self.provider))
        provider_user = provider.owner
        template_content = [
            {'name':'appliance_type','content':appliance.manufacturer+':'+appliance.model},
            {'name':'provider_name','content':provider.name},
            {'name':'store_name','content':store.name}
        ]
        to = [{'email':provider_user.key().name(),'name':provider_user.name,'type':'to'}]
        send_mandrill_email('work-order-disapproved', template_content, to)

    def send_wo_approved_email(self, wo_id):
        appliance = Appliance.get_by_id(long(self.appliance))
        store = appliance.store
        provider = Provider.get_by_id(long(self.provider))
        provider_user = provider.owner
        template_content = [
            {'name':'appliance_type','content':appliance.manufacturer+':'+appliance.model},
            {'name':'provider_name','content':provider.name},
            {'name':'store_name','content':store.name}
        ]
        to = [{'email':provider_user.key().name(),'name':provider_user.name,'type':'to'}]
        send_mandrill_email('work-order-approved', template_content, to)

    def send_wo_completed_email(self, wo_id):
        template_content = [
            {'name':'store_name','content':self.store.name},
            {'name':'appliance_type','content':self.appliance_obj.manufacturer+':'+self.appliance_obj.model},
            {'name':'provider_name','content':self.provider_obj.name}
        ]
        to = [{'email':self.provider_user.key().name(),'name':self.provider_user.name,'type':'cc'},
              {'email':self.owner_user.key().name(),'name':self.owner_user.name,'type':'to'},
              {'email':self.manager_user.key().name(),'name':self.provider_user.name,'type':'to'}]
        send_mandrill_email('work-order-completed', template_content, to)

    def send_wo_rejected_email(self, remarks):
        template_content = [
            {'name':'store_name','content':self.store.name},
            {'name':'appliance_type','content':self.appliance_obj.manufacturer+':'+self.appliance_obj.model},
            {'name':'provider_name','content':self.provider_obj.name}
        ]
        to = [{'email':self.provider_user.key().name(),'name':self.provider_user.name,'type':'to'},
              {'email':self.owner_user.key().name(),'name':self.owner_user.name,'type':'cc'},
              {'email':self.manager_user.key().name(),'name':self.provider_user.name,'type':'cc'}]
        send_mandrill_email('work-order-rejected', template_content, to)

    def store_login(self, role):
        if role == 'manager' or role == 'owner':
            return True
        return False

    def provider_login(self, role):
        if role == 'provider':
            return True
        return False

    def owner_login(self, role):
        if role == 'owner':
            return True
        return False    

    def update_state(self, params, role):
        ret_val = {'status':'success'}
    	if not self.curr_state:
            if not self.store_login(role):
                ret_val = {'status':'error', 'message':'Only a store manager or owner can create a work order'}
                return ret_val
            self.curr_state = work_order_states[0]
            self.appliance = params['appliance']
            self.provider = params['provider']
            notes = params['remarks'] + separator + params['priority']
            self.create_wo_history(notes)
            self.put()
            self.send_wo_created_email(self.key().id(), params['remarks'], params['priority'])
        elif self.curr_state == 'ESTIMATED':
            if not self.owner_login(role):
                ret_val = {'status':'error', 'message':'Only a store owner can approve a work order'}
                return ret_val
            if params['approval'] == '1':
                self.curr_state = 'APPROVED'
                self.send_wo_approved_email(self.key().id())
            else:
                self.curr_state = 'DISAPPROVED'
                self.send_wo_disapproved_email(self.key().id())
            self.create_wo_history(None)
            self.put()
            self.put()
        elif self.curr_state == 'APPROVED':
            self.curr_state = work_order_states[work_order_states.index(["APPROVED", "DISAPPROVED"]) + 1]
            self.create_wo_history(None)
            self.put()
        elif self.curr_state == 'PROVIDER_CHECKED_IN':
            self.curr_state = work_order_states[work_order_states.index('PROVIDER_CHECKED_IN') + 1]
            self.create_wo_history(params['notes'])
            self.put()
            self.send_wo_completed_email(self.key().id())
        return ret_val

    def estimate(self, notes, approval_str):
        ret_val = {'status':'success'}
        if self.curr_state != 'CREATED':
            ret_val = {'status':'error', 'message':'Only a work order in created state can be estimated'}
            return ret_val
        approval = int(approval_str)
        self.create_wo_history(notes)
        if approval == 1:
            estimate = long(notes)
            if estimate > 250:
                self.curr_state = "ESTIMATED"
                self.send_wo_approval_email(notes, self.key().id())
            else:
                self.curr_state = 'APPROVED'
                self.create_wo_history(None)
                self.send_wo_approved_email(self.key().id())
        else:
            self.curr_state = "REJECTED"
            self.send_wo_rejected_email(notes)
        self.put()
        return ret_val

    def get_action_url(self, role):
        if self.curr_state == 'CREATED':
            return self.action_url if role == 'provider' else None
        elif self.curr_state == 'ESTIMATED':
            return self.action_url if role == 'owner' else None
        elif self.curr_state == 'APPROVED':
            return self.action_url if role == 'owner' or role == 'manager' else None
        elif self.curr_state == 'PROVIDER_CHECKED_IN':
            return self.action_url if role == 'owner' or role == 'manager' else None
        return None
