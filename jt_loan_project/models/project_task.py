from odoo import api, fields, models, _
import socket
from odoo.exceptions import UserError,ValidationError
import werkzeug.urls
from datetime import datetime, date, timedelta
import pytz
from pytz import timezone
import base64
import xmltodict
from odoo.http import request
from urllib.request import urlopen
import re as r



class ProjectTask(models.Model):
    _inherit = 'project.task'

    ekyc_ip = fields.Char(string="IP Address", tracking=True)
    loan_pro_id = fields.Many2one('account.loan', string="Loan",copy=False)
    disbursment_amount = fields.Monetary(related="loan_pro_id.loan_amount", currency_field='currency_id', string="Disbursement Amount", tracking=True)
    stage_loan = fields.Selection([('ekyc','Ekyc'), ('submit_doc', 'Submit Docs & Fill Form'), ('to_approve', 'To Approve'),
        ('sch_att', 'Schedule Attestation'), ('esign','Esignature'), ('disbursed', 'Loan Disbursement'),
        ('terminate', 'Terminated')], default="ekyc")
    currency_id = fields.Many2one('res.currency', readonly=True)
    date_ekyc = fields.Datetime(string="Ekyc Date", tracking=True)
    front_id = fields.Binary(string="Verify Front ID")
    front_id_file = fields.Char(string="Front ID File")
    back_id = fields.Binary(string="Verify Back ID")
    back_id_file = fields.Char(string="Back ID File")
    face_verify = fields.Binary(string="Verify Face")
    face_verify_file = fields.Char(string="Verify Face File")

    is_recommend = fields.Boolean(string="Recommended?")
    is_disbursed = fields.Boolean(string="Is Disbursed?")

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
    payslips_pdf = fields.Binary(string="Payslip (1st Month)")
    payslip_2_pdf = fields.Binary(string="Payslip (2nd Month)")
    payslip_3_pdf = fields.Binary(string="Payslip (3rd Month)")
    bank_statement_pdf = fields.Binary(string="Bank Statement (last 6 Month)")
   
    epf_statement = fields.Binary(string="EPF Statement (with minimum 12 months contribution)")
    lst_utility_bill = fields.Binary(string="Latest Utility Bill (as per home address)")

    payslips_pdf_file = fields.Char(string="Payslip (1st Month) File")
    payslip_2_pdf_file = fields.Char(string="Payslip (2nd Month) File")
    payslip_3_pdf_file = fields.Char(string="Payslip (3rd Month) File")
    bank_statement_pdf_file = fields.Char(string="Bank Statement (1st Month) File")
    lst_utility_bill_file = fields.Char(string="Latest Utility Bill (as per home address) File")

    # Self Employee document form fields
    self_employed_ssm_register_1_pdf = fields.Binary(string="Employee SSM Registration")
    self_employed_latest_utility_bill_pdf = fields.Binary(string="Employee Utility Bill")
    personal_bank_statement_pdf = fields.Binary(string="Personal Bank Statement (last 6 Months)")
    
    company_bank_statement_pdf = fields.Binary(string="Company Bank Statement (6 Months)")
    
    self_employed_ssm_register_1_pdf_file = fields.Char(string="Employee SSM Registration File")
    self_employed_latest_utility_bill_pdf_file = fields.Char(string="Employee Utility Bill File")
    personal_bank_statement_pdf_file = fields.Char(string="Personal Bank Statement (last 6 Month) File")
    
    company_bank_statement_pdf_file = fields.Char(string="Company Bank Statement (1st Month) File")
    

    month_id = fields.Many2one('loan.month', string="Loan Tenure", tracking=True)
    app_form_date = fields.Datetime("Application Form Date", tracking=True)
    app_form_ip = fields.Char('Application Form IP', tracking=True)
    salary_amt = fields.Char("Total Monthly Income", tracking=True)
    loan_amt = fields.Char("Loan Amount", tracking=True)
    monthly_repayment = fields.Float("Monthly Repayment", tracking=True)
    stamping_fee = fields.Float("Stamping Fee", tracking=True)
    interest_rate = fields.Float("Interest Rate", tracking=True)
    total_int_get = fields.Float("Total Interest", tracking=True)
    total_repayment = fields.Float("Total Repayment", tracking=True)

    attestation_date = fields.Datetime("Attestation Date", tracking=True)
    attestation_ip = fields.Char("Attestation IP", tracking=True)
    attestation_method = fields.Selection([('self_recorded','Self Recorded'), ('in_person', 'In-Person')])
    attestation_video_file = fields.Char(string="Attestation Video File Name")
    attestation_video = fields.Binary("Attestation Video")
    meeting_link = fields.Char("Meeting Link")

    accept_attestation_ip = fields.Char('Accept Attestation IP', tracking=True)
    accept_attestation_date = fields.Datetime('Accept Attestation Date', tracking=True)

    terminate_reason_id = fields.Many2one('terminate.reason', string="Termination Reason")
    terminate_user_id = fields.Many2one('res.users', string="User")
    terminate_date = fields.Datetime('Terminate Date', tracking=True)
    terminate_ip = fields.Char('Terminate IP', tracking=True)

    loan_disbused_ip = fields.Char("Loan Disbursement IP", tracking=True)
    disbursment_date = fields.Datetime("Disbursement Date", tracking=True)
    disbursment_ip = fields.Char("Disbursement IP", tracking=True)
    
    esign_date = fields.Datetime("Esignature Date", tracking=True)
    esign_ip = fields.Char("Esignature IP", tracking=True)
    current_ip = fields.Char("IP")
    res_binary = fields.Binary("SIGN PDF")
    sign_file_name = fields.Char(default="Sign PDF File", string="Sign PDF Name")
    esign_pdf_file = fields.Char(string="Esign PDF File Name")
    esign_pdf = fields.Binary(string="Esign PDF File")
    esign_sign_file = fields.Char(string="Esign Sign File Name")
    esign_sign = fields.Binary(string="Signature")

    attestation_url = fields.Char(" Attestation URL")
    attestation_no_url = fields.Char("URL")
    rejected_url = fields.Char("Reject URL")
    do_attestation_url = fields.Char("Do Attestation URL")
    do_esign_url = fields.Char("Esign URL")

    video_attestation_expiry_date = fields.Datetime(string="Expiry to upload video attestation", tracking=True)
    video_inperson_expiry_date = fields.Datetime(string="Expiry to upload In-Person attestation", tracking=True)
    expiry_to_sign_agreement_expiry_date = fields.Datetime(string="Expiry to sign agreement", tracking=True)

    loan_approval_date = fields.Datetime("Loan Approval Date", tracking=True)
    loan_approval_ip = fields.Char("Loan Approval Ip", tracking=True)

    product_id = fields.Many2one('product.product',string="Product")
    cale_event_id = fields.Many2one('calendar.event', string='Events link')
    comp_info_bank_statement_1_pdf=fields.Binary(string="Bank Statement 01")
    comp_info_bank_statement_1_pdf_file=fields.Char(string="Bank Statement 01 File")
    comp_info_bank_statement_2_pdf=fields.Binary(string="Bank Statement 02")
    comp_info_bank_statement_2_pdf_file=fields.Char(string="Bank Statement 02 File")
    comp_info_bank_statement_3_pdf=fields.Binary(string="Bank Statement 03")
    comp_info_bank_statement_3_pdf_file=fields.Char(string="Bank Statement 03 File")

    bank_statement_1_pdf=fields.Binary(string="Bank Statements 01")
    bank_statement_1_pdf_file=fields.Char(string="Bank Statements 01 File")
    bank_statement_2_pdf=fields.Binary(string="Bank Statements 02")
    bank_statement_2_pdf_file=fields.Char(string="Bank Statements 02 File")
    bank_statement_3_pdf=fields.Binary(string="Bank Statements 03")
    bank_statement_3_pdf_file=fields.Char(string="Bank Statements 03 File")

    def get_user_time(self,date_data,user_timezone):
        cur_time = date_data.astimezone(timezone(user_timezone))
        con_date_str = cur_time.strftime("%Y-%m-%d %H:%M:%S")
        con_str_date = datetime.strptime(con_date_str,"%Y-%m-%d %H:%M:%S")
        return con_str_date

    def get_current_time(self):
        cur_time = datetime.now(pytz.timezone('UTC'))
        con_date_str = cur_time.strftime("%Y-%m-%d %H:%M:%S")
        con_str_date = datetime.strptime(con_date_str,"%Y-%m-%d %H:%M:%S")
        return con_str_date

    def write(self, vals):
        res = super(ProjectTask, self).write(vals)
        for record in self:
            if 'stage_id' in vals:
                stage_task_id = vals.get('stage_id')
                stage = self.env['project.task.type'].search([('id', '=', stage_task_id)])
                ekyc = self.env.ref('jt_loan_project.project_loan_stage_0')
                app_hs = self.env['loan.application.history'].sudo().search([('task_id','=',record.id)], order='id desc',limit=1)
                if stage == ekyc:
                    record.write({
                        'stage_loan': 'ekyc'
                    })
                    if app_hs:
                        app_hs.is_loan_reject = False
                submit_doc = self.env.ref('jt_loan_project.project_loan_stage_1')
                if stage == submit_doc:
                    record.write({
                        'stage_loan': 'submit_doc'
                    })
                    if app_hs:
                        app_hs.is_loan_reject = False
                
                recommend_approval = self.env.ref('jt_loan_project.project_loan_stage_3')
                if stage == recommend_approval:
                    record.write({
                        'is_recommend': False,
                        'stage_loan': 'to_approve'
                    })
                    if app_hs:
                        app_hs.is_loan_reject = False

                schedule_etestation = self.env.ref('jt_loan_project.project_loan_stage_4')
                if stage == schedule_etestation:
                    record.write({
                        'stage_loan': 'sch_att'
                    })
                    if app_hs:
                        app_hs.is_loan_reject = False

                esgignture = self.env.ref('jt_loan_project.project_loan_stage_5')
                if stage == esgignture:
                    record.write({
                        'stage_loan': 'esign',
                        'esign_date' : False,
                        'esign_ip'  : False, 
                    })
                    if app_hs:
                        app_hs.is_loan_reject = False
                        app_hs.e_sign_otp = False
                        app_hs.e_sign_done = False
                        
                disbursment = self.env.ref('jt_loan_project.project_loan_stage_6')
                if stage == disbursment:
                    record.write({
                        'is_disbursed':False,
                        'stage_loan': 'disbursed'                      
                    })
                    if app_hs:
                        app_hs.is_loan_reject = False

                terminate = self.env.ref('jt_loan_project.project_loan_stage_7')
                if stage == terminate:
                    record.write({
                        'stage_loan': 'terminate'                        
                    })
                    if app_hs:
                        app_hs.is_loan_reject = True
        return res

    def unlink(self):
        for project in self:
            if project.loan_pro_id and project.loan_pro_id.state != "cancelled":
                raise ValidationError(_("You can not delete task Loan is already Validated."))
            app_hs = self.env['loan.application.history'].search([('task_id.id','=',project.id)])
            if app_hs:
                for history in app_hs:
                    history.unlink()
        return super(ProjectTask,self).unlink()

    def recommend_approval(self):
        self.write({
            'is_recommend': True
        })

    def approved_attestation(self):      
        exp_att = self.env['ir.config_parameter'].sudo().get_param('jt_loan_project.sign_attestation_time')
        shift_time = float(exp_att)
        hour, minute = divmod(shift_time, 1)
        minute = minute*60
        cur_time = datetime.now(pytz.timezone('UTC')) + timedelta(hours=hour,minutes=minute)
        con_date_str = cur_time.strftime("%Y-%m-%d %H:%M:%S")
        con_str_date = datetime.strptime(con_date_str,"%Y-%m-%d %H:%M:%S")
        self.write({
            'stage_id': self.env.ref('jt_loan_project.project_loan_stage_5').id,
            'attestation_date': self.get_current_time(),
            'attestation_ip': self.current_ip,
            'expiry_to_sign_agreement_expiry_date': con_str_date,
        })
        self.set_do_esign_url()
        
        template_id = self.env.ref('jt_loan_project.customer_notify_mail_template')
        exp_esign = self.env['ir.config_parameter'].sudo().get_param('jt_loan_project.sign_attestation_time')
        shift_time = float(exp_esign)
        hour, minute = divmod(shift_time, 1)
        minute = minute*60
        hours = int(hour)
        minutes = int(minute)
        # msg ='<p>Your Attestation Is Completed.</p><p>Last Step E-Sign Loan Agreement.</p><p>Attestation Has been Completed.</p><p>Last Step, Your Signature is required for the Loan Agreement.</p><p><b>Note : Please sign in '+ str(hours and hours or '0')+':'+str(minutes and minutes or '0')+' hours.</p><p>In the event you do not sign within the timeframe - Loan Will be canceled.</p>'
        if template_id:
            template_id.sudo().with_context({'hour':hours,'minutes':minutes}).send_mail(self.id, force_send=True) 

    def approved(self):
        for record in self:
            if record.sudo().loan_pro_id and record.sudo().loan_pro_id.state=="draft":
                record.loan_pro_id.sudo().post_loan()            
        self.set_video_verification_url()
        # Send Approval loan email to user when click on Approve button
        template = self.env.ref('jt_loan_project.mail_template_data_loan_approved')
        exp_att = self.env['ir.config_parameter'].sudo().get_param('jt_loan_project.expire_attestation_time')
        shift_time = float(exp_att)
        hour, minute = divmod(shift_time, 1)
        minute = minute*60
        hours = int(hour)
        minutes = int(minute)        
        if template:
            template.sudo().with_context({'hours':hours,'minutes':minutes}).send_mail(self.id, force_send=True)
        self.video_verification_expiry_date_set()
        self.video_inperson_expiry_date_set()
        self.write({
            'loan_approval_date': self.get_current_time(),
            'loan_approval_ip': self.current_ip,
            'stage_id': self.env.ref('jt_loan_project.project_loan_stage_4').id,
            })
        app_hs = self.env['loan.application.history'].sudo().search([('task_id','=',self.id)], order='id desc',limit=1)
        if app_hs:
            app_hs.is_loan_approve = True
    
    def send_stamped_agreement(self):
        for loan in self:
            self.write({'stage_id':self.env.ref('jt_loan_project.project_loan_stage_6').id,})
            mail_server_id = self.env['ir.mail_server'].sudo().search([],limit=1)
            template_id = self.env.ref('jt_loan_project.stamped_agreement_mail_template')
            if not template_id:
                _logger.info('template not found...')
            # if not mail_server_id:
            #     raise UserError(_("Please configure email server!"))
            # msg ='<p>Your Loan Agreement(unstamped) is ready</p><p><b>Note : within 14 days we will send u the stamped agreement.</b></p><p>You will Also me notified via email when loan has been disbursed (2-3 Working Days)</p>'
            if template_id:
                template_id.send_mail(loan.id, force_send=True)

    def video_verification_expiry_date_set(self):
        exp_att = self.env['ir.config_parameter'].sudo().get_param('jt_loan_project.expire_attestation_time')
        shift_time = float(exp_att)
        hour, minute = divmod(shift_time, 1)
        minute = minute*60        
        self.attestation_video = False        
        self.meeting_link = ""        
        self.attestation_date = False        
        self.attestation_ip = False
        cur_time = datetime.now(pytz.timezone('UTC')) + timedelta(hours=hour,minutes=minute)
        con_date_str = cur_time.strftime("%Y-%m-%d %H:%M:%S")
        con_str_date = datetime.strptime(con_date_str,"%Y-%m-%d %H:%M:%S")
        self.write({'video_attestation_expiry_date': con_str_date})


    def video_inperson_expiry_date_set(self):
        inper_att = self.env['ir.config_parameter'].sudo().get_param('jt_loan_project.expire_inperson_att_time')
        shift_time = float(inper_att)
        hour, minute = divmod(shift_time, 1)
        minute = minute*60    
        self.attestation_video = False        
        self.meeting_link = ""        
        self.attestation_date = False        
        self.attestation_ip = False        
        self.accept_attestation_date = False        
        self.accept_attestation_ip = False
        inper_time = datetime.now(pytz.timezone('UTC')) + timedelta(hours=hour,minutes=minute)
        inper_date_str = inper_time.strftime("%Y-%m-%d %H:%M:%S")
        inper_str_date = datetime.strptime(inper_date_str,"%Y-%m-%d %H:%M:%S")
        self.write({'video_inperson_expiry_date': inper_str_date})

    def video_attestation_expiry_date_set(self):
        exp_att = self.env['ir.config_parameter'].sudo().get_param('jt_loan_web.expire_attestation_time')

        shift_time = float(exp_att)
        hour, minute = divmod(shift_time, 1)
        minute = minute*60
        
        self.attestation_video = False
        
        self.meeting_link = ""
        
        self.attestation_date = False
        
        self.attestation_ip = False

        cur_time = datetime.now(pytz.timezone('UTC')) + timedelta(hours=hour,minutes=minute)
        con_date_str = cur_time.strftime("%Y-%m-%d %H:%M:%S")
        con_str_date = datetime.strptime(con_date_str,"%Y-%m-%d %H:%M:%S")
        self.write({'video_attestation_expiry_date': con_str_date})

    def disbursement_done(self):

        self.write({
            'disbursment_date': self.get_current_time(),
            'disbursment_ip': self.current_ip,
            'is_disbursed': True,
        })
        
        if self.stage_loan == 'to_approve' :
            body = 'Loan Amount: %s <br/>\n Disbursement Date: %s' % (self.disbursment_amount, self.disbursment_date)
            self.loan_pro_id.message_post(body=body)

    def set_video_verification_url(self):
        route = 'pre-video-upload'
        route_no = 'appointment/member'
        route_reject = 'loan-reject'
        route_do_attestation = 'approve_loan_dashboard'
        users = self.env.user
        query = dict(db=self.env.cr.dbname)
        query['task_id'] = self.id
        query['partner_id'] = self.partner_id.id
        base_url = users.partner_id.get_base_url()
        yes_url = "/%s?%s&&" % (route,werkzeug.urls.url_encode(query))
        yes_url = werkzeug.urls.url_join(base_url, yes_url)
        no_url = "/%s?%s&&" % (route_no,werkzeug.urls.url_encode(query))
        no_url = werkzeug.urls.url_join(base_url, no_url)
        reject_url = "/%s?%s&&" % (route_reject,werkzeug.urls.url_encode(query))
        reject_url = werkzeug.urls.url_join(base_url, reject_url)
        attestation_url = "/%s?%s&&" % (route_do_attestation,werkzeug.urls.url_encode(query))
        attestation_url = werkzeug.urls.url_join(base_url, attestation_url)
        self.write({
            'attestation_url': yes_url,
            'attestation_no_url': no_url,
            'rejected_url': reject_url,
            'do_attestation_url':attestation_url,
            })  


    def set_do_esign_url(self):
        route = 'esign_dashboard'
        route_no = 'appointment/member'
        route_reject = 'loan-reject'
        route_do_attestation = 'approve_loan_dashboard'
        users = self.env.user
        query = dict(db=self.env.cr.dbname)
        query['task_id'] = self.id
        query['partner_id'] = self.partner_id.id
        base_url = users.partner_id.get_base_url()
        esign_url = "/%s?%s&&" % (route,werkzeug.urls.url_encode(query))
        esign_url = werkzeug.urls.url_join(base_url, esign_url)
        
        self.write({
            'do_esign_url':esign_url,
            })  

    def confirm_documents(self):
        self.write({
            'stage_id': self.env.ref('jt_loan_project.project_loan_stage_3').id,
            'app_form_date': self.get_current_time(),
            'app_form_ip': self.current_ip,
        })

    def pass_ekyc(self):
        if self.front_id and self.back_id and self.face_verify:
            self.write({
                'date_ekyc':self.get_current_time(),
                'ekyc_ip':self.current_ip,
                'stage_id': self.env.ref('jt_loan_project.project_loan_stage_1').id,
            })
        else:
            raise ValidationError(_("Please Upload All ekyc Documents."))

    def esignature_done(self):
        self.write({
            'esign_date':self.get_current_time(),
            'esign_ip':self.current_ip,
            })
        self.create_loan_from_task()

    def create_loan_from_task(self):
        for record in self:
            if not record.loan_pro_id:
                # product = self.env['product.product'].search([('detailed_type', '=', 'property')], limit=1)
                if record.product_id:
                    tax_product = self.env['product.product'].search([('type','=','tax')],limit=1)
                    insurance_product = self.env['product.product'].search([('type','=','insurance')],limit=1)
                    current_date = fields.Date.today()
                    current_date_temp = datetime.strptime(str(current_date), "%Y-%m-%d")
                    newdate = current_date_temp + timedelta(days=5)
                    loan_id = self.env['account.loan'].sudo().create({
                        'partner_id': record.partner_id.id,
                        'loan_amount': record.loan_amt,
                        'down_payment': 0,
                        'product_id': record.product_id.id,
                        'insurance_product_id': insurance_product.id,
                        'tax_product_id': tax_product.id,
                        'start_date': current_date,
                        'first_payment_due': newdate,
                        'rate': 10,
                        'interest_type': 'simple',
                        'method_period': 1,
                        'periods': record.month_id and record.month_id.name or 12,
                    })
                    if loan_id:
                        record.write({
                            'loan_pro_id': loan_id.id,
                        })
                        
                else:
                    raise ValidationError(_("Please create a product."))
            else:
                record.loan_pro_id.write({'loan_amount': record.loan_amt,
                    'periods': record.month_id and record.month_id.name or 12
                    })

class LoanMonth(models.Model):
    _name = 'loan.month'
    _description = 'Tenure Month Model'
    _order = 'name'

    name = fields.Integer(string="Month")

class ProductTemplate(models.Model):

    _inherit = "product.template"

    detailed_type = fields.Selection(selection_add=[('loan','Loan')],ondelete={'loan': 'set default'})
    type = fields.Selection(selection_add=[('loan', 'Loan')])
    stamp_duty_type = fields.Selection([('fixed','Fixed'),('percentage','Percentage')],string="Stamp Duty Type",default='fixed')
    stamp_duty_percentage = fields.Float("Percentage(%)")
    interest_rate = fields.Float(string="Interest Rate", copy=False)
    interest_type = fields.Selection([('simple','Simple Interest'),('compound','Compound Interest')],default='simple')
    start_date = fields.Integer('Start Date(Days)')
    inst_due_date = fields.Integer('Installment Due Date(Days)')
    installment_time = fields.Integer(string='Time between two installments(In Month)', default=1,
        help="State here the time between 2 installments, in months", required=True)
