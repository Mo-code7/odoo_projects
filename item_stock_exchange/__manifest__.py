{
    'name': 'بورصة الأصناف',
    'version': '1.0',
    'summary': 'متابعة أسعار الأصناف مثل البورصة',
    'author': 'Your Can',
    'category': 'Inventory',
    'depends': ['base','product','sale','sale_management','stock'],
    'data': [
        'security/ir.model.access.csv',
        'views/item_exchange_views.xml',
        'views/product_template_view.xml',
        'views/updating_models_view.xml',
    ],
    'images': ['static/description/icon.png'],
    'installable': True,
    'application': True,
}