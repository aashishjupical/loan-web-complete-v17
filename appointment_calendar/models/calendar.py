# -*- coding: utf-8 -*-
##############################################################################
#
#    Jupical Technologies Pvt. Ltd.
#    Copyright (C) 2018-TODAY Jupical Technologies Pvt. Ltd.(<http://www.jupical.com>).
#    Author: Jupical Technologies Pvt. Ltd.(<http://www.jupical.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    It is forbidden to publish, distribute, sublicense, or sell copies
#    of the Software or modified copies of the Software.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################


import pytz
from datetime import datetime, timedelta

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

TIME_FORMAT = '%Y-%m-%d %H:%M:%S'


@api.model
def _tz_get(self):
    # put POSIX 'Etc/*' entries at the end to avoid confusing users - see bug 1086728
    return [(tz, tz) for tz in sorted(pytz.all_timezones, key=lambda tz: tz if not tz.startswith('Etc/') else '_')]


class AppointmentCalendar(models.Model):
    _name = 'appointment.calendar'
    _description = 'Appointment Calendar'

    def get_tz_offset(self, name):
        return datetime.now(pytz.timezone(name or self.env.user.tz)).strftime('%z')

    name = fields.Char()
    app_cal_partner_id = fields.Many2one(comodel_name="res.partner", string="Team Member", default=lambda self: self.env.user.partner_id)
    tz = fields.Selection(_tz_get, string='Timezone', default=lambda self: self._context.get('tz'),
                          help="The partner's timezone, used to output proper date and time values "
                               "inside printed reports. It is important to set a value for this field. "
                               "You should use the same timezone that is otherwise used to pick and "
                               "render date and time values: your computer's timezone.")
    tz_offset = fields.Char(compute='_compute_tz_offset', string='Timezone offset')
    minutes_slot = fields.Char("Slot in mins.", required=True)
    lunch_start = fields.Float("Lunch Start")
    lunch_end = fields.Float("Lunch End")
    start_date = fields.Date(string='Start Date', required=True, default=fields.Datetime.now)
    start_time = fields.Float("Start Time", required=True)
    end_time = fields.Float("End TIme", required=True)
    duration = fields.Integer('Duration in days', required=True)
    calendar_line_ids = fields.One2many('appointment.calendar.line', 'line_id', 'Calendar Lines', copy=True)
    holiday_ids = fields.One2many('appointment.calendar.holidays', 'jt_calendar_id', 'Holidays')
    alarm_ids = fields.Many2many(
        'calendar.alarm', 'appointment_calendar_alarm_calendar_event_rel',
        string='Reminders', ondelete="restrict")
    weekoff_ids = fields.Many2many("appointment.calendar.weekoff", string="Weekoff Days")

    @api.depends('tz')
    def _compute_tz_offset(self):
        for partner in self:
            partner.tz_offset = datetime.datetime.now(pytz.timezone(partner.tz or 'GMT')).strftime('%z')

    # Gets local time in given format
    def get_current_local_time():
        local = datetime.datetime.now()

    @api.model
    def get_utc_date(self, date=None, timezone=None):
        to_zone = pytz.timezone('UTC')
        from_zone = pytz.timezone(timezone)
        return from_zone.localize(date).astimezone(to_zone)

    @api.model
    def get_tz_date(self, date=None, timezone=None):
        to_zone = pytz.timezone(timezone)
        from_zone = pytz.timezone('UTC')
        return from_zone.localize(date).astimezone(to_zone)

    @api.model
    def generate_calendar(self):
        for appointment in self:
            start_date = datetime(year=appointment.start_date.year, month=appointment.start_date.month, day=appointment.start_date.day)
            start_minutes = float(appointment.start_time) * 60
            end_minutes = float(appointment.end_time) * 60
            min_slot = appointment.minutes_slot
            lunch_start_min = float(appointment.lunch_start) * 60
            lunch_end_min = float(appointment.lunch_end) * 60
            if lunch_start_min and lunch_end_min:
                appointment.get_exception_slots()
            start = start_date + timedelta(minutes=start_minutes)
            stop = start_date + timedelta(minutes=end_minutes)
            for days in range(appointment.duration):
                start = start_date + timedelta(minutes=start_minutes)
                stop = start_date + timedelta(minutes=end_minutes)
                while start < stop:
                    t1 = start
                    t2 = t1 + timedelta(minutes=int(min_slot))
                    utc_date1 = appointment.get_utc_date(t1, appointment.tz)
                    utc_date2 = appointment.get_utc_date(t2, appointment.tz)
                    lines = {
                        'line_id': appointment.id,
                        'duration': appointment.minutes_slot,
                        'start_datetime': fields.Datetime.to_string(utc_date1),
                        'end_datetime': fields.Datetime.to_string(utc_date2),
                        'partner_id': appointment.app_cal_partner_id.id

                    }
                    already_line = self.env['appointment.calendar.line'].sudo().search([('start_datetime', '=', fields.Datetime.to_string(utc_date1)), ('end_datetime', '=', fields.Datetime.to_string(utc_date2)), ('line_id', '=', appointment.id)])
                    if not already_line:
                        if appointment.holiday_ids:
                            create_line = False
                            lst = []
                            for holiday in appointment.holiday_ids:
                                sdrange = [holiday.jt_start_date+timedelta(days=x) for x in range((holiday.jt_end_date-holiday.jt_start_date).days + 1)]
                                lst += sdrange
                            if utc_date1.date() not in lst:
                                if appointment.weekoff_ids:
                                    weekoffdays = appointment.weekoff_ids.mapped('dayofweek')
                                    if not str(utc_date1.date().weekday()) in weekoffdays:
                                        create_line = True
                                else:
                                    create_line = True
                            else:
                                create_line = False
                            if create_line:
                                self.env['appointment.calendar.line'].sudo().create(lines)
                        elif appointment.weekoff_ids:
                            weekoffdays = appointment.weekoff_ids.mapped('dayofweek')
                            if str(utc_date1.date().weekday()) not in weekoffdays:
                                self.env['appointment.calendar.line'].sudo().create(lines)
                        else:
                            self.env['appointment.calendar.line'].sudo().create(lines)
                    start = t2
                if days == 0:
                    start_date = start_date + timedelta(days=days + 1)
                else:
                    start_date = start_date + timedelta(days=1)
                days = days + 1
        return True

    def get_exception_slots(self):
        start_date = datetime.strptime(self.start_date, '%Y-%m-%d')
        min_slot = self.minutes_slot
        lunch_start_min = float(self.lunch_start) * 60
        lunch_end_min = float(self.lunch_end) * 60
        ex_slots = []
        for appointment in self:
            for days in range(self.duration):
                if lunch_start_min and lunch_end_min:
                    ex_start = start_date + timedelta(minutes=lunch_start_min)
                    ex_stop = start_date + timedelta(minutes=lunch_end_min)
                    while ex_start < ex_stop:
                        ex_t1 = ex_start
                        ex_t2 = ex_t1 + timedelta(minutes=int(min_slot))
                        ex_slots.append(ex_t1)
                        ex_slots.append(ex_t2)
                        ex_start = ex_t2
                if days == 0:
                    start_date = start_date + timedelta(days=days + 1)
                else:
                    start_date = start_date + timedelta(days=1)
                days = days + 1
        return ex_slots

    @api.model_create_multi
    def create(self, vals):
        appointment = super(AppointmentCalendar, self).create(vals)
        for app_rec in appointment:
            app_rec.generate_calendar()
        return appointment

    def write(self, values):
        appointment = super(AppointmentCalendar, self).write(values)
        lst = ['minutes_slot', 'start_date', 'start_time', 'end_time', 'duration', 'holiday_ids', 'weekoff_ids']
        if any(key in values for key in lst):
            for rec in self:
                rec.calendar_line_ids.unlink()
                rec.generate_calendar()
        return appointment


