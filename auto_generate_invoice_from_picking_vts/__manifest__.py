{
    # App information

    'name': 'Auto Invoice When Validate Delivery/Incoming Shipment',
    'version': '14.0.10.12.2020',
    'category': 'Accounting',
    'summary': 'Auto Create Invoice when Validate Delivery Order/Incoming Shipment',
    
    # Dependencies

    'depends': ['stock', 'purchase_stock', 'sale_management', 'account', 'base'],

    # Views

    'data': [
        'view/stock_picking.xml',
        'view/res_company.xml',
        'view/sale_order.xml',
        ],

    # Odoo Store Specific

    'images': ['static/description/auto_inv.jpg'],

    'author': 'Vraja Technologies',

    'demo': [],
    'price': '30' ,
    'currency': 'EUR',
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'OPL-1',
}
