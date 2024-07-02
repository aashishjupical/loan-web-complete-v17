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


class LoanMainController(http.Controller):
    
    @http.route('/my_loan', auth='public', type='http', website=True)
    def my_loan(self ,**post):   
        part_id = request.env.user.partner_id
        app_hs = request.env['loan.application.history'].sudo().search([('partner_id','=',part_id.id)], order='id desc',limit=1)
        if not app_hs:
            if post.get('product_val'):
                product_val = int(post.get('product_val'))
            else:
                product_val = request.env['product.product'].sudo().search([('detailed_type','=','loan')],limit=1).id
            return request.redirect('/demo?product_val=%s' % product_val )
        elif app_hs.filtered(lambda x: x.stages in ('sign_completed')): 
            return request.redirect('/active_loan_details')
        elif app_hs.filtered(lambda x: x.stages in ('apply_now')):
            if post.get('product_val'):
                product_val = int(post.get('product_val'))
            else:
                product_val = request.env['product.product'].sudo().search([('detailed_type','=','loan')],limit=1).id
            return request.redirect('/demo?product_val=%s'  % product_val)
        elif app_hs.filtered(lambda x: x.stages in ('fron_id')):
            return request.redirect('/upload_front_documents')
        elif app_hs.filtered(lambda x: x.stages in ('back_id')):
            return request.redirect('/upload_back_documents')
        elif app_hs.filtered(lambda x: x.stages in ('face_id')):
            return request.redirect('/upload_photo_documents')
        elif app_hs.filtered(lambda x: x.stages in ('review_submit_ekyc')):
            return request.redirect('/identity_success')
        elif app_hs.filtered(lambda x: x.stages in ('submit_doc_dashbord')):
            return request.redirect('/my_loan_calculation')
        elif app_hs.filtered(lambda x: x.stages in ('fill_loan_details','personal_info')):
            return request.redirect('/per_emergency_info')
        elif app_hs.filtered(lambda x: x.stages in ('bank_info')):
            return request.redirect('/emp_bank_acc_info')
        elif app_hs.filtered(lambda x: x.stages in ('document_form','submit_document')):
            return request.redirect('/review_submit_doc')
        elif app_hs.filtered(lambda x: x.stages in ('submit_document_close')):
            return request.redirect('/approve_loan_dashboard')
        elif app_hs.filtered(lambda x: x.stages in ('approved_dashbord')):
            return request.redirect('/start_attestation')
        elif app_hs.filtered(lambda x: x.stages in ('attestation_step_next','watch_att_video','review_agree_attestation','in_person_attestation','in_person_attestation_sch')):
            return request.redirect('/video_attestation')
        elif app_hs.filtered(lambda x: x.stages in ('attestation_completed')):
            return request.redirect('/esign_dashboard')
        elif app_hs.filtered(lambda x: x.stages in ('sign_upload','sign_completed')): 
            return request.redirect('/esign_process')
        else:
            return http.request.render('jt_loan_project.approve_loan_dashboard')

    @http.route(['/demo'], type='http', auth="user", website=True, csrf=False)
    def demo_page(self,  **post):
        if post.get('product_val'):
            product_val = int(post.get('product_val'))
        
        search_product = request.env['product.product'].sudo().search([('id', '=',product_val)])
        # verify_otp_data = False
        opt_recive_data = False
        verified_otp_data = False
        error_message = False
        partner = request.env.user
        part_id = request.env.user.partner_id
        # if post.get('otp_count'):
        #     otp_count = int(post.get('otp_count'))
        # else:
        #     otp_count = 0

        vals = {} 
        app_hs = request.env['loan.application.history'].sudo().search([('partner_id','=',part_id.id),('stages', '!=','submit_document')], order='id desc',limit=1)
        # if app_hs and app_hs.stages=='apply_now':
        #     return request.redirect('/upload_front_doc')
        if request.httprequest.method == 'POST':                
            # if post.get('verified_otp_data',False):
            #     request.env['loan.application.history'].sudo().create({'product_id':search_product.id,'partner_id':part_id.id,'stages':'apply_now'})
            # return request.redirect('/upload-front-doc')
            update_data = {}
            states = request.env['res.country.state'].sudo().search([])

            if post.get('fname'):
                update_data.update({'name':post.get('fname')})
            if post.get('email'):
                update_data.update({'email':post.get('email')})
            if post.get('phone'):
                update_data.update({'mobile':post.get('phone')})
            if post.get('house_number1'):
                update_data.update({'street':post.get('house_number1')})
            if post.get('house_number2'):
                update_data.update({'street2':post.get('house_number2')})
            if post.get('district'):
                update_data.update({'city':post.get('district')}) 
            if post.get('postcode'):
                update_data.update({'zip':post.get('postcode')})
            if post.get('state_id'):
                update_data.update({'state_id':int(post.get('state_id'))})
            if post.get('country'):
                update_data.update({'country_id':int(post.get('country'))})
            if update_data:
                part_id.sudo().write(update_data)

            if not error_message: 
                if app_hs.is_info_failed:
                    if app_hs.is_front_failed:
                        return request.redirect('/upload_front_documents')
                    elif app_hs.is_back_failed:
                        return request.redirect('/upload_back_doc')
                    elif app_hs.is_face_failed:
                        return request.redirect('/upload_scan_doc')
                    else:
                        return request.redirect('/ekyc-img')

                else:
                    vals={'product_id':search_product.id,
                        'partner_id':part_id.id,
                        'stages':'apply_now'}
                    if not app_hs:
                        request.env['loan.application.history'].sudo().create(vals)
                    else:
                        app_hs.write(vals)
                    return request.redirect('/upload_front_documents')
        else:
            cr = []
            cr = request.env.user.login
            partner = request.env.user.partner_id
            vals.update({
                'partner':partner,
                'fname':partner.name,
                'country_id': part_id.country_id and part_id.country_id.id,
                'state_id': part_id.state_id and part_id.state_id.id,
                'city': partner.city,
                'district' : partner.city,
                'phone': partner.mobile,
                'email': partner.email,
                'house_number1':partner.street,
                'house_number2':partner.street2,
                'postcode':partner.zip,
                'error_message' : error_message     
            })
            return request.render("jt_loan_project.demo", vals)

    @http.route(['/upload_front_documents'], type='http', auth="user", website=True, csrf=False)
    def loan_upload_front(self, **post):
        partner = request.env.user
        part_id = request.env.user.partner_id
        app_hs = request.env['loan.application.history'].sudo().search([('partner_id','=',part_id.id),('stages', '!=','submit_document')], order='id desc',limit=1)
        
        if request.httprequest.method == 'POST':
            front_image_process = post.get('front_image_data')

            data_write = {}
            if front_image_process:
                data_write.update({'front_image_file': base64.b64encode(front_image_process.read()),
                    'front_image_name' : front_image_process.filename,
                    'stages' : 'fron_id',
                    })
                app_hs.write(data_write)

            if app_hs.is_front_failed:   
                if app_hs.is_back_failed:
                    return request.redirect('/upload_back_documents')
                elif app_hs.is_face_failed:
                    return request.redirect('/upload_photo_documents')
                else:

                    return request.redirect('/review_identity',vals)
            return request.redirect('/upload_back_documents')


        return request.render("jt_loan_project.front_document")

    @http.route(['/upload_back_documents'], type='http', auth="user", website=True, csrf=False)
    def upload_back_doc(self, **post):
        partner = request.env.user
        part_id = request.env.user.partner_id
        app_hs = request.env['loan.application.history'].sudo().search([('partner_id','=',part_id.id),('stages', '!=','submit_document')], order='id desc',limit=1)
        if request.httprequest.method == 'POST':
            back_image_process = post.get('back_image_data')
            data_write = {}
            if back_image_process:
                data_write.update({'back_image_file': base64.b64encode(back_image_process.read()),
                    'back_image_name' : back_image_process.filename,
                    'stages' : 'back_id',
                    })
                app_hs.write(data_write)
            if app_hs.is_back_failed:   
                if app_hs.is_face_failed:
                    return request.redirect('/upload_photo_documents')
                else:
                    return request.redirect('/review_identity')
            return request.redirect('/upload_photo_documents')

        return request.render("jt_loan_project.back_document")

    @http.route(['/upload_photo_documents'], type='http', auth="user", website=True, csrf=False)
    def upload_photo_doc(self, **post):
        partner = request.env.user
        part_id = request.env.user.partner_id
        app_hs = request.env['loan.application.history'].sudo().search([('partner_id','=',part_id.id),('stages', '!=','submit_document')], order='id desc',limit=1)
        if request.httprequest.method == 'POST':
            photo_image_process = post.get('photo_image_data')
            data_write = {}
            if photo_image_process:
                data_write.update({'face_image_file': base64.b64encode(photo_image_process.read()),
                    'face_image_name' : photo_image_process.filename,
                    'stages' : 'face_id',
                    })
                app_hs.write(data_write)

            
            return request.redirect('/review_identity')

        return request.render("jt_loan_project.photo_document")

    @http.route(['/review_identity'], type='http', auth="user", website=True, csrf=False)
    def review_identity(self, **post):
        partner = request.env.user
        part_id = request.env.user.partner_id
        app_hs = request.env['loan.application.history'].sudo().search([('partner_id','=',part_id.id)], order='id desc',limit=1)
        data_write = {}
        child_id = app_hs.partner_id
        if request.httprequest.method == 'POST':
            pro_data = request.env.ref('jt_loan_project.project_project_loan').id
            history_doc = {}
            history_doc.update({'stages':'review_submit_ekyc'})
            
            data_write.update({
                'project_id': pro_data,
                'name': part_id.name,
                'partner_id':part_id.id,
                'front_id':app_hs.front_image_file,
                'front_id_file' : app_hs.front_image_name,
                'back_id':app_hs.back_image_file,
                'back_id_file' : app_hs.back_image_name,
                'face_verify' : app_hs.face_image_file,
                'face_verify_file' : app_hs.face_image_name,
                'product_id' : app_hs.product_id.id,
                'current_ip' : post.get('get_cuurent_ip',''),
                })
            
            if app_hs.task_id:
                project_task = app_hs.task_id.write(data_write)
            else:
                project_task = request.env['project.task'].sudo().create(data_write)
                app_hs.task_id = project_task.id 
                app_hs.task_id.sudo().pass_ekyc()
                                             
                
            task_history = app_hs.write(history_doc)
            return request.redirect('/identity_success')                           
        vals = {'full_name':child_id.name,
                'email' : child_id.email,
                'address_1' : child_id.street,
                'address_2' : child_id.street2,
                'person_district' : child_id.city,
                'person_postcode' : child_id.zip,
                'person_state' : child_id.state_id.name,
                'person_country' : child_id.country_id.name,
                }       
        return request.render("jt_loan_project.review_identity",vals)

    @http.route(['/identity_success'], type='http', auth="user", website=True, csrf=False)
    def identity_success(self, **post):
        partner = request.env.user
        part_id = request.env.user.partner_id
        app_hs = request.env['loan.application.history'].sudo().search([('partner_id','=',part_id.id)], order='id desc',limit=1)
        if request.httprequest.method == 'POST':
            app_hs.stages = 'submit_doc_dashbord'
            return request.redirect('/my_loan_calculation')
        return request.render("jt_loan_project.identity_success")

    @http.route(['/create-acc'], type='http', auth="public", website=True, csrf=False)
    def create_account(self, **post):
        if post.get('error_message_input',False) and post.get('error_message_input',False)=='1':
            return
        error_msg = False
        error_pwd_msg = False
        error_match_pwd = False
        user_email = post.get('email',False)
        user_name = post.get('name',False)
        user_mobile = post.get('mobile_no',False)
        
      
        box_visible = False
        call_resend_pop = 0
        err_number_msg = False
        err_len = False
        err_lower = False
        err_caps = False
        err_digit = False
        err_special = False
        get_method_load = True
        if post.get('call_resend_pop',0):
            box_visible = True
            user_email = post.get('email')
            user_name = post.get('name')
            user_mobile = post.get('mobile_no')
            call_resend_pop = 1
            request.env['res.users'].email_verification_mail(post['email'],True)

        if request.httprequest.method == 'POST' and post.get('password'):
            user_email = post.get('email')
            user_name = post.get('name')
            user_mobile = post.get('mobile_no')
            user_password = post.get('password')
            user_confirm_password = post.get('confirm_password')
            get_method_load = False
            # if user_email:
            #     match = re.match('^[_a-z0-9-]+(\.[_a-z0-9-]+)*@[a-z0-9-]+(\.[a-z0-9-]+)*(\.[a-z]{2,4})$', user_email)
            #     if match == None:
            #         error_msg = 'Please enter the correct an email format'

            # if user_password:
            #     if (len(user_password)<8):
            #         err_len = True
            #         error_pwd_msg = 'Please enter the correct password'
            #     if not re.search("[a-z]", user_password):
            #         err_lower = True
            #         error_pwd_msg = 'Please enter the correct password'
            #     if not re.search("[A-Z]", user_password):
            #         err_caps = True
            #         error_pwd_msg = 'Please enter the correct password'
            #     if not re.search("[0-9]", user_password):
            #         err_digit = True
            #         error_pwd_msg = 'Please enter the correct password'
            #     if not re.search("[_!@.,#$%^&*/;|]" , user_password):
            #         err_special = True
            #         error_pwd_msg = 'Please enter the correct password'
            #     if re.search("\s" , user_password):
            #         error_pwd_msg = 'Please enter the correct password'

            if user_password and user_confirm_password and user_password != user_confirm_password:
                error_match_pwd = "Your password doesn't match!"

            if not error_msg and not error_pwd_msg and not error_match_pwd:
                exist_user = request.env['res.users'].sudo().search([('login','=',user_email)],limit=1)
                exist_number = request.env['res.partner'].sudo().search([('mobile','=',user_mobile)],limit=1)
                if exist_number:
                    err_number_msg = 'Your mobile number is already registered to another account'              
                if not exist_user and not exist_number:
                    values = {
                        'name': user_name,
                        'login': user_email,
                        'temp_password': user_password,
                    }
                    try:
                        exist_user = request.env.user._signup_create_user(values)
                        exist_user.partner_id.write({
                        'mobile':user_mobile,
                        'email':user_email,
                        })
                        sudo_users = request.env["res.users"].with_context(create_user=True,signup_force_type_in_url='mail_verification').sudo()
                        sudo_users.email_verification_mail(user_email,False)
                        box_visible = True
                        call_resend_pop = 1
                    except Exception as e:
                        return e
                elif exist_user:
                    error_msg = 'Already User registered'
        vals = {
                'email':user_email,
                'name':user_name,
                'mobile_no':user_mobile,
                'error_msg': error_msg,
                'err_number_msg': err_number_msg,
                'error_pwd_msg': error_pwd_msg,
                'error_match_pwd': error_match_pwd,
                'box_visible': box_visible,
                'call_resend_pop' : call_resend_pop,
                'err_len' : err_len,
                'err_lower' : err_lower,
                'err_caps' : err_caps,
                'err_digit' : err_digit,
                'err_special' : err_special,
                'get_method_load' : get_method_load,
                }
        return request.render('jt_loan_project.create_account_page',vals)
