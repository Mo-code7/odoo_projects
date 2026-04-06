/** @odoo-module */
import { ReceiptScreen } from "@point_of_sale/app/screens/receipt_screen/receipt_screen";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";

patch(ReceiptScreen.prototype, {
    setup() {
        super.setup(...arguments);
        this.orm = useService("orm");
        this.actionService = useService("action");
        // شلنا الـ popup service لأنه غير متاح
    },

    async generatePosReport() {
        const order = this.pos.getOrder();
        const lines = order.getOrderlines().map(line => ({
            product: line.getProduct().display_name,
            barcode: line.getProduct().barcode || "",
            qty: line.getQuantity(),
            weight: line.getProduct().weight || 0,
            volume: line.getProduct().volume || 0,
        }));

        const result = await this.orm.call(
            "pos.order.wizard",
            "generate_report",
            [order.name, lines]
        );

        this.actionService.doAction(result);
    }
});