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
import json
from werkzeug import urls
from datetime import datetime, timedelta
from odoo import models, api, _, fields
from odoo.exceptions import UserError
GOOGLE_AUTH_ENDPOINT = "https://accounts.google.com/o/oauth2/auth"


class User(models.Model):
    _inherit = "res.users"

    client_id = fields.Char(string="Client ID", store=True)  # Our identifier
    client_secret = fields.Char("Client Secret", store=True)
    google_notify_checkbox = fields.Boolean("Send Notifications to Google account")
    calendar_refresh_token = fields.Char("Refresh Token", copy=False)
    calendar_token = fields.Char("User token", copy=False)
    calendar_token_validity = fields.Datetime(
        "Token Validity", copy=False, readonly=True
    )
    is_generate_meet = fields.Boolean(string="Generate Meet")

    def action_redirect_setup_token(self, **kw):
        context = kw.get("local_context", {})
        client_id = self.client_id
        if not client_id:
            raise UserError(
                _(
                    "Something is messing please add your client_id and client_secret from your project"
                )
            )
        if self.need_authorize():
            # Make dynamic url
            url = self.with_context(context).authorize_google_uri(
                from_url=self.env["ir.config_parameter"]
                .sudo()
                .get_param("web.base.url")
            )
            return {
                "type": "ir.actions.act_url",
                "target": "new",
                "url": url,
            }

    def _get_token(self):
        self.ensure_one()
        if not self.calendar_token_validity or self.calendar_token_validity < (
            datetime.now() + timedelta(minutes=1)
        ):
            self._do_refresh_token()
            self.refresh()
        return self.calendar_token

    def _do_refresh_token(self):
        all_token = self.env["google.service"]._refresh_google_calendar_token_json(
            self.calendar_refresh_token, "calendar", self.company_id
        )
        self.sudo().write(
            {
                "calendar_token_validity": datetime.now()
                + timedelta(seconds=all_token.get("expires_in")),
                "calendar_token": all_token.get("access_token"),
            }
        )

    def need_authorize(self):
        return True

    def authorize_google_uri(self, from_url="http://www.odoo.com"):
        url = self._get_authorize_uri(
            from_url, "calendar", scope="https://www.googleapis.com/auth/calendar"
        )
        return url

    @api.model
    def _get_authorize_uri(self, from_url, service, scope=False):
        """This method return the url needed to allow this instance of Odoo to access to the scope
        of gmail specified as parameters
        """
        state = {"d": self.env.cr.dbname, "s": service, "f": from_url}
        get_param = self.env["ir.config_parameter"].sudo().get_param
        base_url = get_param("web.base.url", default="http://www.odoo.com?NoBaseUrl")
        client_id =self.client_id
        encoded_params = urls.url_encode(
            {
                "response_type": "code",
                "client_id": client_id,
                "state": json.dumps(state),
                "scope": scope
                or "%s/auth/%s" % ("https://www.googleapis.com", service),
                "redirect_uri": base_url + "/google_account/authentication/calendar",
                "approval_prompt": "force",
                "access_type": "offline",
            }
        )
        return "%s?%s" % (GOOGLE_AUTH_ENDPOINT, encoded_params)

    def set_all_google_tokens(self, authorization_code):
        all_token = self.env["google.service"]._get_google_calender_token_json(
            authorization_code, "calendar", self.env.user.company_id
        )
        self.env.user.sudo().write(
            {
                "calendar_refresh_token": all_token.get("refresh_token"),
                "calendar_token": all_token.get("access_token"),
                "calendar_token_validity": datetime.now()
                + timedelta(seconds=all_token.get("expires_in")),
            }
        )
