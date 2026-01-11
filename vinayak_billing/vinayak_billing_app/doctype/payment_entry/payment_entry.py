# Copyright (c) 2026, PANDITOFCODES
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class PaymentEntry(Document):

    # ----------------------------
    # VALIDATION
    # ----------------------------
    def validate(self):
        if self.amount <= 0:
            frappe.throw("Payment amount must be greater than zero")

        invoice = frappe.get_doc("Invoice", self.invoice)

        if invoice.docstatus != 1:
            frappe.throw("Payment can be made only against submitted invoices")

        if invoice.status == "Cancelled":
            frappe.throw("Cannot make payment against cancelled invoice")

        if self.amount > invoice.outstanding_amount:
            frappe.throw(
                f"Payment amount cannot exceed outstanding amount "
                f"({invoice.outstanding_amount})"
            )

    # ----------------------------
    # APPLY PAYMENT (SUBMIT)
    # ----------------------------
    def on_submit(self):
        invoice = frappe.get_doc("Invoice", self.invoice)

        paid_amount = (invoice.paid_amount or 0) + self.amount
        outstanding_amount = invoice.net_total - paid_amount

        if outstanding_amount <= 0:
            outstanding_amount = 0
            status = "Paid"
        elif paid_amount > 0:
            status = "Partially Paid"
        else:
            status = "Unpaid"

        # 🔒 Correct way to update submitted documents
        invoice.db_set("paid_amount", paid_amount, update_modified=False)
        invoice.db_set("outstanding_amount", outstanding_amount, update_modified=False)
        invoice.db_set("status", status, update_modified=False)

    # ----------------------------
    # REVERSE PAYMENT (CANCEL)
    # ----------------------------
    def on_cancel(self):
        invoice = frappe.get_doc("Invoice", self.invoice)

        paid_amount = (invoice.paid_amount or 0) - self.amount
        if paid_amount < 0:
            paid_amount = 0

        outstanding_amount = invoice.net_total - paid_amount

        if paid_amount == 0:
            status = "Unpaid"
        elif outstanding_amount == 0:
            status = "Paid"
        else:
            status = "Partially Paid"

        invoice.db_set("paid_amount", paid_amount, update_modified=False)
        invoice.db_set("outstanding_amount", outstanding_amount, update_modified=False)
        invoice.db_set("status", status, update_modified=False)
