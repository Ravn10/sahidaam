# -*- coding: utf-8 -*-
# Copyright (c) 2018, Crisco Consulting and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.website.website_generator import WebsiteGenerator
from frappe import throw, msgprint, _


class PriceCalculator(WebsiteGenerator):
    def validate(self):
        if self.parameters:
            return frappe.msgprint(_("OTP Secret has been reset. Re-registration will be required on next login."))
