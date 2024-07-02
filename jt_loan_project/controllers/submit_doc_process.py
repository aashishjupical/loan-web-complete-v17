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

class LoanSubmitDocController(http.Controller):

    @http.route(['/my_submit_loan'], type='http', auth="user", website=True, csrf=False)
    def my_loan(self, **post):
        part_id = request.env.user.partner_id
        app_hs = request.env['loan.application.history'].sudo().search([('partner_id','=',part_id.id)], order='id desc',limit=1)
        data_write = {}

        if request.httprequest.method == 'POST':
            return request.redirect('/per_emergency_info')
        company_currency = request.env.company.currency_id
        currency_sym = company_currency.symbol
        total_repayment_amt = currency_sym + ' '+ "0.00"
        get_loan_amt =currency_sym + ' '+  "0.00"
        monthly_repayment = currency_sym + ' '+ "0.00"
        stamping_fee = currency_sym + ' '+ "0.00"
        if app_hs.task_id:
            if app_hs.task_id.total_repayment:
                total_repayment_amt = float(app_hs.task_id.total_repayment)
                # total_repayment_amt = currency_sym + ' '+ str('{:,.2f}'.format(app_hs.task_id.total_repayment))
            
            if app_hs.task_id.loan_amt:   
                get_loan_amt = float(app_hs.task_id.loan_amt)
                # get_loan_amt = currency_sym + ' '+ str('{:,.2f}'.format(float(app_hs.task_id.loan_amt)))

            if app_hs.task_id.monthly_repayment:
                monthly_repayment =float(app_hs.task_id.monthly_repayment)    
                # monthly_repayment = currency_sym + ' '+ str('{:,.2f}'.format(app_hs.task_id.monthly_repayment))    

            if app_hs.task_id.stamping_fee:
                stamping_fee = float(app_hs.task_id.stamping_fee)
                # stamping_fee = currency_sym + ' '+ str('{:,.2f}'.format(app_hs.task_id.stamping_fee))
        vals = {
                'monthly_repayment': monthly_repayment,
                'principal_sum': get_loan_amt,
                'total_repayment': total_repayment_amt,
                'interest_rate': app_hs.interest_rate,
                'tenure_duration':app_hs.month_id and str(app_hs.month_id.name)+ " Months" or '',
                'stamping_fee': stamping_fee,
        } 
        return request.render("jt_loan_project.submit_doc_dashboard",vals)

    @http.route(['/per_emergency_info'], type='http', auth="user", website=True, csrf=False)
    def per_emerg_info(self, **post):
        part_id = request.env.user.partner_id
        app_hs = request.env['loan.application.history'].sudo().search([('partner_id','=',part_id.id)], order='id desc',limit=1)
        emg_cont_relationship = []
        emg_cont_relationship = dict(part_id._fields['emergency_contact_relationship'].selection)
        address_line_1 = False
        address_line_2 = False
        fill_district = False
        fill_postcode = False
        state_id = False
        country_id = False
        person_full_name = False
        emergency_phone_no = False
        select_relationship = False
        error_msg = False
        partner_dob_get = False
        convert_date = False
        is_error = False 
        error_address_line_1 = False
        error_address_line_2 = False
        error_address_line_2 = False
        error_fill_district = False
        error_fill_postcode = False
        error_state_id = False
        error_country_id = False
        error_person_full_name = False
        error_emergency_phone_no = False
        error_select_relationship = False
        error_partner_dob_get = False

        if request.httprequest.method == 'POST':
            # new partner data create
            if post.get('c_add1',False):
               address_line_1 = post.get('c_add1')
            else:
                error_address_line_1 = True
                is_error = True   

            if post.get('c_add2',False):
               address_line_2 = post.get('c_add2')
            else:
                error_address_line_2 = True
                is_error = True   

            if post.get('fill_district',False):
               fill_district = post.get('fill_district')
            else:
                error_fill_district = True
                is_error = True   

            if post.get('fill_postcode',False):
               fill_postcode = post.get('fill_postcode')
            else:
                error_fill_postcode = True
                is_error = True    

            if post.get('state_id',False):
               state_id = post.get('state_id')
               state_id = int(state_id)
            else:
                error_state_id = True
                is_error = True

            if post.get('country_id',False):
               country_id = post.get('country_id')
               country_id = int(country_id)
            else:
                error_country_id = True
                is_error = True   


            # current partner data write
            if post.get('person_full_name',False):
               person_full_name = post.get('person_full_name')
            else:
                error_person_full_name = True
                is_error = True      

            if post.get('emergency_phone_no',False):
               emergency_phone_no = post.get('emergency_phone_no')
            else:
                error_emergency_phone_no = True
                is_error = True

            if post.get('select_relationship',False):
               select_relationship = post.get('select_relationship')
            else:
                error_select_relationship = True
                is_error = True

            update_partner = {
                'emergency_contact_name': person_full_name,
                'emergency_contact_no':emergency_phone_no,
                'emergency_contact_relationship':select_relationship,
            }
            if part_id.mobile == emergency_phone_no:
                error_msg = True
                is_error = True


            if part_id:
                part_id.write(update_partner)

                if app_hs:
                    app_hs.stages = 'personal_info'

                return request.redirect('/emp_bank_acc_info')        

        child_id = part_id
        vals = {}
        if child_id:
            vals = {
                'full_name': child_id.name,
                'email':child_id.email,
                'add_1': child_id.street,
                'person_district': child_id.city,
                'person_postcode': child_id.zip,
                'person_country': child_id.country_id.name,
                'person_country_id': child_id.country_id.id,
                'person_state_id': child_id.state_id.id,
                'person_state': child_id.state_id.name,
                'error_msg':error_msg,
                'country_id' : child_id.country_id.id,


            }
        current_child_id = part_id
        if current_child_id:
            vals.update({
                'c_add1':current_child_id.street,
                'c_add2':current_child_id.street2,
                'fill_district':current_child_id.city,
                'fill_postcode':current_child_id.zip,
                'country_id': current_child_id.country_id.id,
                'state_id': current_child_id.state_id.id,
            })

        emg_contact_no = False
        if part_id.emergency_contact_no:
           emg_contact_no = part_id.emergency_contact_no
        

        
        vals.update({
            'person_full_name': part_id.emergency_contact_name,
            'emergency_phone_no': emg_contact_no,
            'select_relationship': part_id.emergency_contact_relationship,
            'emg_cont_relationship': emg_cont_relationship,
            'error_address_line_1':error_address_line_1,
            'error_address_line_2':error_address_line_2,
            'error_fill_district':error_fill_district,
            'error_fill_postcode':error_fill_postcode,
            'error_state_id':error_state_id,
            'error_country_id':error_country_id,
            'error_person_full_name':error_person_full_name,
            'error_emergency_phone_no':error_emergency_phone_no,
            'error_select_relationship':error_select_relationship,
        })
        
        return request.render("jt_loan_project.per_emergency_info",vals)

    @http.route(['/emp_bank_acc_info'], type='http', auth="user", website=True, csrf=False)
    def emp_bank_acc_info(self, **post):
        part_id = request.env.user.partner_id
        app_hs = request.env['loan.application.history'].sudo().search([('partner_id','=',part_id.id)], order='id desc',limit=1)

        #bank Search
        bank_search = request.env['res.bank'].sudo().search([])
        if bank_search:
            bank_data = bank_search

        
        employee_type = []
        for rec in part_id:
            employee_type = dict(rec._fields['select_employee_type'].selection)
        # vals = {}
        is_error = False 
        company_business_name = False
        select_employee_type = False
        com_bussiness_contact_no = False
        position_designation_type = False
        registeration_no = False
        bussiness_address_line_1 = False
        bussiness_address_line_2 = False
        company_district = False
        company_postcode = False
        country_id = False
        state_id = False
        account_holder_name = False
        account_number = False
        
        error_company_business_name = False
        error_bank_name = False
        error_select_employee_type = False
        error_com_bussiness_contact_no = False
        error_position_designation_type = False
        error_registeration_no = False
        error_bussiness_address_line_1 = False
        error_bussiness_address_line_2 = False
        error_company_district = False
        error_company_postcode = False
        error_country_id = False
        error_state_id = False
        error_account_holder_name = False
        error_account_number = False
        if request.httprequest.method == 'POST':
            if post.get('company_business_name',False):
                company_business_name = post.get('company_business_name',False)
            else:
                is_error = True
                error_company_business_name = True

            if post.get('selected_employee_type_id',False):
                select_employee_type = post.get('selected_employee_type_id',False)
            else:
                select_employee_type = 'self_employed'
               
            if post.get('com_bussiness_contact_no',False):
                com_bussiness_contact_no = post.get('com_bussiness_contact_no',False)
            else:
                is_error = True
                error_com_bussiness_contact_no = True
            if post.get('position_designation_type',False):
                position_designation_type = post.get('position_designation_type',False)
            else:
                is_error = True
                error_position_designation_type = True

            if post.get('registeration_no',False):
                registeration_no = post.get('registeration_no',False)
            else:
                is_error = True
                error_registeration_no = True 

            if post.get('bussiness_address_line_1',False):
                bussiness_address_line_1 = post.get('bussiness_address_line_1',False)
            else:
                is_error = True
                error_bussiness_address_line_1 = True 

            if post.get('bussiness_address_line_2',False):
                bussiness_address_line_2 = post.get('bussiness_address_line_2',False)
            else:
                is_error = True
                error_bussiness_address_line_2 = True 

            if post.get('company_district',False):
                company_district = post.get('company_district',False)
            else:
                is_error = True
                error_company_district = True

            if post.get('company_postcode',False):
                company_postcode = post.get('company_postcode',False)
            else:
                is_error = True
                error_company_postcode = True

            if post.get('account_holder_name',False):
                account_holder_name = post.get('account_holder_name',False)
            else:
                is_error = True
                error_account_holder_name = True

            if post.get('account_number',False):
                account_number = post.get('account_number',False)
            else:
                is_error = True
                error_account_number = True

            if post.get('select_bank_name_id',False):
                bank_name = int(post.get('select_bank_name_id',False))
            else:
                is_error = True
                error_bank_name = True    
            if not is_error:
                part_id.update({
                    'company_business_name': company_business_name,
                    'select_employee_type': 'self_employed' if select_employee_type == 'Choose here' else select_employee_type,
                    'com_bussiness_contact_no': com_bussiness_contact_no,
                    'position_designation_type': position_designation_type,
                    'registeration_no': registeration_no,
                    'bussiness_address_line_1': bussiness_address_line_1,
                    'bussiness_address_line_2': bussiness_address_line_2,
                    'company_district': company_district,
                    'company_postcode': company_postcode,
                    'company_country_id': country_id,
                    'company_state_id': state_id,
                    'function' : position_designation_type,
                })
            bank_create = request.env['res.partner.bank'].sudo().search([('acc_number', '=',account_number)])
            if not bank_create and not is_error:
                
                bank_create.create({
                    'acc_number': account_number,
                    'partner_id':part_id.id,
                    'bank_id': bank_name,
                    'acc_holder_name':account_holder_name,
                })

            if app_hs and not is_error:
                app_hs.stages = 'bank_info'
            
            if not is_error:    
                if select_employee_type == 'self_employed':
                    return request.redirect('/doc_self_emp')

                elif select_employee_type == 'salaried_employed':
                    return request.redirect('/doc_salarised_emp')
        
        bank_get = app_hs and app_hs.partner_id and app_hs.partner_id.bank_ids and  app_hs.partner_id.bank_ids[0] or False
        vals = {
                'select_bank_name':bank_data or False, 
                'select_employee_type':employee_type,
                'company_business_name': part_id.company_business_name,
                'select_employee_type_id': part_id.select_employee_type,
                'com_bussiness_contact_no': part_id.com_bussiness_contact_no,
                'position_designation_type': part_id.position_designation_type,
                'registeration_no': part_id.registeration_no,
                'bussiness_address_line_1': part_id.bussiness_address_line_1,
                'bussiness_address_line_2': part_id.bussiness_address_line_2,
                'company_district': part_id.company_district,
                'company_postcode': part_id.company_postcode,
                'country_id': part_id.company_country_id.id,
                'state_id': part_id.company_state_id.id,
                'function' : part_id.position_designation_type,
                'account_holder_name':bank_get and bank_get.acc_holder_name or '',
                'account_number':bank_get and bank_get.acc_number or '',

                'select_bank_set': bank_get and bank_get.bank_id.id or '',

                'error_company_business_name': error_company_business_name,
                'error_select_employee_type':error_select_employee_type,
                'error_com_bussiness_contact_no':error_com_bussiness_contact_no,
                'error_position_designation_type':error_position_designation_type,
                'error_registeration_no':error_registeration_no,
                'error_bussiness_address_line_1':error_bussiness_address_line_1,
                'error_bussiness_address_line_2':error_bussiness_address_line_2,
                'error_company_district':error_company_district,
                'error_company_postcode':error_company_postcode,
                'error_country_id':error_country_id,
                'error_state_id':error_state_id,
                'error_account_holder_name':error_account_holder_name,
                'error_account_number':error_account_number,
                'error_bank_name':error_bank_name,

            }
        return request.render("jt_loan_project.emp_bank_acc_info",vals)

    @http.route(['/doc_salarised_emp'], type='http', auth="user", website=True, csrf=False)
    def doc_salarised_emp(self, **post):
        part_id = request.env.user.partner_id
        app_hs = request.env['loan.application.history'].sudo().search([('partner_id','=',part_id.id)], order='id desc',limit=1)
        error_1 = False
        error_2 = False
        error_3 = False
        error_4 = False
        error_5 = False
        is_error = False
        payslips_pdf_get = False
        payslip_2_pdf = False
        payslip_3_pdf = False
        bank_statement_pdf = False
        lst_utility_bill = False


        if request.httprequest.method == 'POST':
            doc_data={}
            payslips_pdf_get1 = post.get('payslips_pdf1',False)
            if payslips_pdf_get1:             
                doc_data.update({'payslips_pdf': base64.b64encode(payslips_pdf_get1.read()),
                    'payslips_pdf_file': payslips_pdf_get1.filename})

            elif not app_hs.task_id.payslips_pdf:
                error_1 = True
                is_error = True

            payslips_pdf_get2 = post.get('payslips_pdf2',False)
            if payslips_pdf_get2:             
                doc_data.update({'payslip_2_pdf': base64.b64encode(payslips_pdf_get2.read()),
                    'payslip_2_pdf_file': payslips_pdf_get2.filename})

            elif not app_hs.task_id.payslip_2_pdf:
                error_2 = True
                is_error = True

            payslips_pdf_get3 = post.get('payslips_pdf3',False)
            if payslips_pdf_get3:             
                doc_data.update({'payslip_3_pdf': base64.b64encode(payslips_pdf_get3.read()),
                    'payslip_3_pdf_file': payslips_pdf_get3.filename})

            elif not app_hs.task_id.payslip_3_pdf:
                error_3 = True
                is_error = True

            bankstatement = post.get('bankstatement',False)
            if bankstatement:             
                doc_data.update({'bank_statement_pdf': base64.b64encode(bankstatement.read()),
                    'bank_statement_pdf_file': bankstatement.filename})

            elif not app_hs.task_id.bank_statement_pdf:
                error_4 = True
                is_error = True

            utility_bill = post.get('utility_bill',False)
            if utility_bill:             
                doc_data.update({'lst_utility_bill': base64.b64encode(utility_bill.read()),
                    'lst_utility_bill_file': utility_bill.filename})

            elif not app_hs.task_id.lst_utility_bill:
                error_5 = True
                is_error = True
            if not is_error and app_hs:
                app_hs.task_id.sudo().write(doc_data)
                app_hs.stages = 'document_form'

                return request.redirect('/review_submit_doc')
        payslips_pdf_get1 = app_hs.task_id.payslips_pdf
        payslips_pdf_get2 = app_hs.task_id.payslip_2_pdf
        payslips_pdf_get3 = app_hs.task_id.payslip_3_pdf
        bankstatement = app_hs.task_id.bank_statement_pdf
        utility_bill = app_hs.task_id.lst_utility_bill
        vals = {
                'error_1':error_1,
                'error_2':error_2,
                'error_3':error_3,
                'error_4':error_4,
                'error_5':error_5,
                'payslips_pdf1': payslips_pdf_get1,
                'payslips_pdf2': payslips_pdf_get2,
                'payslips_pdf3': payslips_pdf_get3,
                'bankstatement':bankstatement,
                'utility_bill':utility_bill,
        }
        return request.render("jt_loan_project.doc_salarised_emp",vals)

    @http.route(['/doc_self_emp'], type='http', auth="user", website=True, csrf=False)
    def doc_self_emp(self, **post):
        part_id = request.env.user.partner_id
        app_hs = request.env['loan.application.history'].sudo().search([('partner_id','=',part_id.id)], order='id desc',limit=1)
        error_1 = False
        error_2 = False
        error_3 = False
        error_4 = False
        is_error = False
        business_registration = False
        personal_bank_statement = False
        comapany_bank_statement = False
        lst_utility_bill = False
        if request.httprequest.method == 'POST':
            doc_data={}
            
            self_employed_ssm_register = post.get('self_employed_ssm_register',False)
            if self_employed_ssm_register:             
                doc_data.update({'self_employed_ssm_register_1_pdf': base64.b64encode(self_employed_ssm_register.read()),
                    'self_employed_ssm_register_1_pdf_file': self_employed_ssm_register.filename})

            elif not app_hs.task_id.self_employed_ssm_register_1_pdf_file:
                error_1 = True
                is_error = True

            self_employed_latest_utility_bill = post.get('self_employed_latest_utility_bill',False)
            if self_employed_latest_utility_bill:             
                doc_data.update({'self_employed_latest_utility_bill_pdf': base64.b64encode(self_employed_latest_utility_bill.read()),
                    'self_employed_latest_utility_bill_pdf_file': self_employed_latest_utility_bill.filename})

            elif not app_hs.task_id.self_employed_latest_utility_bill_pdf:
                error_2 = True
                is_error = True



            personal_bank_statement = post.get('personal_bank_statement',False)
            if personal_bank_statement:             
                doc_data.update({'personal_bank_statement_pdf': base64.b64encode(personal_bank_statement.read()),
                    'personal_bank_statement_pdf_file': personal_bank_statement.filename})

            elif not app_hs.task_id.company_bank_statement_pdf:
                error_3 = True
                is_error = True

            company_bank_statement = post.get('company_bank_statement',False)
            if company_bank_statement:             
                doc_data.update({'company_bank_statement_pdf': base64.b64encode(company_bank_statement.read()),
                    'company_bank_statement_pdf_file': company_bank_statement.filename})

            elif not app_hs.task_id.company_bank_statement_pdf:
                error_4 = True
                is_error = True
            
            app_hs.task_id.sudo().write(doc_data)
            if app_hs:
                app_hs.stages = 'document_form'

            return request.redirect('/review_submit_doc')
        self_employed_latest_utility_bill = app_hs.task_id.self_employed_latest_utility_bill_pdf
        personal_bank_statement_pdf = app_hs.task_id.personal_bank_statement_pdf
        company_bank_statement_pdf = app_hs.task_id.company_bank_statement_pdf
        self_employed_ssm_register = app_hs.task_id.self_employed_ssm_register_1_pdf
        vals = {
                'error_1':error_1,
                'error_2':error_2,
                'error_3':error_3,
                'error_4':error_4,
                'self_employed_ssm_register':self_employed_ssm_register,
                'self_employed_latest_utility_bill': self_employed_latest_utility_bill,
                'personal_bank_statement': personal_bank_statement_pdf,
                'company_bank_statement': company_bank_statement_pdf,
        }
        return request.render("jt_loan_project.doc_self_emp",vals)

    @http.route(['/review_submit_doc'], type='http', auth="user", website=True, csrf=False)
    def review_submit_doc(self, **post):
        stampping_fee = False
        monthly_repayment =False
        principal_sum =False
        total_repayment =False
        interest_rate =False
        tenure =False
        part_id = request.env.user.partner_id
        app_hs = request.env['loan.application.history'].sudo().search([('partner_id','=',part_id.id)], order='id desc',limit=1)
        
        if request.httprequest.method == 'POST':
            if app_hs:
                app_hs.task_id.sudo().confirm_documents()
                app_hs.stages = 'submit_document'
            return request.redirect('/submit_doc_success')
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
                'tenure_duration':app_hs.month_id and str(app_hs.month_id.name) +" Months"or '',
                'stamping_fee': stamping_fee,
        }
        return request.render("jt_loan_project.review_submit_doc",vals)

    @http.route(['/submit_doc_success'], type='http', auth="user", website=True, csrf=False)
    def submit_doc_success(self, **post):
        part_id = request.env.user.partner_id
        app_hs = request.env['loan.application.history'].sudo().search([('partner_id','=',part_id.id)], order='id desc',limit=1)
        if request.httprequest.method == 'POST':
            if app_hs:
                app_hs.stages = 'submit_document_close'
            return request.redirect('/approve_loan_dashboard')
        return request.render("jt_loan_project.submit_doc_success")

    @http.route(['/my_loan_calculation'], type='http', auth="user", website=True, csrf=False)
    def my_loan_calculation(self, **post):
        part_id = request.env.user.partner_id
        err_msg_loan_amt = False
        err_msg_monthly_amt = False
        app_hs = request.env['loan.application.history'].sudo().search([('partner_id','=',part_id.id)], order='id desc',limit=1)
        if request.httprequest.method == 'POST':
            total_repayment_get = False
            if app_hs:
                #loan_amt
                get_loan_amount = False
                convert_loan_amt = False

                if post.get('loan_amount','0.00'):
                    get_loan_amount = re.sub("[^0-9.]","",str(post.get('loan_amount','0.00')))
                    convert_loan_amt = float(get_loan_amount)

                if not convert_loan_amt:
                    err_msg_loan_amt = "Please enter valid loan amount"

                # For this code : Error Message to covert string to float
                if post.get('monthly_income','0.00'):
                    monthly_income_val = re.sub("[^0-9.]","",str(post.get('monthly_income','0.00')))
                    if monthly_income_val:
                        convert_monthly_income_val = float(monthly_income_val)
                    else:
                        convert_monthly_income_val = 0.0

                if not convert_monthly_income_val:
                    err_msg_monthly_amt = "Please enter valid Gross Monthly Income"
                # End Error Message covert code

                #total_int_get
                get_total_int_get = False
                convert_total_int_get = False
                if post.get('total_int_get','0.00'):
                    get_total_int_get = re.sub("[^0-9.]","",str(post.get('total_int_get','0.00')))
                    if get_total_int_get:
                        convert_total_int_get = float(get_total_int_get)
                    else:
                        convert_total_int_get = 0.0

                #other charges
                get_other_chargers = False
                convert_other_chargers = False
                if post.get('other_chargers','0.00'):
                    get_other_chargers = re.sub("[^0-9.]","",str(post.get('other_chargers','0.00')))
                    convert_other_chargers = float(get_other_chargers)   
                total_repayment_get = convert_loan_amt + convert_total_int_get
                app_data = {'stages':'fill_loan_details',
                        'loan_amt':post.get('loan_amount','0.00'),
                        'month_id' : post.get('loan_id') and int(post.get('loan_id')) or False,
                        'salary_amt' : post.get('monthly_income'),
                        'monthly_repayment' : post.get('calculation_set_get','0.00'),
                        'stamping_fee' : post.get('other_chargers','0.00'),
                        'interest_rate' : post.get('interest_rate_get','0.0%'),
                        'total_int_get' : post.get('total_int_get','0.0'),
                        'total_repayment' :str(total_repayment_get),                        
                        }
                app_hs.write(app_data)
            
            if app_hs.task_id:

                #loan_amt
                get_loan_amount = False
                convert_loan_amt = False
                
                if post.get('loan_amount','0.00'):
                    get_loan_amount = re.sub("[^0-9.]","",str(post.get('loan_amount','0.00')))
                    if get_loan_amount:
                        convert_loan_amt = float(get_loan_amount)
                    else:
                        convert_loan_amt = 0.0
                #salary_amt
                get_monthly_income = False
                convert_monthly_income = False
                if post.get('monthly_income','0.00'):
                    get_monthly_income = re.sub("[^0-9.]","",str(post.get('monthly_income','0.00')))
                    if get_monthly_income:
                        convert_monthly_income = float(get_monthly_income)
                    else:
                        convert_monthly_income = 0.0


                #monthly_repayment
                get_monthly_repayment = False
                convert_monthly_repayment = False
                if post.get('calculation_set_get','0.00'):
                    get_monthly_repayment = re.sub("[^0-9.]","",str(post.get('calculation_set_get','0.00')))
                    if get_monthly_repayment:
                        convert_monthly_repayment = float(get_monthly_repayment)
                    else:
                        convert_monthly_repayment = 0.0

                #stamping_fee
                get_stamping_fee = False
                convert_stamping_fee = False
                if post.get('other_chargers','0.00'):
                    get_stamping_fee = re.sub("[^0-9.]","",str(post.get('other_chargers','0.00')))
                    if get_stamping_fee:
                        convert_stamping_fee = float(get_stamping_fee)
                    else:
                        convert_stamping_fee = 0.0
                
                #interest_rate
                get_interest_rate = False
                convert_interest_rate = False
                if post.get('interest_rate_get','0.00'):
                    get_interest_rate = re.sub("[^0-9.]","",str(post.get('interest_rate_get','0.00')))
                    if get_interest_rate:
                        convert_interest_rate = float(get_interest_rate)
                    else:
                        convert_interest_rate = 0.0

                #total_int_get
                get_total_int_get = False
                convert_total_int_get = False
                if post.get('total_int_get','0.00'):
                    get_total_int_get = re.sub("[^0-9.]","",str(post.get('total_int_get','0.00')))
                    if get_total_int_get:
                        convert_total_int_get = float(get_total_int_get)    
                    else:
                        convert_total_int_get = 0.0

                task_data = {
                        'loan_amt':convert_loan_amt,
                        'salary_amt' : convert_monthly_income,
                        'month_id' : post.get('loan_id') and int(post.get('loan_id')) or False,
                        'monthly_repayment' : convert_monthly_repayment,
                        'stamping_fee' : convert_stamping_fee,
                        'interest_rate' : convert_interest_rate,
                        'total_int_get' : convert_total_int_get,
                        'total_repayment': convert_loan_amt + convert_total_int_get
                        }
               
                app_hs.task_id.write(task_data)
            if not err_msg_loan_amt and not err_msg_monthly_amt:
                return request.redirect('/my_submit_loan')
        vals={'product_stmp_price':0.0}
        if app_hs:
            product_stmp_price = 0
            if app_hs.task_id.stamping_fee:
                product_stmp_price = app_hs.task_id.stamping_fee
            elif app_hs.stamping_fee:
                get_stamping_fee = re.sub("[^0-9.]","",str(app_hs.stamping_fee))
                if get_stamping_fee:
                    product_stmp_price = float(get_stamping_fee)
                else:
                    product_stmp_price = 0.0

            vals.update({
                'loan_amount':app_hs.loan_amt,
                'loan_id': app_hs.month_id.id,
                'monthly_income': app_hs.salary_amt,
                'calculation_set_get':app_hs.monthly_repayment,
                'total_int_get':app_hs.total_int_get,
                'product_stmp_price' : product_stmp_price,
                'product':app_hs.product_id and app_hs.product_id.id,
            })
        product_stmp_id = False
        process_fee_pro_id = request.env['ir.config_parameter'].sudo().get_param('jt_loan_management.processing_fee_prod_id')
        if process_fee_pro_id:
            product_stmp_id = request.env['product.product'].sudo().browse(int(process_fee_pro_id))
        vals.update({'product_stamping':product_stmp_id,
                    'err_msg_loan_amount':err_msg_loan_amt,
                    'err_msg_monthly_income':err_msg_monthly_amt})
        return request.render("jt_loan_project.my_loan_calculation",vals)