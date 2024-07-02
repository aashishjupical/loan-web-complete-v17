from odoo import api, fields, models, _
import logging
from odoo.addons.auth_signup.models.res_partner import SignupError, now
from odoo.exceptions import UserError,ValidationError
import werkzeug.urls
_logger = logging.getLogger(__name__)

class ResUsers(models.Model):
    _inherit = 'res.users'
    temp_password = fields.Char("Temp Password")
    verify_email_url = fields.Char("vertify email url")
    is_verified_user = fields.Boolean(copy=False,default=False)
    
    def email_verification_mail(self, login,resend_mail):

        users = self.sudo().search([('login', '=', login)],limit=1)
        if not users:
            users = self.sudo().search([('email', '=', login)],limit=1)
        if len(users) != 1:
            raise Exception(_('Reset password: invalid username or email'))
        if not resend_mail:
            expiration = now(days=+1)
            route = 'mail_verification'
            query = dict(db=self.env.cr.dbname)
            users.partner_id.sudo().signup_prepare("signup",expiration)
            base_url = users.partner_id.get_base_url()

            query['token'] = users.partner_id.sudo().signup_token
            query['login'] = login
            signup_url = "/web/%s?%s" % (route, werkzeug.urls.url_encode(query))
            signup_url = werkzeug.urls.url_join(base_url, signup_url)
            users.verify_email_url = signup_url
        mail_server_id = self.env['ir.mail_server'].sudo().search([],limit=1)
        template_id = self.env.ref('jt_loan_project.sign_up_notify_tmp')
       
        if not template_id:
            _logger.info('template not found...')

        # if not mail_server_id:
        #raise UserError(_("Please configure email server!"))

       
        email_value = {
        'email_from':mail_server_id and mail_server_id.smtp_user or ''
        }

        if template_id:
            template_id.sudo().send_mail(users.id, force_send=True,email_values=email_value)

       
       



