from __future__ import unicode_literals
from frappe import _
def get_data():
    config = [
        {
            "label": _("Barcode Scanner"),
            "items": [
                {
                    "type": "doctype",
                    "name": "Barcode",
                    "onboard": 1,
                }
            ]
        }
    ]
    return config