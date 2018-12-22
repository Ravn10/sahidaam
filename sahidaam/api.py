from __future__ import unicode_literals
import frappe
from frappe.utils import cint, get_gravatar,flt,format_datetime, now_datetime,add_days,today,formatdate,date_diff,getdate,get_last_day
from frappe import throw, msgprint, _
from frappe.utils.password import update_password as _update_password
from frappe.desk.notifications import clear_notifications
from frappe.utils.user import get_system_managers
from erpnext.accounts.doctype.sales_invoice.sales_invoice import make_delivery_note
import frappe.permissions
import frappe.share
import re
import string
import random
import json
import time
from datetime import datetime
from datetime import date
from datetime import timedelta
import collections
import math
import logging
from operator import itemgetter 
import traceback


@frappe.whitelist()
def app_error_log(title,error):
	d = frappe.get_doc({
			"doctype": "Custom Error Log",
			"title":str("User:")+str(title+" "+"App Name:Sahidam"),
			"error":traceback.format_exc()
		})
	d = d.insert(ignore_permissions=True)
	return d


@frappe.whitelist(allow_guest=True)
def generateResponse(_type,status=None,message=None,data=None,error=None):
	response= {}
	if _type=="S":
		status_code=''
		if status:
			response["status"]=status
		else:
			status_code=200
			response["status"]=status_code
		response["message"]=message
		response["data"]=data
	else:
		error_log=app_error_log(frappe.session.user,str(error))
		if status:
			response["status"]=int(status)
		else:
			status_code=500
			response["status"]=status_code
		if message:
			response["message"]=message
		else:
			response["message"]="Something Went Wrong"		
		response["message"]=message
		response["data"]=None
	return dict(response)
		



@frappe.whitelist(allow_guest=True)
def makeUser(first_name,last_name,email,telephone,address1,address2,zone,city,postalcode,country,password,sponser=None):
	try:
		obj=[]
		user_email=frappe.db.get_value("User",email,"name")
		if user_email:
			return generateResponse("S",message="Already Registerd",data=obj)
		
		user=frappe.get_doc(dict(
			doctype="User",
			email=email,
			first_name=first_name,
			last_name=last_name,
			phone=telephone,
			mobile_no=telephone
	
		)).insert(ignore_permissions=True)
		if user:
			_update_password(user.name,password)
			full_name=''
			if last_name:
				full_name=first_name+' '+last_name
			else:
				full_name=first_name
			result=makeCustomer(full_name,address1,address2,zone,city,postalcode,telephone,country,user.name,sponser)
			if result:
				return generateResponse("S",message="Successfully Registred",data=user)
	except Exception as e:
		return generateResponse("F",error=e)



@frappe.whitelist()
def makeCustomer(full_name,address1,address2,zone,city,postalcode,telephone,country,user,sponser=None):
	customer=frappe.get_doc(dict(
			doctype="Customer",
			customer_name=full_name,
			customer_group='Individual',
			territory='India',
			customer_type='Individual',
			user=user		
	)).insert(ignore_permissions=True)
	if customer:
		add_result=makeAddress(customer.name,address1,address2,zone,city,postalcode,'India',telephone,sponser)
		if add_result:
			return add_result
	


@frappe.whitelist()
def makeAddress(customer,address1,address2,zone,city,postalcode,country,telephone,sponser):
	doc1=frappe.get_doc({
			"docstatus": 0,
			"doctype": "Address",
			"address_type": "Billing",
			"country":str(country),
			"is_primary_address": 1,
			"is_shipping_address": 0,
			"is_your_company_address": 0,
			"links": [{
					"docstatus": 0,
					"doctype": "Dynamic Link",
					"parentfield": "links",
					"parenttype": "Address",
					"idx": 1,
					"link_doctype": "Customer",
					"link_name":customer
				}],
			"address_line1":str(address1),
			"address_line2":str(address2),
			"city": str(city),
			"pincode":str(postalcode),
			"phone":telephone,
			"gstin":"NA",
			"state_code": "NA",
			"place_of_supply": ""
			})
	address=doc1.insert(ignore_permissions=True)
	return address

@frappe.whitelist(allow_guest=True)
def getItemList():
	try:
		items=frappe.get_all("Item",filters=[["Item","show_in_website","=","1"],["Item","disabled","=","0"]],fields=["item_name", "item_code", "standard_rate","image", "description"])
		item_dict=[]
		if items:
			for item in items:
				res=checkBalance(item["item_code"])
				if res:
					if int(res[0][0])>0:
						item_dict.append(item)

		return generateResponse("S",message="Successfully Get Item List",data=item_dict)

	except Exception as e:
		return generateResponse("F",error=e)
			
					
				


def checkBalance(item_code):
	warehouse=frappe.db.get_value("Sahidaam Setting","Sahidaam Parameter", "selling_warehouse")
	return frappe.db.sql("""select qty_after_transaction from `tabStock Ledger Entry`	
			where item_code=%s and is_cancelled='No' and warehouse=%s order by posting_date desc, posting_time desc, name desc limit 1""", (item_code,warehouse))
				


