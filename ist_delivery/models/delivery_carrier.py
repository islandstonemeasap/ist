# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, Warning, UserError
from odoo.addons import decimal_precision as dp
from odoo.tools import float_compare, float_round
from odoo.addons.delivery_easypost.models.easypost_request import EasypostRequest

import json
import requests
from werkzeug.urls import url_join
from odoo.tools.float_utils import float_round


class EasypostRequest(EasypostRequest):
    # # for debug purpose here
    # def _make_api_request(self, endpoint, request_type='get', data=None):
    #     return super(EasypostRequest, self)._make_api_request(endpoint, request_type=request_type, data=data)

    def _is_receiver_payment_type(self, order):
        return order and order.delivery_payment_type == 'receiver' and order.delivery_account_id
    
    def _prepare_options_payment(self, shipment_id, order):
        payment = {}
        # order should contain all the info we need in order to put in the payment account
        if self._is_receiver_payment_type(order) and order.partner_shipping_id.country_id.code and order.partner_shipping_id.zip:  # should use the address helper here
            values = {
                'type': order.delivery_payment_type,
                'account': order.delivery_account_id.account_number,
                'country': order.partner_shipping_id.country_id.code,
                'postal_code': order.partner_shipping_id.zip
            }
            for key, value in values.items():
                payment['order[shipments][%d][options][%s][%s]' % (shipment_id, 'payment', key)] = value
        return payment

    def _prepare_picking_shipments(self, carrier, picking):
        
        shipment = super(EasypostRequest, self)._prepare_picking_shipments(carrier, picking)
        
        # it is awkward but we need shipment id in order to put in payment
        shipment_id = 0
        move_lines_with_package = picking.move_line_ids.filtered(lambda ml: ml.result_package_id)
        move_lines_without_package = picking.move_line_ids - move_lines_with_package
        if move_lines_without_package:
            payment = self._prepare_options_payment(shipment_id, picking.group_id and picking.group_id.sale_id)
            shipment.update(payment)
            shipment_id += 1
        if move_lines_with_package:
            # Generate an easypost shipment for each package in picking.
            for package in picking.package_ids:
                payment = self._prepare_options_payment(shipment_id, picking.order)
                shipment.update(payment)
                shipment_id += 1
        return shipment

    def _prepare_order_shipments(self, carrier, order):
        """ Method used in order to estimate delivery
        cost for a quotation. It estimates the price with
        the default package defined on the carrier.
        e.g: if the default package on carrier is a 10kg Fedex
        box and the customer ships 35kg it will create a shipment
        with 4 packages (3 with 10kg and the last with 5 kg.).
        It ignores reality with dimension or the fact that items
        can not be cut in multiple pieces in order to allocate them
        in different packages. It also ignores customs info.
        """
        # Max weight for carrier default package
        max_weight = carrier._easypost_convert_weight(carrier.easypost_default_packaging_id.max_weight)
        # Order weight
        total_weight = carrier._easypost_convert_weight(sum([(line.product_id.weight * line.product_uom_qty) for line in order.order_line]))

        # Create shipments
        shipments = super(EasypostRequest, self)._prepare_order_shipments(carrier, order)
        if max_weight and total_weight > max_weight:
            # Integer division for packages with maximal weight.
            total_shipment = int(total_weight // max_weight)
            # Remainder for last package.
            last_shipment_weight = float_round(total_weight % max_weight, precision_digits=1)
            for shp_id in range(0, total_shipment + 1):  # double check here wth
                payment = self._prepare_options_payment(shp_id, order)
                shipments.update(payment)
        else:
            payment = self._prepare_options_payment(0, order)
            shipments.update(payment)
            
        return shipments


# Need to overload all methods in Delivery Carrier so that it calls our new EasypostRequest object here
class DeliverCarrier(models.Model):
    _inherit = 'delivery.carrier'

    def action_get_carrier_type(self):
        """ Return the list of carriers configured by the customer
        on its easypost account.
        """
        if self.delivery_type == 'easypost' and self.sudo().easypost_production_api_key:
            ep = EasypostRequest(self.sudo().easypost_production_api_key, self.log_xml)
            carriers = ep.fetch_easypost_carrier()
            if carriers:
                action = self.env.ref('delivery_easypost.act_delivery_easypost_carrier_type').read()[0]
                action['context'] = {
                    'carrier_types': carriers,
                    'default_delivery_carrier_id': self.id,
                }
                return action
        else:
            raise UserError('A production key is required in order to load your easypost carriers.')

    def easypost_rate_shipment(self, order):
        """ Return the rates for a quotation/SO."""
        ep = EasypostRequest(self.sudo().easypost_production_api_key if self.prod_environment else self.sudo().easypost_test_api_key, self.log_xml)
        response = ep.rate_request(self, order.partner_shipping_id, order.warehouse_id.partner_id, order)
        # Return error message
        if response.get('error_message'):
            return {
                'success': False,
                'price': 0.0,
                'error_message': response.get('error_message'),
                'warning_message': False
            }

        # Update price with the order currency
        rate = response.get('rate')
        if order.currency_id.name == rate['currency']:
            price = float(rate['rate'])
        else:
            quote_currency = self.env['res.currency'].search([('name', '=', rate['currency'])], limit=1)
            price = quote_currency._convert(float(rate['rate']), order.currency_id, self.env['res.users']._get_company(), fields.Date.today())

        return {
            'success': True,
            'price': price,
            'error_message': False,
            'warning_message': response.get('warning_message', False)
        }

    def easypost_send_shipping(self, pickings):
        """ It creates an easypost order and buy it with the selected rate on
        delivery method or cheapest rate if it is not set. It will use the
        packages used with the put in pack functionality or a single package if
        the user didn't use packages.
        Once the order is purchased. It will post as message the tracking
        links and the shipping labels.
        """
        res = []
        ep = EasypostRequest(self.sudo().easypost_production_api_key if self.prod_environment else self.sudo().easypost_test_api_key, self.log_xml)
        for picking in pickings:
            result = ep.send_shipping(self, picking.partner_id, picking.picking_type_id.warehouse_id.partner_id, picking=picking)
            if result.get('error_message'):
                raise UserError(_(result['error_message']))
            rate = result.get('rate')
            if rate['currency'] == picking.company_id.currency_id.name:
                price = float(rate['rate'])
            else:
                quote_currency = self.env['res.currency'].search([('name', '=', rate['currency'])], limit=1)
                price = quote_currency._convert(float(rate['rate']), picking.company_id.currency_id, self.env['res.users']._get_company(), fields.Date.today())

            # return tracking information
            carrier_tracking_link = ""
            for track_number, tracker_url in result.get('track_shipments_url').items():
                carrier_tracking_link += '<a href=' + tracker_url + '>' + track_number + '</a><br/>'

            carrier_tracking_ref = ' + '.join(result.get('track_shipments_url').keys())

            labels = []
            for track_number, label_url in result.get('track_label_data').items():
                label = requests.get(label_url)
                labels.append(('LabelEasypost-%s.%s' % (track_number, self.easypost_label_file_type), label.content))

            logmessage = (_("Shipping label for packages"))
            picking.message_post(body=logmessage, attachments=labels)
            picking.message_post(body=carrier_tracking_link)

            shipping_data = {'exact_price': price,
                             'tracking_number': carrier_tracking_ref}
            res = res + [shipping_data]
            # store order reference on picking
            picking.ep_order_ref = result.get('id')
        return res

    def easypost_get_tracking_link(self, picking):
        """ Returns the tracking links from a picking. Easypost reutrn one
        tracking link by package. It specific to easypost since other delivery
        carrier use a single link for all packages.
        """
        ep = EasypostRequest(self.sudo().easypost_production_api_key if self.prod_environment else self.sudo().easypost_test_api_key, self.log_xml)
        tracking_urls = ep.get_tracking_link(picking.ep_order_ref)
        return len(tracking_urls) == 1 and tracking_urls[0][1] or json.dumps(tracking_urls)

    def easypost_cancel_shipment(self, pickings):
        # Note: Easypost API not provide shipment/order cancel mechanism
        raise UserError(_("You can't cancel Easypost shipping."))

    def _easypost_get_services_and_product_packagings(self):
        """ Get the list of services and product packagings by carrier
        type. They are stored in 2 dict stored in 2 distinct static json file.
        The dictionaries come from an easypost doc parsing since packages and
        services list are not available with an API request. The purpose of a
        json is to replace the static file request by an API request if easypost
        implements a way to do it.
        """
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        response_package = requests.get(url_join(base_url, '/delivery_easypost/static/data/packagings_by_carriers.json'))
        response_service = requests.get(url_join(base_url, '/delivery_easypost/static/data/services_by_carriers.json'))
        packages = response_package.json()
        services = response_service.json()
        return packages, services

    @api.onchange('delivery_type')
    def _onchange_delivery_type(self):
        if self.delivery_type == 'easypost':
            self = self.sudo()
            if not self.easypost_test_api_key or not self.easypost_production_api_key:
                carrier = self.env['delivery.carrier'].search([('delivery_type', '=', 'easypost'), ('company_id', '=', self.env.user.company_id.id)], limit=1)
                if carrier.easypost_test_api_key and not self.easypost_test_api_key:
                    self.easypost_test_api_key = carrier.easypost_test_api_key
                if carrier.easypost_production_api_key and not self.easypost_production_api_key:
                    self.easypost_production_api_key = carrier.easypost_production_api_key

    def _generate_services(self, rates):
        """ When a user do a rate request easypost returns
        a rates for each service available. However some services
        could not be guess before a first API call. This method
        complete the list of services for the used carrier type.
        """
        services_name = [rate.get('service') for rate in rates]
        existing_services = self.env['easypost.service'].search_read([
            ('name', 'in', services_name),
            ('easypost_carrier', '=', self.easypost_delivery_type)
        ], ["name"])
        for service_name in set([service['name'] for service in existing_services]) ^ set(services_name):
            self.env['easypost.service'].create({
                'name': service_name,
                'easypost_carrier': self.easypost_delivery_type
            })

    def _easypost_convert_weight(self, weight):
        """ Each API request for easypost required
        a weight in pounds.
        """
        weight_uom_id = self.env['product.template']._get_weight_uom_id_from_ir_config_parameter()
        weight_in_pounds = weight_uom_id._compute_quantity(weight, self.env.ref('uom.product_uom_lb'))
        weigth_in_ounces = float_round((weight_in_pounds * 16), precision_digits=1)
        return weigth_in_ounces
