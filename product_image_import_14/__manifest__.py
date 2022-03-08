# -*- coding: utf-8 -*-
# Powered by Kanak Infosystems LLP.
# © 2020 Kanak Infosystems LLP. (<https://www.kanakinfosystems.com>)

{
    'name': 'Product Image Import',
    'version': '1.0',
    'summary': 'Allows Product Image import in bulk using reference numbers',
    'description': """
    Allows Product Image import in bulk using reference numbers
    """,
    'category': 'Product',
    'license': 'OPL-1',
    'author': 'Kanak Infosystems LLP.',
    'website': 'https://www.kanakinfosystems.com',
    'images': ['static/description/banner.jpg'],
    'depends': ['product', 'stock'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/knk_import_view.xml',
    ],
    'sequence': 1,
    'installable': True,
    'application': False,
    'auto_install': False,
    'price': 20,
    'currency': 'EUR'
}
