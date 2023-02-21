# -*- encoding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import time
import xlsxwriter
import base64
import io
import logging

class PromedixRotacionAbastecimientoWizard(models.TransientModel):
    _name = 'promedix.rotacion_abastecimiento_wizard'


    fecha_inicio = fields.Datetime(string="Fecha Inicial", required=True,  default=fields.Datetime.now)
    fecha_fin = fields.Datetime(string="Fecha Final", required=True,  default=fields.Datetime.now)
    meses_proyeccion = fields.Float('Meses proyección')
    producto_ids = fields.Many2many("product.product", string="Productos", required=True)
    name = fields.Char('Nombre archivo', size=32)
    archivo = fields.Binary('Archivo', filters='.xls')

    def obtener_costo_productos(self, fecha_inicio, lista_productos):
        dic_costos = {}
        for producto in self.env['product.product'].with_context({'to_date': fecha_inicio.strftime("%Y-%m-%d  %H:%M:%S")}).search([('id', 'in', lista_productos)]):
            if producto not in dic_costos:
                dic_costos[producto.id] = producto.standard_price
        return dic_costos

    def obtener_unidades_vendidas(self, fecha_inicio, fecha_fin,lista_productos):
        unidades_vendidas = {}
        venta_linea_ids = self.env['sale.order.line'].search([('order_id.date_order','>=', fecha_inicio),('order_id.date_order','<=',fecha_fin),('product_id','in', lista_productos),('state','=','sale')])
        if len(venta_linea_ids) > 0:
            for linea in venta_linea_ids:
                if linea.product_id.id not in unidades_vendidas:
                    unidades_vendidas[linea.product_id.id] = 0
                unidades_vendidas[linea.product_id.id] += linea.product_uom_qty
        return unidades_vendidas

    def obtener_dias(self, fecha_inicio, fecha_fin, lista_productos):
        producto_dias = {}
        productos_str = ','.join([str(x) for x in lista_productos])
        self.env.cr.execute('select l.product_id, l.product_uom_qty, s.date_order '\
        'from sale_order_line l join sale_order s on(l.order_id = s.id)'\
        'where s.state = \'sale\' and s.date_order >= %s and s.date_order < %s and l.product_id in ('+productos_str+') ORDER BY s.date_order ASC;', (fecha_inicio,fecha_fin))
        for m in self.env.cr.dictfetchall():
            if m['product_id'] not in producto_dias:
                dias =  m['date_order'] - fecha_inicio
                logging.warning(dias.days)
                producto_dias[m['product_id']] = dias.days
            # logging.warning('producto qer')
            # logging.warning( m['date_order'] - fecha_inicio)
            # logging.warning(m)
        logging.warning(producto_dias)
        return producto_dias

    def print_report_excel(self):
        for w in self:
            f = io.BytesIO()
            libro = xlsxwriter.Workbook(f)
            hoja = libro.add_worksheet('Reporte rotacion abastecimiento')
            formato_fecha = libro.add_format({'num_format': 'dd/mm/yy'})

            hoja.write(0, 0, 'Rotacion para abastecimiento')
            hoja.write(1, 0, 'Fecha inicio')
            hoja.write(1, 1, str(w.fecha_inicio))
            hoja.write(1, 2, 'Rotacionfin')
            hoja.write(1, 1, str(w.fecha_fin))

            hoja.write(3, 0, 'Código')
            hoja.write(3, 1, 'Nombre')
            hoja.write(3, 2, 'Costo')
            hoja.write(3, 3, 'Cantidad')
            hoja.write(3, 4, 'Fecha inicio')
            hoja.write(3, 5, 'Fecha fin')
            hoja.write(3, 6, 'Unidades')
            hoja.write(3, 7, 'Días')
            hoja.write(3, 8, 'Indice rotacion diario')
            hoja.write(3, 9, 'Indice rotacion mensual')
            hoja.write(3, 10, 'Inventario proyectado')
            hoja.write(3, 11, 'Inventario necesario')

            costo_productos = self.obtener_costo_productos(w.fecha_inicio,w.producto_ids.ids)
            unidades_vendidas = self.obtener_unidades_vendidas(w.fecha_inicio,w.fecha_fin,w.producto_ids.ids)
            dias_venta = self.obtener_dias(w.fecha_inicio,w.fecha_fin,w.producto_ids.ids)
            y = 4
            for producto in w.producto_ids:
                hoja.write(y, 0, producto.default_code)
                hoja.write(y, 1, producto.name)
                hoja.write(y, 2, costo_productos[producto.id] if producto.id in costo_productos else 0)
                hoja.write(y, 3, producto.qty_available)
                hoja.write(y, 4, str(w.fecha_inicio))
                hoja.write(y, 5, str(w.fecha_fin))
                unidades = unidades_vendidas[producto.id] if producto.id in unidades_vendidas else 0
                hoja.write(y, 6, unidades)
                producto_dias = self.obtener_dias(w.fecha_inicio, w.fecha_fin, w.producto_ids.ids)
                dias = dias_venta[producto.id] if producto.id in dias_venta else 0
                hoja.write(y, 7, dias)
                rotacion_diaria = (unidades / dias) if dias > 0 else 0
                hoja.write(y, 8, rotacion_diaria)
                rotacion_mensual = rotacion_diaria * 30
                hoja.write(y, 9, rotacion_mensual)
                inventario_proyectado = rotacion_mensual * w.meses_proyeccion
                hoja.write(y, 10, inventario_proyectado)
                inventario_necesario = producto.qty_available - inventario_proyectado

                y += 1

            libro.close()
            datos = base64.b64encode(f.getvalue())
            self.write({'archivo':datos, 'name':'rotacion_abastecimiento.xlsx'})

        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'promedix.rotacion_abastecimiento_wizard',
            'res_id': self.id,
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
