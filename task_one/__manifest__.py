{
    'name': 'todo.task',
    'author': 'Moaz',
    'depends': ['base','mail'],
    'data': [
        'security/ir.model.access.csv',
        'data/sequence.xml',
        'views/base_menu.xml',
        'views/task_view.xml',
        'wizard/change_state_wizard_view.xml',
        'report/task_report.xml',
    ],
    'application': True,
}
