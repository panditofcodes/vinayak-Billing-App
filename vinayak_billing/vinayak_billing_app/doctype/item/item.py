# Copyright (c) 2026, PANDITOFCODES and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class Item(Document):
    
    def before_save(self):
        if not self.company:
            company = frappe.get_single("Company")

            if company:
                self.company = company.company_name or "Company"

                if hasattr(self, "company_address") and company.address:
                    self.company_address = company.address
    
    def validate(self):
        old_qty = self.get_db_value("quantity")
        if old_qty is not None and old_qty != self.quantity:
            frappe.throw("Item quantity cannot be edited manually")