class AppointmentCalendarLine(models.Model):
    _name = 'appointment.calendar.line'
    _description = 'Appointment Calendar Line'

    line_id = fields.Many2one('appointment.calendar', 'Lines', ondelete='cascade')
    partner_id = fields.Many2one(comodel_name="res.partner")
    start_datetime = fields.Datetime()
    end_datetime = fields.Datetime()
    duration = fields.Float('Duration in mins')

    @api.constrains('start_datetime', 'end_datetime')
    def _check_closing_date(self):
        for line in self:
            if line.start_datetime and line.end_datetime < line.start_datetime:
                line.duration = 0.0
                raise ValidationError(_('Ending datetime cannot be set before starting datetime.'))
            if line.start_datetime and line.end_datetime < line.start_datetime:
                line.duration = 0.0
                raise ValidationError(_('Ending date cannot be set before starting date.'))

    @api.onchange('start_datetime', 'end_datetime')
    def onchange_start_end_time(self):
        if self.start_datetime and self.end_datetime:
            if self.start_datetime < self.end_datetime:
                self.duration = self._get_duration()
            else:
                self.duration = 0.0
                raise ValidationError(_('Ending date cannot be set before starting date or equal to starting date.'))

    @api.model_create_multi
    def create(self, vals):
        # compute duration, if not given
        if not vals.get('duration'):
            vals['duration'] = self._get_duration(vals['start_datetime'], vals['end_datetime'])
        return super(AppointmentCalendarLine, self).create(vals)

    @api.model
    def _get_duration(self):
        """ Get the duration value between the 2 given dates. """
        start = self.start_datetime
        stop = self.end_datetime
        if start and stop:
            diff = fields.Datetime.from_string(stop) - fields.Datetime.from_string(start)
            if diff:
                duration = (float(diff.days) * 24 + (float(diff.seconds) / 3600)) * 60.0
                return round(duration, 2)
            return 0.0


class AppointmentCalendarHolidays(models.Model):
    _name = 'appointment.calendar.holidays'
    _description = 'Appointment Calendar Holidays'

    name = fields.Char("Reason", required=True)
    jt_start_date = fields.Date("Start Date")
    jt_end_date = fields.Date("End Date")
    jt_calendar_id = fields.Many2one('appointment.calendar', 'Appointment Calendar', ondelete='cascade')


class AppointmentCalendarWeekoff(models.Model):
    _name = 'appointment.calendar.weekoff'
    _description = 'Appointment Calendar Weekoff'

    name = fields.Char(required=True)
    dayofweek = fields.Selection([
        ('0', 'Monday'),
        ('1', 'Tuesday'),
        ('2', 'Wednesday'),
        ('3', 'Thursday'),
        ('4', 'Friday'),
        ('5', 'Saturday'),
        ('6', 'Sunday')
        ], 'Day of Week', required=True, index=True, default='6')


class ResPatner(models.Model):
    _inherit = 'res.partner'

    calendar_id = fields.Many2one('appointment.calendar', string='Booking Calendar')
    is_available = fields.Boolean(string='Is for Appointment')
