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
from odoo.exceptions import UserError,ValidationError
import logging
from dateutil.relativedelta import relativedelta as rd
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from datetime import datetime, timedelta
_logger = logging.getLogger(__name__)

class AccountLoanLine(models.Model):
    _name = 'account.loan.line'
    _description = 'Annuity'
    _order = 'sequence asc, paid_on desc, date desc'

    name = fields.Char(compute='_compute_name')
    loan_id = fields.Many2one('account.loan', required=True, readonly=True, ondelete='cascade')
    sequence = fields.Integer(readonly=True)
    date = fields.Date(required=True, help='Date when the payment will be accounted for')
    currency_id = fields.Many2one('res.currency', related='loan_id.currency_id')
    pending_principal_amount = fields.Monetary(currency_field='currency_id', readonly=True,
        help='Pending amount of the loan before the next payment')
    payment_amount = fields.Monetary(currency_field='currency_id', readonly=True,
                                     help='Total amount that will be paid (installment)')
    interests_amount = fields.Monetary(currency_field='currency_id', readonly=True,
        help='Amount from the the payment that will be set aside as interest')
    principal_amount = fields.Monetary(currency_field='currency_id',
        compute='_compute_amounts', help='Amount of the payment that will reduce the pending loan principal amount')
    final_pending_principal_amount = fields.Monetary(currency_field='currency_id',
        compute='_compute_amounts', help='Pending amount of the loan after the payment')
    invoice_ids = fields.One2many('account.move', inverse_name='loan_line_id')
    has_invoices = fields.Boolean(compute='_compute_has_invoices', string="Has Invoices?")
    paid_on = fields.Date('Paid on', compute='_get_paid_date')
    total_invoice_amount = fields.Monetary('Total EMI', compute='get_invoice_amt_detail', store=True)
    total_amount_due = fields.Monetary('Amount Due', compute='get_invoice_amt_detail', store=True)
    all_lines_has_invoice = fields.Boolean('All lines has invoice?', compute='check_all_line_has_invoice', store=True)
    emi = fields.Boolean("Is EMI?")
    is_down_payment = fields.Boolean("Is Down Payment?")
    penalty_amount = fields.Monetary('Penalty', compute='get_invoice_penalty_amount', store=True)
    postpone_penalty = fields.Float("Postpone Penalty",copy=False)
    interests_inv_amt = fields.Boolean(string="Line Invoice Paid",default=False,compute="all_line_has_with_int_invoice",copy=False,store=True)

    @api.depends('invoice_ids.amount_residual')
    def all_line_has_with_int_invoice(self):
        for line in self:
            line.interests_inv_amt = False
            for inv_ln in line.invoice_ids:
                if inv_ln.amount_residual == 0:
                    line.interests_inv_amt = True

    @api.depends('invoice_ids')
    def check_all_line_has_invoice(self):
        """
        Check all line has invoice and based on that displyed Total invoice amt and Total due amt in line list view.
        :return:
        """
        for line in self:
            line.all_lines_has_invoice = False
            if line.has_invoices == True:
                line.all_lines_has_invoice = True

    @api.depends('invoice_ids.invoice_line_ids','postpone_penalty')
    def get_invoice_penalty_amount(self):
        """
        Calculate Total Invoice amount and Total Due Amount of line invoice.
        :return:
        """
        penalty_product_id = self.env.company and self.env.company.sudo().penalty_product_id
        for line in self:
            total_penalty = 0
            if line.invoice_ids:               
                for invoice in line.invoice_ids:
                    total_amt = 0
                    for inv_line in invoice.invoice_line_ids:
                        if inv_line.product_id.id ==  penalty_product_id.id:
                            total_amt += inv_line.price_subtotal
                    total_penalty += total_amt
            line.penalty_amount = total_penalty

    @api.depends('invoice_ids.amount_total')
    def get_invoice_amt_detail(self):
        """
        Calculate Total Invoice amount and Total Due Amount of line invoice.
        :return:
        """
        for line in self:
            if line.invoice_ids:
                total_amt = amt_due = 0
                for invoice in line.invoice_ids:
                    total_amt += invoice.amount_total
                    amt_due += invoice.amount_residual
                line.total_invoice_amount = total_amt
                line.total_amount_due = amt_due

    @api.depends('invoice_ids.state')
    def _get_paid_date(self):
        """
        Update date on 'paid_on' when invoice fully paid.
        :return:
        """
        payment_obj = self.env['account.payment']
        for record in self:
            if not record.paid_on and record.invoice_ids:
                for invoice in record.invoice_ids:
                    payment_ids = payment_obj.search([('reconciled_invoice_ids','in',invoice.ids)])
                    if payment_ids and invoice.amount_residual == 0:
                        list_payment = payment_ids.ids
                        list_payment.sort()
                        last_payment = payment_obj.browse(list_payment[-1])
                        record.paid_on = last_payment.date

    @api.depends('invoice_ids')
    def _compute_has_invoices(self):
        """
        Update has_invoices flag if any invoice is created for line.
        :return:
        """
        for record in self:
            record.has_invoices = bool(record.invoice_ids)

    @api.depends('loan_id.name', 'sequence')
    def _compute_name(self):
        """
        Update loan line name based on loan name and sequence.
        :return:
        """
        for record in self:
            record.name = '%s-%d' % (record.loan_id.name, record.sequence)

    @api.depends('payment_amount', 'interests_amount',
                 'pending_principal_amount')
    def _compute_amounts(self):
        """
        Calculate principal_amount, final_pending_principal_amount and payment_amount.
        :return:
        """
        for rec in self:
            rec.final_pending_principal_amount = (
                rec.pending_principal_amount - rec.payment_amount +
                rec.interests_amount
            )
            rec.principal_amount = rec.payment_amount - rec.interests_amount
            if rec.payment_amount > rec.pending_principal_amount:
                rec.principal_amount = rec.pending_principal_amount
                rec.payment_amount = rec.principal_amount + rec.interests_amount

    def compute_amount(self):
        """
        Computes the payment amount
        :return: Amount to be payed on the annuity
        """
        return self.loan_id.fixed_amount

    def check_amount(self):
        """Recompute amounts if the annuity has not been processed"""
        if self.invoice_ids:
            raise UserError(_(
                'Amount cannot be recomputed if invoices exists '
                'already'
            ))
        if not self.loan_id.round_on_end:
            if self.loan_id.interest_type == 'simple':
                if  self.loan_id.ln_payment_mode == 'bi_monthly':
                    self.interests_amount = self.loan_id.fixed_loan_amount * (self.loan_id.rate_period/2) / 100
                else:
                    self.interests_amount = self.loan_id.fixed_loan_amount * self.loan_id.rate_period / 100
                self.payment_amount = self.currency_id.round(self.compute_amount())
            else:
                if  self.loan_id.ln_payment_mode == 'bi_monthly':
                    self.interests_amount = self.pending_principal_amount * (self.loan_id.rate_period/2) / 100
                else:
                    self.interests_amount = self.currency_id.round(
                        self.pending_principal_amount * self.loan_id.rate_period / 100)
                self.payment_amount = self.currency_id.round(self.compute_amount())
        else:
            if self.loan_id.interest_type == 'simple':
                if  self.loan_id.ln_payment_mode == 'bi_monthly':
                    self.interests_amount = self.loan_id.fixed_loan_amount * (self.loan_id.rate_period/2) / 100
                else:
                    self.interests_amount = self.loan_id.fixed_loan_amount * self.loan_id.rate_period / 100
                self.payment_amount = self.compute_amount()
            else:
                if  self.loan_id.ln_payment_mode == 'bi_monthly':
                    self.interests_amount = self.pending_principal_amount * ((self.loan_id.rate_period/2) / 100)
                else:
                    self.interests_amount = (
                        self.pending_principal_amount * self.loan_id.rate_period / 100)
                self.payment_amount = self.compute_amount()

    def _get_pricelist_price_before_discount(self,product):
        """Compute the price used as base for the pricelist price computation.

        :return: the product sales price in the order currency (without taxes)
        :rtype: float
        """
        self.ensure_one()
        product.ensure_one()

        return self.env['product.pricelist.item']._compute_price_before_discount(
            product=product,
            quantity=1.0,
            uom=product.uom_id,
            date=fields.Datetime.now,
            currency=self.currency_id,
        )

    def _get_display_price(self, product):
        partner = self.loan_id.partner_id
        pricelist = partner.property_product_pricelist
        if pricelist.discount_policy == 'with_discount':
            return product.with_context(pricelist=pricelist.id).lst_price
        final_price = pricelist._get_product_price(product, 1.0, self.currency_id)
        base_price = self._get_pricelist_price_before_discount(product)

        return max(base_price, final_price)

    # def _get_display_price(self, product):
    #     partner = self.loan_id.partner_id
    #     pricelist = partner.property_product_pricelist
    #     if pricelist.discount_policy == 'with_discount':
    #         return product.with_context(pricelist=pricelist.id).lst_price
    #     final_price, rule_id = pricelist.get_product_price_rule(product, 1.0, partner)
    #     context_partner = dict(self.env.context, partner_id=partner.id, date=fields.Datetime.now)
    #     base_price, currency_id = self.with_context(context_partner)._get_real_price_currency(product, rule_id, 1.0,
    #                               product.uom_id, pricelist.id)
    #     return max(base_price, final_price)

    def invoice_line_vals(self):
        vals = list()
        loan = self.loan_id
        product_obj = self.env['product.product']
        interest_prod_id = self.env.company and self.env.company.sudo().loan_interest_prod_id
        principal_prod_id = self.env.company and self.env.company.sudo().loan_principal_prod_id
        # interest_prod = product_obj.browse(int(interest_prod_id))
        income_acc_id = self.env.company and self.env.company.sudo().loan_income_acc_id
        if not principal_prod_id:
            raise UserError(_("Please Configure Principal product from Loans -> Configurations -> Settings!"))
        if not income_acc_id:
            raise UserError(_("Please Configure Income Account from Loans -> Configurations -> Settings!"))
        if not interest_prod_id:
            raise UserError(_("Please configure 'Interest Product' from Loan -> Configurations -> Account"
                            " Setting!"))
        receivable_principal_acc_id = self.env.company.sudo().loan_acc_rec_id and \
                                      self.env.company.sudo().loan_acc_rec_id.id or False
        if not receivable_principal_acc_id:
            raise UserError(
                _("Please Configure Principal Receivable Account from Loans -> Configurations -> Settings!"))
        if self.postpone_penalty:
            penalty_product_id = self.env.company and self.env.company.sudo().penalty_product_id
            name="Penalty Of Postpone"
            vals.append({
                'product_id': penalty_product_id and penalty_product_id.id or False,
                'name': name,
                'quantity': 1,
                'price_unit': self.postpone_penalty,
                'tax_ids':False,
                'account_id': penalty_product_id.property_account_income_id and penalty_product_id.property_account_income_id.id or int(income_acc_id),
            })
        if loan.insurance_product_id:
            insurance_product = loan.insurance_product_id
            vals.append({
                'product_id': insurance_product.id,
                'name': insurance_product.name,
                'quantity': 1,
                'price_unit': self._get_display_price(insurance_product),
                'tax_ids':False,
                'account_id': insurance_product.property_account_income_id and insurance_product.property_account_income_id.id or int(income_acc_id),
            })
        if loan.tax_product_id:
            tax_product = loan.tax_product_id
            vals.append({
                'product_id': tax_product.id,
                'name': tax_product.name,
                'quantity': 1,
                'price_unit': self._get_display_price(tax_product),
                'tax_ids':False,
                'account_id': tax_product.property_account_income_id and tax_product.property_account_income_id.id or int(income_acc_id),
            })
        dict_principal = {
            'quantity': 1,
            'price_unit': self.principal_amount,
            'tax_ids':False,
            'name': "Principal"
        }
        dict_principal.update({'account_id': receivable_principal_acc_id, 'product_id': principal_prod_id.id,})
        vals.append(dict_principal)
        dict_interest = {
            'quantity': 1,
            'price_unit': self.interests_amount,
            'tax_ids':False,
            'product_id': interest_prod_id.id,
            'name': interest_prod_id.name
        }
        dict_interest.update({'account_id': interest_prod_id.property_account_income_id and interest_prod_id.property_account_income_id.id or int(income_acc_id)})
        vals.append(dict_interest)
        return vals

    def create_invoice(self):
        res = []
        acc_rec_id = self.env.company and self.env.company.sudo().loan_acc_rec_id
        if not acc_rec_id:
            raise UserError(_("Please Configure Account receivable from Loan -> Configurations -> Account Setting!"))
        acc_rec = self.env['account.account'].browse(int(acc_rec_id))
        loan_jou_id = self.env.company and self.env.company.sudo().loan_jou_id
        if not loan_jou_id:
            raise UserError(_('Please configure Loan Journal from Loan -> Configurations -> Account Settings!'))
        loan_jou = self.env['account.journal'].browse(int(loan_jou_id))

        if acc_rec and loan_jou:
            for rec in self:
                inv_obj = self.env['account.move']
                due_date = datetime.strptime(str(rec.date), DF).date()
                ins_date = self.loan_id.inv_create_date
                invoice_date = due_date - rd(days=ins_date)
                rec.loan_id.inv_counter = rec.loan_id.inv_counter +1  
                payment_term_id = self.env['account.payment.term'].search([('name','=','Immediate Payment')])
                line_vals = self.invoice_line_vals()
                print ("Line vals :::",line_vals)
                loan_move_type = self.env['ir.config_parameter'].sudo().get_param('jt_loan_management.invoice_type')
                
                inv_data = {
                    'loan_line_id': rec.id,
                    'loan_id': rec.loan_id.id,
                    'partner_id': rec.loan_id.partner_id.id,
                    'currency_id': self.env.company.currency_id.id,
                    'move_type': loan_move_type,
                    'invoice_date_due':due_date,
                    'invoice_payment_term_id':False,
                    'invoice_date': invoice_date,
                    'journal_id': loan_jou and loan_jou.id or False,
                    'company_id': self.env.company.id,
                    'invoice_line_ids': [(0, 0, vals) for vals in
                                         line_vals]
                }
                inv_id = inv_obj.create(inv_data)
                if inv_id:
                    inv_id.emi = True
                    inv_id.action_post()
                res.append(inv_id.id)
            return

    def view_account_values(self):
        """Shows the invoice if it is a leasing or the move if it is a loan"""
        self.ensure_one()
        return self.view_account_invoices()

    def view_process_values(self):
        self.ensure_one()
        amount = 0
        if amount < self.payment_amount:
            if self.loan_id.state != 'posted':
                raise UserError("Please validate loan first")
            self.create_invoice()
            return self.view_account_values()

    def view_account_invoices(self):
        self.ensure_one()
        action = self.env.ref('account.action_move_out_invoice_type')
        result = action.read()[0]
        loan_move_type = self.env['ir.config_parameter'].sudo().get_param('jt_loan_management.invoice_type')
        result['context'] = {
            'default_loan_line_id': self.id,
            'default_loan_id': self.loan_id.id
        }
        result['domain'] = [
            ('loan_line_id', '=', self.id),
            ('move_type', '=', loan_move_type)
        ]
        if len(self.invoice_ids) == 1:
            res = self.env.ref('account.view_move_form')
            result['views'] = [(res and res.id or False, 'form')]
            result['res_id'] = self.invoice_ids.id
        return result
