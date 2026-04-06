# -*- coding: utf-8 -*-

from . import models


def post_init_hook(env):
    """
    Post-installation hook to set up initial data and configurations for livestock management
    """
    # Ensure animal tag sequence exists
    animal_sequence = env['ir.sequence'].search([('code', '=', 'livestock.animal')], limit=1)
    if not animal_sequence:
        env['ir.sequence'].create({
            'name': 'Animal Tag Number',
            'code': 'livestock.animal',
            'prefix': 'ANM/%(y)s/',
            'padding': 5,
            'number_next': 1,
            'number_increment': 1,
        })
    
    # Set up default animal types if none exist
    # Note: This part creates sample animals, which is fine.
    animal_types = env['livestock.animal'].search([('type', '!=', False)])
    if not animal_types:
        # Create some sample animals to demonstrate the system
        default_animals = [
            {
                'name': 'بقرة تجريبية',
                'tag_no': 'ANM/2024/00001',
                'type': 'بقرة',
                'breed': 'هولشتاين',
                'gender': 'أنثى',
                'birth_date': '2023-01-15',
                'weight': 450.0,
                'status': 'حي',
            },
            {
                'name': 'خروف تجريبي',
                'tag_no': 'ANM/2024/00002',
                'type': 'خروف',
                'breed': 'نعيمي',
                'gender': 'ذكر',
                'birth_date': '2023-03-20',
                'weight': 65.0,
                'status': 'حي',
            },
        ]
        
        for animal_data in default_animals:
            env['livestock.animal'].create(animal_data)


def uninstall_hook(cr, registry=None):
    """
    Uninstallation hook to clean up livestock module data
    """
    from odoo import api, SUPERUSER_ID
    
    env = api.Environment(cr, SUPERUSER_ID, {})
    
    # Remove animal sequences
    sequences_to_remove = [
        'livestock.animal',
    ]
    
    for seq_code in sequences_to_remove:
        sequence = env['ir.sequence'].search([('code', '=', seq_code)], limit=1)
        if sequence:
            sequence.unlink()
    
    # Optionally remove all animal records (uncomment if needed)
    # animals = env['livestock.animal'].search([])
    # if animals:
    #     animals.unlink()
