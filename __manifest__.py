# -*- encoding: utf-8 -*-

{
    'name': 'Promedix',
    'version': '1.0',
    'category': 'Custom',
    'description': """ Promedix""",
    'author': 'Aquih',
    'website': 'http://aquih.com/',
    'depends': ['stock','point_of_sale'],
    'data': [
        'views/reporte_rotacion_abastecimiento_view.xml',
        'security/ir.model.access.csv',
    ],
    'assets':{
        'web.assets_qweb':[
            'promedix/static/src/xml/**/*.xml',
        ],
    },
    'demo': [],
    'installable': True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
