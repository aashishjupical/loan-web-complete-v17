from odoo import api, fields, models, _
import socket
from datetime import datetime, date, timedelta
import pytz

class TerminateWizard(models.TransientModel):
    _name = 'terminate.wizard'
    _description = 'Termination from loan'

    terminate_reason_id = fields.Many2one('terminate.reason', string="Termination Reason")
    user_id = fields.Many2one('res.users', string="User", default=lambda self: self.env.user)
    task_id = fields.Many2one('project.task', string="project Task", default=lambda self: self.env.context.get('active_id'))
    terminate_date = fields.Datetime('Terminate Date', default=fields.Datetime.now)

    def terminated(self):
        self.task_id.write({
            'stage_id': self.env.ref('jt_loan_project.project_loan_stage_7').id,
            'terminate_reason_id': self.terminate_reason_id,
            'terminate_user_id': self.user_id,
            'terminate_date': self.terminate_date,
            'terminate_ip': self.task_id.current_ip,
        })
        cur_time = datetime.now(pytz.timezone('UTC'))
        con_date_str = cur_time.strftime("%Y-%m-%d %H:%M:%S")
        con_str_date = datetime.strptime(con_date_str,"%Y-%m-%d %H:%M:%S")
        # Send Terminate email to user when click on terminate button
        template = self.env.ref('jt_loan_project.terminate_mail_template')
        if self.task_id.app_form_date:
            a_date = self.task_id.get_user_time(self.task_id.app_form_date,self.env.user.partner_id.tz)
        else :
            a_date = ""
        # msg = '<p>Your Loan has been Rejected</p><br/><p>We are Sorry,Your Loan has been Rejected.</p><br/><b>Application No. :</b>'+str(self.task_id.loan_pro_id.name and self.task_id.loan_pro_id or '')+',<br/><b>Date Applied :</b>'+str(a_date and a_date or '')
        if template:
            template.sudo().with_context({'a_date':a_date}).send_mail(self.task_id.id, force_send=True)

class TerminateReason(models.Model):
    _name = 'terminate.reason'
    _description = 'Reason for laon Termination'

    name = fields.Char(string="Reason")