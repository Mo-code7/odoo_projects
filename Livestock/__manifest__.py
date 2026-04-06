{
    'name': 'Livestock Management',
    'version': '18.0.2.0.0',
    'category': 'Agriculture',
    'summary': 'Comprehensive livestock management system',
    'author': 'Livestock Team',
    'website': 'https://www.livestock-management.com',
    'support': 'support@livestock-management.com',
    'license': 'LGPL-3',
    'depends': ['base', 'mail', 'web', 'product', 'stock' ,'stock_account','hr_payroll'],
    'data': [
          "data/sequence_data.xml",
        'security/ir.model.access.csv',
       
        'views/livestock_animal_views.xml',
       ],
    'demo': [
        'demo/livestock_species_demo.xml',
        'demo/livestock_breed_demo.xml',
        'demo/livestock_location_demo.xml',
        'demo/livestock_status_demo.xml',
        'demo/livestock_animal_demo.xml',
    ],
    # 'assets': {
    #     'web.assets_backend': [
    #         'livestock_management/static/src/scss/livestock_dashboard.scss',
    #         'livestock_management/static/src/js/livestock_dashboard.js',
    #         'livestock_management/static/src/xml/livestock_dashboard.xml',
    #         'livestock_management/static/description/icon.png',
    #     ],
    # },
    'images': ['static/description/icon.png'],
    'application': True,
    'installable': True,
    'auto_install': False,
    'sequence': 10,
    'icon': '/livestock_management/static/description/icon.png',
}
