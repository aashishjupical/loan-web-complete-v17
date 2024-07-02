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
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from odoo.exceptions import UserError,ValidationError
from dateutil.relativedelta import relativedelta as rd
from dateutil import relativedelta
import logging

_logger = logging.getLogger(__name__)

class AccountLoanPayAmount(models.TransientModel):
    _name = 'account.loan.pay.amount'
    _description = "Extra Amount"

    loan_id = fields.Many2one(
        'account.loan',
        required=True,
        readonly=True,
    )
    currency_id = fields.Many2one(
        'res.currency',
        related='loan_id.currency_id',
        readonly=True
    )
    cancel_loan = fields.Boolean(
        default=False, string='Close Loan'
    )
    date = fields.Date(required=True, default=fields.Date.today(), string="Payment Date")
    amount = fields.Monetary(
        currency_field='currency_id',
        string='Amount to Pay',
    )
    extra_payment = fields.Selection([('pay_1','Settle with next due instalment rest with principal'),
                                    ('pay_2','Cover all next due installments'),
                                    ('pay_3','Cover only principal outstanding')], string='Extra Payment Type',
                                     default='pay_2')

    journal_id = fields.Many2one('account.journal', string='Payment Journal')
    residual_amount = fields.Float(string="Unpaid invoices")
    remaining_principal_amount = fields.Float(string="Remaining Principal")

    @api.onchange('cancel_loan')
    def _onchange_cancel_loan(self):
        if self.cancel_loan:
            amount_to_reduce = 0.0
            for loan_line in self.loan_id.line_ids:
                if loan_line.invoice_ids:
                    for line_invoice in loan_line.invoice_ids:
                        if line_invoice.state == 'open':
                            amount_to_reduce += line_invoice.amount_residual
                            self.residual_amount = amount_to_reduce

            remaining_installment = self.env['account.loan.line'].search([('loan_id', '=', self.loan_id.id),
                ('invoice_ids','=',False),('payment_amount', '!=', self.loan_id.down_payment)], limit=1)
            if remaining_installment:
                amount_to_reduce += remaining_installment.pending_principal_amount
            self.amount = amount_to_reduce
            self.remaining_principal_amount = remaining_installment.pending_principal_amount


    def new_line_val(self, sequence, date, amount):
        return {
            'loan_id': self.loan_id.id,
            'sequence': sequence,
            'date': date,
            'pending_principal_amount': amount,
        }

    def new_line_vals(self, sequence, date, amount, payment):
        if self.extra_payment == 'pay_3':
            amount = amount - self.amount
        else:
            amount = amount
        if not self.loan_id.round_on_end:
            interests_amount = self.currency_id.round(
                amount * self.loan_id.rate_period / 100)
            if sequence == self.loan_id.periods:
                if self.extra_payment == 'pay_3':
                    payment_amount = amount + interests_amount - self.loan_id.residual_amount - self.amount
                else:
                    payment_amount = amount + interests_amount - self.loan_id.residual_amount
            else:
                payment_amount = self.currency_id.round(payment)
        else:
            interests_amount = (
                amount * self.loan_id.rate_period / 100)
            if sequence == self.loan_id.periods:
                if self.extra_payment == 'pay_3':
                    payment_amount = amount + interests_amount - self.loan_id.residual_amount - self.amount
                else:
                    payment_amount = amount + interests_amount - self.loan_id.residual_amount
            else:
                payment_amount = payment

        return {
            'loan_id': self.loan_id.id,
            'sequence': sequence,
            'payment_amount': payment_amount,
            'interests_amount': interests_amount,
            'date': date,
            'pending_principal_amount': amount
        }

    def compute_loan_lines(self):
        self.ensure_one()
        self.loan_id.fixed_periods = self.loan_id.periods
        self.loan_id.fixed_loan_amount = self.loan_id.loan_amount
        amount = self.loan_id.loan_amount
        sequence = len(self.loan_id.line_ids) + 1
        payment = self.amount
        if self.loan_id.is_down_payment and self.loan_id.state == 'posted':
            amount -= self.loan_id.down_payment
            payment = self.loan_id.loan_amount - self.loan_id.down_payment
            self.loan_id.fixed_loan_amount = payment
        if self.loan_id.start_date:
            date = datetime.strptime(str(self.loan_id.start_date), DF).date()
        else:
            date = datetime.today().date()
        delta = relativedelta(months=self.loan_id.method_period)
        if self.loan_id.line_ids:
            return True
        else:
            if not self.loan_id.payment_on_first_period:
                date += delta
        inv_lines = self.env['account.move'].search([('loan_line_id', '=', self.loan_id.id)])
        if inv_lines:
            pass
        else:
            for i in range(sequence, self.loan_id.periods + 1):
                line = self.env['account.loan.line'].create(
                    self.new_line_vals(i, date, amount, payment)
                )
                line.check_amount()
                date += delta
                amount -= line.payment_amount - line.interests_amount

    def invoice_line_vals(self, line):
        prod_obj = self.env['product.product']
        principal_prod_id = self.env.company and self.env.company.sudo().loan_principal_prod_id
        interest_prod_id = self.env.company and self.env.company.sudo().loan_interest_prod_id
        principal_prod = prod_obj.browse(int(principal_prod_id))
        interest_prod = prod_obj.browse(int(interest_prod_id))

        vals = list()
        loan = line.loan_id

        dict = {
            'name': "Principal Amount",
            'quantity': 1,
            'price_unit': line.principal_amount,
        }

        if principal_prod.property_account_income_id:
            account_id = principal_prod.property_account_income_id
        else:
            account_id = principal_prod.categ_id.property_account_income_categ_id
        dict.update({'product_id': principal_prod and principal_prod.id or False,
                     'name': principal_prod.name,
                     'account_id': account_id and account_id.id or False,
                     })

        vals.append(dict)
        if line.interests_amount != 0:
            dict_interest = {
                'name': "Interest",
                'quantity': 1,
                'price_unit': line.interests_amount,
            }

            if interest_prod.property_account_income_id:
                account_id = interest_prod.property_account_income_id
            else:
                account_id = interest_prod.categ_id.property_account_income_categ_id
            dict_interest.update({'product_id': interest_prod and interest_prod.id or False,
                                  'name': interest_prod.name,
                                  'account_id': account_id and account_id.id or False,
                                  })
            vals.append(dict_interest)
        return vals

    def create_payment(self, invoice, date, amount, journal):
        if invoice:
            payment_obj = self.env['account.payment']
            sequence_code = 'account.payment.customer.invoice'
            default_journal = self.env['account.journal'].search([('type','=','bank')], limit=1)
            payment_data = {
                'payment_type': 'inbound',
                'partner_type': 'customer',
                'name': self.env['ir.sequence'].with_context(ir_sequence_date=date).next_by_code(sequence_code),
                'partner_id': invoice.partner_id and invoice.partner_id.id or False,
                'amount': amount,
                'date': date,
                'ref': invoice.name,
                'journal_id': journal and journal.id if journal else default_journal and default_journal.id or False,
                'payment_method_line_id': journal.inbound_payment_method_line_ids[0].payment_method_id.id if journal.inbound_payment_method_line_ids \
                    else False
            }
            payment = payment_obj.create(payment_data)
            if payment:
                payment.action_post()   
                if payment and invoice.line_ids:        
                    # When using the payment tokens, the payment could not be posted at this point (e.g. the transaction failed)        
                    # and then, we can't perform the reconciliation.        
                    payment_lines = payment.line_ids
                    for account in payment_lines.account_id:        
                        (payment_lines + invoice.line_ids).filtered_domain([('account_id', '=', account.id), ('reconciled', '=', False)]).reconcile() 
            return payment

    def create_invoice_with_payment_date(self, loan_line, journal_id, account_id):
        due_date = datetime.strptime(str(loan_line.date), DF).date()
        ins_date = self.loan_id.inv_create_date
        invoice_date = due_date - rd(days=ins_date)
        loan_line.loan_id.inv_counter = loan_line.loan_id.inv_counter + 1   
        payment_term_id = self.env['account.payment.term'].search([('name','=','Immediate Payment')])             
        invoice = self.env['account.move'].create({
            'loan_line_id': loan_line.id,
            'loan_id': loan_line.loan_id.id,
            'invoice_payment_term_id':payment_term_id and payment_term_id.id or False,
            'partner_id': self.loan_id.partner_id.id,
            'currency_id': self.loan_id.company_id.currency_id.id,
            'move_type': 'out_invoice',
            'invoice_date_due': due_date,
            'invoice_date': invoice_date,
            'journal_id': journal_id or False,
            'company_id': self.env.user.company_id.id,
            'invoice_line_ids': [(0, 0, vals) for vals in self.invoice_line_vals(loan_line)]
        })
        return invoice

    def create_invoice(self, line, date):
        loan_acc_rec_id = self.env.company and self.env.company.sudo().loan_acc_rec_id
        if not loan_acc_rec_id:
            raise Warning(_("Please Configure 'Loan Account Receivable' from Loans -> Configurations -> Settings!"))
        loan_acc_rec = self.env['account.account'].browse(int(loan_acc_rec_id))

        loan_jou_id = self.env.company and self.env.company.sudo().loan_jou_id
        if not loan_jou_id:
            raise Warning(_("Please Configure Loan Journal from Loans -> Configurations -> Settings!"))
        loan_jou = self.env['account.journal'].browse(int(loan_jou_id))

        inv_obj = self.env['account.move']
        due_date = datetime.strptime(str(line.date), DF).date()
        ins_date = self.loan_id.inv_create_date
        invoice_date = due_date - rd(days=ins_date)
        line.loan_id.inv_counter = line.loan_id.inv_counter + 1 
        payment_term_id = self.env['account.payment.term'].search([('name','=','Immediate Payment')])

        inv_data = {
            'loan_line_id': line.id,
            'loan_id': line.loan_id.id,
            'name':str(line.loan_id.name)+'-'+str(line.loan_id.inv_counter),    
            'partner_id': line.loan_id.partner_id.id,
            'currency_id': self.loan_id.company_id.currency_id.id,
            'move_type': 'out_invoice',
            'invoice_date_due': due_date,
            'invoice_payment_term_id':payment_term_id and payment_term_id.id or False,
            'invoice_date': invoice_date,
            'journal_id': loan_jou and loan_jou.id or False,
            'company_id': self.env.user.company_id.id,
            'emi': True,
            'invoice_line_ids': [(0, 0, vals) for vals in line.invoice_line_vals()]
        }
        inv_id = inv_obj.create(inv_data)
        if inv_id:
            inv_id.action_post()
            return inv_id

    def remove_zero_amt_and_change_amt(self, loan, loan_line_obj):
        zero_lines = loan_line_obj.search([('loan_id', '=', loan.id),
                                                           ('pending_principal_amount', '<=', 0)])
        if zero_lines:
            zero_lines.unlink()

    def change_next_lines(self, loan, loan_line_obj, loan_line, date):
        add_in_last_line = False
        created_line_sequence = loan_line.sequence
        next_lines = loan_line_obj.search([('sequence', '>', created_line_sequence), ('loan_id', '=', loan.id)])
        last_lines = []
        for loan_line in next_lines:
            need_to_update = True
            if loan_line.invoice_ids and loan_line.invoice_ids[0] and loan_line.invoice_ids[0].name \
                and loan_line.invoice_ids[0].name[-1] == 'A':
                need_to_update = False
            if need_to_update:
                if add_in_last_line:
                    last_lines.append(loan_line)
                before_line = loan_line_obj.search([('loan_id', '=', loan.id), ('sequence', '=', loan_line.sequence - 1)],
                                                   limit=1)
                if before_line:
                    loan_line.pending_principal_amount = before_line.pending_principal_amount - \
                                                       before_line.principal_amount
                    if not loan_line.invoice_ids:
                        if not loan.round_on_end:
                            loan_line.interests_amount = self.currency_id.round(
                                loan_line.pending_principal_amount * loan.rate_period / 100)
                        else:
                            loan_line.interests_amount = (
                                loan_line.pending_principal_amount * loan.rate_period / 100)
                            loan_line.principal_amount = loan_line.payment_amount - loan_line.interests_amount
                    if loan_line.pending_principal_amount <= loan_line.payment_amount:
                        add_in_last_line = True
                        loan_line.payment_amount = loan_line.pending_principal_amount + \
                                                   loan_line.interests_amount
                        loan_line.principal_amount = loan_line.pending_principal_amount

        for line in last_lines[1:]:
            line.unlink()

    def do_process_for_without_invoices_loan(self, loan, loan_line_obj, loan_loan_jou_id, date, loan_acc_rec,
                                             loan_acc_rec_id, payments):
        next_lines = loan_line_obj.search([('invoice_ids', '=', False), ('loan_id', '=', loan.id)])
        if next_lines:
            next_lines[0].payment_amount = self.amount
            next_lines[0].interests_amount = 0
            next_lines[0].principal_amount = self.amount
            if not loan_acc_rec:
                raise Warning(_("Please Configure 'Account receivable' from Loan ->"
                                " Configuration -> Setting!"))
            if not loan.partner_id:
                raise ValidationError(_('Enter Customer Name'))
            invoice = self.create_invoice_with_payment_date(next_lines[0], int(loan_loan_jou_id),
                                                            int(loan_acc_rec_id))
            if invoice:
                invoice.action_post()
                payment = self.create_payment(invoice, date, next_lines[0].principal_amount,
                                               self.journal_id)
                payments.append(payment)
            for line in next_lines[1:]:
                before_line = loan_line_obj.search([('loan_id', '=', loan.id),
                                                    ('date', '<', line.date)], limit=1, order='id desc')
                line.pending_principal_amount = before_line.pending_principal_amount - \
                                                before_line.principal_amount
                if not loan.round_on_end:
                    line.interests_amount = self.currency_id.round(
                        line.pending_principal_amount * loan.rate_period / 100)
                else:
                    line.interests_amount = (
                        line.pending_principal_amount * loan.rate_period / 100)
                    line.principal_amount = line.payment_amount - line.interests_amount
            self.remove_zero_amt_and_change_amt(loan, loan_line_obj)
            last_line = loan_line_obj.search([('loan_id', '=', loan.id)], order='id desc', limit=1)
            if last_line:
                if not loan.round_on_end:
                    last_line.interests_amount = self.currency_id.round(
                        last_line.pending_principal_amount * loan.rate_period / 100)
                else:
                    last_line.interests_amount = (
                        last_line.pending_principal_amount * loan.rate_period / 100)
                last_line.payment_amount = last_line.pending_principal_amount + last_line.interests_amount

    def _get_payment_refernce(self, payments):
        name_referece = []
        for payment in payments:
            name_referece.append(payment.name)
        return name_referece

    def run(self):
        self.ensure_one()
        loan_acc_rec_id = self.env.company and self.env.company.sudo().loan_acc_rec_id
        if not loan_acc_rec_id:
            raise Warning(_("Please Configure 'Loan Account Receivable' from Loans -> Configurations -> Settings!"))
        loan_acc_rec = self.env['account.account'].browse(int(loan_acc_rec_id))

        loan_jou_id = self.env.company and self.env.company.sudo().loan_jou_id
        if not loan_jou_id:
            raise Warning(_("Please Configure Loan Journal from Loans -> Configurations -> Settings!"))

        loan = self.loan_id
        date = self.date
        all_lines_wihout_moves = True
        for line in loan.line_ids:
            if line.invoice_ids:
                all_lines_wihout_moves = False
                break
        loan_line_obj = self.env['account.loan.line']
        payments = []
        invoices = []
        if self.cancel_loan and self.amount:
            has_invoice_loan_lines = loan_line_obj.search([('loan_id', '=', loan.id),
                    ('invoice_ids','!=', False)])
            for loan_line in has_invoice_loan_lines:
                for invoice in loan_line.invoice_ids:
                    if invoice.state == 'posted' and invoice.payment_state != 'paid' :
                        payment = self.create_payment(invoice, date, invoice.amount_residual, self.journal_id)
                        # payment.action_post()
                        payments.append(payment)
                        invoices.append(invoice)
            loan_lines = loan_line_obj.search([('loan_id', '=', loan.id),
                ('invoice_ids', '=', False), ('payment_amount', '!=', loan.down_payment)])
            if loan_lines:
                principal_amount = 0
                for loan_line in loan_lines:
                    principal_amount += loan_line.principal_amount
                sequence = loan_lines[0].sequence
                loan_lines.unlink()
                new_line = loan_line_obj.create({
                    'sequence':sequence,
                    'date': date,
                    'pending_principal_amount': principal_amount,
                    'payment_amount':principal_amount
                })
                if new_line:
                    if not loan.partner_id:
                        raise ValidationError(_('Enter Customer Name'))
                    invoice = self.create_invoice_with_payment_date(new_line, int(loan_jou_id),
                                                                     int(loan_acc_rec_id))
                    if invoice:
                        invoice.action_post()
                    payment = self.create_payment(invoice, date, invoice.amount_total, self.journal_id)
                    # payment.action_post()
                    payments.append(payment)
                    invoices.append(invoice)
            loan.state = 'closed'
            loan.close_date = date

        if self.extra_payment == 'pay_1' and not self.cancel_loan:
            extra_amount = self.amount
            covered_one_invoice = False
            covered_line = False
            loan_lines = loan_line_obj.search([('loan_id', '=', loan.id), ('is_down_payment', '=', False),
                                               ('emi', '=', True)])
          
            principal_prod = self.env.ref('jt_loan_management.principal_prod')
            for loan_line in loan_lines:
                if extra_amount > 0 and not covered_one_invoice and principal_prod:
                    if loan_line.invoice_ids:
                        for invoice in loan_line.invoice_ids:
                            if extra_amount > 0 and invoice.state not in ('cancel') and invoice.payment_state != 'paid' and not \
                                    covered_one_invoice:
                                if extra_amount < principal_prod.list_price:
                                    amount = extra_amount
                                else:
                                    amount = principal_prod.list_price
                                payment = self.create_payment(invoice, date, amount, self.journal_id)
                                extra_amount -= amount
                                covered_line = loan_line
                                payments.append(payment)
                                invoices.append(invoice)
                    else:
                        invoice = self.create_invoice(loan_line, date)
                        if extra_amount < loan_line.invoice_ids[0].amount_residual:
                            amount = extra_amount
                        else:
                            amount = loan_line.invoice_ids[0].amount_residual
                        extra_amount -= amount
                        payment = self.create_payment(invoice, date, amount, self.journal_id)
                        covered_line = loan_line
                        payments.append(payment)
                        invoices.append(invoice)

            

        if self.extra_payment == 'pay_2' and not self.cancel_loan:
            if self.amount and date:
                extra_amount = self.amount
                loan_lines = loan_line_obj.search([('loan_id', '=', loan.id), ('is_down_payment', '=', False),
                                                   ('emi', '=', True)], order = 'sequence')
                for loan_line in loan_lines:
                    if extra_amount > 0:
                        if loan_line.invoice_ids:
                            for invoice in loan_line.invoice_ids:
                                if invoice.name and not invoice.name[-1] == 'A':
                                    if extra_amount > 0 and invoice.state not in ('cancel') and invoice.payment_state != 'paid':
                                        if extra_amount < invoice.amount_residual:
                                            amount = extra_amount
                                        else:
                                            amount = invoice.amount_residual
                                        payment = self.create_payment(invoice, date, amount, self.journal_id)
                                        extra_amount -= amount
                                        # payment.action_post()
                                        payments.append(payment)
                                        invoices.append(invoice)
                        else:
                            invoice = self.create_invoice(loan_line, date)
                            if extra_amount < loan_line.invoice_ids[0].amount_residual:
                                amount = extra_amount
                            else:
                                amount = loan_line.invoice_ids[0].amount_residual
                            extra_amount -= amount
                            payment = self.create_payment(invoice, date, amount, self.journal_id)
                            # payment.action_post()
                            payments.append(payment)
                            invoices.append(invoice)

        if self.extra_payment == 'pay_3' and not self.cancel_loan:
            if all_lines_wihout_moves:
                if self.amount and date:
                    self.do_process_for_without_invoices_loan(loan, loan_line_obj, int(loan_jou_id), date,
                                                              loan_acc_rec, loan_acc_rec_id, payments)
            else:
                if self.amount and date:
                    extra_amount = self.amount
                    first_line = False
                    last_line_pen_prin = 0
                    last_line_prin = 0
                    first_line_seq = False
                    for loan_line in loan.line_ids:
                        if not loan_line.invoice_ids and not first_line:
                            first_line = loan_line
                            first_line_seq = first_line.sequence
                        if loan_line.invoice_ids and not first_line:
                            last_line_pen_prin = loan_line.pending_principal_amount
                            last_line_prin = loan_line.principal_amount

                    if first_line:
                        next_lines = loan_line_obj.search(
                            [('loan_id', '=', loan.id), ('sequence', '>=', first_line.sequence)], order='sequence desc')

                    if extra_amount > 0:
                        next_lines = loan_line_obj.search(
                            [('invoice_ids', '=', False), ('loan_id', '=', loan.id)], order='sequence desc')
                
                        line_data = {
                            'loan_id': loan.id,
                            'payment_amount': extra_amount,
                            'principal_amount': extra_amount,
                            'interests_amount': 0,
                            'date': date,
                            'pending_principal_amount': last_line_pen_prin - last_line_prin
                        }
                        create_line = loan_line_obj.create(line_data)
                        if create_line:
                            if not loan_acc_rec:
                                raise Warning(_("Please Configure 'Account receivable' from Loan ->"
                                " Configuration -> Setting!"))
                            if not loan.partner_id:
                                raise ValidationError(_('Enter Customer Name'))
                            invoice = self.create_invoice_with_payment_date(create_line, int(loan_jou_id),
                                                                            int(loan_acc_rec_id))
                            if invoice:
                                invoice.action_post()
                                payment = self.create_payment(invoice, date, create_line.principal_amount,
                                                              self.journal_id)
                                # payment.action_post()
                                payments.append(payment)
                                invoices.append(invoice)
                            self.change_next_lines(loan, loan_line_obj, create_line, date)
                            self.remove_zero_amt_and_change_amt(loan, loan_line_obj)

        # Create Payment History
        loan_payment_history_obj = self.env['account.payment.history']
        loan_payment_history_obj.create({
            'amount': self.amount,
            'loan_id': self.loan_id and self.loan_id.id or False,
            'partner_id': self.loan_id.partner_id and self.loan_id.partner_id.id or False,
            'payment_date': self.date,
            'journal_id': self.journal_id and self.journal_id.id or False,
            'payment_ids': [(4, payment.id) for payment in payments],
            'description': 'Payment Received',
            'invoice_ids': [(4, invoice.id) for invoice in invoices],
            'payment_method': self.extra_payment
        })
        # Create Transaction History
        loan_transaction_history_obj = self.env['loan.transaction.history']
        loan_transaction_history_obj.create({
            'date': self.date,
            'loan_id': loan and loan.id or False,
            'reference': ','.join(self._get_payment_refernce(payments)),
            'description': 'Payment Received',
            'credit': self.amount,
            'payment_ids': [(4, payment.id) for payment in payments]
        })