/** @odoo-module **/

import { registry } from "@web/core/registry";
import { RentalPropertyDashboard } from "@rental_management/components/rental_property_dashboard";

console.log('[rental_management] Initializing module registration...');

// Register the property_dashboard client action
try {
    registry.category("actions").add("property_dashboard", RentalPropertyDashboard);
    console.log('[rental_management] ✓ Successfully registered property_dashboard action');
} catch (error) {
    console.error('[rental_management] ✗ Failed to register property_dashboard action:', error);
    // Try again after a short delay if registration fails
    setTimeout(() => {
        try {
            registry.category("actions").add("property_dashboard", RentalPropertyDashboard);
            console.log('[rental_management] ✓ Successfully registered property_dashboard action (retry)');
        } catch (error2) {
            console.error('[rental_management] ✗ Still failed after retry:', error2);
        }
    }, 100);
}
