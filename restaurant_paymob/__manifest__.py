# -*- coding: utf-8 -*-
{
    'name': 'Restaurant PayMob Integration',
    'version': '19.0.1.0.0',
    'category': 'Restaurant',
    'summary': 'إدارة طلبات المطعم مع بوابة دفع PayMob',
    'description': """
        موديول متكامل لإدارة طلبات المطعم مع دعم الدفع الإلكتروني عبر PayMob.
        - إدارة الطلبات والمراحل
        - دفع إلكتروني عبر PayMob (3 خطوات رسمية)
        - Webhook لتأكيد الدفع تلقائياً مع HMAC security
        - داشبورد بإحصائيات اليوم والأسبوع
        - تقارير المبيعات (Pivot + Graph)
        - طباعة فاتورة PDF بالعربي
    """,
    'author': 'Moaz Omar',
    'depends': ['base', 'mail', 'product', 'account'],
    'data': [
        'security/ir.model.access.csv',
        'data/sequence_data.xml',
        'views/restaurant_order_views.xml',
        'views/restaurant_sale_report_views.xml',
        'views/restaurant_dashboard_views.xml',
        'views/report_restaurant_invoice.xml',
        'views/res_config_settings_views.xml',
        'views/menu_views.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
