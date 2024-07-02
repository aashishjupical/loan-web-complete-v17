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
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from datetime import datetime, date, timedelta
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta
from dateutil.relativedelta import relativedelta as rd
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT, ustr
import logging
import calendar

_logger = logging.getLogger(__name__)
try:
    import numpy_financial as npf
except (ImportError, IOError) as err:
    _logger.debug(err)

class AccountLoan(models.Model):

    _name = 'account.loan'
    _description = 'Loan'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    def _default_company(self):
        force_company = self._context.get('force_company')
        if not force_company:
            return self.env.company.id
        return force_company

    def _get_next_number(self):
        self.check_access_rights('read')
        force_company = self._context.get('force_company')
        if not force_company:
            force_company = self.env.company.id
        seq_ids = self.env['ir.sequence'].sudo().search([('code', '=', 'account.loan'),
                                ('company_id', 'in', [force_company, False])], limit=1, order='company_id')
        if not seq_ids:
            _logger.debug(
                "No ir.sequence has been found for code '%s'. Please make sure a sequence is set for current "
                "company." % 'account.loan')
            return False
        seq_id = seq_ids[0]
        next_number = str(seq_id.number_next_actual)
        if len(next_number) < 5:
            next_number = '0' * (5 - len(next_number)) + next_number
        name = 'LC' + str(next_number)
        return name

    def get_auto_invoice_days(self):
        for rec in self:
            rec.inv_create_date = self.env.company and self.env.company.sudo().loan_inv_create_date

    name = fields.Char(copy=False, string='Name')
    partner_id = fields.Many2one('res.partner', string='Customer',
                                 help='Name of Customer that borrows the money at an interest rate.')
    company_id = fields.Many2one('res.company', default=_default_company)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('posted', 'Validated'),
        ('cancelled', 'Cancelled'),
        ('closed', 'Closed'),
    ], required=True, copy=False, default='draft', tracking=True)
    line_ids = fields.One2many('account.loan.line', inverse_name='loan_id', copy=False)
    periods = fields.Integer(required=True, string='Installments', default=1,
        help='Number of periods (months) that the loan will last')
    method_period = fields.Integer(string='Time between two installments(In Month)', default=1,
        help="State here the time between 2 installments, in months", required=True)
    inv_create_date = fields.Integer(compute="get_auto_invoice_days",string='No. of Days', help="Installment Invoice Create Date before how much days from installment due date.")
    start_date = fields.Date(copy=False,
        help='Initial date of the loan/first period as given in contract')
    expected_end_date = fields.Date(string="Closing Date", compute="_get_expected_end_date",
        help='Expected end date of closing loan', copy=False)
    close_date = fields.Date(help='Close Date', readonly=True, copy=False)
    interest_type = fields.Selection([('simple','Simple Interest'),('compound','Compound Interest')],default='simple',copy=False)
    rate_type = fields.Selection([('fixed','Fixed'),('variable','Variable')],default="fixed",string="Rate Type",copy=False)
    rate = fields.Float(required=True, default=12.0,string="Rate per year",
        digits=(5, 1), help='Currently applied rate', tracking=True)
    rate_period = fields.Float(string='Rate per month', compute='_compute_rate_period',
        digits=(5, 2), help='Real rate that will be applied on each period')
    rate_period_day = fields.Float(string='Rate per Day', compute='compute_rate_period_day', help='Real rate that will be applied on each period')
    fixed_amount = fields.Monetary(
        currency_field='currency_id',
        compute='_compute_fixed_amount',
    )
    fixed_loan_amount = fields.Monetary(
        currency_field='currency_id',
        readonly=True,
        copy=False,
        default=0,
    )
    fixed_periods = fields.Integer(
        readonly=True,
        copy=False,
        default=0,
    )
    loan_amount = fields.Monetary(currency_field='currency_id', required=True)
    round_on_end = fields.Boolean(default=True,
        help='When checked, the differences will be applied on the last period'
             ', if it is unchecked, the annuity will be recalculated on each '
             'period (i.e. amount won\'t be the same every month).'
    )
    payment_on_first_period = fields.Boolean(default=True,
        help='When checked, the first payment will be expected on Start Date,'
            'otherwise 1 period (month) after the Start Date.')
    currency_id = fields.Many2one('res.currency', readonly=True)
    # is_leasing = fields.Boolean(default=True, string='Is Land Contract')
    product_id = fields.Many2one('product.product', string='Product')
    down_payment = fields.Monetary(currency_field='currency_id', string="Down Payment", required=True)
    residual_amount = fields.Monetary(
        currency_field='currency_id',
        default=0.,
        required=True,
        readonly=True,
        states={'draft': [('readonly', False)]},
        help='Residual amount of the land contract that must be paid at the end '
            ' in order to acquire the property',
    )
    is_down_payment = fields.Boolean(string="Any Down Payment?", default=True)
    insurance_product_id = fields.Many2one('product.product', string='Property Insurance')
    tax_product_id = fields.Many2one('product.product', string='Property Tax')
    invoice_count = fields.Integer(compute='_compute_invoices')
    agent_count = fields.Integer(compute='_compute_agent_invoices')
    is_compute_items = fields.Boolean(string='Compute Items', default=False, copy=False)
    insurance_balance = fields.Float(string='Insurance', compute='cal_ins_tax')
    tax_balance = fields.Float(string='Tax', compute='cal_ins_tax')
    insurance_sale_price = fields.Float(related='insurance_product_id.list_price', store=True,
                                        string="Insurance product price")
    tax_sale_price = fields.Float(related='tax_product_id.list_price', store=True, string="Tax product price")
    loan_inv_ids = fields.One2many('loan.invoice', inverse_name='loan_id', string="Loan Invoices")
    total_invoice_amount = fields.Float("Upcomming Invoice Amount", compute='get_total_invoice_amount')
    total_principal_balance = fields.Float('Principal Balance', compute='cal_princi_inter')
    total_interest_balance = fields.Float('Interest Paid', compute='cal_princi_inter')
    total_received_interest_balance = fields.Float('Interest Paid', compute='cal_rec_princi_inter')
    total_received_principal_balance = fields.Float('Interest Paid', compute='cal_rec_princi_inter')
    first_payment_due = fields.Date(string="Installment Due Date", copy=False)
    loan_payment_change_ids = fields.One2many('loan.changes',inverse_name='loan_id', string="Loan Changes", readonly=1)
    comment = fields.Text("Internal Notes")
    transaction_balance = fields.Float('Transaction Balance', compute='_compute_transcation_balance')
    payment_day = fields.Integer('Payment Day')
    total_payments = fields.Float("Total Paid Payments", compute="compute_total_payments")
    amount_due = fields.Float('Total Amount Due', compute='compute_amount_ln_inv_total', store=True, readonly=True)
    days_past_due = fields.Float('Days Due', compute='compute_amount_and_days_due', store=True, readonly=True)
    processing_fee_inv_id = fields.Many2one('account.move', string="Processing Fee Invoice")
    outstanding_bal = fields.Float("Outstanding Balance", compute='compute_outstanding_bal')
    move_by_keep_tax_ins = fields.Boolean("Moved by Keep Tax and Insurance")
    penalty_paid = fields.Float('Penalty Paid', compute='compute_amount_and_days_due', store=True, readonly=True)
    penalty_pending = fields.Float('Penalty Paid', compute='compute_penalty_pending', store=True, readonly=True)
    penalty_received = fields.Float('Penalty Paid', compute='compute_penalty_pending', store=True, readonly=True)
    penalty_due = fields.Float('Penalty Outstanding', compute='compute_amount_and_days_due', store=True, readonly=True)
    inv_counter = fields.Integer("Count Invoice", default=0, copy=False)
    down_payment_show = fields.Boolean(compute="setting_down_payment_show",string="Show Down Payment",copy=False)
    ln_processing_fee = fields.Float(string="Processing Fee %",copy=False)
    ln_agent_fee = fields.Float(string="Agent Fee %",copy=False)
    ln_consultant_id = fields.Many2one('hr.employee',string="Agent")
    commission_amount = fields.Float(compute="change_agent_fee_commission",string="Commission Amount",copy=False)
    ln_payment_mode = fields.Selection([('monthly','Monthly'),('bi_monthly','Bi-Monthly')],default="monthly",string="Payment Mode")
    no_month = fields.Integer(string='No. of Months', default=1, help='Number of months that the loan will last')
    ttl_interest_amt = fields.Float(string="Total Interest Amount",compute="cal_ttl_int_amt")
    prcessing_fee_amt = fields.Float(string="Processing Fee Amount")

    def cal_ttl_int_amt(self):
        for rec in self:
            rec.ttl_interest_amt = 0
            for rec_line in rec.line_ids:
                rec.ttl_interest_amt += rec_line.interests_amount

    @api.onchange('no_month','ln_payment_mode')
    def month_change_installment(self):
        if self.ln_payment_mode == 'bi_monthly':
            self.periods = self.no_month * 2
        else:
            self.periods = self.no_month

    @api.constrains('ln_agent_fee')
    def check_agent_amount(self):
        for loan in self:
            if loan.ln_consultant_id and loan.ln_agent_fee <= 0:
                raise UserError("Agent Fee is mandatory")

    @api.onchange('rate_period','rate')
    def change_rate_period_on_month(self):
        if self.rate_period:
            self.rate = self.rate_period * 12
        elif self.rate:
            self.rate_period = self.rate / 12

    @api.onchange('ln_processing_fee','loan_amount')
    def change_procssing_fee(self):
        fee_product = self.env.company.sudo().loan_processing_fee_prod_id or False
        if self.ln_processing_fee and self.loan_amount and fee_product:
            fee_product.lst_price = self.loan_amount * self.ln_processing_fee / 100
            self.prcessing_fee_amt = self.loan_amount * self.ln_processing_fee / 100

    @api.depends('ln_agent_fee')
    def change_agent_fee_commission(self):
        for rec in self:
            rec.commission_amount = 0
            if rec.ln_agent_fee and rec.loan_amount:
                rec.commission_amount = rec.loan_amount * rec.ln_agent_fee / 100

    def setting_down_payment_show(self):
        for loan in self:
            loan.down_payment_show = self.env['ir.config_parameter'].sudo().get_param('jt_loan_management.down_payment', False)

    _sql_constraints = [
        ('name_uniq', 'unique(name, company_id)', 'Loan name must be unique')]

    @api.depends('inv_counter')
    def compute_amount_ln_inv_total(self):
        for loan in self:
            loan.amount_due = 0
            loan_move_type = self.env['ir.config_parameter'].sudo().get_param('jt_loan_management.invoice_type')
            invoices = self.env['account.move'].search([('move_type','=',loan_move_type)
                                                            ,('loan_id','=',loan.id),
                                                            ('state', '=', 'posted'),
                                                            ('amount_residual', '>', 0)])
            for ln_inv in invoices:
                loan.amount_due += ln_inv.amount_residual

    # @api.multi
    @api.depends('line_ids.invoice_ids.amount_residual')
    def compute_amount_and_days_due(self):
        """
        Calculate Amount due and Days past due
        :return: Amount Due and Days past due
        """
        invoice_line_obj = self.env['account.move.line']
        penalty_paid = 0
        penalty_product = self.env.company and self.env.company.sudo().penalty_product_id
        if penalty_product:
            for loan in self:
                domain = [('product_id.id','=',penalty_product.id), ('move_id.loan_id','=',loan.id),
                          ('move_id.payment_state', 'in' ,['paid','in_payment'])]
                invoice_lines = invoice_line_obj.search(domain)
                penalty_paid = sum(x.price_total for x in invoice_lines)
        self.penalty_paid =  penalty_paid

    @api.depends('line_ids.invoice_ids.amount_residual')
    def compute_penalty_pending(self):
        invoice_line_obj = self.env['account.move.line']
        penalty_product_id = self.env.company and self.env.company.sudo().penalty_product_id or False
        for loan in self.search([]):
            loan.penalty_pending = 0
            loan.penalty_received = 0
            if penalty_product_id:
                # total_received_inter = 0
                penalty_domain = [('product_id.id', '=', penalty_product_id.id),('move_id.is_penlty','=',True),('move_id.loan_id.id', '=', loan.id),('move_id.amount_residual', '>', 0)]
                penalty_received_domain = [('product_id.id', '=', penalty_product_id.id),('move_id.is_penlty','=',True),('move_id.loan_id.id', '=', loan.id),('move_id.amount_residual', '=', 0)]
                invoice_penlty_ln_rec = invoice_line_obj.search_read(penalty_domain,['price_total'])       
                invoice_penlty_recevied_rec = invoice_line_obj.search_read(penalty_received_domain,['price_total'])       

                # Calculate total balance
                loan.penalty_pending = sum([price['price_total'] for price in invoice_penlty_ln_rec])
                loan.penalty_received = sum([price['price_total'] for price in invoice_penlty_recevied_rec])

    def compute_total_payments(self):
        """
        Calculate total payment of this customer for this loan
        :return: Total Payment Amount
        """
        pay_his = self.env['account.payment.history']
        for loan in self:
            payment_history_rec = pay_his.search([('loan_id', '=', loan.id)])
            total = sum(rec.amount for rec in payment_history_rec)
            loan.total_payments = total

    @api.onchange('first_payment_due')
    def set_payment_day(self):
        """
        Calculate Payment day using First Payment Date
        :return:  Payment Day
        """
        if self.first_payment_due:
            first_payment_due = self.first_payment_due
            if not isinstance(first_payment_due, str):
                first_payment_due = str(first_payment_due)
            day = datetime.strptime(first_payment_due, DF).day
            self.payment_day = day

    @api.onchange('down_payment')
    def _onchange_down_payment(self):
        """
        Update is_down_payment flag if there is any downpayment for this loan
        :return: is_down_payment
        """
        if self.down_payment > 0:
            self.is_down_payment = True
        else:
            self.is_down_payment = False

    def _get_total_invoice_amount(self, loan, emi_ids):
        current_month = datetime.today().strftime("%m")
        ins_price = tax_price = 0
        if loan.insurance_product_id:
            ins_price = loan.insurance_product_id.lst_price
        if loan.tax_product_id:
            tax_price = loan.tax_product_id.lst_price
        for emi in emi_ids:
            if loan.loan_amount != emi.pending_principal_amount:
                if not isinstance(emi.date, str):
                    loan_month = datetime.strptime(str(emi.date), DF).strftime("%m")
                else:
                    loan_month = datetime.strptime(str(emi.date), DF).strftime("%m")
                if current_month == loan_month:
                    return emi.payment_amount + ins_price + tax_price

    def get_total_invoice_amount(self):
        """
        Calculate Total Invoice Amount of EMI
        :return: Total invoice amount
        """
        for loan in self:
            total_amount = self._get_total_invoice_amount(loan, loan.line_ids)
            loan.total_invoice_amount = total_amount

    def view_disbursement_entries(self):
        self.ensure_one()
        disbursement_acc_id = self.env.company and self.env.company.sudo().loan_disbursement_acc_id
        if disbursement_acc_id:
            action = self.env.ref('account.action_account_moves_all_a')
            result = action.read()[0]
            result['domain'] = [('move_id.loan_id', '=', self.id),('account_id.account_type', '=', 'asset_current'),('move_id.amount_residual','=',0)]
            return result

    def compute_outstanding_bal(self):
        disbursement_acc_id = self.env.company and self.env.company.sudo().loan_disbursement_acc_id
        move_line_obj = self.env['account.move.line']
        for loan in self:
            # lines = move_line_obj.search([('move_id.loan_id', '=', loan.id),
            #                               ('account_id', '=', int(disbursement_acc_id))])
            lines = move_line_obj.search([('move_id.loan_id', '=', loan.id),
                                          ('account_id.account_type', '=', 'asset_current'),('move_id.amount_residual','=',0)])
            debit = sum(line.debit for line in lines)
            credit = sum(line.credit for line in lines)
            # loan.outstanding_bal = credit - debit
            loan.outstanding_bal = debit - credit

    @api.model
    def default_get(self, fields):
        res = super(AccountLoan, self).default_get(fields)
        loan_jou_id = self.env.company and self.env.company.sudo().loan_jou_id
        loan_jou = self.env['account.journal'].browse(int(loan_jou_id))

        if loan_jou:
            res.update({
                'currency_id': loan_jou.currency_id.id or \
                               loan_jou.company_id.currency_id.id or False
            })
        else:
            raise UserError(_("Please configure 'Loan Journal' from Loans -> Configurations -> Settings!"))
        return res

    def cal_ins_tax(self):
        """
        This function returns the insurance and tax balance.
        :return: Insurance and Tax Balance
        """
        invoice_line_obj = self.env['account.move.line']
        for loan in self:
            loan.insurance_balance =  0
            loan.tax_balance = 0
        for loan in self.search(['|', ('insurance_product_id', '!=', False),
                                 ('tax_product_id', '!=', False)]):
            insurance_product = tax_product = False
            if loan.insurance_product_id:
                insurance_product = loan.insurance_product_id
            if loan.tax_product_id:
                tax_product = loan.tax_product_id
            fam_inv_ins = fam_inv_tax = 0
            domain = [('move_id.loan_id', '=', loan.id), ('move_id.state', '=', 'posted'),('move_id.move_type','=','out_invoice')]
            if insurance_product and tax_product:
                domain.append('|', )
                domain.append(('product_id', '=', insurance_product.id), )
                domain.append(('product_id', '=', tax_product.id))
            elif tax_product and not insurance_product:
                domain.append(('product_id', '=', tax_product.id))
            elif insurance_product and not tax_product:
                domain.append(('product_id', '=', insurance_product.id))
            for invoice_line in invoice_line_obj.search(domain):
                product_id = invoice_line.product_id.id
                if insurance_product and product_id == insurance_product.id:
                    fam_inv_ins += invoice_line.price_total
                if tax_product and product_id == tax_product.id:
                    fam_inv_tax += invoice_line.price_total
            # Calculate total balance
            loan.insurance_balance =  fam_inv_ins
            loan.tax_balance = fam_inv_tax

    def cal_ins_tax_from_report(self, loan):
        """
        This function returns the insurance and tax balance.
        :return: Insurance and Tax Balance
        """
        invoice_line_obj = self.env['account.move.line']
        insurance_product = tax_product = False
        if loan.insurance_product_id:
            insurance_product = loan.insurance_product_id
        if loan.tax_product_id:
            tax_product = loan.tax_product_id

        fam_inv_ins = fam_inv_tax = 0

        domain = [('move_id.loan_id', '=', loan.id), ('move_id.state', '=', 'paid')]
        if insurance_product and tax_product:
            domain.append('|', )
            domain.append(('product_id', '=', insurance_product.id), )
            domain.append(('product_id', '=', tax_product.id))
        elif tax_product and not insurance_product:
            domain.append(('product_id', '=', tax_product.id))
        elif insurance_product and not tax_product:
            domain.append(('product_id', '=', insurance_product.id))

        for invoice_line in invoice_line_obj.search(domain):
            product_id = invoice_line.product_id.id

            if insurance_product and product_id == insurance_product.id:
                fam_inv_ins += invoice_line.price_total
            elif tax_product and product_id == tax_product.id:
                fam_inv_tax += invoice_line.price_total

        # Calculate total balance
        return [fam_inv_ins, fam_inv_tax]

    def cal_princi_inter_form_report(self, loan):
        """
        This function returns the insurance and tax balance.
        :return: Insurance and Tax Balance
        """
        invoice_line_obj = self.env['account.move.line']
        principal_prod_id = self.env.company and self.env.company.sudo().loan_principal_prod_id
        interest_prod_id = self.env.company and self.env.company.sudo().loan_interest_prod_id

        total_princi = total_inter = 0
        domain = [('move_id.loan_id', '=', loan.id), ('move_id.state', '=', 'paid')]
        if principal_prod_id and interest_prod_id:
            domain.append('|', )
            domain.append(('product_id', '=', int(principal_prod_id)), )
            domain.append(('product_id', '=', int(interest_prod_id)))
        elif interest_prod_id and not principal_prod_id:
            domain.append(('product_id', '=', int(interest_prod_id)))
        elif principal_prod_id and not interest_prod_id:
            domain.append(('product_id', '=', int(principal_prod_id)))

        for invoice_line in invoice_line_obj.search(domain):
            product_id = invoice_line.product_id.id

            if principal_prod_id and product_id == int(principal_prod_id):
                total_princi += invoice_line.price_total
            elif interest_prod_id and product_id == int(interest_prod_id):
                total_inter += invoice_line.price_total

        # Calculate total balance
        return [total_princi, total_inter]

    def cal_princi_inter(self):
        """
        This function returns the insurance and tax balance.
        :return: Insurance and Tax Balance
        """
        invoice_line_obj = self.env['account.move.line']
        loan_line_obj = self.env['account.loan.line']
        principal_prod_id = self.env.company and self.env.company.sudo().loan_principal_prod_id.id or False
        interest_prod_id = self.env.company and self.env.company.sudo().loan_interest_prod_id
        for loan in self.search([]):
            principle_domain = [('move_id.loan_id', '=', loan.id),'|',('account_id.account_type', '=', 'asset_current'),('product_id.id', '=', principal_prod_id),('journal_id.type','in',['sale','general']),('move_id.amount_residual','=',0)]
            interst_domain = [('loan_id.id', '=', loan.id)]
            invoice_ln_rec = invoice_line_obj.search_read(principle_domain,['debit','credit'])
            invoice_int_ln_rec = loan_line_obj.search_read(interst_domain,['interests_amount'])
            # total_princi = total_inter = 0
            # domain = [('move_id.loan_id', '=', loan.id), ('move_id.state', '=', 'posted'), ('move_id.move_type','=','out_invoice')]
            # for invoice_line in invoice_line_obj.search(domain):
            #     product_id = invoice_line.product_id.id
            #     if invoice_line.account_id.account_type == 'asset_current':
            #         total_princi += invoice_line.price_total
            #     elif interest_prod_id and product_id == int(interest_prod_id):
            #         total_inter += invoice_line.price_total
            # # Calculate total balance
            int_amt = 0
            invoice_int_ln_recs = loan_line_obj.search(interst_domain)
            for line_rec in invoice_int_ln_recs:
                for ln_inv in line_rec.invoice_ids:
                    if ln_inv.amount_residual == 0:
                        for inv_ln in ln_inv.invoice_line_ids:
                            if inv_ln.product_id and inv_ln.product_id.id == int(interest_prod_id):
                                int_amt += inv_ln.price_total
            loan.total_principal_balance = abs(sum([inv_ln['debit'] - inv_ln['credit'] for inv_ln in invoice_ln_rec]))
            total_balance_interest = sum([price['interests_amount'] for price in invoice_int_ln_rec])
            loan.total_interest_balance = total_balance_interest - int_amt

    def cal_rec_princi_inter(self):
        invoice_line_obj = self.env['account.move.line']
        principal_prod_id = self.env.company and self.env.company.sudo().loan_principal_prod_id.id or False
        loan_move_type = self.env['ir.config_parameter'].sudo().get_param('jt_loan_management.invoice_type')
        # invoice_lines = self.env['account.move.line'].search(domain).ids
        interest_prod_id = self.env.company and self.env.company.sudo().loan_interest_prod_id
        for loan in self.search([]):
            loan.total_received_principal_balance = loan.total_received_interest_balance = 0
            # total_received_inter = 0
            interst_domain = [('move_id.loan_id', '=', loan.id), ('product_id', '=', int(interest_prod_id)),('move_id.amount_residual','=',0)]
            principle_domain = [('move_id.loan_id', '=', loan.id), ('product_id.id', '=', principal_prod_id),('move_id.amount_residual','=',0)]
            invoice_ln_rec = invoice_line_obj.search_read(principle_domain,['credit'])       
            invoice_int_ln_rec = invoice_line_obj.search_read(interst_domain,['price_total'])

            # Calculate total balance
            loan.total_received_principal_balance = sum([price['credit'] for price in invoice_ln_rec])
            loan.total_received_interest_balance = sum([price['price_total'] for price in invoice_int_ln_rec])

    @api.depends('line_ids')
    def _get_expected_end_date(self):
        """
        This method is defined to update expected end date based on last installment due date.
        :return: Expected loan ending date will be updated.
        """
        if not self.expected_end_date:
            inv_obj = self.env['account.move']
            for loan in self:
                invoice = inv_obj.search([('loan_id', '=', loan.id),
                        ('emi', '=', True)], order='invoice_date_due desc', limit=1)
                if invoice:
                    date = invoice.invoice_date_due
                    loan.expected_end_date = date
                    if loan.line_ids:
                        last_installment = loan.line_ids[-1]
                        end_date = last_installment.date
                        if end_date > date:
                            loan.expected_end_date = end_date
                else:
                    if loan.line_ids:
                        last_installment = loan.line_ids[-1]
                        if last_installment:
                            loan.expected_end_date = last_installment.date

    def _compute_invoices(self):
        """
        Computes the total invoices of loan.
        :return: invoice_count
        """
        for loan in self:
            loan_move_type = self.env['ir.config_parameter'].sudo().get_param('jt_loan_management.invoice_type')
            invoice_ids = self.env['account.move'].search([('loan_id','=',loan.id),('move_type', '=', loan_move_type)])
            loan.invoice_count += len(invoice_ids)

    def _compute_agent_invoices(self):
        """
        Computes the total invoices of loan.
        :return: agent_count
        """
        for loan in self:
            loan_move_type = self.env['ir.config_parameter'].sudo().get_param('jt_loan_management.invoice_type')
            invoice_ids = self.env['account.move'].search([('loan_id','=',loan.id),('move_type', '=', loan_move_type),('is_agent','=',True)])
            loan.agent_count += len(invoice_ids)

    def _compute_transcation_balance(self):
        history_obj = self.env['loan.transaction.history']
        for loan in self:
            pay_transactions = history_obj.search([('loan_id', '=', loan.id), ('description', '=', 'Payment Received')])
            inv_transactions = history_obj.search([('loan_id', '=', loan.id), ('description', '!=', 'Payment Received'),
                                                   ('date', '<', date.today())])
            debit = sum(inv_trans.debit for inv_trans in inv_transactions)
            credit = sum(pay_trans.credit for pay_trans in pay_transactions)
            loan.transaction_balance = debit - credit


    @api.onchange('product_id')
    def get_loan_amount(self):
        """
        Set default loan amount from product if loan amount is Zero
        :return: Loan Amount
        """
        for loan in self:
            if loan.product_id and loan.loan_amount <= 0:
                loan.loan_amount = loan.product_id.lst_price

    @api.depends('rate_period', 'fixed_loan_amount', 'fixed_periods',
                 'currency_id')
    def _compute_fixed_amount(self):
        """
        Computes the fixed amount in order to be used if round_on_end is
        checked. On fix-annuity interests are included and on fixed-principal
        and interests it isn't.
        :return:
        """
        for record in self:
            if record.interest_type=='simple':
                f_rate = 0
                if self.ln_payment_mode == 'bi_monthly':
                    f_rate = record.fixed_loan_amount * (record.rate_period/2) / 100
                    f_rate = f_rate * record.fixed_periods
                    f_rate = record.fixed_loan_amount + f_rate
                elif self.ln_payment_mode == 'monthly':
                    f_rate = record.fixed_loan_amount * record.rate_period / 100
                    f_rate = f_rate * record.fixed_periods
                    f_rate =  record.fixed_loan_amount + f_rate
                if record.fixed_periods:
                    f_rate = f_rate/record.fixed_periods
                record.fixed_amount = f_rate
            else:
                if self.ln_payment_mode == 'bi_monthly':
                    record.fixed_amount = - record.currency_id.round(npf.pmt(
                        (record.rate_period/2) / 100,
                        record.fixed_periods,
                        record.fixed_loan_amount,
                        -record.residual_amount
                    ))
                else:
                    record.fixed_amount = - record.currency_id.round(npf.pmt(
                        record.rate_period / 100,
                        record.fixed_periods,
                        record.fixed_loan_amount,
                        -record.residual_amount
                    ))

    @api.depends('rate', 'method_period')
    def _compute_rate_period(self):
        """
        Calculate rate period based on period method and rate.
        :return:
        """
        for record in self:
            record.rate_period = record.rate / 12 * record.method_period

    @api.depends('rate_period')
    def compute_rate_period_day(self):
        """
        Calculate rate period day based on period.
        :return:
        """
        for record in self:
            record.rate_period_day = record.rate_period / 30

    @api.model
    def create(self, vals):

        # principal_prod_id =  self.env.company and self.env.company.sudo().loan_principal_prod_id
        interest_prod_id = self.env.company and self.env.company.sudo().loan_interest_prod_id
        loan_jou_id = self.env.company and self.env.company.sudo().loan_jou_id
        loan_jou = self.env['account.journal'].browse(int(loan_jou_id))

        if not interest_prod_id:
            raise UserError(_('Please configure Interest product from Loan -> Configurations ->'
                            'Settings!'))
        if not loan_jou:
            raise UserError(_('Please configure Loan Journal from Loan -> Configurations ->'
                            'Settings!'))
        if loan_jou:
            vals.update({
                'currency_id': loan_jou.currency_id.id or loan_jou.company_id.currency_id.id or False
            })
        return super(AccountLoan, self).create(vals)


    def post(self):
        self.ensure_one()
        if not self.start_date:
            self.start_date = fields.Datetime.now()
        if not self.first_payment_due:
            self.first_payment_due = fields.Datetime.now()
        if not self.is_down_payment and self.down_payment != 0:
            self.compute_draft_lines()
            self.write({'state':'posted'})
        else:
            self.write({'state':'posted'})

    def close(self):
        self.close_date = date.today()
        self.write({'state': 'closed'})

    def compute_lines(self):
        self.ensure_one()
        if self.state == 'draft':
            return self.compute_draft_lines()
        return self.compute_posted_lines()

    def compute_posted_lines(self):
        """
        Recompute the amounts of not finished lines. Useful if rate is changed
        """
        amount = self.loan_amount
        if self.is_down_payment:
            amount -= self.down_payment
        for line in self.line_ids.sorted('sequence'):
            if line.move_ids:
                amount = line.final_pending_principal_amount
            else:
                line.rate = self.rate_period
                line.pending_principal_amount = amount
                line.check_amount()
                amount -= line.payment_amount - line.interests_amount

    def new_line_vals(self, sequence, date, amount):
        return {
            'loan_id': self.id,
            'sequence': sequence,
            'date': date,
            'pending_principal_amount': amount,
            'emi': True
        }

    def compute_update_rate_lines(self):

        self.ensure_one()
        self.fixed_periods = self.periods
        self.fixed_loan_amount = self.loan_amount

        amount = self.loan_amount

        if self.is_down_payment and self.state == 'posted':
            amount -= self.down_payment
            self.fixed_loan_amount = self.loan_amount - self.down_payment
        if self.first_payment_due:
            if not isinstance(self.first_payment_due, str):
                date = datetime.strptime(str(self.first_payment_due), DF).date()
            else:
                date = datetime.strptime(self.first_payment_due, DF).date()
        else:
            date = datetime.today().date()
        delta = relativedelta(months=self.method_period)
        if not self.payment_on_first_period:
            date += delta
        # if self.line_ids:
        #     self._cr.execute("delete from account_loan_line WHERE loan_id=%s", (self.id))
        loan_move_type = self.env['ir.config_parameter'].sudo().get_param('jt_loan_management.invoice_type')
        inv_lines = self.env['account.move'].search([('is_down_payment','=',True),('loan_id','=',self.id),('move_type','=',loan_move_type)])
        if inv_lines:
            pass
        else:
            loan_line = self.env['account.loan.line'].search([('loan_id','=',self.id)])
            for ln in loan_line:
                if ln.invoice_ids:
                    pass
                else:
                    ln.check_amount()
                    amount -= ln.payment_amount - ln.interests_amount

    def compute_draft_lines(self):

        self.ensure_one()
        self.fixed_periods = self.periods
        self.fixed_loan_amount = self.loan_amount

        amount = self.loan_amount

        if self.is_down_payment and self.state == 'posted':
            amount -= self.down_payment
            self.fixed_loan_amount = self.loan_amount - self.down_payment
        if self.first_payment_due:
            if not isinstance(self.first_payment_due, str):
                date = datetime.strptime(str(self.first_payment_due), DF).date()
            else:
                date = datetime.strptime(self.first_payment_due, DF).date()
        else:
            date = datetime.today().date()
        delta = relativedelta(months=self.method_period)
        if not self.payment_on_first_period:
            date += delta
        if self.line_ids:
            self._cr.execute("delete from account_loan_line WHERE loan_id=%s", (self.id,))
        loan_move_type = self.env['ir.config_parameter'].sudo().get_param('jt_loan_management.invoice_type')
        inv_lines = self.env['account.move'].search([('is_down_payment','=',True),('loan_id','=',self.id),('move_type','=',loan_move_type,)])
        if inv_lines:
            pass
        else:
            day_count = 0
            first_count = 0
            previos_date = False
            feb_month_days = 0
            for i in range(1, self.periods + 1):
                if self.ln_payment_mode == 'bi_monthly':
                    if date.day == 31:
                        date += timedelta(days=1)
                elif self.ln_payment_mode == 'monthly':
                    if date.day == 31:
                        date += timedelta(days=1)
                line = self.env['account.loan.line'].create(
                    self.new_line_vals(i, date, amount)
                )
                previos_date = date
                line.check_amount()
                if self.ln_payment_mode == 'bi_monthly':

                    old_month = date.month
                    date = date.replace(month=4)
                    date += timedelta(days=15+feb_month_days)
                    if date.month!=4:
                        old_month+=1

                        if old_month > 12:
                            date += relativedelta(years=1)
                            old_month = 1
                    
                    try:
                        date = date.replace(month=old_month)
                        feb_month_days = 0
                    except:
                        date_days = date.day
                        date = date.replace(day=1)
                        date = date.replace(month=old_month)
                        last_day = calendar.monthrange(date.year, date.month)[1]
                        date = date.replace(day=last_day)
                        feb_month_days = date_days - last_day
                    

                    # if date.day > 15 and date.month in (1,3,5,7,8,10,12):
                    #     date += timedelta(days=16)
                    # # elif date.day > 15 and date.month == 2:
                    # #     last_day = calendar.monthrange(date.year, date.month)[1]
                    # #     if last_day == 28:
                    # #        date += timedelta(days=13)
                    # #     else:
                    # #        date += timedelta(days=14)
                    # elif date.month == 2 and previos_date and previos_date.day in [14,15]:
                    #      last_day = calendar.monthrange(date.year, date.month)[1]
                    #      date = date.replace(day=last_day)
                    # else:
                    #     print("previos_date",previos_date)
                    #     if previos_date.day in [28,29] and previos_date.month==2 and self.first_payment_due.day==14:
                    #         date += timedelta(days=14)
                    #     else:
                    #         date += timedelta(days=15)

                elif self.ln_payment_mode == 'monthly':
                    date += delta
                    if date.month == 2 and date.day in (29,30,31):
                        last_day = calendar.monthrange(date.year, date.month)[1]
                        if last_day == 29:
                            date = date.replace(day=last_day)
                        elif last_day == 28:
                            date = date.replace(day=last_day)
                    else:
                        if self.first_payment_due.day == 29:
                            if date.month == 2:
                                last_day = calendar.monthrange(date.year, date.month)[1]
                                if last_day == 29:
                                    date = date.replace(day=last_day)
                                elif last_day == 28:
                                    date = date.replace(day=last_day)
                            else:
                                date = date.replace(day=29)
                        elif self.first_payment_due.day == 30:
                            if date.month == 2:
                                last_day = calendar.monthrange(date.year, date.month)[1]
                                if last_day == 29:
                                    date = date.replace(day=last_day)
                                elif last_day == 28:
                                    date = date.replace(day=last_day)
                            else:
                                date = date.replace(day=30)

                amount -= line.payment_amount - line.interests_amount

    def view_insurance_balance(self):
        """
        This method is called from Insurance widget to display all invoice line of Insurance Product for loan
        :return:  Invoice line tree view
        """
        self.ensure_one()
        if self.insurance_product_id:
            action = self.env.ref('jt_loan_management.loan_invoice_line_action')
            result = action.read()[0]
            result['domain'] = [('product_id', '=', self.insurance_product_id.id), ('move_id.loan_id', '=', self.id)]
            return result

    def view_tax_balance(self):
        """
        This method is called from Tax widget to display all invoice line of Tax Product for loan
        :return:  Invoice line tree view
        """
        self.ensure_one()
        if self.tax_product_id:
            action = self.env.ref('jt_loan_management.loan_invoice_line_action')
            result = action.read()[0]
            result['domain'] = [('product_id', '=', self.tax_product_id.id), ('move_id.loan_id', '=', self.id)]
            return result

    def view_principal_balance(self):
        """
        This method is called from Pricipal widget to display all invoice line of Pricipal Product for loan
        :return: Invoice line tree view
        """
        self.ensure_one()

        principal_prod_id = self.env.company and self.env.company.sudo().loan_principal_prod_id.id or False
        # domain = [('move_id.loan_id', '=', self.id), ('account_id.account_type', '=', 'asset_current')]
        domain = [('move_id.loan_id', '=', self.id),'|',('account_id.account_type', '=', 'asset_current'),('product_id.id', '=', principal_prod_id),('journal_id.type','in',['sale','general']),('move_id.amount_residual','=',0)]
        invoice_lines = self.env['account.move.line'].search(domain).ids
        action = self.env.ref('account.action_account_moves_all')
        result = action.read()[0]
        result['domain'] = [('id', 'in', invoice_lines)]
        return result

    def view_principal_balance_received(self):
        """
        This method is called from Pricipal widget to display all invoice line of Pricipal Product for loan
        :return: Invoice line tree view
        """
        self.ensure_one()

        principal_prod_id = self.env.company and self.env.company.sudo().loan_principal_prod_id.id or False
        domain = [('move_id.loan_id', '=', self.id),('product_id.id', '=', principal_prod_id),('move_id.move_type','=','out_invoice'),('move_id.amount_residual','=',0)]
        invoice_lines = self.env['account.move.line'].search(domain).ids
        action = self.env.ref('account.action_account_moves_all')
        result = action.read()[0]
        result['domain'] = [('id', 'in', invoice_lines)]
        return result

    def view_interest_balance(self):
        """
        This method is called from Interest widget to display all invoice line of Interest Product for loan
        :return: Invoice line tree view
        """
        self.ensure_one()

        interest_prod_id = self.env.company and self.env.company.sudo().loan_interest_prod_id

        # domain = [('move_id.loan_id', '=', self.id), ('product_id', '=', int(interest_prod_id))]
        domain = [('loan_id.id', '=', self.id),('interests_inv_amt','!=',True)]

        loan_lines = self.env['account.loan.line'].search(domain).ids
        action = self.env.ref('jt_loan_management.action_loan_line_smt')
        result = action.read()[0]
        result['domain'] = [('id', 'in', loan_lines)]
        return result

    def view_interest_balance_received(self):
        """
        This method is called from Interest widget to display all invoice line of Interest Product for loan
        :return: Invoice line tree view
        """
        self.ensure_one()

        interest_prod_id = self.env.company and self.env.company.sudo().loan_interest_prod_id

        domain = [('move_id.loan_id', '=', self.id), ('product_id', '=', int(interest_prod_id)),('move_id.amount_residual','=',0)]

        invoice_lines = self.env['account.move.line'].search(domain).ids
        action = self.env.ref('jt_loan_management.loan_invoice_line_action')
        result = action.read()[0]
        result['domain'] = [('id', 'in', invoice_lines)]
        return result

    def view_loan_transactions(self):
        """
        This method id called from Transaction widget to display all the transactions
        :return: Transaction tree view
        """
        self.ensure_one()
        transactions = self.env['loan.transaction.history'].search([('loan_id', '=', self.id)]).ids
        action = self.env.ref('jt_loan_management.action_loan_transaction')
        result = action.read()[0]
        result['domain'] = [('id', 'in', transactions)]
        return result

    def view_account_invoices(self):
        """
        This method is called from Invoices widget to display all the invoice related to loan
        :return: Invoices tree view
        """
        self.ensure_one()
        action = self.env.ref('account.action_move_out_invoice_type')
        loan_move_type = self.env['ir.config_parameter'].sudo().get_param('jt_loan_management.invoice_type')
        result = action.read()[0]
        result['domain'] = [
            ('loan_id', '=', self.id), ('move_type', '=', loan_move_type)
        ]
        return result

    def view_account_agent_invoices(self):
        """
        This method is called from Invoices widget to display all the invoice related to loan
        :return: Invoices tree view
        """
        self.ensure_one()
        loan_move_type = self.env['ir.config_parameter'].sudo().get_param('jt_loan_management.invoice_type')
        action = self.env.ref('account.action_move_in_invoice_type')
        result = action.read()[0]
        result['domain'] = [
            ('loan_id', '=', self.id), ('move_type', '=', loan_move_type),('is_agent','=',True)
        ]
        return result

    def view_pending_penalty_invoice(self):
        self.ensure_one()
        penalty_product_id = self.env.company and self.env.company.sudo().penalty_product_id
        if penalty_product_id:
            action = self.env.ref('jt_loan_management.loan_invoice_line_action')
            result = action.read()[0]
            result['domain'] = [('product_id.id', '=', penalty_product_id.id),('move_id.is_penlty','=',True),('move_id.loan_id.id', '=', self.id),('move_id.amount_residual', '>', 0)]
            return result

    def view_received_penalty_invoice(self):
        self.ensure_one()
        penalty_product_id = self.env.company and self.env.company.sudo().penalty_product_id
        if penalty_product_id:
            action = self.env.ref('jt_loan_management.loan_invoice_line_action')
            result = action.read()[0]
            result['domain'] = [('product_id.id', '=', penalty_product_id.id),('move_id.is_penlty','=',True),('move_id.loan_id.id', '=', self.id),('move_id.amount_residual', '=', 0)]
            return result

    def view_open_penalty_invoice(self):
        """
        This method is called from Invoices widget to display all the invoice related to loan penalty
        :return: Invoices tree view
        """
        self.ensure_one()
        action = self.env.ref('account.action_invoice_tree1')
        result = action.read()[0]
        result['domain'] = [
            ('loan_id', '=', self.id), ('state','in',('in_payment','open')),('move_type', '=', 'out_invoice'),('interest_inv_id','!=',False)
        ]
        return result

    def view_payments(self):
        """
        This method is called from Payment widget to diplay all the payment history of loan
        :return: Payment History tree view
        """
        self.ensure_one()
        action = self.env.ref('jt_loan_management.view_payments')
        result = action.read()[0]
        return result

    def _get_loan_invoices(self, loan):
        loan_invoices = self.env['account.move'].search([('loan_id', '=', loan.id), ('splitted_invoice', '=', False),
                                    ('state', 'not in', ('draft', 'cancel'))], order='invoice_date_due')
        if loan_invoices:
            return loan_invoices
        else:
            return []

    def get_code_with_zeros(self, code, sequence):
        padding = sequence.padding
        missing_len = padding - len(code)
        prepare_zeros = ''
        for x in range(0, missing_len):
            prepare_zeros += '0'
        return  prepare_zeros + code

    def _get_month_or_year(self, month=None, year=None, date=None):
        date_format_string = ["%m", "%y", "%Y"]
        if month in date_format_string:
            month = datetime.strftime(datetime.strptime(str(date), '%Y-%m-%d'), month)
        else:
            month = ""
        if year in date_format_string:
            year = datetime.strftime(datetime.strptime(str(date), '%Y-%m-%d'), year)
        else:
            year = ""
        return month, year

    def _get_period_info(self, sequence, date_invoice):
        if sequence.prefix:
            if '%(y)s/%(range_month)s' == sequence.prefix:
                month, year = self._get_month_or_year(month="%m", year="%y", date =date_invoice)
                prepared_range = year + '/' + month
                return prepared_range
            elif '%(range_year)s' == sequence.prefix:
                month, year = self._get_month_or_year(month=None, year="%y", date =date_invoice)
                prepared_range = year
                return prepared_range
            elif '%(range_month)s' == sequence.prefix:
                month, year = self._get_month_or_year(month="%m", year=None, date =date_invoice)
                prepared_range = month
                return prepared_range
            elif '%(year)s' == sequence.prefix:
                month, year = self._get_month_or_year(month=None, year="%Y", date =date_invoice)
                prepared_range = year
                return prepared_range
            elif '%(range_month)s/%(y)s' == sequence.prefix:
                month, year = self._get_month_or_year(month="%m", year="%y", date =date_invoice)
                prepared_range = month + '/' + year
                return prepared_range
            elif '%(year)s/%(range_month)s' == sequence.prefix:
                month, year = self._get_month_or_year(month="%m", year="%Y", date =date_invoice)
                prepared_range = year + '/' + month
                return prepared_range
            elif '%(y)s' == sequence.prefix:
                month, year = self._get_month_or_year(month=None, year="%y", date =date_invoice)
                prepared_range = year
                return prepared_range
            elif '%(range_y)s' == sequence.prefix:
                month, year = self._get_month_or_year(month=None, year="%y", date =date_invoice)
                prepared_range = year
                return prepared_range
            elif '%(range_year)s' == sequence.prefix:
                month, year = self._get_month_or_year(month=None, year="%Y", date =date_invoice)
                prepared_range = year
                return prepared_range
            else:
                return ''

    def reset_old_loan_invoices_sequence(self):
        """
        Remove old invoice history and reset old loan invoices.
        :return:
        """
        loan_inv_obj = self.env['loan.invoice']
        inv_obj = self.env['account.move']
        loan_tran_his_obj = self.env['loan.transaction.history']
        for loan in self:
            if loan.state == 'posted':
                # Removing old invoice history
                loan.loan_inv_ids = [(5, 0, 0)]
                if not loan.loan_inv_ids:
                    invoice_ids = loan.processing_fee_inv_id
                    invoice_ids += self._get_loan_invoices(loan)
                    # assiging temp number to existin invoice to avoid duplicate error!
                    temp = 1
                    for inv in invoice_ids:
                        inv.name = chr(temp)
                        temp += 1
                    for inv in invoice_ids:
                        new_number = inv.journal_id.code or ''
                        new_number += '/'
                        period_data = self._get_period_info(inv.journal_id.secure_sequence_id, inv.invoice_date)
                        if period_data:
                            new_number += period_data

                        if inv.invoice_date:
                            year = datetime.strptime(str(inv.invoice_date), DEFAULT_SERVER_DATE_FORMAT).year
                            month = datetime.strptime(str(inv.invoice_date), DEFAULT_SERVER_DATE_FORMAT).month
                            last_invoice = self.env['loan.invoice'].search([('year', '=', year),
                                                                            ('loan_id', '=', loan.id),
                                                                            ('move_id', '!=', inv.id)],
                                                                          )
                            if last_invoice:
                                exist_invoice = len(last_invoice)
                                sequence = exist_invoice + 1
                            else:
                                sequence = 1
                            new_number += '/'
                            number = self.get_code_with_zeros(str(sequence), inv.journal_id.secure_sequence_id)
                            new_number += str(number)
                            inv.name = new_number
                            histories = loan_tran_his_obj.search([('move_id', '=', inv.id)])
                            for his in histories:
                                his.reference = inv.number

                            # creating reference for sequence under loan
                            test = loan_inv_obj.create({
                                'name': new_number,
                                'loan_id': loan.id,
                                'move_id': inv.id,
                                'month': month,
                                'year': year,
                                'date_invoice': inv.invoice_date,
                                'sequence_number': sequence,
                            })
                        splitted_invs = inv_obj.search([('loan_id', '=', loan.id), ('splitted_invoice', '=', True)])
                        for splitted_inv in splitted_invs:
                            if splitted_inv.loan_line_id:
                                main_inv = splitted_inv.move_id if \
                                    splitted_inv.main_invoice_id else False
                                if main_inv and main_inv.number:
                                    splitted_inv.number = main_inv.number + 'A'
                                    main_loan_inv = loan_inv_obj.search([('move_id', '=', main_inv.id)], limit=1)
                                    year = datetime.strptime(str(splitted_inv.invoice_date), DEFAULT_SERVER_DATE_FORMAT).year
                                    month = datetime.strptime(str(splitted_inv.invoice_date), DEFAULT_SERVER_DATE_FORMAT).month
                                    loan_inv_obj.create({
                                        'name': splitted_inv.number,
                                        'loan_id': loan.id,
                                        'move_id': splitted_inv.id,
                                        'month': month,
                                        'year': year,
                                        'date_invoice': splitted_inv.invoice_date,
                                        'sequence_number': main_loan_inv.sequence_number,
                                    })

    def generate_old_loan_invoices(self):
        """
        Generate invoices of all old EMIs.
        :return:
        """
        active_ids = self._context.get('active_ids')
        loans = self.env['account.loan'].browse(active_ids)
        date_now = datetime.now()
        for loan in loans:
            if loan.state == 'posted':
                for line in loan.line_ids:
                    if line.date and line.has_invoices == False:
                        inv_date = date_now + timedelta(days=12)
                        if datetime.strptime(str(line.date), DF) <= inv_date and line.payment_amount != loan.down_payment:
                            line.view_process_values()

    def _check_is_invoice_open(self, invoice_ids):
        is_open = False
        for invoice in invoice_ids:
            if invoice.state in ('draft','open'):
                return True

        return is_open

    def create_invoice(self):
        """
        This method is called from scheduler to create automatic invoice.
        :return: Create automatic invoice
        """
        loan_move_type = self.env['ir.config_parameter'].sudo().get_param('jt_loan_management.invoice_type')
        compare_date = date.today() + timedelta(days=7)
        invoices = self.env['account.move'].search([('move_type','=',loan_move_type),('state','=','posted'),('invoice_date_due','=',compare_date),('is_move_sent','=', False)])
        for inv_id in invoices:
            template = self.env.ref(inv_id._get_mail_template())
            result_data =  self.env['account.move.send'].with_context(
                active_model='account.move',
                active_ids=inv_id.ids,
            ).create({
                'mail_template_id': template.id,
                'checkbox_download': False,
                'checkbox_send_mail': True,
                'checkbox_send_by_post': False,
            })
            result_data.action_send_and_print()

        date_now = datetime.now()
        for loan in self.search([('state', '=', 'posted')]):
            for i in loan.line_ids:
                due_date = datetime.strptime(str(i.date), DF)
                if i.date and i.has_invoices == False:
                    inv_date = datetime.strptime(str(i.date), DF) - rd(days=loan.inv_create_date)
                    if date_now >= inv_date and date_now >= due_date and i.payment_amount != loan.down_payment:
                        i.view_process_values()

    def close_loan(self):
        """
        Don't allow to delete loan if there is any partial or fully paid invoice of EMI, Otherwise cancel the all
        draft and open invoices and add the 'C' at the end of the Loan name.
        :return:
        """
        self.ensure_one()
        for loan_line in self.line_ids:
            for invoice in loan_line.invoice_ids:
                if invoice.state == 'posted' and invoice.payment_state == 'partial':
                    raise UserError(_("Some payments are already registered. You need to cancel them."))

        # Cancel the draft and open invoices
        for loan_line in self.line_ids:
            for invoice in loan_line.invoice_ids:
                if (invoice.state == 'draft' or invoice.state == 'posted') and invoice.payment_state == 'not_paid':
                    invoice.button_cancel()
        self.write({'state': 'closed'})
        # Rename Loan with loan name + C
        self.name = self.name + 'C'

    def cancel_loan(self):
        """
        Cancel all open and draft invoices and mark partial paid invoices as fully paid.
        :return:
        """
        self.ensure_one()
        account_obj = self.env['account.account']
        write_off_account_id = self.env.company and self.env.company.sudo().loan_write_off_account_id
        if not write_off_account_id:
            raise UserError(_("Please configure 'Write off Account' from Loan -> "
                            "Configurations -> Settings!"))
        write_off_acc = account_obj.browse(int(write_off_account_id))
        loan_jou_id = self.env.company and self.env.company.sudo().loan_jou_id
        if not loan_jou_id:
            raise UserError(_("Please Configure Loan Journal from Loans -> Configurations -> Settings!"))
        loan_jou = self.env['account.journal'].browse(int(loan_jou_id))
        if not loan_jou.default_account_id:
            raise UserError(_("Please Configure Default Credit Account for 'Loan Journal'!"))
        date = fields.Date.today()
        for loan_line in self.line_ids:
            for invoice in loan_line.invoice_ids:
                if (invoice.state == 'draft' or invoice.state == 'posted') and invoice.payment_state == 'not_paid':
                    invoice.button_cancel()
                elif invoice.state == 'posted' and invoice.payment_state == 'partial':
                    raise UserError(_("Some invoices payments are partially paid. You need to pay them."))
                    
        self.write({'state': 'cancelled'})

    def invoice_line_vals(self, income_acc_id):
        principal_prod_id = self.env.company and self.env.company.sudo().loan_principal_prod_id
        principal_prod = self.env['product.product'].browse(int(principal_prod_id))
        vals = {
            'name': "Down Payment",
            'product_id': principal_prod and principal_prod.id or False,
            'quantity': 1,
            'price_unit': self.down_payment,
            'account_id': income_acc_id,
        }
        return vals

    def _get_pricelist_price(self,product):
        self.ensure_one()
        product.ensure_one()

        price = self.pricelist_item_id._compute_price(
            product=self.product_id.with_context(**self._get_product_price_context()),
            quantity=self.product_uom_qty or 1.0,
            uom=self.product_uom,
            date=self.order_id.date_order,
            currency=self.currency_id,
        )

        return price

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
        partner = self.partner_id
        pricelist = partner.property_product_pricelist
        if pricelist.discount_policy == 'with_discount':
            return product.with_context(pricelist=pricelist.id).lst_price
        final_price = pricelist._get_product_price(product, 1.0, self.currency_id)
        base_price = self._get_pricelist_price_before_discount(product)

        return max(base_price, final_price)

    def _get_loan_number(self):
        sequence = self.env['ir.sequence'].next_by_code('accounting.loan.sequence')
        _logger.info("Sequence Generated for loan : %s",sequence)
        return sequence

    def post_loan(self):
        """
        Create down payment invoice if any down payment amount and reset all lines and posted the loan.
        :return:
        """
        if not self.line_ids:
           raise UserError('Please Compute Loan Items first after that you can post the loan!')
        else:
            self.ensure_one()
            inv_obj = self.env['account.move']
            loan_acc_rec_id = self.env.company.sudo().loan_acc_rec_id and self.env.company.sudo().loan_acc_rec_id.id or False
            if not loan_acc_rec_id:
                raise UserError(_("Please Configure 'Loan Account Receivable' from Loans -> Configurations -> Settings!"))
            loan_jou_id = self.env.company.sudo().loan_jou_id and self.env.company.sudo().loan_jou_id.id or False
            if not loan_jou_id:
                raise UserError(_("Please Configure Loan Journal from Loans -> Configurations -> Settings!"))
            fee_product = self.env.company.sudo().loan_processing_fee_prod_id and self.env.company.sudo().loan_processing_fee_prod_id or False
            if not fee_product:
                raise UserError(_("Please Configure Processing Fee Product from Loans -> Configurations -> Settings!"))
            agent_fee_product = self.env.company.sudo().loan_agent_fee_prod_id and self.env.company.sudo().loan_agent_fee_prod_id or False
            if not agent_fee_product:
                raise UserError(_("Please Configure Agent Fee Product from Loans -> Configurations -> Settings!"))
            income_acc_id = self.env.company.sudo().loan_income_acc_id and self.env.company.sudo().loan_income_acc_id.id or False
            if not income_acc_id:
                raise UserError(_("Please Configure Income Account from Loans -> Configurations -> Settings!"))

            disbursement_acc_id = self.env.company.sudo().loan_disbursement_acc_id and \
                                  self.env.company.sudo().loan_disbursement_acc_id.id or False
            if not disbursement_acc_id:
                raise UserError(_("Please Configure Disbursement Account from Loans -> Configurations -> Settings!"))

            receivable_principal_acc_id = self.env.company.sudo().loan_acc_rec_id and \
                                  self.env.company.sudo().loan_acc_rec_id.id or False
            if not receivable_principal_acc_id:
                raise UserError(_("Please Configure Principal Receivable Account from Loans -> Configurations -> Settings!"))

            disbursement_journal_id = self.env.company.sudo().loan_disbursement_journal_id and \
                                      self.env.company.sudo().loan_disbursement_journal_id.id or False
            if not disbursement_journal_id:
                raise UserError(_("Please Configure Disbursement Journal from Loans -> Configurations -> Settings!"))

            partner = self.partner_id
            today = datetime.today().date()
            loan_amt = self.loan_amount
            move = inv_obj.create({
                'journal_id': disbursement_journal_id,
                'loan_id': self.id or False,
                'ref': 'Disbursement Entry',
                'date': today,
                'partner_id': partner and partner.id or False,
                'company_id': self.env.company.id,
            })
            lines = [{
                'account_id': receivable_principal_acc_id,
                'partner_id': partner and partner.id or False,
                'debit': loan_amt,
                'credit': 0,
                'date': today,
                'ref': 'Disbursement Entry',
            }, {
                'account_id': disbursement_acc_id,
                'partner_id': partner and partner.id or False,
                'debit': 0,
                'credit': loan_amt,
                'date': today,
                'ref': 'Disbursement Entry',
            }]
            move.line_ids = [(0, 0, val) for val in lines]
            move.action_post()
            price_fee_product = self._get_display_price(fee_product)
            if self.ln_processing_fee and price_fee_product > 0:
                loan_move_type = self.env['ir.config_parameter'].sudo().get_param('jt_loan_management.invoice_type')
                # fees_price = self._get_display_price(fee_product)
                ln_fee_price = 0
                if fee_product and self.ln_agent_fee:
                    ln_fee_price = fee_product.list_price + (self.loan_amount * self.ln_agent_fee / 100)
                elif fee_product and not self.ln_agent_fee:
                    ln_fee_price = fee_product.list_price

                fee_inv_line1_dict = {
                    'name': fee_product.name,
                    'product_id': fee_product and fee_product.id,
                    'quantity': 1,
                    'price_unit': ln_fee_price,
                    'tax_ids':False,
                    'account_id': fee_product.property_account_income_id and fee_product.property_account_income_id.id or income_acc_id,
                    }
                payment_term_id = self.env['account.payment.term'].search([('name','=','Immediate Payment')])
                self.inv_counter = self.inv_counter+1
                fee_inv = inv_obj.create({
                    'loan_id': self.id,
                    'company_id': self.env.company.id,
                    'partner_id': self.partner_id.id,
                    'currency_id': self.env.company.currency_id and self.env.company.currency_id.id or False,
                    'move_type': loan_move_type,
                    'invoice_payment_term_id':payment_term_id and payment_term_id.id or False,
                    'journal_id': loan_jou_id,
                    'invoice_date': self.start_date and self.start_date or datetime.today().date(),
                })
                fee_inv.line_ids = [(0, 0, fee_inv_line1_dict)]
                if fee_inv:
                    self.processing_fee_inv_id = fee_inv.id
                    fee_inv.loan_id = self.id
                    fee_inv.with_context(from_validate=True).action_post()
            # if self.ln_agent_fee:
                # write_off_account_id = self.env.company and self.env.company.sudo().loan_write_off_account_id
                # agent_fee_inv_line1_dict = {
                #     'name': agent_fee_product and agent_fee_product.name or '',
                #     'product_id': agent_fee_product and agent_fee_product.id or False,
                #     'quantity': 1,
                #     'price_unit': self.loan_amount * self.ln_agent_fee / 100 or 0,
                #     'account_id': write_off_account_id and write_off_account_id.id or False,
                #     }
                # self.inv_counter = self.inv_counter+1
                # agent_fee_inv = inv_obj.create({
                #     'loan_id': self.id,
                #     'is_agent':True,
                #     'company_id': self.env.company.id,
                #     'partner_id': self.ln_consultant_id and self.ln_consultant_id.work_contact_id and self.ln_consultant_id.work_contact_id.id or False,
                #     'currency_id': self.env.company.currency_id and self.env.company.currency_id.id or False,
                #     'move_type': 'in_invoice',
                #     'invoice_payment_term_id':payment_term_id and payment_term_id.id or False,
                #     'invoice_date': self.start_date and self.start_date or datetime.today().date(),
                # })
                # agent_fee_inv.line_ids = [(0, 0, agent_fee_inv_line1_dict)]
                # if agent_fee_inv:
                #     agent_fee_inv.loan_id = self.id
                #     agent_fee_inv.with_context(from_validate=True).action_post()
            self.is_compute_items = True
            if self.state != 'draft':
                raise UserError(_('Only loans in Draft state can be posted'))
            if self.is_down_payment and self.down_payment != 0:
                if self.start_date:
                    date = datetime.strptime(str(self.start_date), DF).date()
                else:
                    date = datetime.today().date()
                delta = relativedelta(months=self.method_period)
                if not self.payment_on_first_period:
                    date += delta
                line_data = {
                    'loan_id': self.id,
                    'payment_amount': self.down_payment,
                    'interests_amount': 0,
                    'date': self.start_date and self.start_date or datetime.today().date(),
                    'pending_principal_amount': self.loan_amount,
                    'is_down_payment': True
                }
                self.write({'state': 'posted'})
                self.compute_draft_lines()
                down_payment_line = self.env['account.loan.line'].create(line_data)
                res = []
                self.inv_counter = self.inv_counter+1       
                payment_term_id = self.env['account.payment.term'].search([('name','=','Immediate Payment')])
                line_vals = self.invoice_line_vals(income_acc_id)
                loan_move_type = self.env['ir.config_parameter'].sudo().get_param('jt_loan_management.invoice_type')
                inv_data = {
                    # 'name':str(self.name)+'-'+str( self.inv_counter),   
                    'loan_id': self.id,
                    'loan_line_id': down_payment_line and down_payment_line.id if down_payment_line else False,
                    'company_id': self.env.company.id,
                    'partner_id': self.partner_id.id,
                    'currency_id': self.env.company.currency_id.id,
                    'move_type': loan_move_type,
                    'invoice_payment_term_id':payment_term_id and payment_term_id.id or False,
                    'journal_id':loan_jou_id,
                    'invoice_date': self.start_date and self.start_date or datetime.today().date(),
                    'invoice_line_ids': [(0, 0, line_vals)],
                }
                inv_id = inv_obj.create(inv_data)
                if inv_id:
                    res.append(inv_id.id)
                    inv_id.is_down_payment = True
                    inv_id.with_context(from_validate=True).action_post()
                self.post()
                loan_number = self._get_loan_number()
                _logger.info("LOAN NEXT NUMBER :: %s", loan_number)
                self.name = loan_number
                return
            else:
                self.post()
                loan_number = self._get_loan_number()
                _logger.info("ELSE LOAN NEXT NUMBER :: %s", loan_number)
                self.name = loan_number

        # for line in self.line_ids:
        #     line.view_process_values()

    def due_date_selection(self):
        """
        Open popup to move due date of EMIs
        :return:
        """
        view_id = self.env.ref('jt_loan_management.move_due_date_of_loan_wizard', False)
        return {
            'name': 'Postpone Installments',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'move.due.date',
            'views': [(view_id.id, 'form')],
            'view_id': view_id.id,
            'target': 'new',
        }

    def send_loan_email(self):
        loan_rec = self.env['account.loan'].search([])
        for loan in loan_rec:
            mail_template = loan.env.ref('jt_loan_management.email_template_loan_details')
            mail_template.send_mail(loan.id, force_send=True)

    
    def action_loan_detail_send(self):
        '''
        This function opens a window to compose an email, with the loan template message loaded by default
        '''
        for loan in self:
            template_id = self.env['ir.model.data']._xmlid_to_res_id('jt_loan_management.email_template_loan_details', raise_if_not_found=False)
            compose_form_id = self.env['ir.model.data']._xmlid_to_res_id('mail.email_compose_message_wizard_form', raise_if_not_found=False)


            record = loan.sudo()
            ctx = {
                'default_model': 'account.loan',
                'default_res_id': loan.ids[0],
                'default_use_template': bool(template_id),
                'default_template_id': template_id,
                'default_composition_mode': 'comment',
                'mark_so_as_sent': True,
                'custom_layout': "mail.mail_notification_paynow",
                'force_email': True,
                'record': record,
                'user_id': self.env.user
            }
            
            return {
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'mail.compose.message',
                'views': [(False, 'form')],
                'view_id': False,
                'target': 'new',
                'context': ctx,
        }
        

