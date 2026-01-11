# Copyright (c) 2026, PANDITOFCODES
# License: see license.txt

import frappe
from frappe.model.document import Document
from vinayak_billing.vinayak_billing_app.utils.stock import update_item_quantity


class Invoice(Document):

    # ----------------------------
    # DEFAULT COMPANY (SINGLE)
    # ----------------------------
    def before_save(self):
        if not self.company:
            company = frappe.get_single("Company")

            if company:
                self.company = company.company_name or "Company"

                if hasattr(self, "company_address") and company.address:
                    self.company_address = company.address

    # ----------------------------
    # VALIDATION PIPELINE
    # ----------------------------
    def validate(self):
        self.calculate_items_total()
        self.validate_stock()
        self.calculate_tax()
        self.calculate_net_total()

    # ----------------------------
    # ITEM TOTALS
    # ----------------------------
    def calculate_items_total(self):
        total = 0

        for row in self.items:
            if row.quantity <= 0:
                frappe.throw("Quantity must be greater than zero")

            # Server-side authority
            row.amount = row.quantity * row.item_price
            total += row.amount

        self.total = total

    # ----------------------------
    # STOCK VALIDATION
    # ----------------------------
    def validate_stock(self):
        for row in self.items:
            available_qty = frappe.db.get_value("Item", row.item, "quantity") or 0

            if available_qty < row.quantity:
                frappe.throw(
                    f"Not enough stock for item {row.item}. "
                    f"Available: {available_qty}"
                )

    # ----------------------------
    # GST / TAX LOGIC (FIXED)
    # ----------------------------
    def calculate_tax(self):
        self.set("tax", [])

        company_state = frappe.db.get_single_value("Company", "state")
        customer_state = frappe.db.get_value("Customer", self.customer, "state")

        if not company_state or not customer_state:
            frappe.throw("Company and Customer state are required for GST")

        # 🔒 NORMALIZATION FIX (THIS WAS THE ISSUE)
        company_state = company_state.strip().lower()
        customer_state = customer_state.strip().lower()

        same_state = company_state == customer_state
        tax_map = {}

        for row in self.items:
            gst_rate = frappe.db.get_value("Item", row.item, "gst_rate") or 0
            if gst_rate <= 0:
                continue

            gst_amount = (row.amount * gst_rate) / 100

            if same_state:
                half_rate = gst_rate / 2
                half_amount = gst_amount / 2

                tax_map.setdefault(("CGST", half_rate), 0)
                tax_map.setdefault(("SGST", half_rate), 0)

                tax_map[("CGST", half_rate)] += half_amount
                tax_map[("SGST", half_rate)] += half_amount
            else:
                tax_map.setdefault(("IGST", gst_rate), 0)
                tax_map[("IGST", gst_rate)] += gst_amount

        for (tax_type, rate), amount in tax_map.items():
            self.append(
                "tax",
                {
                    "tax_type": tax_type,
                    "rate": rate,
                    "amount": round(amount, 2),
                },
            )

        self.total_tax = sum(row.amount for row in self.tax)

    # ----------------------------
    # NET TOTAL & STATUS
    # ----------------------------
    def calculate_net_total(self):
        self.net_total = self.total + self.total_tax

        self.paid_amount = self.paid_amount or 0
        self.outstanding_amount = self.net_total - self.paid_amount

        if self.outstanding_amount <= 0:
            self.status = "Paid"
            self.outstanding_amount = 0
        elif self.paid_amount > 0:
            self.status = "Partially Paid"
        else:
            self.status = "Unpaid"

    # ----------------------------
    # STOCK OUT (SUBMIT)
    # ----------------------------
    def on_submit(self):
        posting_time = frappe.utils.now()

        for row in self.items:
            rate = row.amount / row.quantity if row.quantity else 0

            frappe.get_doc(
                {
                    "doctype": "Stock Ledger Entry",
                    "posting_time": posting_time,
                    "item": row.item,
                    "qty": -row.quantity,
                    "voucher_type": "Sales Invoice",
                    "voucher_no": self.name,
                }
            ).insert(ignore_permissions=True)

            update_item_quantity(row.item, self.company)

    # ----------------------------
    # STOCK REVERSE (CANCEL)
    # ----------------------------
    def on_cancel(self):
        posting_time = frappe.utils.now()

        for row in self.items:
            rate = row.amount / row.quantity if row.quantity else 0

            frappe.get_doc(
                {
                    "doctype": "Stock Ledger Entry",
                    "posting_time": posting_time,
                    "item": row.item,
                    "qty": row.quantity,
                    "voucher_type": "Sales Invoice Cancel",
                    "voucher_no": self.name,
                }
            ).insert(ignore_permissions=True)

            update_item_quantity(row.item, self.company)

        self.status = "Cancelled"
