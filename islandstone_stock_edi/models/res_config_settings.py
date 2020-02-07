# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    ftp_host_wayfair = fields.Char(string='Host', default='',
                                   config_parameter='islandstone_stock_edi.ftp_host_wayfair')
    ftp_port_wayfair = fields.Integer(string='Port', required=True, default=22,
                                      config_parameter='islandstone_stock_edi.ftp_port_wayfair')
    ftp_protocol_wayfair = fields.Selection(selection=[('ftp', 'FTP - File Transfer Protocol'),
                                                       ('sftp', 'SFTP - SSH File Transfer Protocol')],
                                            config_parameter='islandstone_stock_edi.ftp_protocol_wayfair',
                                            string='Protocol', required=True, default='ftp')
    ftp_login_wayfair = fields.Char(string='Username', required=True, default='',
                                    config_parameter='islandstone_stock_edi.ftp_login_wayfair')
    ftp_password_wayfair = fields.Char(string='Password', required=True, default='',
                                       config_parameter='islandstone_stock_edi.ftp_password_wayfair')

    email_wayfair = fields.Char(string='Email', required=True, default='',
                                    config_parameter='islandstone_stock_edi.email_wayfair')
