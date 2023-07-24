from odoo import models, fields, api


class TimekeepingDeviceEmployee(models.Model):
    _name = "timekeeping.device.employee"
    _description = "Time Keeping Device Employee Model"
    _sort = "user_id"

    user_id = fields.Integer(string="User IDs.")
    name = fields.Char(string="Employee Name")
    image_url = fields.Char()
    valid_date_start = fields.Datetime()
    valid_date_end = fields.Datetime()
