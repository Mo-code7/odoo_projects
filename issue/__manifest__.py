{
    'name': 'Project Issue Tracker',
    'version': '1.0',
    'summary': 'Module to register and track project issues',
    'category': 'Project',
    'author': 'You Can',
    'depends': ['base', 'project','sale_management','repair'],
    
    'data': [
        'views/project_issue_views.xml',
        "data/sequence_data.xml",
        'security/ir.model.access.csv',
    ],
        # 'assets': {
        # 'web.assets_backend': [
        #     'issue/static/src/js/employee_loan_dashboard.js',
        # ],
    'installable': True,
    'application': True,
}
