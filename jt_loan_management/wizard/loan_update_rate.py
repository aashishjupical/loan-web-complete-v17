# -*- coding: utf-8 -*-

from odoo import models,fields,api,_

class UpdateRate(models.TransientModel):

	_name = "update.rate.wizard"
	_description = "Update Rate Wizard"

	name = fields.Char(string="Name")
	update_rate = fields.Float(required=True, default=12.0,digits=(5, 1), help='Currently applied rate')
	loan_id = fields.Many2one('account.loan',string="Loan",default=lambda self: self.env.context.get('active_id', None))


	def confirm_rate(self):
		if self.loan_id:
			self.loan_id.rate = self.update_rate
			self.loan_id.compute_update_rate_lines()
			mail_template = self.loan_id.env.ref('jt_loan_management.email_template_update_rate_loan_details')
			mail_template.send_mail(self.loan_id.id, force_send=True)
