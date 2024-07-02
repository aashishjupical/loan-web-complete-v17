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

from odoo import api,models,_,fields

class ProductProduct(models.Model):

    _inherit = "product.product"

    ins_product_id = fields.Many2one('account.loan',string="loan insurance product")

    def view_customer_invoice_lines(self):
        self.ensure_one()
        action = self.env.ref('jt_loan_management.action_invoice_line_product')
        result = action.read()[0]
        return result

    def view_vandor_bill_lines(self):
        self.ensure_one()
        action = self.env.ref('jt_loan_management.action_vendor_bill_line_product')
        result = action.read()[0]
        return result

class ProductTemplate(models.Model):

    _inherit = "product.template"

    invoice_amount = fields.Float('Invoice Amount', compute='calculate_invoice_bill_amount')
    bill_amount = fields.Float('Bill Amount', compute='calculate_invoice_bill_amount')
    detailed_type = fields.Selection(selection_add=[('property', 'Property')], string='Product Type',ondelete={'property': 'set default'})
    type = fields.Selection(selection_add=[('property', 'Property')])

    def view_customer_invoice_lines(self):
        self.ensure_one()
        action = self.env.ref('jt_loan_management.action_invoice_line_product_tem')
        result = action.read()[0]
        return result

    def view_vandor_bill_lines(self):
        self.ensure_one()
        action = self.env.ref('jt_loan_management.action_vendor_bill_line_product_tem')
        result = action.read()[0]
        return result

    def calculate_invoice_bill_amount(self):
        """
        Calculate invoice and bill amount.
        :return:
        """
        invoice_line_obj = self.env['account.move.line']
        for product in self:
            invoice_amount = bill_amount = 0
            invoice_lines = invoice_line_obj.search([('product_id.product_tmpl_id', '=', product.id),
                                                     ('move_id.state', '=', 'paid')])
            for line in invoice_lines:
                if line.move_id.move_type == 'out_invoice':
                    invoice_amount += line.price_total
                if line.move_id.move_type == 'in_invoice':
                    bill_amount += line.price_total
            product.invoice_amount = invoice_amount
            product.bill_amount = bill_amount