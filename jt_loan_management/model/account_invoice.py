# -*- coding: utf-8 -*-
##############################################################################
#
#    Jupical Technologies Pvt. Ltd.
#    Copyright (C) 2018-TODAY Jupical Technologies Pvt. Ltd.(<http://www.jupical.com>).
#    Author: Jupical Technologies Pvt. Ltd.(<http://www.jupical.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    It is forbidden to publish, distribute, sublicense, or sell copies
#    of the Software or modified copies of the Software.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from odoo import api, fields, models, _
from datetime import datetime, date, timedelta
import logging
from dateutil.relativedelta import *
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from dateutil.relativedelta import relativedelta as rd
_logger = logging.getLogger(__name__)

try:
    import numpy
except (ImportError, IOError) as err:
    _logger.error(err)

class AccountInvoice(models.Model):
    _inherit = 'account.move'

    emi = fields.Boolean('Is Installment?')
    is_down_payment = fields.Boolean('Is Downpayment?')
    splitted_invoice = fields.Boolean("Splitted Invoice")
    main_invoice_id = fields.Many2one("account.move")
    penalty = fields.Boolean(string="Penalty?", copy=False)
    interest_inv_id = fields.Integer(string="Interest inv ref", copy=False)
    interest_due_date = fields.Date(string="Interest Due Date", copy=False)
    penalty_day_counter = fields.Integer("Penalty day counter")
    penalty_charged_till = fields.Date("Penalty Charged Till")
    loan_hide = fields.Boolean(default=False,string="Loan btn hide",copy=False)

    def action_loan_lines(self):
        self.ensure_one()
        source_loan_installments = self.loan_id.line_ids
        result = self.env['ir.actions.act_window']._for_xml_id('jt_loan_management.action_loan_line_view')
        if self.loan_id.processing_fee_inv_id.id == self.id and len(source_loan_installments) > 1:
            result['domain'] = [('id', 'in', source_loan_installments.ids),('loan_id.processing_fee_inv_id','=',self.id)]
            self.loan_hide = False
        # elif len(source_loan_installments) == 1:
        #     result['views'] = [(self.env.ref('jt_loan_management.account_loan_line_form', False).id, 'form')]
        #     result['res_id'] = source_loan_installments.id
        else:
            self.loan_hide = True
            result = {'type': 'ir.actions.act_window_close'}
        return result

    def _prepare_inv_line(self, penalty_prod_id, name, qty, uom_id, unit_price, account_id, invoice):
        invoice_line = {
                'product_id': penalty_prod_id,
                'name': name,
                'quantity': qty,
                'product_uom_id': uom_id,
                'price_unit': unit_price,
                'tax_ids':False,
                'account_id': account_id,
                'move_id':invoice.id
            }
        print ("Invoice Line :::",invoice_line)
        return invoice_line

    def _get_inv_principal(self, inv):
        inv_amount = 0.0
        for inv_line in inv.invoice_line_ids:
            if inv_line.account_id and inv_line.account_id.account_type == 'asset_current':
                inv_amount += inv_line.price_subtotal
            elif inv_line.account_id and inv_line.account_id.account_type == 'income':
                inv_amount += inv_line.price_subtotal
        return inv_amount
        
    @api.model
    def check_due_invoice(self):

        invoice_line_obj = self.env['account.move.line']
        current_date = datetime.strptime(str(fields.Date.context_today(self)), DF).date()
        loan_move_type = self.env['ir.config_parameter'].sudo().get_param('jt_loan_management.invoice_type')
        domain = [('move_type', '=', loan_move_type),
                  ('state', '=', 'posted'),
                  ('payment_state', '!=', 'paid'),
                  ('company_id.id','=',self.env.user.company_id.id)]
        # Checking penalty configuration
        IPC = self.env['ir.config_parameter'].sudo()
        penalty_option = IPC.get_param(
            'jt_loan_management.penalty_option')
        charge_option = IPC.get_param(
            'jt_loan_management.charge_option')
        charge = float(IPC.get_param(
            'jt_loan_management.charge'))
        of_days = int(IPC.get_param(
            'jt_loan_management.of_days'))
        invoice_ids = self.search(domain)
        _logger.info("Checking Due Invoices")
        try:
            if penalty_option:
                penalty_product_id = self.env.company and self.env.company.sudo().penalty_product_id
                name = 'Penalty Charged for'
                if penalty_option == 'interest':
                    name = 'Interest Charged for '
                for inv in invoice_ids:
                    if not inv.penalty_charged_till:
                        due_date = inv.invoice_date_due
                        new_dt = due_date + rd(days=of_days)
                    else:
                        new_dt = inv.penalty_charged_till
                    if new_dt < current_date and inv.loan_id:
                        gap = ((current_date - new_dt).days) - 1
                        new_dt = new_dt + rd(days=gap)
                        inv_principal = self._get_inv_principal(inv)
                        charge_amt = inv.loan_id and inv.loan_id.rate_period_day or 0
                        if penalty_option == 'interest':
                            charge_amt = (charge_amt * inv_principal * gap) / 100
                        elif penalty_option == 'penalty' and charge_option =='percentage':
                            charge_amt = (charge_amt * inv_principal * gap) / 100
                        elif penalty_option =='penalty' and charge_option == 'fixed':
                            charge_amt = (charge_amt * inv_principal * gap) / 100
                        if charge_amt:
                            inv_create_date = self.env.company and self.env.company.sudo().loan_inv_create_date
                            income_acc_id = self.env.company.sudo().loan_income_acc_id and self.env.company.sudo().loan_income_acc_id.id or False
                            account = penalty_product_id.property_account_income_id and penalty_product_id.property_account_income_id.id or income_acc_id
                            invoice = self.env['account.move'].create({'partner_id':inv.partner_id.id,
                                                    'invoice_date_due':inv.invoice_date_due,
                                                    'invoice_date':inv.invoice_date_due - timedelta(days=inv_create_date) or False,
                                                    'penalty_charged_till':new_dt,
                                                    'loan_line_id':inv.loan_line_id.id,
                                                    'loan_id':inv.loan_id.id,
                                                    'is_penlty':True,
                                                    'move_type':loan_move_type})
                            inv_line = self._prepare_inv_line(penalty_product_id.id, name, 1, penalty_product_id.uom_id.id,
                                                               charge_amt, account, invoice)
                            # inv.button_draft()
                            try:
                                invoice_line_obj.create(inv_line)
                                invoice.update({'penalty_charged_till':new_dt})
                                invoice.action_post()
                                inv.penalty_charged_till = new_dt
                            except Exception as error:
                                _logger.error("Error ::",error)
                                # inv.action_post()
            return True
        except:
            _logger.info("Please check due invoice penalty configuration !")

        def write(self, vals):
            result = super(AccountInvoice, self).write(vals)
            if 'date_due' in vals:
                for rec in self:
                    rec.interest_due_date = vals['invoice_date_due']

class PartnerInherit(models.Model):
    _inherit = 'res.partner'

    loan_count = fields.Integer(string='Loans', compute="get_loan_count")
    total_payment_amount = fields.Float('Total Payment Amount', compute='cal_payment_amt')

    # @api.multi
    def cal_payment_amt(self):
        """
        Calculate total payment amount of loan.
        :return:
        """
        pay_his_obj = self.env['account.payment.history']
        for partner in self:
            histories = pay_his_obj.search([('partner_id', '=', partner.id)])
            partner.total_payment_amount = sum(history.amount for history in histories)
    
    # # @api.multi
    def get_loan_count(self):
        """
        Count total loan of partner.
        :return:
        """
        loan = self.env['account.loan']
        for partner in self:
            partner.loan_count = len(loan.search([('partner_id', '=', partner.id)]))