class GetLoanRange(models.Model):
    _name = 'loan.invoice'
    _description = "Loan Invoices"

    name = fields.Char("Loan Invoice Range")
    loan_id = fields.Many2one('account.loan', string="Loan")
    move_id = fields.Many2one('account.move', string="Invoice")
    month = fields.Integer("Month")
    year = fields.Integer("year")
    sequence_number = fields.Char("Sequence")
    date_invoice = fields.Date("Invoice Date")

class PaymentHistory(models.Model):

    _name = 'account.payment.history'
    _description = "Payment History"

    partner_id = fields.Many2one('res.partner', "Partner", readonly=True)
    payment_date = fields.Date("Payment Date", readonly=True)
    journal_id = fields.Many2one('account.journal', readonly=True)
    amount = fields.Float("Paid Amount", readonly=True)
    loan_id = fields.Many2one('account.loan')
    payment_ids = fields.Many2many('account.payment', 'rel_payment_history', 'payment_history_id', 'rel_pay_history_id')
    invoice_ids = fields.Many2many('account.move', 'rel_inv_pay_history', 'inv_pay_history_id',
                                   'rel_inv_pay_history_id', string='Invoices')
    description = fields.Char('Description')
    payment_method = fields.Selection([('reg_pay', 'Register Payment (on Invoice)'),
                                       ('pay_1', 'Settle with next due instalment rest with principal'),
                                       ('pay_2', 'Cover all next due installments'),
                                       ('pay_3', 'Cover only principal outstanding')], string='Payment Method')

