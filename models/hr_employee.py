from odoo import models, fields, api, exceptions


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    UserID = fields.Integer()
