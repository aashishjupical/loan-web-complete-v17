from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    emergency_contact_name = fields.Char(string="Emergency Contact Name")
    emergency_contact_no = fields.Char(string="Emergency Contact Number")
    emergency_contact_relationship = fields.Selection([('spouse', 'Spouse'),('father', 'Father'),
                                                        ('mother', 'Mother'),('siblings', 'Siblings'),
                                                        ('others', 'others')], string="Contact Relationship")


    #Employment & Bank Account Info
    company_business_name = fields.Char(string="Company/Business Name")
    select_employee_type = fields.Selection([('self_employed','Self Employed'),('salaried_employed','Salaried Employee')], string="Occupation")
    com_bussiness_contact_no = fields.Char(string="Company/Business Contact")
    position_designation_type = fields.Char(string="Position/Designation")
    registeration_no = fields.Char(string="Business Registration Number")
    bussiness_address_line_1 = fields.Char(string="Address 1")
    bussiness_address_line_2 = fields.Char(string="Address 2")
    company_district = fields.Char(string="District")
    company_postcode = fields.Char(string="Postcode")
    company_country_id = fields.Many2one(string="Country ", comodel_name='res.country')
    company_state_id = fields.Many2one('res.country.state', 'States', domain="[('country_id', '=', country_id)]")
