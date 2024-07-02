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

{
    'name': 'Appointment Calendar',
    'version': '16.0.0.0',
    'summary': 'Calendar appointment booking with a strong backend and a very intuitive web UI | appointment | website booking | booking calendar | Slot Booking | Online Booking | Online Meeting | Schedule Meeting',
    'description': """
Appointment Calendar
    """,
    'category': 'Website/Website',
    'depends': ['website', 'mail', 'calendar', 'contacts', 'sale', 'stock', 'website_payment'],
    'data': [
        'data/appointment_data.xml',
        'data/appointment_email.xml',
        'security/ir.model.access.csv',
        'views/appointment_calendar_view.xml',
        'views/res_partner_view.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'appointment_calendar/static/src/css/appointment.css',
            # 'appointment_calendar/static/src/js/appointment.js', # this not use so this file hide.
            'appointment_calendar/static/lib/datetime/css/datepicker.css',
            'appointment_calendar/static/lib/datetime/js/bootstrap-datepicker.js',
        ],
    },
    'license':'OPL-1',
    'installable': True,
    'application': True,
    'auto_install': False,
    'price': 110,
    'currency': 'EUR',
}
