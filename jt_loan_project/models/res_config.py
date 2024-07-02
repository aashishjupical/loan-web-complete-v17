from odoo import api, fields, models, modules


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    expire_attestation_time = fields.Float(string="Expiry to Review and Agree Attestation")
    expire_inperson_att_time = fields.Float(string="Expiry To In-person Attestation")
    sign_attestation_time = fields.Float(string="Expiry To Sign Agreement")
    product_disclosure = fields.Binary(string="Product Disclosure")

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        res.update(
            expire_attestation_time=self.env['ir.config_parameter'].sudo(
            ).get_param('jt_loan_project.expire_attestation_time'),
            expire_inperson_att_time=self.env['ir.config_parameter'].sudo(
            ).get_param('jt_loan_project.expire_inperson_att_time'),
            sign_attestation_time=self.env['ir.config_parameter'].sudo(
            ).get_param('jt_loan_project.sign_attestation_time'),
            product_disclosure=self.env['ir.config_parameter'].sudo(
            ).get_param('jt_loan_project.product_disclosure'),
        )
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        param = self.env['ir.config_parameter'].sudo()

        field1 = self.expire_attestation_time or False
        field2 = self.sign_attestation_time or False
        field3 = self.expire_inperson_att_time or False
        field4 = self.product_disclosure or False

        param.set_param('jt_loan_project.expire_attestation_time', field1)
        param.set_param('jt_loan_project.sign_attestation_time', field2)
        param.set_param('jt_loan_project.expire_inperson_att_time', field3)
        param.set_param('jt_loan_project.product_disclosure', field4)
