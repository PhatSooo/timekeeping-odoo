from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
import requests, json
from requests.auth import HTTPDigestAuth
import ipaddress


from ..util.services import *

API_GET_USER_IN_DEVICE = "recordFinder.cgi?action=find&name=AccessControlCard"
API_GET_DEVICE_INFO = "cgi-bin/magicBox.cgi?action="


class TimekeepingDevice(models.Model):
    _name = "timekeeping.device"
    _description = "Timekeeping Device Model"
    _sql_constraints = [
        (
            "check_unique_host",
            "UNIQUE(host)",
            "Host Name must be unique",
        ),
    ]

    host = fields.Char(string="IP Address", required=True)
    username = fields.Char(string="Username", required=True)
    password = fields.Char(string="Password", required=True)
    machinename = fields.Char(string="Machine Name")
    softwareversion = fields.Char(string="Software Version")
    hardwareversion = fields.Char(string="Hardware Version")
    machineseri = fields.Char(string="Machine Seri No.")
    state = fields.Boolean(default=False)

    # Relation fields
    employee_ids = fields.Many2many(
        "timekeeping.device.employee", string="Employee In Device"
    )
    employees_mapped = fields.Many2many("hr.employee", string="Employees")
    user_id = fields.Many2one("res.users", string="User")

    def Check_Connection(self):
        data = {
            "getMachineName": "machinename",
            "getSoftwareVersion": "softwareversion",
            "getHardwareVersion": "hardwareversion",
            "getSerialNo": "machineseri",
        }
        for endpoint, attribute in data.items():
            try:
                ipaddress.ip_address(self.host)
            except ValueError:
                raise ValidationError(f"{self.host} is not a valid IP address")

            for endpoint, attribute in data.items():
                url = f"http://{self.host}/{API_GET_DEVICE_INFO}{endpoint}"
                try:
                    response = requests.get(
                        url,
                        auth=HTTPDigestAuth(self.username, self.password),
                        timeout=5,
                    )
                    if response.status_code == 200:
                        setattr(self, attribute, response.text.split("=")[1])
                    else:
                        raise UserError(
                            f"API request failed for endpoint {endpoint} with status code {response.status_code}"
                        )
                except requests.Timeout:
                    raise UserError(f"API request timed out for endpoint {endpoint}")

        self.state = True

    def Load_User_In_Device(self):
        field_mapping = {
            "user_id": "UserID",
            "name": "CardName",
            "valid_date_start": "ValidDateStart",
            "valid_date_end": "ValidDateEnd",
        }

        url = f"http://{self.host}/cgi-bin/{API_GET_USER_IN_DEVICE}"
        try:
            response = requests.get(
                url,
                auth=HTTPDigestAuth(self.username, self.password),
                timeout=5,
            )
            if response.status_code == 200:
                data = toObject(self, response.text)
                model_data = {}

                for dt in data["records"]:
                    for field, key in field_mapping.items():
                        model_data[field] = dt[key]
                    existing_record = self.employee_ids.search(
                        [
                            (
                                "user_id",
                                "=",
                                dt["UserID"],
                            ),
                            ("name", "=", dt["CardName"]),
                        ],
                        limit=1,
                    )
                    if existing_record:
                        existing_record.write(model_data)
                    else:
                        self.employee_ids |= self.employee_ids.new(model_data)

        except requests.Timeout:
            raise UserError(f"API request timed out for endpoint")

    def Mapping(self):
        pass
