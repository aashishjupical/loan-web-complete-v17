import logging
from odoo import http, _
from odoo.http import request,route
from odoo.exceptions import UserError
from odoo.addons.web.controllers.utils import ensure_db
from odoo.addons.auth_signup.controllers.main import AuthSignupHome
from email_validator import EmailSyntaxError, EmailUndeliverableError, validate_email
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.addons.auth_signup.models.res_users import SignupError
import base64
import socket
from datetime import datetime
import re

_logger = logging.getLogger(__name__)

class AuthSighup(AuthSignupHome):

    @http.route()
    def web_login(self, *args, **kw):
        ensure_db()
        if request.httprequest.method == 'POST':
            values = request.params.copy()
            user = request.env['res.users'].sudo().search([('login', '=', request.params.get('login'))], limit=1)
            if user and user.verify_email_url and not user.is_verified_user:
                values['error'] = _("Your email address has not been verified. Please check your inbox")
                response = request.render('web.login', values)
                response.headers['X-Frame-Options'] = 'DENY'
                return response

        response = super(AuthSighup, self).web_login(*args, **kw)
        return response 

    @http.route('/web/resend_mail', type='http', auth='public', website=True, sitemap=False)
    def web_auth_mail_resend(self, *args, **kw):
        request.env['res.users'].email_verification_mail(kw['login'],True)
        
    @http.route('/web/mail_verification', type='http', auth='public', website=True, sitemap=False)
    def web_auth_mail_verification(self, *args, **kw):
        
        qcontext = self.get_auth_signup_qcontext()
        if not kw.get('token'):
            raise werkzeug.exceptions.NotFound()
        
        if 'error' not in kw:

            try:
                if kw.get('token'):
                    partner = request.env['res.partner'].sudo()._signup_retrieve_partner(kw.get('token'),True,True)
                    if partner:
                        partner_user = partner.user_ids and partner.user_ids[0] or False
                        if partner_user:
                            partner_user.sudo().write({'password':partner_user.temp_password})
                            qcontext.update({'confirm_password':partner_user.temp_password,'password':partner_user.temp_password})
                            partner_user.is_verified_user = True
                        self.do_signup(qcontext)

                        return request.redirect('/')

            except UserError as e:
                # qcontext['error'] = str("Link is Expire")
                qcontext['error'] = e.args[0]
            except SignupError:
                
                qcontext['error'] = _("Could not reset your password")
                _logger.exception('error when resetting password')
            except Exception as e:
                qcontext['error'] = e.args[0]
                # qcontext['error'] = str("Link is Expire")
        
        return request.redirect('/web/login')
