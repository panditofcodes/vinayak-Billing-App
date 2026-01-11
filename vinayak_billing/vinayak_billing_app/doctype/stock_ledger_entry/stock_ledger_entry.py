# Copyright (c) 2026, PANDITOFCODES
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class StockLedgerEntry(Document):
    
    def before_save(self):
        if not self.company:
            company = frappe.get_single("Company")

            if company:
                self.company = company.company_name or "Company"

                if hasattr(self, "company_address") and company.address:
                    self.company_address = company.address

    def before_update(self):
        frappe.throw("Stock Ledger Entry cannot be modified")

    def on_trash(self):
        frappe.throw("Stock Ledger Entry cannot be deleted")

    def before_cancel(self):
        frappe.throw("Stock Ledger Entry cannot be cancelled")
