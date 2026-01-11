# Copyright (c) 2026, PANDITOFCODES
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from vinayak_billing.vinayak_billing_app.utils.stock import update_item_quantity


class PurchaseInvoice(Document):
    
    def before_save(self):
        if not self.company:
            company = frappe.get_single("Company")

            if company:
                self.company = company.company_name or "Company"

                if hasattr(self, "company_address") and company.address:
                    self.company_address = company.address


    def validate(self):
        self.calculate_totals()
        self.validate_items()
        self.validate_opening_stock()

    # ----------------------------
    # TOTAL CALCULATION
    # ----------------------------
    def calculate_totals(self):
        total_amount = 0

        for row in self.items:
            if row.quantity <= 0:
                frappe.throw("Quantity must be greater than zero")

            # amount is entered by user
            total_amount += row.amount

        self.total_amount = total_amount

    # ----------------------------
    # BASIC VALIDATIONS
    # ----------------------------
    def validate_items(self):
        seen_items = set()

        for row in self.items:
            if row.item in seen_items:
                frappe.throw(f"Item {row.item} is duplicated in Purchase Invoice")
            seen_items.add(row.item)

            if row.amount < 0:
                frappe.throw("Amount cannot be negative")

    # ----------------------------
    # OPENING STOCK RULES
    # ----------------------------
    def validate_opening_stock(self):
        if not self.is_opening_stock:
            return

        for row in self.items:
            # Only one opening stock per item
            exists = frappe.db.exists(
                "Stock Ledger Entry",
                {
                    "item": row.item,
                    "company": self.company,
                    "voucher_type": "Opening Stock",
                },
            )
            if exists:
                frappe.throw(f"Opening stock already entered for item {row.item}")

            # Block opening stock after sales
            sale_exists = frappe.db.exists(
                "Stock Ledger Entry",
                {
                    "item": row.item,
                    "company": self.company,
                    "voucher_type": "Sales Invoice",
                },
            )
            if sale_exists:
                frappe.throw(
                    f"Cannot add opening stock for item {row.item} after sales"
                )

    # ----------------------------
    # STOCK IN
    # ----------------------------
    def on_submit(self):
        
        for row in self.items:
            rate = row.amount / row.quantity if row.quantity else 0

            frappe.get_doc(
                {
                    "doctype": "Stock Ledger Entry",
                    "posting_time": frappe.utils.now(),
                    "item": row.item,
                    "qty": row.quantity,
                    "rate": rate,
                    "voucher_type": (
                        "Opening Stock" if self.is_opening_stock else "Purchase Invoice"
                    ),
                    "voucher_no": self.name,
                    "company": self.company,
                }
            ).insert(ignore_permissions=True)

            update_item_quantity(row.item, self.company)

    # ----------------------------
    # STOCK REVERSE
    # ----------------------------
    def on_cancel(self):
        if self.is_opening_stock:
            frappe.throw("Opening Stock cannot be cancelled")

        for row in self.items:
            rate = row.amount / row.quantity if row.quantity else 0

            frappe.get_doc(
                {
                    "doctype": "Stock Ledger Entry",
                    "posting_datetime": self.posting_date,
                    "item": row.item,
                    "qty": -row.quantity,
                    "rate": rate,
                    "voucher_type": "Purchase Invoice Cancel",
                    "voucher_no": self.name,
                    "company": self.company,
                }
            ).insert(ignore_permissions=True)

            update_item_quantity(row.item, self.company)
