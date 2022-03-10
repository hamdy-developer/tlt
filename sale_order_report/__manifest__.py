# Author: Damien Crier
# Author: Julien Coux
# Copyright 2016 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    'name': 'sale order report',
    'version': '2',
    'category': 'Reporting',
    'summary': 'OCA Financial Reports',
    'depends': [
        'base',
        'sale',
        'stock',
    ],
    'data': [
        'view/view.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
