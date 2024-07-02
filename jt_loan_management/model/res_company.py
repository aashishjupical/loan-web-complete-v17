from odoo import api, fields, models, _

class ResCompany(models.Model):
    _inherit = 'res.company'

    start_loan = fields.Boolean("Start Loan for this company")
    loan_disbursement_acc_id = fields.Many2one('account.account',string="Disbursement Account", copy=False)
    loan_write_off_account_id = fields.Many2one('account.account', string='Write-Off Account', copy=False)
    loan_interest_prod_id = fields.Many2one('product.product', string='Interest',
            help='Product used to invoice as interest of the loans.', copy=False)
    loan_processing_fee_prod_id = fields.Many2one('product.product', string='Processing Fee',
           help='Product used as Processing fee of the loans.', copy=False)
    loan_agent_fee_prod_id = fields.Many2one('product.product', string='Agent Fee',
           help='Product used as Agent fee of the loans.', copy=False)
    loan_acc_rec_id = fields.Many2one('account.account', string="Current Assets", copy=False)
    loan_income_acc_id = fields.Many2one('account.account', string="Loan Income Account", copy=False)
    loan_jou_id = fields.Many2one('account.journal', string="Loans Journal", copy=False)
    loan_disbursement_journal_id = fields.Many2one('account.journal', string="Disbursement Journal", copy=False)
    loan_inv_create_date = fields.Integer(string='No. of Days', help="Create installment invoice before no. of days of due date of invoice.", copy=False)
    loan_counter = fields.Integer("Loan counter", compute="_compute_company_loan", copy=False)
    penalty_product_id = fields.Many2one("product.product", string="Penalty Product", copy=False)
    loan_principal_prod_id = fields.Many2one("product.product", string="Principal Product", copy=False)

    def _compute_company_loan(self):
        for company in self:
            if self.env['account.loan'].search([('company_id','=',company.id), ('state','=','posted')], limit=1):
                company.loan_counter = 1
            else:
                company.loan_counter = 0
