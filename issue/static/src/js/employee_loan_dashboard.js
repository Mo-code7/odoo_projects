odoo.define('project_issue.scroll_last', function (require) {
    "use strict";

    const ListRenderer = require('web.ListRenderer');
    const ListController = require('web.ListController');

    ListController.include({
        renderButtons: function ($node) {
            this._super.apply(this, arguments);
            if (this.$buttons) {
                this.$buttons.find('.o_button_scroll_last').click(this._onScrollLast.bind(this));
            }
        },
        _onScrollLast: function () {
            // نبحث عن كل One2many table داخل form
            this.$el.find('table.o_list_table').each(function() {
                const $tbody = $(this).find('tbody');
                if ($tbody.length) {
                    $tbody.scrollTop($tbody[0].scrollHeight);
                }
            });
        },
    });
});
