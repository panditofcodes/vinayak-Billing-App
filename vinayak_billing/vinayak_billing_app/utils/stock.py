import frappe


def update_item_quantity(item,company):
    qty = frappe.db.sql(
        """
        SELECT IFNULL(SUM(qty), 0)
        FROM `tabStock Ledger Entry`
        WHERE item = %s
        """,
        (item),
    )[0][0]

    frappe.db.set_value("Item", item, "quantity", qty)
