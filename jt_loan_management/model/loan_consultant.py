# -*- coding: utf-8 -*-

from odoo import api, models, fields, _


class LoanEmployee(models.Model):

	_inherit = 'hr.employee'

	ln_commission_count = fields.Integer(string="Commission Count",compute="get_loan_commision_count")

	def get_loan_commision_count(self):
		loan = self.env['account.loan']
		for partner in self:
			partner.ln_commission_count = len(loan.search([('ln_consultant_id', '=', partner.id)]))