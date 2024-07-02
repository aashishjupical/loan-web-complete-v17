import logging
from odoo import http, _
from odoo.http import request,route
from odoo.exceptions import UserError
from odoo.addons.web.controllers.main import ensure_db, Home
from odoo.addons.auth_signup.controllers.main import AuthSignupHome
#from odoo.addons.web.controllers.main import SIGN_UP_REQUEST_PARAMS
from odoo.addons.appointment_calendar.controllers.main import MemberAppointment 
from email_validator import EmailSyntaxError, EmailUndeliverableError, validate_email
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.addons.auth_signup.models.res_users import SignupError
import base64
import socket
from datetime import datetime
import re
from datetime import datetime, timedelta
from odoo import fields, http, _
import pytz
from pytz import timezone
from odoo.tools import format_datetime

_logger = logging.getLogger(__name__)

class LoanDoAttestationController(MemberAppointment):

    @http.route(['/start_attestation'], type='http', auth="user", website=True, csrf=False)
    def start_attestation(self, **post):
        part_id = request.env.user.partner_id
        app_hs = request.env['loan.application.history'].sudo().search([('partner_id','=',part_id.id)], order='id desc',limit=1)        
        if request.httprequest.method == 'POST':
            if app_hs:
                app_hs.stages = 'attestation_step_next'
            return request.redirect('/video_attestation')
        return request.render("jt_loan_project.start_attestation")

    @http.route(['/video_attestation'], type='http', auth="user", website=True, csrf=False)
    def video_attestation(self, **post):
        part_id = request.env.user.partner_id
        app_hs = request.env['loan.application.history'].sudo().search([('partner_id','=',part_id.id)], order='id desc',limit=1)
        if request.httprequest.method == 'POST':
            if app_hs:
                att_time = datetime.now(pytz.timezone('UTC'))
                att_date_str = att_time.strftime("%Y-%m-%d %H:%M:%S")
                att_str_date = datetime.strptime(att_date_str,"%Y-%m-%d %H:%M:%S")
                app_hs.task_id.accept_attestation_ip = app_hs.task_id.current_ip
                app_hs.task_id.accept_attestation_date = att_str_date
                app_hs.task_id.attestation_method = 'self_recorded'
                app_hs.task_id.video_attestation_expiry_date = False
                app_hs.task_id.video_inperson_expiry_date = False
                app_hs.task_id.attestation_date = False
                app_hs.stages = 'watch_att_video'
                acceptance_date = app_hs.task_id.accept_attestation_date
                acceptance_ip = app_hs.task_id.accept_attestation_ip
                if request.env.user and request.env.user.tz:
                    to_zone = pytz.timezone(request.env.user.tz)
                    from_zone = pytz.timezone('UTC')
                    acceptance_date = from_zone.localize(acceptance_date).astimezone(to_zone)
                acceptance_date = acceptance_date.strftime("%d/%m/%Y %H:%M:%S")

                body = _(
                    "\n <b>Self Recorded Acceptance</b> <br/>\n <b>Acceptance Date:</b> %s <br/>\n <b>Acceptance IP:</b> %s <br/>\n ") % (
                           acceptance_date,acceptance_ip)
                app_hs.task_id.message_post(body=body)
                app_hs.task_id.video_attestation_expiry_date_set()
                app_hs.task_id.approved_attestation()
            return request.redirect('/review_agree_attestation')
        return request.render("jt_loan_project.video_attestation")

    @http.route(['/review_agree_attestation'], type='http', auth="user", website=True, csrf=False)
    def review_agree_attestation(self, **post):
        part_id = request.env.user.partner_id
        app_hs = request.env['loan.application.history'].sudo().search([('partner_id','=',part_id.id)], order='id desc',limit=1)
        if request.httprequest.method == 'POST':
            if app_hs and app_hs.task_id:
                app_hs.stages = 'attestation_completed'
                app_hs.task_id.approved_attestation()
                return request.redirect('/attestation_success')
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

        return request.render("jt_loan_project.review_agree_attestation",vals)

    @http.route(['/attestation_success'], type='http', auth="user", website=True, csrf=False)
    def attestation_success(self, **post):
        if request.httprequest.method == 'POST':
            return request.redirect('/esign_dashboard')
        return request.render("jt_loan_project.attestation_success")

    @http.route(['/inperson-attestation'], type='http', auth="user", website=True, csrf=False)
    def inperson_attestation(self,**post):
        part_id = request.env.user.partner_id
        app_hs = request.env['loan.application.history'].sudo().search([('partner_id','=',part_id.id)], order='id desc',limit=1)
        part_err_msg = False
        vals = {'slots':False,'slots_2':False}
        app_hs.task_id.attestation_method = 'in_person'
        calender = request.env['appointment.calendar'].search([],limit=1)
        if calender:
            vals = self.schedule_meet(partner_id=None, day=None, calendar=calender, selectedDate=None)
        legal_group = request.env.ref('jt_loan_project.cg_group_legal')
        if legal_group and legal_group.sudo().users:
            user_meet = legal_group.sudo().users.filtered_domain([('is_generate_meet', '=', True)])
            if user_meet:
                vals.update({'partner_id': user_meet.partner_id and user_meet.partner_id.id or False})
            else:
                part_err_msg = "Please configure legal person to generate meet access."
        if request.httprequest.method == 'POST':
            if not post.get('partner_id'):
                return request.redirect('/inperson-attestation')
            data_vals = self.confirm_booking_att(**post)
            if app_hs:
                app_hs.stages = 'in_person_attestation'     
                return request.redirect('/in-person-attestation-sch')
            else:
                vals.update(data_vals)
        else:
            app_hs.task_id.video_inperson_expiry_date_set()

        vals.update({'part_err_msg':part_err_msg})
        return request.render("jt_loan_project.In_Person_Attestation_page",vals)

    @http.route(['/in-person-attestation-sch'], type='http', auth="user", website=True, csrf=False)
    def in_person_attestation_sch(self,**post):
        part_id = request.env.user.partner_id
        app_hs = request.env['loan.application.history'].sudo().search([('partner_id','=',part_id.id)], order='id desc',limit=1)
        vals = {}
        if app_hs and app_hs.task_id and app_hs.task_id.cale_event_id:
            start_time = app_hs.task_id.cale_event_id.start
            
            to_zone = pytz.timezone(request.env.user.tz)
            from_zone = pytz.timezone('UTC')
            
            start_time = from_zone.localize(start_time).astimezone(to_zone)
            
            vals.update({'week_days':start_time.strftime('%A'),
                'booking_date':start_time.strftime('%d %B %Y'),
                'booking_time' : start_time.strftime('%I:%M%p')  
                })
        
        if request.httprequest.method == 'POST':
            if app_hs:
                app_hs.stages = 'attestation_completed'
                return request.redirect('/review_agree_attestation')
                
        return request.render("jt_loan_project.in_person_attestation_sch_page",vals)

    def _prepare_vals(self, partner, loan_history, post, calender, calender_line, event_user=False):
        start_date = calender_line.start_datetime
        stop_date = start_date + timedelta(minutes=int(post.get('minutes_slot')))
        return {
                'name': 'Attestation Meeting with %s' % (partner.name),
                'partner_ids': [(6, 0, [partner.id, int(post.get('partner_id'))])],
                'start': fields.Datetime.to_string(start_date),
                'stop': fields.Datetime.to_string(stop_date),
                'alarm_ids': [(6, 0, calender.alarm_ids.ids)],
                'genrate_google_meet_link':True,
                'event_tz' : calender.tz,
                'task_id':loan_history.task_id and loan_history.task_id.id or False,
                'user_id':event_user and event_user.id or False,
            }

    def confirm_booking_att(self, **post):
        team_member = request.env.user.partner_id
        if post.get('calendar_id'):
            calendar = request.env['appointment.calendar'].sudo().browse(int(post.get('calendar_id')))
            calender_line = request.env['appointment.calendar.line'].sudo().browse(int(post.get('slot_data_get')))
            start_date = calender_line.start_datetime #datetime.strptime(post.get('start_datetime'), '%Y-%m-%d %H:%M:%S')
            stop_date = start_date + timedelta(minutes=int(post.get('minutes_slot')))
            post['team_member'] = team_member
            app_hs = request.env['loan.application.history'].sudo().search([('partner_id','=',team_member.id)], order='id desc',limit=1)
            event_user_id = request.env['res.users'].sudo().search([('partner_id','=',int(post.get('partner_id')))],limit=1)
            event_values = self._prepare_vals(team_member, app_hs, post, calendar, calender_line, event_user_id)
            if app_hs and not event_user_id:
                error_msg = "Please configure your token generation"
                event_values = self._prepare_vals(team_member, app_hs, post, calendar, calender_line)
                return event_values
            else:
                try:
                    event = request.env['calendar.event'].sudo().with_context({'no_mail': True}).with_user(event_user_id.id).create(event_values)
                    app_hs.task_id.cale_event_id = event.id
                    app_hs.task_id.meeting_link = app_hs.task_id.cale_event_id.videocall_location
                    app_hs.task_id.attestation_method = 'in_person'
                    att_name = ''
                    if post.get("in_person_attestation_current_ip",False):
                        app_hs.task_id.current_ip = post.get("in_person_attestation_current_ip",False)
                    for attendee in app_hs.task_id.cale_event_id.attendee_ids:
                        att_name = att_name +"<br>" +attendee.partner_id.name
                    start_time = format_datetime(request.env, app_hs.task_id.cale_event_id.start, dt_format=False)
                    stop_time = format_datetime(request.env, app_hs.task_id.cale_event_id.stop, dt_format=False)
                    body = _(
                        "%s has created this meeting, <br/><br/>\n <b>Details of the event:</b> <br/>\n %s <br/>\n <b>Attendees:</b> %s <br/>\n <b>Starting At:</b> %s <br/>\n <b>Ending At:</b> %s <br/>\n <b>Duration:</b> %s") % (
                               app_hs.task_id.partner_id.name, app_hs.task_id.cale_event_id.name, att_name,
                               start_time, stop_time, app_hs.task_id.cale_event_id.duration)
                    app_hs.task_id.message_post(body=body)
                    domain = [('line_id', '=', int(post.get('calendar_id'))), ('start_datetime', '=', fields.Datetime.to_string(start_date)), ('end_datetime', '=', fields.Datetime.to_string(stop_date))]
                    lines = request.env['appointment.calendar.line'].sudo().search(domain)
                    lines.unlink()
                    post['event_id'] = event
                except Exception as error_msg:
                    return {  
                        'error':error_msg,
                        'booking_time': ' %s %s , %s' % ( start_date.strftime('%B'), start_date.day, start_date.year),
                        'start_datetime': fields.Datetime.to_string(start_date),
                        'start': fields.Datetime.to_string(start_date),
                        'stop': fields.Datetime.to_string(stop_date),
                        'duration': round((float(post.get('minutes_slot')) / 60.0), 2),
                        'calendar_id': int(post.get('calendar_id')),
                        'minutes_slot': int(post.get('minutes_slot')),
                        'partner':request.env['res.partner'].sudo().browse(int(post.get('partner_id'))),
                    }
            return post
