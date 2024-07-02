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

import requests
import logging
import random
import string
import pytz
from datetime import datetime, timedelta
from requests.exceptions import HTTPError
from odoo import api, models, fields, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

GOOGLE_AUTH_ENDPOINT = "https://accounts.google.com/o/oauth2/auth"
GOOGLE_TOKEN_ENDPOINT = "https://accounts.google.com/o/oauth2/token"

_get_random_number = (
    lambda rid: f'{"".join(random.choice(string.ascii_letters + string.digits) for _ in range(10))}-{rid}'
)

class CalendarAttendee(models.Model):
    _inherit = "calendar.attendee"

    def send_mail_to_customer(self):
        template = self.env.ref('calendar.calendar_template_meeting_invitation')
        if template:
            template.sudo().send_mail(self.id,force_send=True)

    def send_mail_to_user(self):
        template_2 = self.env.ref('jt_loan_project.custom_meet_mail_template')
        if template_2:
            template_2.sudo().send_mail(self.id,force_send=True)


class CalendarEventNew(models.Model):
    _inherit = "calendar.event"

    genrate_google_meet_link = fields.Boolean(default=False)
    generate_link = fields.Char(
        string="Generate Meet Link",
        help="Copy think and send it to people you want to meet with",
        copy=False,
    )
    task_id = fields.Many2one('project.task',string="Task")
    
    calender_id_hpl = fields.Char(string="calendarID", copy=False)
    event_id_hpl = fields.Char(string="eventID", copy=False)
    description = fields.Text("Description", copy=False)

    @api.model_create_multi
    def create(self, vals):
        meetings = super(
            CalendarEventNew, self.with_context(no_mail_to_attendees=True)
        ).create(vals)
        for meeting in meetings:
            if meeting.genrate_google_meet_link:
                meeting.get_meet_link()
            if meeting.user_id:
                to_notify= meeting.user_id.partner_id.email

                for attendee in meeting.attendee_ids:
                    if to_notify != attendee.email:
                        attendee.send_mail_to_customer()

                    if to_notify == attendee.email:
                        attendee.send_mail_to_user()
        return meetings

    def unlink(self):
        for rec in self:
            if (
                rec.genrate_google_meet_link
                and rec.event_id_hpl
                and rec.calender_id_hpl
            ):
                rec.unlink_event()
        return super(CalendarEventNew, self).unlink()

    def write(self, values):
        res = super(CalendarEventNew, self).write(values)
        if values.get("genrate_google_meet_link"):
            self.get_meet_link()
        elif (
            "attendee_ids" in values or "start" in values or "duration" in values
        ) and self.videocall_location:
            self.update_event()
        return res

    def join_meeting(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_url",
            "url": self.videocall_location,
            "target": "new",
        }

    def request_calendar(self, url, method="POST", payload=None, params=None):
        self.ensure_one()
        headers = {
            "Authorization": "Bearer %s" % self.env.user._get_token(),
            "Content-Type": "application/json",
        }
        try:
            response = requests.request(
                method, url, json=payload, headers=headers, params=params
            )
            try:
                response.raise_for_status()
                _logger.info("Validate Notification %s" % response.text)
            except HTTPError:
                _logger.error(response)
        except requests.exceptions.RequestException:
            _logger.exception("Unable to connect with calendar: %s", url)
            raise ValidationError(
                "Calendar: " + _("Could not the connection to the API.")
            )
        if int(response.status_code) == 204:  # No Content
            return True
        return response.json()

    def event_create(self):
        emails = []
        for partner_id in self.partner_ids:
            rec = self.env["res.partner"].browse([partner_id.id])
            emails.append({"email": str(rec.email)})
        event_create = self
        if "error" in event_create:
            raise ValidationError(
                _(
                    "Request had invalid authentication credentials. Expected OAuth 2 access token, login cookie or other valid authentication credential"
                )
            )
        event_params = {
            "sendNotifications": True
            if self.env.user.google_notify_checkbox
            else False,
            "sendUpdates": "all",
        }
        create_event_vals = {
            "summary": self.name,
            "sendUpdates": "all",
            "calendarId": "primary",
            "start": {
                "dateTime": self.start.strftime("%Y-%m-%dT%H:%M:%S"),
                "timeZone": "UTC",
            },
            "end": {
                "dateTime": self.stop.strftime("%Y-%m-%dT%H:%M:%S"),
                "timeZone": "UTC",
            },
            "attendees": emails,
        }
        event_id = self.request_calendar(
            f"https://www.googleapis.com/calendar/v3/calendars/primary/events",
            payload=create_event_vals,
            params=event_params,
        
        )
        
        if "error" in event_id:
            err_message = event_id.get('error',{}).get('message','')
            if err_message:
                raise ValidationError(
                    _(
                        err_message
                    )
                )
            else:            
                raise ValidationError(
                    _(
                        "Something went to wrong! Request had invalid please check the event date which you entered!"
                    )
                )

        vals = {
            "event_id": event_id.get("id"),
        }
        self.write({"event_id_hpl": event_id.get("id"), "calender_id_hpl": "primary"})
        return vals

    def get_meet_link(self):
        emails = []
        for partner_id in self.partner_ids:
            rec = self.env["res.partner"].browse([partner_id.id])
            emails.append({"email": str(rec.email)})
        vals = self.event_create()
        event_calendar_id = vals.get("event_id")
        meetlink_params = {
            "conferenceDataVersion": 1,
            "alwaysIncludeEmail": True,
            "sendUpdates": "externalOnly",
            "sendNotifications": True
            if self.env.user.google_notify_checkbox
            else False,
        }
        meetlink_vals = {
            "summary": self.name,
            "calendarId": "primary",
            "conferenceData": {
                "createRequest": {
                    "conferenceSolutionKey": {"type": "hangoutsMeet"},
                    "requestId": _get_random_number(self.id),
                    "attendees": emails,
                }
            },
        }
        meetlink_id = self.request_calendar(
            f"https://www.googleapis.com/calendar/v3/calendars/primary/events/{event_calendar_id}",
            method="patch",
            payload=meetlink_vals,
            params=meetlink_params,
        )
        if "error" in meetlink_id:
            raise ValidationError(
                _(
                    "Try again!Evenet ID not found, Request had invalid please check credentials! "
                )
            )
        # Handle error
        hangout_link = meetlink_id.get("hangoutLink")
        self.videocall_location = hangout_link
        if self.description:
            self.description += hangout_link
        self.description = hangout_link
        return {
            "event_calendar_id": event_calendar_id,
            "self.videocall_location": hangout_link,
        }

    def update_event(self):
        emails = []
        for partner_id in self.partner_ids:
            rec = self.env["res.partner"].browse([partner_id.id])
            emails.append({"email": str(rec.email)})
        update_event_params = {
            "conferenceDataVersion": 1,
            "alwaysIncludeEmail": True,
            "sendUpdates": "all",
            "sendNotifications": True
            if self.env.user.google_notify_checkbox
            else False,
        }
        update_event_vals = {
            "summary": self.name,
            "calendarId": "primary",
            "start": {
                "dateTime": self.start.strftime("%Y-%m-%dT%H:%M:%S"),
                "timeZone": "UTC",
            },
            "end": {
                "dateTime": self.stop.strftime("%Y-%m-%dT%H:%M:%S"),
                "timeZone": "UTC",
            },
            "attendees": emails,
        }
        update_cal_event = self.request_calendar(
            f"https://www.googleapis.com/calendar/v3/calendars/primary/events/{self.event_id_hpl}",
            method="PUT",
            payload=update_event_vals,
            params=update_event_params,
        )
        return update_cal_event

    def unlink_event(self):
        return self.request_calendar(
            f"https://www.googleapis.com/calendar/v3/calendars/primary/events/{self.event_id_hpl}",
            method="delete",
        )

    def do_refresh_token(self):
        current_user = self.env.user
        all_token = self.env["google.service"]._refresh_google_token_json(
            current_user.google_calendar_rtoken, self.STR_SERVICE
        )
        vals = {}
        vals[
            "google_%s_token_validity" % self.STR_SERVICE
        ] = datetime.now() + timedelta(seconds=all_token.get("expires_in"))
        vals["google_%s_token" % self.STR_SERVICE] = all_token.get("access_token")

    def need_authorize(self):
        current_user = self.env.user
        return current_user.google_calendar_rtoken is False

    def authorize_google_uri(self, from_url="http://www.odoo.com"):
        url = self.env["google.service"]._get_authorize_uri(
            from_url, "calendar", scope="https://www.googleapis.com/auth/calendar"
        )
        return url
