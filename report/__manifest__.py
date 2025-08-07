{
    'name': 'Custom Invoice Report',
    'version': '1.0',
    'category': 'Accounting',
    'summary': 'Custom report to print multiple invoices per page',
    'author': 'Majid Siapa Lagi',
    'depends': ['account'],
    'data': [
        'reports/invoice_template.xml',
        'views/report_action.xml',
    ],
    'installable': True,
    'application': False,
}