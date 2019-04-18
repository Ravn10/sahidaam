from __future__ import unicode_literals
import frappe
from frappe.utils import cint, get_gravatar,flt,format_datetime, now_datetime,add_days,today,formatdate,date_diff,getdate,get_last_day
from frappe import throw, msgprint, _
from frappe.utils.password import update_password as _update_password
from frappe.desk.notifications import clear_notifications
from frappe.utils.user import get_system_managers
from erpnext.accounts.doctype.sales_invoice.sales_invoice import make_delivery_note
from frappe.core.doctype.communication.email import make
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
def makeUser(first_name,last_name,email,telephone,address1,address2,city,postalcode,password,state=None,country=None,zone=None,sponser=None):
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
			mobile_no=telephone,
			send_welcome_email=0
	
		)).insert(ignore_permissions=True)
		if user:
			_update_password(user.name,password)
			full_name=''
			if last_name:
				full_name=first_name+' '+last_name
			else:
				full_name=first_name
			result=makeCustomer(full_name,address1,address2,city,postalcode,user.name,telephone,state)
			if result:
				return generateResponse("S",message="Successfully Registred",data=user)
	except Exception as e:
		return generateResponse("F",error=e)



@frappe.whitelist()
def makeCustomer(full_name,address1,address2,city,postalcode,user,telephone=None,state=None):
	customer=frappe.get_doc(dict(
			doctype="Customer",
			customer_name=full_name,
			customer_group='Individual',
			territory='India',
			customer_type='Individual',
			user=user		
	)).insert(ignore_permissions=True)
	if customer:
		add_result=makeAddress(customer.name,address1,address2,city,postalcode,telephone,state)
		if add_result:
			return add_result
	


