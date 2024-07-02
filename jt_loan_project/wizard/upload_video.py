from odoo import api, fields, models, _
import socket

class UploadWizard(models.TransientModel):
    _name = 'upload.wizard'
    _description = 'Upload video'

    attestation_video_file = fields.Char(string="Attestation Video File Name")
    attestation_video = fields.Binary("Attestation Video")
    task_id = fields.Many2one("project.task",default= lambda self:self.env.context.get('active_id'))


    def uploaded(self):
        task = self.task_id
        if self.attestation_video:
            task.write({
            'attestation_method':'in_person',
            'attestation_video_file':self.attestation_video_file,
            'attestation_video':self.attestation_video,
            })