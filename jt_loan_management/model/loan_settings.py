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

from odoo import api, fields, models,_
from odoo.exceptions import UserError

class ResConfigSettings(models.TransientModel):

    _inherit = 'res.config.settings'

    write_off_account_id = fields.Many2one('account.account', string='Write-Off Account', related="company_id.loan_write_off_account_id")
    interest_prod_id = fields.Many2one('product.product', string='Interest Product',
            help='Product used to invoice as interest of the loans.', related="company_id.loan_interest_prod_id")
    processing_fee_prod_id = fields.Many2one('product.product', string='Processing Fee',
           help='Product used as Processing fee of the loans.', related="company_id.loan_processing_fee_prod_id")
    acc_rec_id = fields.Many2one('account.account', string="Loan Account Receivable", related="company_id.loan_acc_rec_id")
    income_acc_id = fields.Many2one('account.account', string="Loan Income Account", related="company_id.loan_income_acc_id")
    loan_jou_id = fields.Many2one('account.journal', string="Loans Journal", related="company_id.loan_jou_id")
    disbursement_acc_id = fields.Many2one('account.account', string="Disbursement Account", related="company_id.loan_disbursement_acc_id")
    disbursement_journal_id = fields.Many2one('account.journal', string="Disbursement Journal", related="company_id.loan_disbursement_journal_id",)
    inv_create_date = fields.Integer(string='No. of Days', related="company_id.loan_inv_create_date", help="Installment Invoice Create Date before how much days from installment due date.")
    penalty_product_id = fields.Many2one("product.product", related="company_id.penalty_product_id")
    principal_product_id = fields.Many2one("product.product", related="company_id.loan_principal_prod_id")
    penalty_option = fields.Selection([
        ('penalty', 'Penalty'),
        ('interest', 'Interest')],
        string="Penalty / Interest ?",
        default='penalty')
    invoice_type = fields.Selection([
        ('out_invoice','Customer Invoice'),
        ('in_invoice', 'Supplier Invoice')],
        string="Invoice Type",
        default='out_invoice')
    charge_option = fields.Selection([
        ('fixed', 'Fixed'),
        ('percentage', 'Percentage')],
        default='fixed',
        string="Due penalty method")

    charge = fields.Float(string="Charge", digits=(16, 2))
    of_days = fields.Integer(string="Allow # of days after due", default=2)
    loan_counter = fields.Integer(related="company_id.loan_counter")
    down_payment = fields.Boolean(string="Enable Down Payment")

    @api.constrains('invoice_type')
    def change_move_type(self):
        for rec in self:
            loan_jou_id = self.env.company.sudo().loan_jou_id or False
            if not loan_jou_id:
                raise UserError(_("Please Configure Loan Journal from Loans -> Configurations -> Settings!"))
            elif rec.invoice_type == 'out_invoice' and loan_jou_id and loan_jou_id.type != 'sale':
                raise UserError(_("Please Configure Loan Customer Journal from Loans -> Configurations -> Settings!"))
            elif rec.invoice_type == 'in_invoice' and loan_jou_id and loan_jou_id.type != 'purchase':
                raise UserError(_("Please Configure Loan Vendor Journal from Loans -> Configurations -> Settings!"))

    @api.onchange('penalty_option')
    def onchange_penalty_option(self):
        if self.penalty_option == 'interest':
            self.charge_option = 'percentage'
        if not self.penalty_option:
            self.charge_option = False
            self.charge = 0.00
            self.of_days = 2
            
    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()
        penalty_option = ICPSudo.get_param(
            'jt_loan_management.penalty_option')
        invoice_type = ICPSudo.get_param(
            'jt_loan_management.invoice_type')
        charge_option = ICPSudo.get_param(
            'jt_loan_management.charge_option')
        charge = float(ICPSudo.get_param(
            'jt_loan_management.charge'))
        of_days = int(ICPSudo.get_param(
            'jt_loan_management.of_days'))
        down_payment = bool(ICPSudo.get_param(
            'jt_loan_management.down_payment'))

        res.update(
            penalty_option=penalty_option,
            invoice_type=invoice_type,
            charge_option=charge_option,
            charge=charge,
            of_days=of_days,
            down_payment=down_payment,
        )
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()
        ICPSudo.set_param(
            'jt_loan_management.down_payment', self.down_payment)
        charge_option = self.charge_option
        if self.penalty_option == 'interest':
            charge_option = 'percentage'
        ICPSudo.set_param(
            'jt_loan_management.penalty_option', self.penalty_option)
        ICPSudo.set_param(
            'jt_loan_management.invoice_type', self.invoice_type)
        ICPSudo.set_param(
            'jt_loan_management.charge_option', charge_option)
        ICPSudo.set_param('jt_loan_management.charge', self.charge)
        ICPSudo.set_param(
            'jt_loan_management.of_days', self.of_days or 2)