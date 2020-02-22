# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import os
import pprint
import logging
import traceback
import tempfile
from lxml import etree

from odoo import fields, models, _

_logger = logging.getLogger(__name__)
pp = pprint.PrettyPrinter(indent=4)


class SyncDocumentType(models.Model):

    _inherit = 'sync.document.type'

    doc_code = fields.Selection(selection_add=[
        ('import_so', '850 - Import Order (Purchase Order)'),
        ('export_invoice', '810 - Export Invoice'),
        ('export_shipping_order', '856 - Export Shipping Order')
    ])

    def _get_missing_required_fields(self, vals):
        required_fields = ['order_line', 'partner_id', 'name']
        missing_fields = []
        for field in required_fields:
            if not vals.get(field):
                missing_fields.append(field)
        return missing_fields

    def _parse_dates(self, dates_ele):
        """
        Method will take Dates (etree.Element) and attempts to create  date or dateime object

        @param address_ele: lxml.etree.Element

        @return int: address id
        """
        dt = False
        date_ele = dates_ele.find('./{}Date')
        time_ele = dates_ele.find('./{}Time')
        if all([date_ele is not None and date_ele.text,
                time_ele is not None and time_ele.text]):
            dt = fields.Datetime.to_datetime(
                '%s %s' % (date_ele.text, time_ele.text))
        elif date_ele is not None and date_ele.text:
            dt = fields.Date.to_date(date_ele.text)
        return dt

    def _parse_line_items(self, line_ele):
        line_fields_map = {
            'product_id': 'OrderLine/{*}ProductID/{*}PartNumber',
            'product_uom_qty': 'OrderLine/{*}OrderQty',
            'product_uom': 'OrderLine/{*}OrderQtyUOM',
            'price_unit': 'PriceInformation/{*}UnitPrice',
        }
        line = {}
        for o_f, e_f in line_fields_map.items():
            field_ele = line_ele.find('./{*}%s' % e_f)
            if field_ele is not None and field_ele.text:
                line.update({o_f: field_ele.text})

        note = ''
        for elem in line_ele.iterfind('./{*}Notes'):
            note_elem = elem.find('./{*}Note')
            if note_elem is not None:
                note = note + ' \n ' + note_elem.text

        if note:
            line['name'] = note

        if line.get('product_id'):
            product_id = self.env['product.product'].search([('default_code', '=', line['product_id'])], limit=1).id
            line['product_id'] = product_id
        if line.get('product_uom'):
            uom_id = self.env['uom.uom'].search([('name', '=', line['product_uom'])], limit=1).id
            line['product_uom'] = uom_id

        # required field in odoo
        if not line.get('product_id') or not line.get('product_uom'):
            line = {}
        return line

    def _parse_address(self, address_ele, trading_partner_id):
        """
        Method will take Address (etree.Element) and find or create address
        and returns the address id

        @param address_ele: lxml.etree.Element

        @return int: address id
        """
        address_types_map = {
            'BT': 'invoice',
            'RT': 'delivery',
            'ST': 'delivery',
            'X_CN': 'contact',
        }
        address_fields_map = {
            'street': 'Address1',
            'street2': 'Address2',
            'city': 'City',
            'zip': 'PostalCode',
            'vat': 'AddressTaxIdNumber',
            'phone': 'Contacts/{*}PrimaryPhone',
            'email': 'Contacts/{*}PrimaryEmail',
            'ref': 'Contacts/{*}ContactReference',
        }

        address_val = False
        address_name_ele = address_ele.find('./{*}AddressName')
        add_type = address_name_ele.text

        if address_name_ele is None and add_type not in address_types_map:
            return False

        add_type = address_types_map.get(add_type, 'contact')
        contact_name = address_ele.find('./{*}AddressName').text

        address_domain = [('name', '=', contact_name), ('trading_partnerid', '=', trading_partner_id)]
        address_val = {
            'name': contact_name,
            'type': add_type,
            'trading_partnerid': trading_partner_id,
        }
        for o_f, e_f in address_fields_map.items():
            field_ele = address_ele.find('./{*}%s' % e_f)
            if field_ele is not None and field_ele.text:
                address_domain.append((o_f, '=', field_ele.text))
                address_val.update({o_f: field_ele.text})
        state_id = False
        country_id = False
        state_ele = address_ele.find('./{*}State')
        country_ele = address_ele.find('./{*}Country')
        if country_ele is not None and country_ele.text:
            country_code = 'US' if country_ele.text == 'USA' else country_ele.text
            country_id = self.env['res.country.state'].search(
                [('code', '=', country_ele.text[:2])], limit=1)
            if country_id:
                address_domain.append(('country_id', '=', country_id.id))
                address_val.update({'country_id': country_id.id})
        if state_ele is not None and state_ele.text:
            state_domain = [('code', '=', state_ele.text)]
            if country_id:
                state_domain.append(('country_id', '=', country_id.id))
            elif not country_id and country_ele is not None and country_ele.text:
                state_domain.append(
                    ('country_id.code', '=', country_ele.text[:2]))
            state_id = self.env['res.country.state'].search(
                state_domain, limit=1)
            if state_id:
                address_domain.append(('state_id', '=', state_id.id))
                address_val.update({'state_id': state_id.id})

        partner_id = self.env['res.partner'].search(address_domain, limit=1)
        address_val.update({'customer': True})
        if not partner_id:
            partner_id = self.env['res.partner'].create(address_val)
        else:
            partner_id.write(address_val)
        return partner_id

    def _do_import_so(self, conn, sync_action_id, values):
        '''
        This is dummy demo method.
        @param conn : sftp/ftp connection class.
        @param sync_action_id: recorset of type `edi.sync.action`
        @param values:dict of values that may be useful to various methods

        @return bool : return bool (True|False)
        '''

        conn._connect()
        conn.cd(sync_action_id.dir_path)
        files = conn.ls()
        for file in files:
            file_path = os.path.join(sync_action_id.dir_path, file)
            file_data = conn.download_incoming_file(file_path).encode('utf-8')
            root = etree.fromstring(file_data)

            for order in root.iterfind('./{*}Order'):
                try:
                    header = order.find('./{*}Header')
                    order_header = header.find('./{*}OrderHeader')
                    # orderheader required edi fields
                    tranding_partner_id = order_header.find(
                        './{*}TradingPartnerId').text
                    order_number = order_header.find(
                        './{*}PurchaseOrderNumber').text

                    # orderheader optional edi fields
                    purpose_code = order_header.find('./{*}TsetPurposeCode')
                    po_type_code = order_header.find('./{*}PrimaryPOTypeCode')
                    order_date = order_header.find('./{*}PurchaseOrderDate')
                    currency = order_header.find('./{*}BuyersCurrency')
                    vendor_number = order_header.find('./{*}Vendor')
                    customer_order_number = order_header.find(
                        './{*}CustomerOrderNumber')

                    order_vals = {
                        'name': order_number,
                        'origin':  customer_order_number.text if customer_order_number is not None else False,
                        'date_order': order_date.text if order_date is not None else False,
                        'purpose_code': purpose_code.text,
                        'po_type_code': po_type_code.text,
                        'currency_id': self.env['res.currency'].search([('name', '=', currency)], limit=1).id
                    }
                    # header dates
                    for edi_date in header.iterfind('./{*}Dates'):
                        if edi_date is not None:
                            date_qf = edi_date.find('./{*}DateTimeQualifier')
                            if date_qf is not None and date_qf.text == '001':
                                order_vals.update(
                                    {'validity_date': self._parse_dates(edi_date)})
                            elif date_qf is not None and date_qf.text == '010':
                                order_vals.update(
                                    {'expected_date': self._parse_dates(edi_date)})
                            elif date_qf is not None and date_qf.text == '011':
                                order_vals.update(
                                    {'commitment_date': self._parse_dates(edi_date)})
                            elif date_qf is not None and date_qf.text == '017':
                                order_vals.update(
                                    {'effective_date': self._parse_dates(edi_date)})

                    # header address
                    for address in header.iterfind('./{*}Address'):
                        if address is not None:
                            add_type_code = address.find(
                                './{*}AddressTypeCode')
                            if add_type_code is not None and add_type_code.text in ('BT', 'DT'):
                                partner_id = self._parse_address(address, tranding_partner_id)
                                if partner_id:
                                    order_vals.update(partner_id=partner_id.id)

                    # line Items
                    for line in order.iterfind('./{*}LineItem'):
                        if line is not None:
                            parse_line = self._parse_line_items(line)
                            if parse_line:
                                order_vals.update(order_line=[(0, 0, parse_line)])

                    # line Items
                    for carrier in header.iterfind('./{*}CarrierInformation'):
                        code = carrier.find('./{*}CarrierAlphaCode')
                        carrier_id = self.env['delivery.carrier'].search([('name', '=', code)], limit=1).id
                        if carrier_id:
                            order_vals.update(carrier_id=carrier_id)

                    # create order
                    missing_fields = self._get_missing_required_fields(order_vals)
                    if missing_fields:
                        error_msg = _('Order could not be created as some required fields are missing. %s') % (','.join(f for f in missing_fields))
                        _logger.error(error_msg)
                    else:
                        self.env['sale.order'].create(order_vals)

                except etree.XMLSyntaxError as e:
                    entry = e.error_log.last_error
                    print(entry)
                except Exception as ex:
                    print(traceback.print_tb(ex))
        conn._disconnect()
        return True

    def _do_export_so(self, conn, sync_action_id, values):
        '''
        This is dummy demo method.
        @param conn : sftp/ftp connection class.
        @param sync_action_id: recorset of type `edi.sync.action`
        @param values:dict of values that may be useful to various methods

        @return bool : return bool (True|False)
        '''
        _logger.info('Not Implemented')

        return True

    def _do_export_invoice(self, conn, sync_action_id, values):
        '''
        This is dummy demo method.
        @param conn : sftp/ftp connection class.
        @param sync_action_id: recorset of type `edi.sync.action`
        @param values:dict of values that may be useful to various methods

        @return bool : return bool (True|False)
        '''
        conn._connect()
        conn.cd(sync_action_id.dir_path)
        # get confirmed order
        invoice = self.env['account.invoice'].search([('state', '=', 'open'), ('edi_status', '=', 'pending')], limit=1)
        if invoice:
            xml = self.get_invoice_xml(invoice)
            # TODO : used upload method of sftp
            tmp_dir = tempfile.mkdtemp()
            filename = 'PO' + invoice.number.replace('/', '') + '.xml'
            filename = filename.strip()
            export_file_path = tmp_dir.rstrip('/') + '/' + filename
            file = open(export_file_path, 'w')
            file.write(xml)
            file.close()
            conn._conn.put(export_file_path, sync_action_id.dir_path + '/' + filename)
            conn._disconnect()

            os.remove(export_file_path)
            os.rmdir(tmp_dir)

            invoice.write({'edi_status': 'sent'})

        return True

    def get_invoice_xml(self, invoice):
        sale_orders = invoice.invoice_line_ids.mapped('sale_line_ids').mapped('order_id')
        sale_order = sale_orders and sale_orders[0]
        values = {
            'TradingPartnerId': invoice.partner_id.trading_partnerid,
            'InvoiceNumber': invoice.number,
            'InvoiceDate': invoice.date_invoice,
            'PurchaseOrderDate': invoice.purchase_id.date_order,
            'PurchaseOrderNumber': invoice.purchase_id.name,
            'BuyersCurrency': invoice.currency_id.name,
            'Vendor': invoice.partner_id.vendor,
            'InvoiceTypeCode': 'DR' if invoice.type == 'in_invoice' else 'CR',
            'TsetPurposeCode': '',
            'Department': '',
            'CustomerOrderNumber': sale_order.name,
            'BillOfLadingNumber': '',
            'CarrierAlphaCode': sale_order.carrier_id.name,
            'CarrierProNumber': '',
            'ShipDate': sale_order and sale_order.picking_ids and sale_order.picking_ids[0].scheduled_date,
            'TermsType': invoice.payment_term_id.terms_type,
            'TermsBasisDateCode': invoice.payment_term_id.terms_basis_date_code,
            'TermsDiscountPercentage': '',
            'TermsDiscountDate': '',
            'TermsNetDueDate': '',
            'TermsNetDueDays': '',
            'TermsDiscountAmount': '',
            'TermsDescription': '',
            'DateTimeQualifier': '',
            'Date': invoice.date_invoice,
            'ContactTypeCode': '',
            'ContactName': invoice.partner_id.name,
            'PrimaryPhone': invoice.partner_id.phone,
            'PrimaryEmail': invoice.partner_id.email,
            'addresses': self._get_addresses(invoice),
            'ReferenceQual': '',
            'ReferenceID': '',
            'Description': '',
            'NoteCode': '',
            'Note': invoice.comment,
            'TaxTypeCode': '',
            'TaxAmount': invoice.amount_tax,
            'TaxPercent': '',
            'JurisdictionQual': '',
            'JurisdictionCode': '',
            'TaxExemptCode': '',
            'TaxID': '',
            'AllowChrgIndicator': invoice.allow_charge_indicator,
            'AllowChrgCode': invoice.allow_charge_code,
            'AllowChrgAmt': invoice.allow_charge_amount,
            'AllowChrgPercentQual': '',
            'AllowChrgPercent': '',
            'AllowChrgHandlingCode': '',
            'AllowChrgHandlingDescription': '',
            'QuantityTotalsQualifier': '',
            'Quantity': sum(invoice.invoice_line_ids.mapped('quantity')),
            'QuantityUOM': invoice.invoice_line_ids[0].uom_id.name,
            "lines": self._get_invoice_lines(invoice),
            'TotalAmount': invoice.amount_total,
            'TotalSalesAmount': invoice.amount_untaxed,
            'TotalTermsDiscountAmount': '',
            'TotalLineItemNumber': len(invoice.invoice_line_ids),
            'InvoiceAmtDueByTermsDate': invoice.residual,

            'StatusCode': '',
            'CarrierTransMethodCode': '',
            'CarrierAlphaCode': '',
            'CarrierRouting': '',
            'EquipmentDescriptionCode': '',
            'CarrierEquipmentNumber': '',
        }

        xml = self.env.ref('edi_sale.export_invoice_xml').render(values)
        xml = '<?xml version="1.0" encoding="utf-8"?>' + '\n' + xml.decode("utf-8")
        return xml

    def _get_addresses(self, invoice):
        return [{
            'AddressTypeCode': 'ST',
            'AddressLocationNumber': '',
            'LocationCodeQualifier': '',
            'AddressName': invoice.partner_id.name,
            'Address1': invoice.partner_id.street,
            'City': invoice.partner_id.city,
            'State': invoice.partner_id.state_id.code,
            'PostalCode': invoice.partner_id.zip,
            'Country': invoice.partner_id.country_id.code,
        }]

    def _get_invoice_lines(self, invoice):
        lines = []
        for line in invoice.invoice_line_ids:
            line_dict = {
                'LineSequenceNumber': line.sequence,
                'BuyerPartNumber': line.product_id.default_code,
                'VendorPartNumber': line.product_id.default_code,
                'ConsumerPackageCode': '',
                'GTIN': '',
                'UPCCaseCode': '',
                'PartNumberQual': 'CB',
                'PartNumber': line.product_id.default_code,
                'InvoiceQty': line.quantity,
                'InvoiceQtyUOM': line.uom_id.name,
                'PurchasePrice': line.product_id.standard_price,
                'ShipQty': '',
                'ShipQtyUOM': '',
                'ProductSizeCode': '',
                'ProductColorCode': '',
                'PriceTypeIDCode': '',
                'UnitPrice': line.price_unit,
                'ProductDescription': '',
                'ProductCharacteristicCode': '',
                'ReferenceQual': '',
                'ReferenceID': line.invoice_id.number,
                'Note': line.name,
                'NoteCode': ''
            }
            lines.append(line_dict)
        return lines

    def _do_export_shipping_order(self, conn, sync_action_id, values):
        '''
        This is dummy demo method.
        @param conn : sftp/ftp connection class.
        @param sync_action_id: recorset of type `edi.sync.action`
        @param values:dict of values that may be useful to various methods

        @return bool : return bool (True|False)
        '''
        conn._connect()
        conn.cd(sync_action_id.dir_path)
        # get confirmed order
        picking = self.env['stock.picking'].search([
                            ('picking_type_code', '=', 'outgoing'),
                            ('edi_status', '=', 'pending'),
                            ('state', '=', 'done')], limit=1)
        if picking:
            xml = self.get_shipping_xml(picking)
            tmp_dir = tempfile.mkdtemp()
            filename = 'PO' + picking.name.replace('/', '') + '.xml'
            filename = filename.strip()
            export_file_path = tmp_dir.rstrip('/') + '/' + filename
            file = open(export_file_path, 'w')
            file.write(xml)
            file.close()
            conn._conn.put(export_file_path, sync_action_id.dir_path + '/' + filename)
            conn._disconnect()

            os.remove(export_file_path)
            os.rmdir(tmp_dir)
            picking.write({'edi_status': 'sent'})

        return True

    def get_shipping_xml(self, picking):
        values = {
            'TradingPartnerId': picking.partner_id.trading_partnerid,
            'ShipmentIdentification': picking.name,
            'ShipDate': picking.scheduled_date and picking.scheduled_date.strftime('%Y-%m-%d'),
            'TsetPurposeCode': '00',
            'ShipNoticeDate': picking.create_date and picking.create_date.strftime('%Y-%m-%d'),
            'ShipNoticeTime': picking.create_date and picking.create_date.strftime('%H:%M:%S'),
            'ASNStructureCode': '0001',
            'BillOfLadingNumber': '123546879',
            'AppointmentNumber': '12345',
            'CurrentScheduledDeliveryDate': picking.scheduled_date and picking.scheduled_date.strftime('%Y-%m-%d'),
            'CurrentScheduledDeliveryTime': picking.scheduled_date and picking.scheduled_date.strftime('%H:%M:%S'),

            'DateTimeQualifier': '011',
            'Date': picking.scheduled_date and picking.scheduled_date.strftime('%Y-%m-%d'),

            'ReferenceQual': '',
            'ReferenceID': '',
            'Description': '',

            'NoteCode': '',
            'Note': '',

            'ContactTypeCode': 'IC',
            'ContactName': picking.partner_id.name,
            'PrimaryPhone': picking.partner_id.phone,
            'PrimaryFax': '',
            'PrimaryEmail': picking.partner_id.email,

            'addresses': self._get_shipping_address(picking),

            'StatusCode': '',
            'CarrierTransMethodCode': '',
            'CarrierAlphaCode': '',
            'CarrierRouting': '',
            'EquipmentDescriptionCode': '',
            'CarrierEquipmentNumber': '',

            'PackingMedium': 'CTN',
            'PackingMaterial': '25',
            'LadingQuantity': sum(sml.qty_done for sml in picking.move_line_ids),
            'WeightQualifier': 'G',
            'Weight': picking.weight,
            'WeightUOM': 'KG',

            'FOBPayCode': 'CC',
            'FOBLocationQualifier': '',
            'FOBLocationDescription': '',

            'QuantityTotalsQualifier': '',
            'Quantity': '',
            'QuantityUOM': '',

            # <OrderHeader> ->
            # <OrderLevel>
            'PurchaseOrderNumber': picking.sale_id.name,
            'ReleaseNumber': '',
            'PurchaseOrderDate': picking.sale_id.date_order,
            'Department': 'SPS',
            'Vendor': picking.sale_id.partner_id.vendor,
            #<QuantityAndWeight>
            'OPackingMedium': 'CTN',
            'OPackingMaterial': '25',
            'OLadingQuantity': sum(sml.qty_done for sml in picking.move_line_ids),
            'OWeightQualifier': 'G',
            'OWeight': picking.weight,
            'OWeightUOM': 'KG',

            #<PackLevel>
            'packages': self._get_packaging(picking),

            #TotalLineItemNumber
            'TotalLineItemNumber': len(picking.move_line_ids)

        }
        xml = self.env.ref('edi_sale.export_shipping_xml').render(values)
        xml = '<?xml version="1.0" encoding="utf-8"?>' + '\n' + xml.decode("utf-8")
        return xml

    def _get_shipping_address(self, order):
        return [
            {
                'AddressTypeCode': 'SF',
                'LocationCodeQualifier': '92',
                'AddressLocationNumber': '12345',
                'AddressName': order.company_id.partner_id.name,
                'Address1': order.company_id.partner_id.street,
                'Address2': order.company_id.partner_id.street2,
                'City': order.company_id.partner_id.city,
                'State': order.company_id.partner_id.state_id.code,
                'PostalCode': order.company_id.partner_id.zip,
                'Country': order.company_id.partner_id.country_id.name,
            },
            {
                'AddressTypeCode': 'ST',
                'LocationCodeQualifier': '92',
                'AddressLocationNumber': '123',
                'AddressName': order.partner_id.name,
                'Address1': order.partner_id.street,
                'Address2': order.partner_id.street2,
                'City': order.partner_id.city,
                'State': order.partner_id.state_id.code,
                'PostalCode': order.partner_id.zip,
                'Country': order.partner_id.country_id.name,
            }
        ]

    def _get_packaging(self, picking):
        res = []
        for package in picking.package_ids:
            pack = {
                'PackLevelType': 'P',
                'ShippingSerialID': '',
                'PackQualifier': '',
                'PackValue': 1,
                'PackSize': 2,
                'PackUOM': '',
                'PackingMedium': 'CTN',
                'PackingMaterial': 94,

                'items': [{
                    'LineSequenceNumber': i,
                    'BuyerPartNumber': '',
                    'VendorPartNumber': '',
                    'ConsumerPackageCode': '',
                    'GTIN': '',
                    'UPCCaseCode': '',
                    'PartNumberQual': '',
                    'PartNumber': item.product_id.default_code,
                    'OrderQty': item.quantity,
                    'OrderQtyUOM': item.product_uom_id.name,
                    'PurchasePrice': item.product_id.standard_price,
                    'ItemStatusCode': '',
                    'ShipQty': item.quantity,
                    'ShipQtyUOM': item.product_uom_id.name,
                    'ProductSizeCode': '',
                    'ProductSizeDescription': '',
                    'ProductColorCode': '',
                    'ProductColorDescription': '',
                    'ProductMaterialDescription': item.product_id.description_picking,
                    'NRFColorCode': '',
                    'NRFSizeCode': '',
                    'PackQualifier': '',
                    'PackValue': '',
                    'PackSize': '',
                    'PackUOM': '',

                    'PriceTypeIDCode': '',
                    'UnitPrice': '',
                    'ProductCharacteristicCode': '',
                    'ProductDescription': item.product_id.description,

                    'DateTimeQualifier': '',
                    'Date': '',
                    'Time': '',

                    'ReferenceQual': '',
                    'ReferenceID': '',

                    'NoteCode': '',
                    'Note': '',
                } for (i, item) in enumerate(package.quant_ids)],
            }
            res.append(pack)

        return res
