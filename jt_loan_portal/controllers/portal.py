# -*- coding: utf-8 -*-
##############################################################################
#
#    Jupical Technologies Pvt. Ltd.
#    Copyright (C) 2018-TODAY Jupical Technologies(<http://www.jupical.com>).
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
from odoo import fields, http, _
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.http import request
from datetime import date
import datetime
from odoo.exceptions import AccessError, MissingError

class LoanPortal(CustomerPortal):


    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        partner = request.env.user.partner_id

        loan_obj = request.env['account.loan']
        if 'loan_count' in counters:
            values['loan_count'] = loan_obj.search_count([('partner_id','=',partner.id)]) \
                if loan_obj.check_access_rights('read', raise_exception=False) else 0
       
        return values


    @http.route(['/my/my_loan'], type='http', auth="user", website=True)
    def portal_my_loan_list(self, page=0, student_data = None,date_begin=None, date_end=None, sortby=None, **kw):

        values = {}
        loan_list=[]
        loan_links =[]
        loan_result ={}

        partner = request.env.user.partner_id
        loan_list_obj = request.env['account.loan']
        loan_list = loan_list_obj.sudo().search([('partner_id','=',partner.id)])

        #loop for Creating URL With ID. 
        for loan in loan_list:
            loan_detail_url = '/my/my_loan_detail/'+str(loan.id)
            loan_links.append(loan_detail_url) 
        
        #loop for combining two list in one dictionary and then send that combined dictionary to template where list is being displayed.    
        for link_info,loan_info in zip(loan_links,loan_list):
            loan_result.update({link_info:loan_info})
        

        values.update({
            'loan_list':loan_result,
        })
        return request.render("jt_loan_portal.portal_loan_list", values)

    @http.route(['/my/my_loan_detail/<model("account.loan"):loan>'], type='http', auth="user", website=True)
    def portal_my_specific_loan(self,loan, page=1, date_begin=None, date_end=None, sortby=None, **kw):
        values = {}
        line_links =[]
        line_result  = {}
        line_detail_url = ""
        loan_obj = request.env['account.loan']
        loan_detail = loan_obj.sudo().search([('id', '=', loan.id)])
        for line in loan_detail.line_ids:
            if line.date.month <=  date.today().month and int(line.date.strftime("%Y")) == datetime.datetime.today().year:
                line_invoice = request.env['account.move'].search([('loan_line_id','=',line.id)])
                if line_invoice:
                    line_detail_url = '/my/invoices/'+str(line_invoice.id)
                line_links.append(line_detail_url)
        for link_info,loan_line_info in zip(line_links,loan_detail.line_ids):
            line_result.update({link_info:loan_line_info})
        values.update({
            'loan_detail': loan_detail,
            'line_ids':line_result
        })
        return request.render("jt_loan_portal.portal_my_loan_details", values)