@frappe.whitelist()
def makeAddress(customer,address1,address2,city,postalcode,telephone=None,state=None):
	doc1=frappe.get_doc({
			"docstatus": 0,
			"doctype": "Address",
			"address_type": "Billing",
			"country":'India',
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
			"state":str(state),
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
def id_generator_otp():
   return ''.join(random.choice('0123456789') for _ in range(6))


@frappe.whitelist(allow_guest=True)
def SendOTP(email,forgot_password=None):
	try:
		if forgot_password==None:	
			obj=[]
			user_email=frappe.db.get_value("User",email,"email")
			if user_email:
				return generateResponse("S",message="Already Registerd",data=obj)
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
			frappe.sendmail(recipients= email,subject='Sahidaam OTP',message=mess)
			return generateResponse("S",message="SMS Sent Successfully",data=res_obj)
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

@frappe.whitelist(allow_guest=True)
def forgotPassword(email,password):
	try:
		_update_password(email,password)
		temp=[]
		return generateResponse("S",message="Password Updated Succesfully",data=temp)

	except Exception as e:
		return generateResponse("F",error=e)

@frappe.whitelist()
def getSalesOrderHistory():
	try:
		user=getUserNameId()
		so_list=frappe.db.sql("""select so.name from `tabSales Order` as so inner join `tabCustomer` as cust on so.customer=cust.name where cust.user=%s""",user)
		so_obj=[]
		if len(so_list)>0:
			for row in so_list:
				so=frappe.get_doc("Sales Order",row[0])
				so_obj.append(so)
				
			return generateResponse("S",message="Sales Order List Get Succesfully",data=so_obj)
		else:
			temp=[]
			return generateResponse("S",message="Sales Order List Get Succesfully",data=temp)
	except Exception as e:
		return generateResponse("F",error=e)

@frappe.whitelist(allow_guest=True)
def getBrandName(category):
	try:

		brand_dict=[]
		brands=frappe.get_all("Brand",filters=[["Website Item Group","item_group","=",category]],fields=["name"])
		if brands:
			return generateResponse("S",message="Brand List Found",data=brands)
		else:
			return generateResponse("S",message="Brand List Found",data=brand_dict)

	except Exception as e:
		return generateResponse("F",error=e)



@frappe.whitelist(allow_guest=True)
def getCategories():
	try:
		itemCategories=frappe.get_all("Item Group",filters=[["Item Group","show_in_sell","=","1"]],fields=["name"])
		item_dict=[]
		if itemCategories:
			return generateResponse("S",message="Successfully Get Item List",data=itemCategories)
		else:
			return generateResponse("S",message="Successfully Get Item List",data=item_dict)

	except Exception as e:
		return generateResponse("F",error=e)

		



@frappe.whitelist(allow_guest=True)
def getModelList(brand,category):
	try:
		items=frappe.get_all("Item",filters=[["Item","brand","=",brand],["Item","item_group","=",category],["Item","is_purchase_item","=","1"]],fields=["item_name", "item_code"])
		item_dict=[]
		if items:
			return generateResponse("S",message="Successfully Get Item List",data=items)
		else:
			return generateResponse("S",message="Successfully Get Item List",data=item_dict)

	except Exception as e:
		return generateResponse("F",error=e)


@frappe.whitelist(allow_guest=True)
def getConditionParameter(model):
	try:
		condition=[]
		condition_doc=frappe.get_doc("Model Wise Parameter",model)
		if condition_doc:
			for cond in condition_doc.condition_parameter_device:
				condition_json={}
				condition_json["condition"]=cond.parameter
				condition.append(condition_json)

		if len(condition)>0:
			return generateResponse("S",message="Successfully Get Condition Parameter",data=condition)
		else:
			temp=[]
			return generateResponse("S",message="Successfully Get Condition Parameter",data=temp)

	except Exception as e:
		return generateResponse("F",error=e)


@frappe.whitelist(allow_guest=True)
def getEstimateValue(model,parameter_obj=None):
	try:
		#parameter_obj='[{"condition":"Switch On","check":"No"},{"condition":"Bettery Working","check":"Yes"}]'
		condition_doc=frappe.get_doc("Model Wise Parameter",model)
		if condition_doc:
			buying_rate=condition_doc.buying_rate
			for param in json.loads(parameter_obj):
				for cond in condition_doc.condition_parameter_device:
					if param["condition"]==cond.parameter:
						if param["check"]=="Yes":
							if cond.parameter=="Dead":
								if condition_doc.buying_rate>=10000:
									return generateResponse("S",message="Successfully Get Estimate Value",data=1500)
								else:
									return generateResponse("S",message="Successfully Get Estimate Value",data=750)
							else:
								buying_rate=buying_rate+(flt(condition_doc.buying_rate)*flt(cond.yes)/100)
						if param["check"]=="No":
							if cond.no>=100:
								return generateResponse("S",message="Successfully Get Estimate Value",data=0)
							buying_rate=buying_rate-(flt(condition_doc.buying_rate)*flt(cond.no)/100)

			return generateResponse("S",message="Successfully Get Estimate Value",data=buying_rate)
						
			

	except Exception as e:
		return generateResponse("F",error=e)



			

	
@frappe.whitelist()
def getConditionParameter1():
	try:
		condition_doc=frappe.get_all("Condition Parameter",filters={'disable':0},fields=["name"])
		if condition_doc:
			return generateResponse("S",message="Successfully Get Parameters",data=condition_doc)
		else:
			temp=[]
			return generateResponse("S",message="Successfully Get Parameters But No Parameters Available",data=temp)
	except Exception as e:
		return generateResponse("F",error=e)


@frappe.whitelist(allow_guest=True)
def makeUserFromSocialLogin(email,auth_token,sl_type,first_name=None,last_name=None,mobile=None):
	try:
		if sl_type=="Google":
			obj=[]
			user_email=frappe.db.get_value("User",email,"name")
			if user_email:
				frappe.db.set_value("User",email,"google_userid",auth_token)
				_update_password(email,auth_token)
				user_obj={}
				user_obj["user"]=email
				user_obj["password"]=auth_token
				obj.append(user_obj)
				return generateResponse("S",message="Login Details",data=obj)
		
			user=frappe.get_doc(dict(
				doctype="User",
				email=email,
				first_name=first_name,
				last_name=last_name,
				phone=mobile if not mobile==None else '',
				mobile_no=mobile if not mobile==None else '',
				google_userid=auth_token
	
			)).insert(ignore_permissions=True)
			if user:
				_update_password(user.name,auth_token)
				user_obj={}
				user_obj["user"]=email
				user_obj["password"]=auth_token
				obj.append(user_obj)
				return generateResponse("S",message="Login Details",data=obj)
				#result=makeCustomer(full_name,address1,address2,zone,city,postalcode,telephone,country,user.name,sponser)
				#if result:


		if sl_type=="Facebook":
			obj=[]
			user_email=frappe.db.get_value("User",email,"name")
			if user_email:
				frappe.db.set_value("User",email,"fb_userid",auth_token)
				_update_password(email,auth_token)
				user_obj={}
				user_obj["user"]=email
				user_obj["password"]=auth_token
				obj.append(user_obj)
				return generateResponse("S",message="Login Details",data=obj)
		
			user=frappe.get_doc(dict(
				doctype="User",
				email=email,
				first_name=first_name,
				last_name=last_name,
				phone=mobile if not mobile==None else '',
				mobile_no=mobile if not mobile==None else '',
				fb_userid=auth_token
	
			)).insert(ignore_permissions=True)
			if user:
				_update_password(user.name,auth_token)
				user_obj={}
				user_obj["user"]=email
				user_obj["password"]=auth_token
				obj.append(user_obj)
				return generateResponse("S",message="Login Details",data=obj)
					
	except Exception as e:
		return generateResponse("F",error=e)


@frappe.whitelist()
def getUserDetails():
	try:
		user=getUserNameId()
		if not user==False:
			user_doc=frappe.get_all("User",filters={'name':user},fields=["name","email","first_name","last_name","phone"])
			if user_doc:
				customer=getCustomerForUser()
				if customer==True:
					user_doc[0]["address"]=True
				else:
					user_doc[0]["address"]=False
				return generateResponse("S",message="Successfully Get User Details",data=user_doc)
			else:
				temp=[]
				return generateResponse("S",message="Successfully Get User Details",data=temp)

	except Exception as e:
		return generateResponse("F",error=e)


@frappe.whitelist()
def getCustomerForUser():
	try:
		user=getUserNameId()
		if not user==False:
			customer_doc=frappe.get_all("Customer",filters={'user':user},fields=["name"])
			if len(customer_doc)>0:
				return True
			else:
				return False

	except Exception as e:
		return generateResponse("F",error=e)



@frappe.whitelist()
def addAddress(address1,address2,city,postalcode,state):
	try:
		user=getUserNameId()
		if not user==False:
			user_doc=frappe.get_doc("User",user)
			full_name=''
			if user_doc.last_name:
				full_name=user_doc.first_name+' '+user_doc.last_name
			else:
				full_name=user_doc.first_name
			result=makeCustomer(full_name,address1,address2,city,postalcode,user_doc.name,state)
			if result:
				return generateResponse("S",message="Successfully Added",data=result)
			else:
				temp=[]
				return generateResponse("S",message="Not Added",data=temp)
		

	except Exception as e:
		return generateResponse("F",error=e)


@frappe.whitelist()
def stockBalance(item_code):
	warehouse=frappe.db.get_value("Sahidaam Setting","Sahidaam Parameter", "selling_warehouse")
	balance=frappe.db.sql("""select qty_after_transaction from `tabStock Ledger Entry`	
			where item_code=%s and is_cancelled='No' and warehouse=%s order by posting_date desc, posting_time desc, name desc limit 1""", (item_code,warehouse))
	if not balance[0][0]==None:
		return balance[0][0]
	else:
		return 0




		



	



	

			
			
	
		


		

	

