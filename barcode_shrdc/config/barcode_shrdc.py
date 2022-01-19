from __future__ import unicode_literals
from frappe import _
def get_data():
    config = [
        {
            "label": _("Barcode Printing"),
            "items": [
                {
                    "type": "doctype",
                    "name": "Barcode Printing",
                    "onboard": 1,
                }
            ]
        },
            {
            "label": _("Barcode Settings"),
            "items": [
                {
                    "type": "doctype",
                    "name": "Barcode Configuration",
                    "onboard": 1,
                },
                {
                    "type": "doctype",
                    "name": "QR Code Configuration",
                    "onboard": 1,
                }
            ]
        }
    ]
    return config