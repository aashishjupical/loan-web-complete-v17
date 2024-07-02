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


from datetime import datetime, timedelta

from odoo import fields, http, _
from odoo.http import request
from odoo.exceptions import ValidationError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT,format_datetime



class MemberAppointment(http.Controller):

    def schedule_meet(self, partner_id=None, day=None, calendar=None, selectedDate=None, **post):
        today = datetime.now()
        today.strftime("%B")
        month_year = '%s  %s' % (today.strftime("%B"), today.year)
        minutes_slot = calendar.minutes_slot
        days = []
        tomorrow = datetime.today().date() + timedelta(days=1)
        single_day = datetime.strftime(tomorrow, '%d')
        month = datetime.strftime(tomorrow, '%m')
        year = datetime.strftime(tomorrow, '%Y')
        selectedDate = single_day + '-' + month + '-' + year
        slots1, slots2 = self.get_time_slots(calendar.id,selectedDate)       
        values = {
            'days': days,
            'calendar_id': calendar.id,
            'partner_id': partner_id,
            'month_year': month_year,
            'minutes_slot': minutes_slot,
            'slots':slots1,
            'slots_2':slots2,
        }        
        return values

    def get_next_working_dates(self,date_next,calendar_id):        
        holidays = request.env['appointment.calendar.holidays'].sudo().search([('jt_start_date','<=',date_next),('jt_end_date','>=',date_next),('jt_calendar_id','=',calendar_id.id)])
        if holidays:
            date_next = date_next + timedelta(days=1) 
            return self.get_next_working_dates(date_next,calendar_id)

        if calendar_id.weekoff_ids:
            weekoffdays = calendar_id.weekoff_ids.mapped('dayofweek')
            if str(date_next.weekday()) in weekoffdays:
                date_next = date_next + timedelta(days=1) 
                return self.get_next_working_dates(date_next,calendar_id)
        
        return date_next

    def get_time_slots(self, calendar_id, selectedDate):
        str_date = str(selectedDate)
        sel_date = str_date.split("-")
        day = sel_date[0]
        month = sel_date[1]
        year = sel_date[2]
        calendar1 = request.env['appointment.calendar'].sudo().browse(int(calendar_id))
 
        limit_date = datetime.today().date() + timedelta(days=1)
        limit_date = self.get_next_working_dates(limit_date,calendar1)
        current_date  = datetime.today().date()
        calendar_line = request.env['appointment.calendar.line'].sudo().search([('line_id', '=', int(calendar_id)),('start_datetime', '>=', limit_date),('start_datetime', '<=', limit_date)])
        slot_dict1 = {}
        slot_dict2 = {}
        slots = []
        for line in calendar_line:
            week_of_day = line.start_datetime.strftime("%d %B, %Y")
            if line.start_datetime.date() == current_date:
                continue
            start_datetime = fields.Datetime.to_string(line.start_datetime)
            date = calendar1.get_tz_date(datetime.strptime(start_datetime, DEFAULT_SERVER_DATETIME_FORMAT), calendar1.tz)
            time_slot = str(date.time())[0:5]
            hours_time = int(time_slot[:2])
            if hours_time==12:
                slots.append([line.id,time_slot+" PM"])
            elif hours_time>12:
                slots.append([line.id,str(hours_time-12)+time_slot[2:]+" PM"])
            else:           
                slots.append([line.id,time_slot+" AM"])
        slot_dict1.update({'slots': slots,'week_of_day':limit_date.day,'days_name':limit_date.strftime('%A')})
        limit_date = limit_date+timedelta(days=1)
        limit_date = self.get_next_working_dates(limit_date,calendar1)
        calendar_line = request.env['appointment.calendar.line'].sudo().search([('line_id', '=', int(calendar_id)),('start_datetime', '<=', limit_date),('start_datetime', '>=', limit_date)])
        slots = []
        for line in calendar_line:
            week_of_day = line.start_datetime.strftime("%d %B, %Y")
            if line.start_datetime.date() == current_date:
                continue
            start_datetime = fields.Datetime.to_string(line.start_datetime)
            date = calendar1.get_tz_date(datetime.strptime(start_datetime, DEFAULT_SERVER_DATETIME_FORMAT), calendar1.tz)
            time_slot = str(date.time())[0:5]
            hours_time = int(time_slot[:2])
            if hours_time==12:
                slots.append([line.id,time_slot+" PM"])
            elif hours_time>12:
                slots.append([line.id,str(hours_time-12)+time_slot[2:]+" PM"])
            else:           
                slots.append([line.id,time_slot+" AM"])
        slot_dict2.update({'slots': slots,'week_of_day':limit_date.day,'days_name':limit_date.strftime('%A')})
        return slot_dict1,slot_dict2    

