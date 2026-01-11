# Copyright (c) 2026, PANDITOFCODES
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class Customer(Document):
    
    def before_save(self):
        if not self.company:
            company = frappe.get_single("Company")

            if company:
                self.company = company.company_name or "Company"

                if hasattr(self, "company_address") and company.address:
                    self.company_address = company.address

    def validate(self):
        self.set_full_address()

    def set_full_address(self):
        parts = []

        if self.address_line_1:
            parts.append(self.address_line_1)

        if self.address_line_2:
            parts.append(self.address_line_2)

        city_line = []

        if self.city:
            city_line.append(self.city)

        if self.state:
            city_line.append(self.state)

        if self.pincode:
            city_line.append(self.pincode)

        if city_line:
            parts.append(", ".join(city_line))

        # Join using newline for Small Text field
        self.address = "\n".join(parts) if parts else ""
