from odoo import models, fields, api

import requests, json
from requests.auth import HTTPDigestAuth
from base64 import b64encode
from datetime import datetime, timedelta, timezone

from ..util.services import *


class TimekeepingData(models.Model):
    _name = "timekeeping.data"
    _description = "TimeKeeping Data"
    _order = "create_time desc"

    attendance_state = fields.Selection(
        [
            ("0", "_"),
            ("1", "Check In"),
            ("2", "Break Out"),
            ("3", "Break In"),
            ("4", "Check Out"),
        ],
        string="Attendance Events",
    )
    card_name = fields.Char(string="Name")
    create_time = fields.Datetime(string="Time")
    user_id = fields.Integer(string="User ID.")
    mask_status = fields.Selection(
        [("0", "_"), ("1", "No mask"), ("2", "Wear mask")], string="Mask"
    )
    status = fields.Boolean(string="Status")
    method = fields.Selection(
        [("0", "Null"), ("4", "Remote"), ("15", "Face"), ("21", "PWD")], string="Mode"
    )
    image_url = fields.Char(string="Image")
    recognize_number = fields.Integer(string="RecNo")

    # Preprocess Fields Before Loading To Views
    image_data = fields.Image(
        string="Preview", compute="_compute_image_data", max_width=200, max_height=120
    )
    # formatted_time = fields.Char(string='Formatted Time', compute='_compute_formatted_time')

    # Date Fields
    date_from = fields.Date(
        string="From",
        store=False,
        default=lambda self: datetime.now(timezone(timedelta(hours=7)))
        .replace(hour=0, minute=0, second=0, microsecond=0)
        .date(),
    )
    date_to = fields.Date(
        string="To",
        store=False,
        default=lambda self: (
            datetime.now(timezone(timedelta(hours=7))).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            + timedelta(days=1)
        ).date(),
    )

    timekeeping_device_id = fields.Many2one(
        "timekeeping.device", string="Property Type"
    )

    @api.depends("image_url")
    def _compute_image_data(self):
        # for record in self:
        #     url = (
        #         API_SERVER
        #         + "FileManager.cgi?action=downloadFile&fileName="
        #         + record.image_url
        #     )
        #     response = requests.get(url, auth=HTTPDigestAuth(USERNAME, PASSWORD))

        #     if response.status_code == 200:
        #         self.image_data = b64encode(response.content)

        #     else:
        #         print(f"An error occurred: {response.status_code} {response.reason}")
        pass

    @api.depends("create_time")
    def _compute_formatted_time(self):
        # for record in self:
        #     dt = datetime.fromtimestamp(record.create_time, timezone(timedelta(hours=7)))
        #     record.formatted_time = dt.strftime('%Y-%m-%d %H:%M:%S')
        pass

    def toObject(self, data):
        lines = data.split("\n")
        result = {}
        for line in lines:
            if not line:
                continue
            key, value = line.split("=", 1)
            value = value.strip()
            if value.isdigit():
                value = int(value)
            elif not value:
                value = None
            if "[" in key:
                key, sub_key = key.split(".")
                index = int(key[key.index("[") + 1 : key.index("]")])
                key = key[: key.index("[")]
                if key not in result:
                    result[key] = []
                if len(result[key]) <= index:
                    result[key].append({})
                result[key][index][sub_key] = value
            else:
                result[key] = value
        return result

    def call_api(self, list, startTime, endTime):
        url = (
            API_SERVER
            + "recordFinder.cgi?action=find&name=AccessControlCardRec&StartTime="
            + startTime
            + "&EndTime="
            + endTime
        )
        response = requests.get(url, auth=HTTPDigestAuth(USERNAME, PASSWORD))

        if response.status_code == 200:
            data = self.toObject(response.text)

            if data["found"] != 1:
                list["found"] += data["found"]
                list["records"] += data["records"]
                return self.call_api(
                    list, str(data["records"][-1]["CreateTime"]), endTime
                )

            json_data = json.dumps(list, ensure_ascii=False, indent=4)
            json_data = json.loads(json_data)

            return json_data
        else:
            print(f"An error occurred: {response.status_code} {response.reason}")

    def Load_Data(self):
        field_mapping = {
            "attendance_state": "AttendanceState",
            "card_name": "CardName",
            "create_time": "CreateTime",
            "user_id": "UserID",
            "mask_status": "Mask",
            "status": "Status",
            "method": "Method",
            "image_url": "URL",
            "recognize_number": "RecNo",
        }
        data = self.call_api({"found": 0, "records": []}, "0", str(get_tomorrow_unix()))
        model_data = {}

        for dt in data["records"]:
            for field, key in field_mapping.items():
                if field in ["attendance_state", "method", "mask_status"]:
                    model_data[field] = str(dt[key])
                elif field == "create_time":
                    model_data[field] = datetime.fromtimestamp(dt[key])
                else:
                    model_data[field] = dt[key]

            existing_record = self.search(
                [
                    ("create_time", "=", datetime.fromtimestamp(dt["CreateTime"])),
                    ("recognize_number", "=", dt["RecNo"]),
                ],
                limit=1,
            )

            if existing_record:
                existing_record.write(model_data)
            else:
                self.create(model_data)
