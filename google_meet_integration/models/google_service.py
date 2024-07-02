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
from odoo import models, api, _, registry
from odoo.http import request
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

GOOGLE_TOKEN_ENDPOINT = "https://accounts.google.com/o/oauth2/token"


class GoogleService(models.AbstractModel):
    _inherit = "google.service"

    @api.model
    def _get_google_calender_token_json(self, authorize_code, service, company_id):
        """Call Google API to exchange authorization code against token, with POST request, to
        not be redirected.
        """
        get_param = self.env["ir.config_parameter"].sudo().get_param
        base_url = get_param("web.base.url", default="http://www.odoo.com?NoBaseUrl")
        client_id = self.env.user.client_id
        client_secret = self.env.user.client_secret

        headers = {"content-type": "application/x-www-form-urlencoded"}
        data = {
            "code": authorize_code,
            "client_id": client_id,
            "client_secret": client_secret,
            "grant_type": "authorization_code",
            "redirect_uri": base_url + "/google_account/authentication/calendar",
        }
        try:
            dummy, response, dummy = self._do_request(
                GOOGLE_TOKEN_ENDPOINT,
                params=data,
                headers=headers,
                method="POST",
                preuri="",
            )
            return response
        except requests.HTTPError:
            error_msg = _(
                "Something went wrong during your token generation. Maybe your Authorization Code is invalid"
            )
            raise self.env["res.config.settings"].get_config_warning(error_msg)

    @api.model
    def _refresh_google_calendar_token_json(self, refresh_token, service, company_id):
        client_id = self.env.user.client_id
        client_secret = self.env.user.client_secret
        if not client_id or not client_secret:
            raise UserError(
                _("The account for the Google service '%s' is not configured.")
                % service
            )

        headers = {"content-type": "application/x-www-form-urlencoded"}
        data = {
            "refresh_token": refresh_token,
            "client_id": client_id,
            "client_secret": client_secret,
            "grant_type": "refresh_token",
        }

        try:
            dummy, response, dummy = self._do_request(
                GOOGLE_TOKEN_ENDPOINT,
                params=data,
                headers=headers,
                method="POST",
                preuri="",
            )
            return response
        except requests.HTTPError as error:
            if error.response.status_code == 400:  # invalid grant
                with registry(request.session.db).cursor() as cur:
                    self.env(cur)["res.users"].browse(self.env.uid).sudo().write(
                        {"calendar_refresh_token": False}
                    )
            error_key = error.response.json().get("error", "nc")
            _logger.exception("Bad google request : %s !", error_key)
            error_msg = (
                _(
                    "Something went wrong during your token generation. Maybe your Authorization Code is invalid or already expired [%s]"
                )
                % error_key
            )
            raise self.env["res.config.settings"].get_config_warning(error_msg)
