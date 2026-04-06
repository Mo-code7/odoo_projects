# -*- coding: utf-8 -*-
{
    'name': "congineer_pos_price",

    'summary': "Short (1 phrase/line) summary of the module's purpose",

    'description': """
Long description of module's purpose
    """,

    'author': "My Company",
    'website': "https://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '19.0.1.0.0',

    # any module necessary for this one to work correctly
    'depends': ['base','point_of_sale'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        'views/pos_order_report.xml',
        'views/pos_order_template.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'congineer_pos_price/static/src/css/product_table.css',
            'congineer_pos_price/static/xml/ProductCard.xml',
            'congineer_pos_price/static/src/js/product_card.js',
            'congineer_pos_price/static/src/css/pos_report_button.css',
            'congineer_pos_price/static/src/js/receipt_screen.js',
            'congineer_pos_price/static/xml/pos_report_button.xml',

        ],
    },

}

