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
import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError, ValidationError
import calendar
from datetime import date, timedelta

class MoveDueDate(models.TransientModel):

    _name = 'move.due.date'
    _description = "Postpone Instaments"

    due_date_selection = fields.Selection([('by_days', 'By Certain Amount of Days'),
                                        ('by_month', 'By Number of Months'),
                                        ('reset', "Reset all Installment's date")],
                                        string="Postpone Installment by", default='by_days')
    property_tax = fields.Boolean("Property Tax", default=True)
    property_ins = fields.Boolean("Property Insurance", default=True)
    # management_fee = fields.Boolean("Management Fee", default=True)
    loan_principal = fields.Boolean("Loan Principal", default=True)
    loan_interest = fields.Boolean("Loan Interest", default=True)
    # any_other_fee = fields.Boolean("Any Other Fee", default=True)
    reason = fields.Text("Reason")
    days_to_add = fields.Integer("Days to Postpone", default=14)
    months_to_add = fields.Integer("Months to Postpone", default=1)
    move_invoices_since = fields.Date("Postpone Installments Since")
    penalty = fields.Boolean("Charge penalty?")
    penalty_type = fields.Selection([('percentage_based', 'Based on Percentage'),('fixed_amt', 'Fixed Amount')],default="percentage_based", string="Charge Penalty")
    charge = fields.Float(string="Charge")
    loan_id = fields.Many2one('account.loan',default=lambda self: self.env.context.get('active_id', None),string="Acconut Loan")

    @api.onchange('penalty_type')
    def onchange_penalty_val(self):
        if self.loan_id and self.penalty_type == 'percentage_based':
            self.charge = self.loan_id.rate_period_day
        else:
            self.charge = 0


    @api.onchange('due_date_selection')
    def onchange_due_date_selection(self):
        if self.due_date_selection and self.due_date_selection=='reset':
            self.charge = 0
            self.penalty = False
            self.penalty_type = False

    def add_penalty_on_postpone(self, line, penalty_added, invoice_id):
        if self.penalty:
            penalty_added = True
            new_line = False
            post_pone_penlty_amt = 0
            if self.penalty_type=='fixed_amt':
                new_line = self.env['account.loan.line'].create({'date':self.move_invoices_since,
                                                                    'loan_id':line.loan_id.id})
                if new_line:
                    new_line.penalty_amount = self.charge
                line.postpone_penalty += self.charge
            elif self.penalty_type=='percentage_based':
                if self.due_date_selection == 'by_days':
                    if line.payment_amount and self.charge and self.days_to_add:
                        postpone_penalty_chrg = (self.charge * line.payment_amount * self.days_to_add) / 100
                        new_line = self.env['account.loan.line'].create({'date':self.move_invoices_since,
                                                                        'loan_id':line.loan_id.id})
                    if new_line:
                        new_line.penalty_amount = postpone_penalty_chrg
                elif self.due_date_selection == 'by_month':
                    if line.payment_amount and self.charge and self.move_invoices_since and self.months_to_add:
                        postponse_days = 0
                        for month in range(self.months_to_add):
                            month_date = self.move_invoices_since + relativedelta(months=month+1)
                            date_moth = month_date.month
                            date_year = month_date.year
                            num_days = calendar.monthrange(date_year, date_moth)[1]
                            postponse_days += num_days
                        if postponse_days:
                            postpone_penalty_chrg = (self.charge * line.payment_amount * postponse_days) / 100
                            new_line = self.env['account.loan.line'].create({'date':self.move_invoices_since,
                                                        'loan_id':line.loan_id.id})
                    if new_line:
                        new_line.penalty_amount = postpone_penalty_chrg

                # if not invoice_id:
                #     total_amount = line.payment_amount 
                #     if line.loan_id.insurance_product_id:
                #         total_amount += line._get_display_price(line.loan_id.insurance_product_id)
                #     if line.loan_id.tax_product_id:
                #         total_amount += line._get_display_price(line.loan_id.tax_product_id)

                #     charge = (total_amount * self.charge)/100
                #     line.postpone_penalty += charge
                # else:
                #     charge = (invoice_id.amount_residual * self.charge)/100
                #     line.postpone_penalty += charge

            # if invoice_id and invoice_id.payment_state != 'paid':
            penalty_product_id = self.env.company and self.env.company.sudo().penalty_product_id
            income_acc_id = self.env.company and self.env.company.sudo().loan_income_acc_id
            inv_create_date = self.env.company and self.env.company.sudo().loan_inv_create_date
            name="Penalty Of Postpone"
            invoice_vals = [(0, 0, {
                    'product_id': penalty_product_id and penalty_product_id.id or False,
                    'name': name,
                    'quantity': 1,
                    'price_unit': new_line and new_line.penalty_amount or 0,
                    'tax_ids':False,
                    'account_id': int(income_acc_id)})]
            loan_move_type = self.env['ir.config_parameter'].sudo().get_param('jt_loan_management.invoice_type')
            invoice = self.env['account.move'].create({'partner_id':line.loan_id.partner_id.id,
                                                'invoice_date_due':new_line and new_line.date or False,
                                                'invoice_date':new_line and new_line.date - timedelta(days=inv_create_date) or False,
                                                'loan_line_id':new_line and new_line.id or False,
                                                'loan_id':new_line and new_line.loan_id.id or False,
                                                'move_type':loan_move_type,
                                                'is_penlty':True,
                                                'invoice_line_ids':invoice_vals})
            if invoice:
                invoice.action_post()
            #     invoice_id.button_cancel()
            #     invoice_id.button_draft()
            #     invoice_id.state = 'draft'
            #     invoice_line_id = invoice_id.invoice_line_ids.filtered(lambda x:x.product_id.id == penalty_product_id.id)
            #     if invoice_line_id:
            #         invoice_line_id[0].price_unit = line.postpone_penalty
            #     else:
            #         name="Penalty Of Postpone"
            #         invoice_id.invoice_line_ids = [(0, 0, {
            #             'product_id': penalty_product_id and penalty_product_id.id or False,
            #             'name': name,
            #             'quantity': 1,
            #             'price_unit': line.postpone_penalty,
            #             'account_id': int(income_acc_id),
            #         })]
            #     invoice_id.action_post()

        return penalty_added

    def _update_due_date(self, loan, due_date_selection):
        old_inv_date = new_inv_date = pay_date = line_new_date = False
        penalty_added = False
        if not self.penalty:
            penalty_added = True
        for line in loan.line_ids:
            if not line.is_down_payment and line.emi:
                updated = False
                for inv in line.invoice_ids:
                    if inv.invoice_date >= datetime.datetime.strptime(str(self.move_invoices_since), DF).date():
                        updated = True
                        if old_inv_date == False:
                            old_inv_date = inv.invoice_date_due
                            invoice_date_due = datetime.datetime.strptime(str(inv.invoice_date_due), DF)
                            if due_date_selection == 'by_days':
                                pay_date = invoice_date_due + relativedelta(days=self.days_to_add)
                            elif due_date_selection == 'by_month':
                                pay_date = invoice_date_due + relativedelta(months=self.months_to_add)
                            inv.invoice_date_due = str(pay_date)
                            inv.invoice_date = str(pay_date - relativedelta(days=loan.inv_create_date))
                            if new_inv_date == False:
                                new_inv_date = inv.invoice_date_due
                            if not penalty_added and not inv.interest_inv_id:
                                penalty_added = self.add_penalty_on_postpone(line,penalty_added,inv)
                if not updated:
                    inv_date = datetime.datetime.strptime(str(line.date), DF) - relativedelta(days=loan.inv_create_date)
                    if inv_date >= datetime.datetime.strptime(str(self.move_invoices_since), DF):
                        if old_inv_date == False:
                            old_inv_date = line.date
                        line_date = datetime.datetime.strptime(str(line.date), DF)
                        if due_date_selection == 'by_days':
                            line_new_date = line_date + relativedelta(days=self.days_to_add)
                        elif due_date_selection == 'by_month':
                            line_new_date = line_date + relativedelta(months=self.months_to_add)
                        line.date = str(line_new_date)
                        if not penalty_added:
                            penalty_added = self.add_penalty_on_postpone(line,penalty_added,False)
                        if new_inv_date == False:
                            new_inv_date = line.date
        loan.expected_end_date = loan.line_ids[-1].date
        return old_inv_date, new_inv_date

    def _create_loan_changes(self, loan, old_inv_date, new_inv_date, monthly_enhance_move_type):
        monthly_enhance_move_type_new = ''
        if self.due_date_selection == 'by_month' and monthly_enhance_move_type == 'whole_invoice':
            monthly_enhance_move_type_new = 'whole_invoice'
        elif self.due_date_selection == 'by_month' and monthly_enhance_move_type != 'whole_invoice':
            monthly_enhance_move_type_new = 'keep_tax_ins'
        loan.loan_payment_change_ids.create({
            'loan_id': loan.id,
            'date': datetime.datetime.today(),
            'due_date_selection': self.due_date_selection,
            'data_added': self.days_to_add if self.due_date_selection == "by_days" else self.months_to_add,
            'reason': self.reason,
            'old_inv_date': old_inv_date,
            'new_inv_date': new_inv_date,
            #'monthly_enhance_move_type': monthly_enhance_move_type_new
        })

    def split_invoice(self, invoice, end_date, insu_prod_id, tax_prod_id, principal_product, interest_product, counter):
        inv_no = invoice.name
        invoice.button_cancel()
        invoice.button_draft()
        invoice.state = 'draft'
        new_invoice = invoice.copy()
        new_invoice.loan_id.inv_counter = new_invoice.loan_id.inv_counter + 1
        if isinstance(end_date, str):
            end_date = datetime.datetime.strptime(str(end_date), DF)
        if new_invoice:
            new_invoice.invoice_date_due = end_date + relativedelta(months=counter)
            due_date = datetime.datetime.strptime(str(invoice.invoice_date_due), DF)
            new_invoice.invoice_date = str(due_date - relativedelta(days=12))
            for new_inv_line in new_invoice.invoice_line_ids:
                if new_inv_line.product_id and not self.property_tax and tax_prod_id and \
                        new_inv_line.product_id.id == tax_prod_id:
                    new_inv_line.with_context(check_move_validity=False).unlink()
                elif new_inv_line.product_id and not self.property_ins and insu_prod_id and \
                        new_inv_line.product_id.id == insu_prod_id:
                    new_inv_line.with_context(check_move_validity=False).unlink()
                elif new_inv_line.product_id and not self.loan_principal and principal_product and \
                        new_inv_line.product_id.id == principal_product:
                    new_inv_line.with_context(check_move_validity=False).unlink()
                elif new_inv_line.product_id and not self.loan_interest and interest_product and \
                        new_inv_line.product_id.id == interest_product:
                    new_inv_line.with_context(check_move_validity=False).unlink()

            # new_invoice.with_context(check_move_validity=False)._onchange_invoice_line_ids()
            new_invoice.with_context(from_move_date=inv_no).action_post()
            new_invoice.splitted_invoice = True
            new_invoice.main_invoice_id = invoice.id
            year = datetime.datetime.strptime(str(new_invoice.invoice_date), DF).year
            month = datetime.datetime.strptime(str(new_invoice.invoice_date), DF).month
            loan_invoice = self.env['loan.invoice'].search([('move_id', '=', new_invoice.id),
                                                            ('loan_id', '=', new_invoice.loan_id.id)])

            if loan_invoice:
                loan_invoice.name = new_invoice.name
                loan_invoice.month = month
                loan_invoice.year = year
                loan_invoice.date_invoice = new_invoice.date_invoice
                loan_invoice.sequence_number = int(loan_invoice.sequence_number) - 1
        for inv_line in invoice.invoice_line_ids:
            if inv_line.product_id and self.property_tax and tax_prod_id and inv_line.product_id.id == tax_prod_id:
                inv_line.with_context(check_move_validity=False).unlink()
            elif inv_line.product_id and self.property_ins and insu_prod_id and inv_line.product_id.id == insu_prod_id:
                inv_line.with_context(check_move_validity=False).unlink()
            elif inv_line.product_id and self.loan_principal and principal_product and \
                    inv_line.product_id.id == principal_product:
                inv_line.with_context(check_move_validity=False).unlink()
            elif inv_line.product_id and self.loan_interest and interest_product and \
                    inv_line.product_id.id == interest_product:
                inv_line.with_context(check_move_validity=False).unlink()
        loan = invoice.loan_id
        new_payment_amount = 0
        if self.loan_principal:
            new_payment_amount += invoice.loan_line_id.principal_amount
        if self.loan_interest:
            new_payment_amount += invoice.loan_line_id.interests_amount
        new_invoice_loan_line = self.env['account.loan.line'].create({
            'sequence': loan.line_ids[-1].sequence + 1,
            'date': new_invoice.invoice_date_due,
            # 'rate': loan.line_ids[-1].rate,
            'pending_principal_amount': invoice.loan_line_id.pending_principal_amount,
            'payment_amount': new_payment_amount,
            'principal_amount': invoice.loan_line_id.principal_amount if self.loan_principal else 0,
            'interests_amount': invoice.loan_line_id.interests_amount if self.loan_interest else 0,
            'final_pending_principal_amount': invoice.loan_line_id.final_pending_principal_amount,
            'loan_id': loan.id
            })
        new_invoice.loan_line_id = new_invoice_loan_line.id
        penalty_added = self.add_penalty_on_postpone(new_invoice_loan_line,False,new_invoice)
        principal_amt = invoice.loan_line_id.principal_amount
        interest_amt = invoice.loan_line_id.interests_amount
        payment_amount = invoice.loan_line_id.payment_amount
        if self.loan_principal:
            payment_amount -= invoice.loan_line_id.principal_amount
        if self.loan_interest:
            payment_amount -= invoice.loan_line_id.interests_amount
        invoice.loan_line_id.payment_amount = payment_amount
        invoice.loan_line_id.principal_amount = 0 if self.loan_principal else principal_amt
        invoice.loan_line_id.interests_amount = 0 if self.loan_interest else interest_amt
        # invoice.with_context(check_move_validity=False)._onchange_invoice_line_ids()
        invoice.action_post()
        counter += 1
        return counter

    def check_invoices(self, loan):
        paid_invoices = self.env['account.move'].search([('loan_id', '=', loan.id),
            ('invoice_date', '>=', self.move_invoices_since), ('payment_state', '=', 'paid')])
        partial_inv = self.env['account.move'].search([('loan_id', '=', loan.id),
            ('invoice_date', '>=', self.move_invoices_since), ('state', '=', 'posted'),
            ('payment_state', '=', 'partial')])
        new_patial_inv = []
        for inv in partial_inv:
            if inv.amount_residual != inv.amount_total:  
                is_paid = False
                payment_ids = self.env['account.payment'].search([('reconciled_invoice_ids','in',inv.ids)])
                for payment in payment_ids:
                    if payment.state in ('posted', 'sent', 'reconciled'):
                        is_paid = True
                if is_paid:
                    new_patial_inv.append(inv)
        if paid_invoices or new_patial_inv:
            raise UserError(_("The invoices can't be moved since %s as payment was " 
                "already registered for an invoice after this date. Please pick "
                "later date for the push back" % str(self.move_invoices_since)))

    def postpone_invoices(self):
        active_id = self._context.get('active_id')
        loan = self.env['account.loan'].search([('id', '=', active_id)])
        inv_obj = self.env['account.move']
        loan_invoices = self.env['loan.invoice']
        monthly_enhance_move_type = ''
        if self.property_ins and self.property_tax and self.loan_principal and self.loan_interest:
            monthly_enhance_move_type = 'whole_invoice'
        if self.due_date_selection == 'reset':
            date = loan.first_payment_due
            if loan.move_by_keep_tax_ins:
                splitted_invoices = inv_obj.search([('loan_id', '=', loan.id),
                    ('splitted_invoice', '=', True)])
                for s_inv in splitted_invoices:
                    main_inv = inv_obj.search([('name', '=', s_inv.name[0:-1]),
                        ('loan_id', '=', loan.id)])
                    if main_inv:
                        if main_inv.payment_state not in ('paid', 'cancel'):
                            main_inv_loan_line = main_inv.loan_line_id
                            invoice_loan_line = s_inv.loan_line_id
                            main_inv_loan_line.principal_amount = invoice_loan_line.principal_amount
                            main_inv_loan_line.payment_amount = invoice_loan_line.payment_amount
                            main_inv_loan_line.interests_amount = invoice_loan_line.interests_amount
                            s_inv.invoice_date = main_inv.invoice_date
                            s_inv.invoice_date_due = main_inv.invoice_date_due
                            s_inv.loan_line_id = main_inv_loan_line.id
                            s_inv.splitted_invoice = False
                            s_inv.main_invoice_id = False
                            main_inv_number = main_inv.name
                            main_inv.action_invoice_cancel()
                            s_inv.action_invoice_cancel()
                            s_inv.action_invoice_draft()
                            s_inv.state = 'draft'
                            for main_inv_line in main_inv.invoice_line_ids:
                                main_inv_line.invoice_id = s_inv.id
                            main_inv.state = 'draft'
                            # mail_loan_invoice = loan_invoices.search([('loan_id', '=', loan.id),
                            #     ('name', '=', main_inv_number)])
                            # if mail_loan_invoice:
                            #     mail_loan_invoice.unlink()
                            s_inv.name = main_inv_number
                            s_inv.action_invoice_open()
                            s_inv.move_id.name = main_inv_number
                            loan_invoice = loan_invoices.search([('loan_id', '=', loan.id),
                                                                 ('invoice_id', '=', s_inv.id)])
                            if loan_invoice:
                                loan_invoice.name = s_inv.name
                            self._cr.execute("DELETE FROM account_invoice WHERE id=%s", (main_inv.id,))
                            self._cr.execute("DELETE FROM account_loan_line WHERE id=%s", (invoice_loan_line.id,))

                for line in loan.line_ids:
                    if not line.is_down_payment and line.emi:
                        if line.paid_on:
                            if date == loan.first_payment_due:
                                date = datetime.datetime.strptime(str(date), DF)
                            else:
                                date = datetime.datetime.strptime(datetime.datetime.strftime(date, DF), DF)
                            date = date + relativedelta(months=loan.method_period)
                            continue
                        line.date = str(date)
                        if line.invoice_ids:
                            invoice = line.invoice_ids[0]
                            if invoice.name and invoice.name[-1] != 'A':
                                invoice.splitted_invoice = False
                                invoice.main_invoice_id = False
                                invoice.invoice_date_due = str(date)
                                invoice_date_due = datetime.datetime.strptime(str(invoice.invoice_date_due), DF)
                                invoice.invoice_date = str(invoice_date_due - relativedelta(days=12))
                        if date == loan.first_payment_due:
                            date = datetime.datetime.strptime(str(date), DF)
                        else:
                            date = datetime.datetime.strptime(datetime.datetime.strftime(date, DF), DF)
                        date = date + relativedelta(months=loan.method_period)
                loan.move_by_keep_tax_ins = False
            else:
                for line in loan.line_ids:
                    if not line.is_down_payment and line.emi:
                        if line.paid_on:
                            if date == loan.first_payment_due:
                                date = datetime.datetime.strptime(str(date), DF)
                            else:
                                date = datetime.datetime.strptime(datetime.datetime.strftime(date, DF), DF)
                            date = date + relativedelta(months=loan.method_period)
                            continue
                        line.date = str(date)
                        if line.invoice_ids:
                            invoice = line.invoice_ids[0]
                            if invoice.name and invoice.name[-1] != 'A':
                                invoice.splitted_invoice = False
                                invoice.main_invoice_id = False
                                invoice.invoice_date_due = str(date)
                                invoice_date_due = datetime.datetime.strptime(str(invoice.invoice_date_due), DF)
                                invoice.invoice_date = str(invoice_date_due - relativedelta(days=12))
                        if date == loan.first_payment_due:
                            date = datetime.datetime.strptime(str(date), DF)
                        else:
                            date = datetime.datetime.strptime(datetime.datetime.strftime(date, DF), DF)
                        date = date + relativedelta(months=loan.method_period)
            loan.loan_payment_change_ids.create({
                'loan_id': loan.id,
                'date': datetime.datetime.today(),
                'due_date_selection': self.due_date_selection,
            })
        elif self.due_date_selection == 'by_days':
            self.check_invoices(loan)
            loan.payment_day += self.days_to_add
            old_inv_date, new_inv_date = self._update_due_date(loan, 'by_days')
            self._create_loan_changes(loan, old_inv_date, new_inv_date, monthly_enhance_move_type)
        elif self.due_date_selection == 'by_month' and monthly_enhance_move_type == 'whole_invoice':
            self.check_invoices(loan)
            old_inv_date, new_inv_date = self._update_due_date(loan, 'by_month')
            self._create_loan_changes(loan, old_inv_date, new_inv_date, monthly_enhance_move_type)
        elif self.due_date_selection == 'by_month' and monthly_enhance_move_type != 'whole_invoice':
            self.check_invoices(loan)
            old_inv_date = new_inv_date = False
            counter = 1
            insu_prod_id = loan.insurance_product_id.id if loan.insurance_product_id else False
            tax_prod_id = loan.tax_product_id.id if loan.tax_product_id else False
            principal_product = int(config_param_obj.get_param('jt_loan_management.principal_prod_id'))
            interest_product = int(config_param_obj.get_param('jt_loan_management.interest_prod_id'))
            end_date = loan.expected_end_date
            for line in loan.line_ids:
                for invoice in line.invoice_ids:
                    if invoice.invoice_date >= self.move_invoices_since:
                        if counter <= self.months_to_add and not invoice.splitted_invoice:
                            if invoice.state == 'open' and invoice.amount_total == invoice.amount_residual and invoice.emi:
                                if not old_inv_date:
                                    old_inv_date = invoice.invoice_date_due
                                counter = self.split_invoice(invoice, end_date, insu_prod_id, tax_prod_id,
                                                             principal_product, interest_product, counter)
                                new_inv_date = invoice.invoice_date_due
            if counter <= self.months_to_add:
                for line in loan.line_ids:
                    if not line.invoice_ids and counter <= self.months_to_add:
                        inv_date = datetime.datetime.strptime(str(line.date), DF) - relativedelta(days=12)
                        if inv_date >= datetime.datetime.strptime(str(self.move_invoices_since), DF):
                            line.create_invoice()
                            for invoice in line.invoice_ids:
                                if not old_inv_date:
                                    old_inv_date = invoice.invoice_date_due
                                counter = self.split_invoice(invoice, end_date, insu_prod_id, tax_prod_id,
                                                             principal_product, interest_product, counter)
                                new_inv_date = invoice.invoice_date_due
            self._create_loan_changes(loan, old_inv_date, new_inv_date, monthly_enhance_move_type)
            loan.move_by_keep_tax_ins =  True
