/** @odoo-module */

import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";

patch(ProductScreen.prototype, {

    setup() {
        super.setup();
        this.pos = useService("pos");
        this.orm = useService("orm"); // إضافة خدمة ORM
    },

    // السعر الأساسي بدون pricelist
    getProductPrice(product) {
        if (!product) {
            return this.env.utils.formatCurrency(0);
        }

        const price = product.list_price || 0;
        return this.env.utils.formatCurrency(price);
    },

    // كمية المنتج في المخزن
    getProductQty(product) {
           console.log(product);
           return product.qty_available || 0;
        },
        
      
    // تكلفة المنتج
    getProductCost(product) {
        return this.env.utils.formatCurrency(product.standard_price || 0);
    },
    getProductWeight(product) {
        return product.weight || 0;
    },

    getProductVolume(product) {
        return product.volume || 0;
    },
    // صورة المنتج
    getTableProductImage(product) {
        if (this.pos.config.show_product_images) {
            return product.getImageUrl();
        }
        return false;
    },

});
