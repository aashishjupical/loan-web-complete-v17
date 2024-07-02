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
from werkzeug.utils import redirect
from odoo import http, registry
from odoo.http import request


class GoogleAuthCalendar(http.Controller):
    @http.route("/google_account/authentication/calendar", type="http", auth="none")
    def google_account_authentication_calendar(self, **kw):
        
        """This route/function is called by Google when user Accept/Refuse the consent of Google"""
        state = json.loads(kw["state"])
        dbname = state.get("d")
        url_return = state.get("f")
        with registry(dbname).cursor() as cr:
            if kw.get("code"):
                request.env(cr, request.session.uid)["res.users"].set_all_google_tokens(
                    kw["code"]
                )
                return redirect(url_return)
            elif kw.get("error"):
                return redirect("%s%s%s" % (url_return, "?error=", kw["error"]))
            else:
                return redirect("%s%s" % (url_return, "?error=Unknown_error"))
