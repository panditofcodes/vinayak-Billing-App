# Copyright (c) 2026, PANDITOFCODES
# For license information, please see license.txt

from frappe.model.document import Document


class Company(Document):

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

        # Store as plain text (Small Text field)
        self.address = "\n".join(parts) if parts else ""
