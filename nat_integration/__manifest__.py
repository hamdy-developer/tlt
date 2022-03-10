# -*- coding: utf-8 -*-


{
    'name': 'nat_integration',
    'version': '3.0',
    'category': 'lenght_width',
    'depends': ['base', 'product', 'stock', 'product_brand_inventory', 'sale','sale_management', 'almuazae_purchase','coupon','payment','deltatech_sale_payment','make_cancel_in_sale',"hr",'add_field_shipp'],
    'data': [
        # "security/ir.model.access.csv",
        "security/ir.model.access.csv",
        "views/view.xml",
        "views/data.xml",
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
