# -*- coding: utf-8 -*-
{
    'name': 'AI-Powered Smart Contract & Subscription Agreement Management',
    'version': '1.0',
    'category': 'Sales/CRM',
    'summary': 'Manage customer contracts, automated billing, and AI contract summary extraction.',
    'description': """
        Enterprise contract and subscription agreement management system.
        Features:
        - Custom Contract levels and lines
        - AI-powered contract analysis and metadata extraction (Simulated Gemini integration)
        - Customer portal for online review, signing, and approval
        - Automated invoicing via recurring cron jobs
        - Built-in analytics dashboard (Pivot, Graph views)
        - Custom REST API endpoints for external service synchronization
    """,
    'author': 'Senior Odoo Developer',
    'website': 'https://github.com/yourprofile',
    'depends': [
        'base',
        'mail',
        'portal',
        'account',
        'website',
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence.xml',
        'data/mail_template.xml',
        'data/cron.xml',
        'views/contract_views.xml',
        'views/contract_menus.xml',
        'views/portal_templates.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            '/smart_contract_ai/static/src/css/portal_style.css',
            '/smart_contract_ai/static/src/js/portal_sign.js',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
