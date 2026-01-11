// Copyright (c) 2026, PANDITOFCODES
// For license information, please see license.txt

frappe.ui.form.on("Invoice", {
	onload(frm) {
		// Set Posting Date
		if (frm.is_new() && !frm.doc.posting_date) {
			frm.set_value("posting_date", frappe.datetime.get_today());
		}

		// Fetch Company from Single DocType
		if (frm.is_new() && !frm.doc.company) {
			frappe.db.get_single_value("Company", "company_name")
				.then(company_name => {
					if (company_name) {
						frm.set_value("company", company_name);
					}
				});

			frappe.db.get_single_value("Company", "address")
				.then(address => {
					if (address && frm.fields_dict.company_address) {
						frm.set_value("company_address", address);
					}
				});
		}
	},

	refresh(frm) {
		// Add Payment Entry button only after submit
		if (frm.doc.docstatus === 1 && frm.doc.outstanding_amount > 0) {
			frm.add_custom_button(
				__("Payment Entry"),
				() => {
					frappe.new_doc("Payment Entry", {
						customer: frm.doc.customer,
						invoice: frm.doc.name,
						amount: frm.doc.outstanding_amount,
						posting_date: frappe.datetime.get_today()
					});
				},
				__("Create")
			);
		}
	},

	customer(frm) {
		if (!frm.doc.customer) return;

		frappe.db.get_value(
			"Customer",
			frm.doc.customer,
			["address", "customer_name"]
		).then(r => {
			if (!r || !r.message) return;

			if (frm.fields_dict.customer_address && r.message.address) {
				frm.set_value("customer_address", r.message.address);
			}

			if (r.message.customer_name) {
				frm.set_value("customer_name", r.message.customer_name);
			}
		});
	}
});


// -----------------------------
// CHILD TABLE: AMOUNT AUTO-FILL
// -----------------------------
frappe.ui.form.on("Invoice Item", {
	quantity(frm, cdt, cdn) {
		update_row_amount(frm, cdt, cdn);
	},

	rate(frm, cdt, cdn) {
		update_row_amount(frm, cdt, cdn);
	}
});

function update_row_amount(frm, cdt, cdn) {
	let row = locals[cdt][cdn];

	if (row.quantity && row.item_price) {
		row.amount = flt(row.quantity) * flt(row.item_price);
	} else {
		row.amount = 0;
	}

	frm.refresh_field("items");
}
