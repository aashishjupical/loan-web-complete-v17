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

class LoanApproveController(http.Controller):

    @http.route(['/approve_loan_dashboard'], type='http', auth="user", website=True, csrf=False)
    def approve_loan_dashboard(self, **post):
        part_id = request.env.user.partner_id
        app_hs = request.env['loan.application.history'].sudo().search([('partner_id','=',part_id.id)], order='id desc',limit=1)
        if app_hs and app_hs.is_loan_approve:
            return request.redirect('/loan_approval_success')
        elif app_hs and app_hs.is_loan_reject:
            return request.redirect('/loan_approval_rejected')
        else:
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
                    'aprrove':True,
            }
            return request.render("jt_loan_project.approve_loan_dashboard",vals)
        
    @http.route(['/loan_approval_success'], type='http', auth="user", website=True, csrf=False)
    def loan_approval_success(self, **post):
        part_id = request.env.user.partner_id
        app_hs = request.env['loan.application.history'].sudo().search([('partner_id','=',part_id.id)], order='id desc',limit=1)
        if request.httprequest.method == 'POST':
            if app_hs:
                app_hs.stages='approved_dashbord'
            return request.redirect('/start_attestation')
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
        return request.render("jt_loan_project.loan_approval_success",vals)

    @http.route(['/loan_approval_rejected'], type='http', auth="user", website=True, csrf=False)
    def loan_approval_rejected(self, **post):
        part_id = request.env.user.partner_id
        app_hs = request.env['loan.application.history'].sudo().search([('partner_id','=',part_id.id)], order='id desc',limit=1)
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
        return request.render("jt_loan_project.loan_approval_rejected",vals)

    @http.route(['/product_page'], type='http', auth="user", website=True, csrf=False)
    def product_page(self, **post):
        return request.render("jt_loan_project.product_page")