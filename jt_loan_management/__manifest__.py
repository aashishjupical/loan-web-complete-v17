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
##############################################################################


{
    "name": "The Complete Loan Management System",
    "version": "17.0.1.4.0",
    'summary': 'The Complete Loan management Solutions',
    'author': 'Jupical Technologies Pvt. Ltd.',
    'maintainer': 'Jupical Technologies Pvt. Ltd.',
    'website': 'http://www.jupical.io',
    "category": "Account",
    'live_test_url': 'https://www.youtube.com/watch?v=HlAKrfZKGIM&list=PL0UBHqQKV6S6Gzqk42_kaa8ly47Gyhfu_',
    "depends": ['account_accountant', 'sale','hr'],
    "data": [
        'security/account_loan_security.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'data/cron.xml',
        'data/ir_rule.xml',
        'views/action_loan_line_view.xml',
        'views/account_move_view.xml',
        'wizard/account_loan_pay_amount_view.xml',
        'wizard/loan_update_rate_view.xml',
        'report/loan_detail_report.xml',
        'views/account_loan_view.xml',
        'views/res_partner.xml',
        'views/account_invoice_view.xml',
        'views/loan_crons.xml',
        'views/loan_settings_view.xml',
        'wizard/move_due_date_of_loan.xml',
        'report/loan_details_report_template.xml',
        'report/loan_detail_email_template.xml',
        'report/loan_invoice_report_tmpl.xml',
        'report/account_loan_summary_view.xml',
        'report/account_invoice_report.xml',
        'views/product_view.xml',
        'views/company_view.xml',
        'views/loan_consultant_view.xml',
        'views/employee_view.xml',
    ],
    'demo': [
        'data/demo_data.xml'
    ],
    'license': 'OPL-1',
    "application": True,
    'installable': True,
    'external_dependencies': {
        'python': [
            'numpy', 'dateutil','numpy_financial'
        ],
    },
    
   
}
