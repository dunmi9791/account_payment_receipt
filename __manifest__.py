# -*- coding: utf-8 -*-
{
    'name': 'Payment Receipt Report',
    'version': '17.0.1.0.0',
    'summary': 'Custom receipt report for payments showing outstanding and new balance',
    'description': """
        Adds a professional PDF receipt report to account.payment that displays:
        - Payment details (date, reference, journal, method)
        - Partner information
        - Outstanding balance before the payment
        - New balance after the payment
        - List of reconciled invoices / bills
    """,
    'category': 'Accounting/Accounting',
    'author': 'Your Company',
    'website': '',
    'license': 'LGPL-3',
    'depends': ['account'],
    'data': [
        'security/ir.model.access.csv',
        'report/report_action.xml',
        'report/report_payment_receipt_template.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
