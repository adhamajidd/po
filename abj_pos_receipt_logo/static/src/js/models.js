/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { PosStore } from "@point_of_sale/app/store/pos_store";
import { formatDate, formatDateTime } from "@web/core/l10n/dates";
import { parseUTCString } from "@point_of_sale/utils";

patch(PosStore.prototype, {
    getReceiptHeaderData(order) {
        var date;
        var res;
        if (order) {
            let date = "Invalid Date";
            if (order?.date_order) {
                let parsedDate = parseUTCString(order.date_order); // Konversi ke Date object

                // Format tanggal (DD/MM/YYYY) dan waktu (HH:mm:ss)
                let formattedDate = formatDate(parsedDate, { format: "dd/MM/yyyy" });
                let formattedTime = formatDateTime(parsedDate).split(" ")[1]; // Ambil hanya waktu

                date = `${formattedDate} ${formattedTime}`;
            }

            // Get customer name
            let customerName = "Walk-In Customer";
            if (order.partner_id && order.partner_id[1]) {
                customerName = order.partner_id[1];
            }

            // Get cashier name
            let cashierName = "Administrator";
            if (order.user_id && order.user_id[1]) {
                cashierName = order.user_id[1];
            }

            // Get company data with address information
            let companyData = {
                ...this.company,
                // Add address fields if they exist in company partner
                street: this.company.partner_id ? this.company.partner_id.street : null,
                city: this.company.partner_id ? this.company.partner_id.city : null,
                state_id: this.company.partner_id ? this.company.partner_id.state_id : null,
                zip: this.company.partner_id ? this.company.partner_id.zip : null,
                country_id: this.company.partner_id ? this.company.partner_id.country_id : null,
            };

            res = {
                ...super.getReceiptHeaderData(order),
                partner: order.partner_id,
                pos_reference: order.pos_reference,
                date: date,
                customer: customerName,
                cashier: cashierName,
                company: companyData,
            };
        } else {
            // For cases when order is not available, use current date
            let currentDate = new Date();
            let formattedDate = formatDate(currentDate, { format: "dd/MM/yyyy" });
            let formattedTime = formatDateTime(currentDate).split(" ")[1];
            date = `${formattedDate} ${formattedTime}`;
            
            res = { 
                ...super.getReceiptHeaderData(order),
                date: date,
                customer: "Walk-In Customer",
                cashier: "Administrator",
            };
        }
        
        // Debug: log the data being returned
        console.log("Receipt Header Data:", res);
        
        return res;
    },
});
