// Copyright (c) 2026, PANDITOFCODES and contributors
// For license information, please see license.txt

frappe.ui.form.on("Purchase Invoice", {
	onload(frm) {
		// Set Company from Single DocType
		if (frm.is_new() && !frm.doc.company) {
			frappe.db.get_doc("Company").then((company) => {
				if (company) {
					frm.set_value("company", company.company_name || "Company");

					// Set company address if field exists
					if (frm.fields_dict.company_address && company.address) {
						frm.set_value("company_address", company.address);
					}
				}
			});
			frm.set_value("posting_date", frappe.datetime.get_today());
		}
	},
});