class LoanTransactionHistory(models.Model):

    _name = 'loan.transaction.history'
    _description = "Transaction History"

    date = fields.Date("Date")
    payment_ids = fields.One2many('account.payment', 'history_id', string="Payment Reference")
    reference = fields.Char('Reference')
    description = fields.Char('Description')
    debit = fields.Float('Debit')
    credit = fields.Float('Credit')
    loan_id = fields.Many2one('account.loan', string="Loan")
    move_id = fields.Many2one('account.move', string="Invoice")
    balance = fields.Float("Balance", compute='_get_transaction_balance')

    def _get_transaction_balance(self):
        balance = 0
        for history in self.search([('loan_id', '=', self._context.get('active_id'))],
                                   order="date, id"):
            if history.description == 'Payment Received':
                balance += history.debit
                balance -= history.credit
            elif datetime.strptime(str(history.date), DF).date() < date.today():
                balance += history.debit
                balance -= history.credit
            history.balance = balance

class AccountPayment(models.Model):
    _inherit = 'account.payment'

    history_id = fields.Many2one('loan.transaction.history')

    # Create Payment History and Disbursement Move when paying invoice

    def create_payment_history_and_disbursement_move(self,payment_ids,invoice_id):
    
            payment_his_obj = self.env['account.payment.history']
    
            today = datetime.today().date()
            move_obj = self.env['account.move'].sudo()
            loan_jou_id = self.env.company and self.env.company.sudo().loan_jou_id
            disbursement_acc_id = self.env.company and self.env.company.sudo().loan_disbursement_acc_id
            disbursement_journal_id = self.env.company.sudo().loan_disbursement_journal_id and self.env.company.sudo().loan_disbursement_journal_id.id or False
            loan_jou = self.env['account.journal'].browse(int(disbursement_journal_id))
            for invoice in invoice_id:
                if invoice.loan_id:
                    if not loan_jou_id:
                        raise UserError(_("Please Configure Loan Journal from Loans -> Configurations -> Settings!"))
                    for payment in payment_ids:
                        pay_histories = payment_his_obj.search([('payment_ids', 'in', payment.id),
                                                                ('loan_id', '=', invoice.loan_id.id)])
                        for history in pay_histories:
                            if (history.invoice_ids and invoice.id not in history.invoice_ids.ids) or not \
                                    history.invoice_ids:
                                history.invoice_ids = [(4, invoice.id)]
                    if disbursement_acc_id:
                        partner = invoice.partner_id
                        loan = invoice.loan_id
                        loan_name = loan.name
                        loan_amt = invoice.loan_line_id.principal_amount
                        move = move_obj.create({
                            # 'name': loan_name,
                            'journal_id': disbursement_journal_id,
                            'loan_id': loan and loan.id or False,
                            'ref': loan_name,
                            'date': today,
                            'partner_id': partner and partner.id or False,
                            'move_type':'entry',
                        })
                        lines = [{
                            'account_id': partner.property_account_receivable_id and partner.property_account_receivable_id.id \
                                          or False,
                            'partner_id': partner and partner.id or False,
                            'debit': 0,
                            'credit': loan_amt,
                            'name': loan_name,
                            'date': today,
                            'ref': 'Disbursement Entry',
                            'loan_invoice_id': invoice.id
                        }, {
                            'account_id': int(disbursement_acc_id),
                            'partner_id': partner and partner.id or False,
                            'debit': loan_amt,
                            'credit': 0,
                            'name': loan_name,
                            'date': today,
                            'ref': 'Disbursement Entry',
                            'loan_invoice_id': invoice.id
                        }]
                        move.line_ids = [(0, 0, val) for val in lines]
                        move.post()

    def action_post(self):
        res = super(AccountPayment, self).action_post()
        context = self._context
        if self._context.get('active_model') == 'account.move':
            invoice = self.env['account.move'].search([('id', '=', context.get('active_id'))], limit=1)
        else:
            invoice = self.reconciled_invoice_ids[0] if self.reconciled_invoice_ids else False
        if invoice:
            self.create_payment_history_and_disbursement_move(self,invoice)
            if invoice and invoice.loan_id and not context.get('paid_amount_from_loan'):
                loan = invoice.loan_id
                # Create Payment History
                loan_payment_history_obj = self.env['account.payment.history']
                loan_payment_history_obj.create({
                    'payment_ids': [(4, self.id)],
                    'description': 'Payment Received',
                    'amount': self.amount,
                    'loan_id': loan and loan.id or False,
                    'partner_id': loan.partner_id and loan.partner_id.id or False,
                    'payment_date': self.date,
                    'journal_id': self.journal_id and self.journal_id.id or False,
                    'invoice_ids': [(4, invoice.id)],
                    'payment_method': 'reg_pay'
                })
                # Create Transaction History
                loan_transaction_history_obj = self.env['loan.transaction.history']
                loan_transaction_history_obj.create({
                    'date': self.date,
                    'loan_id': loan and loan.id or False,
                    'reference': self.name,
                    'description': 'Payment Received',
                    'credit': self.amount,
                    'payment_ids': [(4, self.id)]
                })

        return res

    def cancel(self):
        res = super(AccountPayment, self).cancel()
        # Unlink Payment reference from loan payment history
        pay_his_obj = self.env['account.payment.history']
        trans_his_obj = self.env['loan.transaction.history']
        for payment in self:
            transactions = trans_his_obj.search([('reference', '=', payment.name)])
            if transactions:
                transactions.unlink()
            histories = pay_his_obj.search([('payment_ids', 'in', payment.id), ('partner_id', '=', self.partner_id.id)])
            for history in histories:
                if len(history.payment_ids.ids) == 1 and history.payment_ids.id == payment.id:
                    history.unlink()
                else:
                    history.payment_ids = [(3, payment.id)]
                    history.amount -= payment.amount
        return res

class LoanChanges(models.Model):
    _name = 'loan.changes'
    _description = "Loan Changes"

    date = fields.Date('Date of Change')
    due_date_selection = fields.Selection([('by_days', 'By Certain Amount of Days'),
                                        ('by_month', 'By Number of Months'),
                                        ('reset', "Reset all Installment's date")], string="Action")
    data_added = fields.Integer("Days/Months Postponed")
    reason = fields.Text("Reason")
    loan_id = fields.Many2one('account.loan', string="Loan")
    old_inv_date = fields.Date("Initial due date")
    new_inv_date = fields.Date("New due date")

