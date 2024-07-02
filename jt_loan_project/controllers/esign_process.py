import logging
from odoo import http, _
from odoo.http import request,route
from odoo.exceptions import UserError
from odoo.addons.web.controllers.main import ensure_db, Home
from odoo.addons.auth_signup.controllers.main import AuthSignupHome
from email_validator import EmailSyntaxError, EmailUndeliverableError, validate_email
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.addons.auth_signup.models.res_users import SignupError
import base64
import socket
from datetime import datetime
import re

_logger = logging.getLogger(__name__)

class LoanEsignProcessController(http.Controller):

    @http.route(['/esign_dashboard'], type='http', auth="user", website=True, csrf=False)
    def esign_dashboard(self, **post):
        part_id = request.env.user.partner_id
        app_hs = request.env['loan.application.history'].sudo().search([('partner_id','=',part_id.id)], order='id desc',limit=1)
        if request.httprequest.method == 'POST':
            # if app_hs:
            #     app_hs.stages = 'attestation_step_next'
            return request.redirect('/esign_agreement')
        company_currency = request.env.company.currency_id
        currency_sym = company_currency.symbol
        total_repayment_amt = currency_sym + ' '+ "0.00"
        get_loan_amt =currency_sym + ' '+  "0.00"
        monthly_repayment = currency_sym + ' '+ "0.00"
        stamping_fee = currency_sym + ' '+ "0.00"
        if app_hs.task_id:
            if app_hs.task_id.total_repayment:
                total_repayment_amt = currency_sym + ' '+ str('{:,.2f}'.format(app_hs.task_id.total_repayment))
            
            if app_hs.task_id.loan_amt:   
                get_loan_amt = currency_sym + ' '+ str('{:,.2f}'.format(float(app_hs.task_id.loan_amt)))

            if app_hs.task_id.monthly_repayment:
                monthly_repayment = currency_sym + ' '+ str('{:,.2f}'.format(app_hs.task_id.monthly_repayment))    

            if app_hs.task_id.stamping_fee:
                stamping_fee = currency_sym + ' '+ str('{:,.2f}'.format(app_hs.task_id.stamping_fee))
        vals = {
                'monthly_repayment': monthly_repayment,
                'principal_sum': get_loan_amt,
                'total_repayment': total_repayment_amt,
                'interest_rate': app_hs.interest_rate,
                'tenure_duration':app_hs.month_id and str(app_hs.month_id.name) + " Months" or '',
                'stamping_fee': stamping_fee,
        }   
        return request.render("jt_loan_project.esign_dashboard",vals)

    @http.route(['/esign_agreement'], type='http', auth="user", website=True, csrf=False)
    def esign_agreement(self, **post):
        part_id = request.env.user.partner_id
        app_hs = request.env['loan.application.history'].sudo().search([('partner_id','=',part_id.id)], order='id desc',limit=1)
        upload_agreement = False
        error_1 = False
        is_error = False
        if request.httprequest.method == 'POST':
            doc_data={}
            upload_agreement_get = post.get('upload_agreement',False)
            if upload_agreement_get:             
                doc_data.update({'esign_pdf': base64.b64encode(upload_agreement_get.read()),
                    'esign_pdf_file': upload_agreement_get.filename})

            elif not app_hs.task_id:
                error_1 = True
                is_error = True
            if not is_error and app_hs:
                app_hs.task_id.esign_date = app_hs.task_id.get_current_time()
                app_hs.task_id.sudo().write(doc_data)
                app_hs.stages = 'sign_upload'
            return request.redirect('/esign_process')
        return request.render("jt_loan_project.esign_agreement")

    @http.route(['/esign_process'], type='http', auth="user", website=True, csrf=False)
    def esign_process(self, **post):
        part_id = request.env.user.partner_id
        app_hs = request.env['loan.application.history'].sudo().search([('partner_id','=',part_id.id)], order='id desc',limit=1)
       
        company_currency = request.env.company.currency_id
        currency_sym = company_currency.symbol
        total_repayment_amt = currency_sym + ' '+ "0.00"
        get_loan_amt =currency_sym + ' '+  "0.00"
        monthly_repayment = currency_sym + ' '+ "0.00"
        stamping_fee = currency_sym + ' '+ "0.00"
        disbursment_done = False
        if app_hs.task_id:
            if app_hs.task_id.total_repayment:
                total_repayment_amt = currency_sym + ' '+ str('{:,.2f}'.format(app_hs.task_id.total_repayment))
            
            if app_hs.task_id.loan_amt:   
                get_loan_amt = currency_sym + ' '+ str('{:,.2f}'.format(float(app_hs.task_id.loan_amt)))

            if app_hs.task_id.monthly_repayment:
                monthly_repayment = currency_sym + ' '+ str('{:,.2f}'.format(app_hs.task_id.monthly_repayment))    

            if app_hs.task_id.stamping_fee:
                stamping_fee = currency_sym + ' '+ str('{:,.2f}'.format(app_hs.task_id.stamping_fee))
            if app_hs.task_id.is_disbursed:
                disbursment_done = True

        vals = {
                'monthly_repayment': monthly_repayment,
                'principal_sum': get_loan_amt,
                'total_repayment': total_repayment_amt,
                'interest_rate': app_hs.interest_rate,
                'tenure_duration':app_hs.month_id and str(app_hs.month_id.name) + " Months" or '',
                'stamping_fee': stamping_fee,
                'esign':True,
        }
        if disbursment_done:
            return request.redirect('/esign_success')
        else:
            return request.render("jt_loan_project.approve_loan_dashboard",vals)
    
    @http.route(['/esign_success'], type='http', auth="user", website=True, csrf=False)
    def esign_success(self, **post):
        part_id = request.env.user.partner_id
        app_hs = request.env['loan.application.history'].sudo().search([('partner_id','=',part_id.id)], order='id desc',limit=1)
        if request.httprequest.method == 'POST':
            if app_hs and app_hs.task_id:
                app_hs.task_id.esignature_done()
                app_hs.stages = 'sign_completed'

            return request.redirect('/active_loan_details')
        return request.render("jt_loan_project.esign_success")

    @http.route(['/active_loan_details'], type='http', auth="user", website=True, csrf=False)
    def active_loan_details(self, **post):
        part_id = request.env.user.partner_id
        app_hs = request.env['loan.application.history'].sudo().search([('partner_id','=',part_id.id)], order='id desc',limit=1)
        monthly_repayment = False
        type_interest = False
        outstanding_amount = False
        no_of_intallment = False
        loan_pro_id = False
        if app_hs.task_id:
            if app_hs.task_id.loan_pro_id:
                loan_pro_id = app_hs.task_id.loan_pro_id
            if loan_pro_id:
                monthly_repayment = loan_pro_id.loan_amount
                no_of_intallment = loan_pro_id.periods
                outstanding_amount = loan_pro_id.outstanding_bal
                # type_interest = loan_pro_id.interest_type
                type_interest = dict(loan_pro_id._fields['interest_type'].selection).get(loan_pro_id.interest_type)
        vals = {
                'monthly_repayment': monthly_repayment,
                'tenure_duration':app_hs.month_id and str(app_hs.month_id.name) + " Months" or '',
                'type_interest': type_interest,
                'outstanding_amount':outstanding_amount,
                'no_of_intallment':no_of_intallment,
                'loan_statement':loan_pro_id and loan_pro_id.line_ids,
        }
        return request.render("jt_loan_project.active_loan_details",vals)

    @http.route(['/active_loan'], type='http', auth="user", website=True, csrf=False)
    def active_loan(self, **post):
        return request.render("jt_loan_project.active_loan")

    @http.route(['/product_disclosure'], type='http', auth="public", website=True, csrf=False)
    def productdiscloser(self,**post):
        report_data = request.env['ir.config_parameter'].sudo().get_param('jt_loan_project.product_disclosure')
        if report_data:
            content_base64 = base64.b64decode(report_data)
            pdfhttpheaders = [('Content-Type', 'application/pdf'), ('Content-Length', len(content_base64))]
            return request.make_response(content_base64, pdfhttpheaders)
        else:
            return request.redirect("/esign_agreement")
