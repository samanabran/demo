/** @odoo-module **/

import { registry } from "@web/core/registry";

// Import the dashboard component
import { RentalPropertyDashboard } from "@sgc_offplan_rental_property_management/components/rental_property_dashboard";

// Register immediately on module load
console.log('[rental_property_dashboard] Starting registration...');

try {
    const actions = registry.category("actions");
    
    // Check if already registered
    try {
        actions.get("property_dashboard");
        console.log('[rental_property_dashboard] Already registered');
    } catch {
        // Not registered yet, register it now
        actions.add("property_dashboard", RentalPropertyDashboard);
        console.log('[rental_property_dashboard] ✓ Registered successfully');
    }
} catch (e) {
    console.error('[rental_property_dashboard] Registration error:', e);
}
