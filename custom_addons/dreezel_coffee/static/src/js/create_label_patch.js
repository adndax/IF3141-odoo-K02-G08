/** @odoo-module **/
import { patch } from "@web/core/utils/patch";
import { ListController } from "@web/views/list/list_controller";
import { KanbanController } from "@web/views/kanban/kanban_controller";

const CREATE_LABELS = {
    "dreezel.transaction": "Transaksi Baru",
    "dreezel.product": "Produk Baru",
    "dreezel.ingredient": "Bahan Baku Baru",
    "dreezel.vendor": "Vendor Baru",
    "dreezel.category": "Kategori Baru",
    "dreezel.discount": "Diskon Baru",
    "dreezel.purchase.order": "Pesanan Baru",
};

patch(ListController.prototype, {
    get createLabel() {
        return CREATE_LABELS[this.props.resModel] || "Baru";
    },
});

patch(KanbanController.prototype, {
    get createLabel() {
        return CREATE_LABELS[this.props.resModel] || "Baru";
    },
});
