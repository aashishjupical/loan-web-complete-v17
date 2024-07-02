# -*- coding: utf-8 -*-
from odoo import fields, models


class LoanAppHistory(models.Model):
    _name = "loan.application.history"
    _description = "Loan Application History"

    name = fields.Char(string="Name",default="Loan Application History")
    partner_id = fields.Many2one('res.partner',string='Full Name')
    email = fields.Char(string="Your Email",related='partner_id.email')
    country_id = fields.Many2one(string="Country", comodel_name='res.country',related='partner_id.country_id')
    state_id = fields.Many2one('res.country.state', 'State', domain="[('country_id', '=', country_id)]",related='partner_id.state_id')
    phone = fields.Char(string="Mobile",related='partner_id.mobile')
    city = fields.Char(string="City",related='partner_id.city')
    stages = fields.Selection([('apply_now', 'Apply Now'),
                                ('fron_id','Front ID'),
                                ('back_id','Back ID'),
                                ('face_id','Face ID'),
                                ('review_submit_ekyc','Review Submit Ekyc'), 
                                ('submit_doc_dashbord','Submit Doc Dashbord'),
                                ('fill_loan_details','Fill Loan Details'),
                                ('personal_info','Personal Info'),
                                ('bank_info','Bank Info'), 
                                ('document_form', 'Document Form'),
                                ('submit_document', 'Submit Document'),
                                ('submit_document_close', 'Submit Document Close'),
                                ('approved_dashbord', 'Approved Dashbord'),
                                ('attestation_step_next','Attestation Step Next'),
                                ('watch_att_video','Watch Att Video'),
                                ('review_agree_attestation','Review Agree Attestation'),
                                ('in_person_attestation','In Person Attestation'),
                                ('in_person_attestation_sch','IN Person Attestation Sch'),
                                ('attestation_completed','Attestation Completed'),
                                ('sign_upload','Sign Upload'),
                                ('sign_completed','Sign Completed'),

                                ], string="Status")
    salary_amt = fields.Char(string="Total Monthly Income")
    loan_amt = fields.Char(string="Loan Amount")
    month_id = fields.Many2one('loan.month', string="Loan Tenure")
    monthly_repayment = fields.Char(string="Monthly Repayment")
    total_repayment = fields.Char(string="Total Repayment")
    interest_rate = fields.Char(string="Interest Rate")
    stamping_fee = fields.Char(string="Stamping Fee")
    total_int_get = fields.Char("Total Interest")

    #Document Section
    salary_slip = fields.Binary(string="Salary slip")   
    salary_slip_file = fields.Char(string="Salary slip File")
    ea_statement = fields.Binary(string="EA Statement")
    ea_statement_file = fields.Char(string="EA Statement File")
    be_form_tax_receipts = fields.Binary(string="BE Form with Tax Receipts")
    be_form_tax_receipts_file = fields.Char(string="BE Form with Tax Receipts File")
    savings_account_statement = fields.Binary(string="Savings Account Statement")
    savings_account_statement_file = fields.Char(string="Savings Account Statement File")
    employment_letter = fields.Binary(string="Employment Letter")
    employment_letter_file = fields.Char(string="Employment Letter File")
    is_loan_approve = fields.Boolean(copy=False,string="Loan Approve")
    is_loan_reject = fields.Boolean(copy=False,string="Loan Reject")
    task_id = fields.Many2one("project.task",string="Task")

    #========================#
    front_image_file = fields.Binary(string="Front Image File")
    front_image_name = fields.Char(string="Front Image Name")
    back_image_file = fields.Binary(string="Back Image File")
    back_image_name = fields.Char(string="Back Image Name")
    face_image_file = fields.Binary(string="Face Image File")
    face_image_name = fields.Char(string="Face Image Name")
    product_id = fields.Many2one('product.product',string="Product Name")
    is_front_failed = fields.Boolean("Front Failed",copy=False)
    is_back_failed = fields.Boolean("Back Failed",copy=False)
    is_face_failed = fields.Boolean("Face Failed")
    is_info_failed = fields.Boolean("User Info Failed")

    #====E-sign Process============#
    e_sign_otp = fields.Boolean("E-sign OTP")
    e_sign_done = fields.Boolean("E-sign Veri")
    sign_image = fields.Binary('Sign')