@frappe.whitelist()
def makeSalesOrder(itemobj,payment_id=None):
	try:
		frappe.session.user=getUserNameId()
		
		customer=frappe.db.sql("""select name from `tabCustomer` where user=%s limit 1""",frappe.session.user)
		so_data=[]
		if customer:
			so=frappe.get_doc(dict(
				doctype="Sales Order",
				customer=customer[0][0],
				transaction_date=today(),
				delivery_date=add_days(today(),5),
				items=json.loads(itemobj)
			)).insert(ignore_permissions=True)
			if so:
				so.submit()
				makeDeliveryNote(customer[0][0],itemobj)
				return generateResponse("S",message="Successfully Order Placed",data=so)
			else:
				return generateResponse("S",message="Something Went Wrong Order Not Placed",data=so_data)
		else:
			return generateResponse("S",message="Customer Not Found For Session User",data=so_data)


	except Exception as e:
		return generateResponse("F",error=e)



@frappe.whitelist()
def makeDeliveryNote(customer,itemobj):
	try:
		dn=frappe.get_doc(dict(
				doctype="Delivery Note",
				customer=customer,
				posting_date=today(),
				items=json.loads(itemobj)
		)).insert(ignore_permissions=True)
		if dn:
			dn.submit()

	except Exception as e:
		return generateResponse("F",error=e)


@frappe.whitelist()
def getBrandName():
	try:
		brand_dict=[]
		brands=frappe.get_all("Brand",filters={},fields=["name"])
		if brands:
			return generateResponse("S",message="Brand List Found",data=brands)
		else:
			return generateResponse("S",message="Brand List Found",data=brand_dict)

	except Exception as e:
		return generateResponse("F",error=e)


@frappe.whitelist()
def getItemListBuying():
	try:
		items=frappe.get_all("Item",filters=[["Item","show_in_website","=","1"],["Item","disabled","=","0"]],fields=["item_name", "item_code", "standard_rate","image", "description"])
		item_dict=[]
		if items:
			return generateResponse("S",message="Successfully Get Item List",data=items)
		else:
			return generateResponse("S",message="Successfully Get Item List",data=item_dict)

	except Exception as e:
		return generateResponse("F",error=e)


@frappe.whitelist()
def getUserDetails():
	try:
		user=getUserNameId()
		if not user==False:
			user_doc=frappe.get_all("User",filters={'name':user},fields=["name","email","first_name","last_name","phone"])
			if user_doc:
				return generateResponse("S",message="Successfully Get User Details",data=user_doc)
			else:
				temp=[]
				return generateResponse("S",message="Successfully Get User Details",data=temp)

	except Exception as e:
		return generateResponse("F",error=e)
@frappe.whitelist()
def id_generator_otp():
   return ''.join(random.choice('0123456789') for _ in range(6))


@frappe.whitelist(allow_guest=True)
def SendOTP(email):
	try:
		otpobj=frappe.db.get("UserOTP", {"user":email})
		if otpobj:
			frappe.db.sql("""delete from tabUserOTP where user='"""+email+"""'""")
		OPTCODE=id_generator_otp()
		mess=OPTCODE+" is your Sahidaam App verification code"
		#jj=json.loads(respon)
		if email=="demo.app0110@gmail.com":
			OPTCODE = "123456"
			userOTP = frappe.get_doc({
				"doctype":"UserOTP",
				"user":email,
				"otp":OPTCODE
			})
			userOTP.flags.ignore_permissions = True
			userOTP.insert()
			return generateResponse("S",message="SMS Sent Successfully",data=email)
		else:			
			userOTP = frappe.get_doc({
				"doctype":"UserOTP",
				"user":email,
				"otp":OPTCODE
			})
			userOTP.flags.ignore_permissions = True
			userOTP.insert()
			user_message="Verification Code Sent Successfully On "+email
			res_obj={}
			res_obj["user"]=str(email)
			return generateResponse("S",message=user_message,data=res_obj)
	except Exception as e:
		return generateResponse("F",error=e)

@frappe.whitelist(allow_guest=True)
def VerifyOTPCode(email,otp):
	try:
		otpobj=frappe.db.get("UserOTP", {"user": email})
		if otpobj.otp==otp:
			temp=[]
			return generateResponse("S",message="Verified",data=temp)
		else:		
			temp=[]
			return generateResponse("S",status=417,message="Authentication Failed",data=temp)
	except Exception as e:
		return generateResponse("F",error=e)



def getUserNameId():
	try:
		user=frappe.db.sql("""select name from `tabUser` where email=%s or phone=%s""",(frappe.session.user,frappe.session.user))
		if user:
			if not user[0][0]==None:
				return user[0][0]
			else:
				return False
		else:
			return False

	except Exception as e:
		return generateResponse("F",error=e)
	

	
@frappe.whitelist()
def getConditionParameter():
	try:
		condition_doc=frappe.get_all("Condition Parameter",filters={'disable':0},fields=["name"])
		if condition_doc:
			return generateResponse("S",message="Successfully Get Parameters",data=condition_doc)
		else:
			temp=[]
			return generateResponse("S",message="Successfully Get Parameters But No Parameters Available",data=temp)
	except Exception as e:
		return generateResponse("F",error=e)
	

			
			
	
		


		

	

