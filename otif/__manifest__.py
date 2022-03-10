# Author: Damien Crier
# Author: Julien Coux
# Copyright 2016 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    'name': 'OTIF',
    'version': '111',
    'category': 'Reporting',
    'summary': 'OCA Financial Reports',
    'depends': [
        'base',
        'report_xlsx',
        'stock',
        'sale',
    ],
    'data': [
        "security/ir.model.access.csv",
        'view/view.xml',
        'view/report_general_ledger_account_wizard.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
