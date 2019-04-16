# -*- coding: utf-8 -*-
# Copyright (c) 2016, Helio de Jesus and contributors
# For license information, please see license.txt

#Date Changed: 16/04/2019

from __future__ import unicode_literals

#from __future__ import unicode_literals
import sys
reload (sys)
sys.setdefaultencoding('utf8')


from frappe.model.document import Document
import frappe.model
import frappe
from frappe.utils import nowdate, cstr, flt, cint, now, getdate
from frappe import throw, _
from frappe.utils import formatdate, encode
from frappe.model.naming import make_autoname
from frappe.model.mapper import get_mapped_doc

from frappe.email.doctype.email_group.email_group import add_subscribers

from frappe.contacts.doctype.address.address import get_company_address # for make_facturas_venda
from frappe.model.utils import get_fetch_values

#import json, os 
#import csv, codecs, cStringIO

import csv 
import json

import xml.etree.ElementTree as ET
from datetime import datetime, date, timedelta




@frappe.whitelist()
def check_caixa_aberto():

	if (frappe.db.sql("""select name from `tabCaixa de Registo` WHERE status_caixa ='Aberto' """, as_dict=False)) != ():
		print "AAAAAAAA"
		return frappe.db.sql("""select name from `tabCaixa de Registo` WHERE status_caixa ='Aberto' """, as_dict=False)
	elif (frappe.db.sql("""select name from `tabCaixa de Registo` WHERE status_caixa ='Em Curso' """, as_dict=False)) != ():
		return frappe.db.sql("""select name from `tabCaixa de Registo` WHERE status_caixa ='Em Curso' """, as_dict=False)
		print "BBBBBBBBB"
		print frappe.db.sql("""select name from `tabCaixa de Registo` WHERE status_caixa ='Aberto' """, as_dict=False)	

@frappe.whitelist()
def caixa_movimentos_in(start,caixa,fecho):

		total_tpa = 0
		total_ccorrente = 0
		total_caixa = 0
		recalcula = False
		for d in  frappe.db.sql("""select hora_atendimento, name,total_servicos,pagamento_por, status_atendimento, bar_tender, company from `tabAtendimento Bar` where status_atendimento ='Fechado' and hora_atendimento >= %(start)s and hora_atendimento <= %(end)s """, {"start": start,"end": frappe.utils.now()	}, as_dict=True):
			
			print "MOVIMENTOS BAR RESTAURANTE +++++++++++++++++++++++++++++++"
			ddd = make_autoname('MOV-' + '.#####')
			if len(frappe.db.sql("SELECT name,descricao_movimento from tabMovimentos_Caixa WHERE descricao_movimento=%(mov)s""",{"mov":d.name}, as_dict=True))==0:
				frappe.db.sql("INSERT into tabMovimentos_Caixa (name, docstatus, parent, parenttype, parentfield, tipo_pagamento, descricao_movimento, valor_pago, hora_atendimento, creation, modified, usuario_movimentos, company) values (%s,0,%s,'Caixa de Registo','movimentos_caixa',%s,%s,%s,%s,%s,%s,%s,%s) ",(ddd, caixa, d.pagamento_por ,d.name, d.total_servicos, d.hora_atendimento, frappe.utils.now(), frappe.utils.now(),d.bar_tender,d.company))
				total_caixa = d.total_servicos+total_caixa
				if (d.pagamento_por == "TPA"):
					total_tpa = d.total_servicos+total_tpa
				
				if (d.pagamento_por == "Conta-Corrente"):
					total_ccorrente = d.total_servicos+total_ccorrente
			else:
				#Recalcula o Caixa ....
				recalcula = True
				total_caixa = d.total_servicos+total_caixa
				if (d.pagamento_por == "TPA"):
					total_tpa = d.total_servicos+total_tpa
				
				if (d.pagamento_por == "Conta-Corrente"):
					total_ccorrente = d.total_servicos+total_ccorrente

		print "Abre Caixa"
		print total_caixa
		reser = frappe.get_doc("Caixa de Registo",caixa)
		if (total_caixa > 1) and (reser.amount_caixa == 0):
			if (recalcula == False):
				reser.amount_caixa = total_caixa+reser.amount_caixa
				reser.amount_tpa = total_tpa+reser.amount_tpa
				reser.amount_conta_corrente = total_ccorrente+reser.amount_conta_corrente
			else:
				reser.amount_caixa = total_caixa
				reser.amount_tpa = total_tpa
				reser.amount_conta_corrente = total_ccorrente

			reser.status_caixa='Em Curso'
			reser.save()
		elif (total_caixa > 1) and (reser.amount_caixa >= 0):
			if (recalcula == False):
				reser.amount_caixa = total_caixa+reser.amount_caixa
				reser.amount_tpa = total_tpa+reser.amount_tpa
				reser.amount_conta_corrente = total_ccorrente+reser.amount_conta_corrente
			else:
				reser.amount_caixa = total_caixa
				reser.amount_tpa = total_tpa
				reser.amount_conta_corrente = total_ccorrente

			reser.save()

		print fecho
		print reser.status_caixa
		if (fecho==2):
			reser.status_caixa='Fechado'
			reser.save()

		

		return total_caixa



@frappe.whitelist()
def get_taxa_ipc():
	#IPC to temp account 37710000

	#locate account 37710000 instead of 34210000
	j= frappe.db.sql(""" select name, description, account_head, parent  from `tabSales Taxes and Charges` where account_head like '3771%' and parenttype ='Sales Taxes and Charges Template' """,as_dict=True)

	print " LISTA TAXE IPC conta 3771"
	print j	

	return j

@frappe.whitelist()
def get_taxa_ipc_1():
	#Original

	#locate account 34210000
	j= frappe.db.sql(""" select name, description, account_head, parent  from `tabSales Taxes and Charges` where account_head like '3421%' and parenttype ='Sales Taxes and Charges Template' """,as_dict=True)

	print " LISTA TAXE IPC conta 3421"
	print j	

	return j


@frappe.whitelist()
def get_contab_taxa_retencao(empresa,fornclien = 'Supplier'):
	#locate account 34130000 or plano contif 2.80.20.20.30 - Ret Fonte a Pagar - Imposto Industrial
	print (empresa).encode('utf-8')
	if (empresa):
		if (fornclien == 'Supplier'):
			j= frappe.db.sql(""" select name, account_name from `tabAccount` where company = %s and account_name like '3413%%'  """,(empresa),as_dict=True)
			print " LISTA CONTAB TAXA RETENCAO conta 3413"
		else:
			j= frappe.db.sql(""" select name, account_name from `tabAccount` where company = %s and account_name like '3414%%'  """,(empresa),as_dict=True)
			print " LISTA CONTAB TAXA RETENCAO conta 3414"
		print j	

		# ****************** Still missing aqui qual a conta para o cliente e para fornecedor
		if (j==[]):
			#Plano CONTIF
			j= frappe.db.sql(""" select name, account_name from `tabAccount` where company = %s and account_name like '2.80.20.20.30%%' """,(empresa),as_dict=True)

			print " LISTA CONTAB TAXA RETENCAO conta 2.80.20.20.20"
			print j	

	return j if (j) else None

@frappe.whitelist()
def get_compras_taxa_retencao():
	#locate account 34130000 or plano contif 2.80.20.20.30 - Ret Fonte a Pagar - Imposto Industrial

	j= frappe.db.sql(""" select name, description, account_head, parent  from `tabPurchase Taxes and Charges` where account_head like '3413%' and parenttype ='Purchase Taxes and Charges Template' """,as_dict=True)

	print " LISTA COMPRA TAXA RETENCAO conta 3413"
	print j	
	if (j==[]):
		#Plano CONTIF
		j= frappe.db.sql(""" select name, description, account_head, parent  from `tabPurchase Taxes and Charges` where account_head like '2.80.20.20.30%' and parenttype ='Purchase Taxes and Charges Template' """,as_dict=True)

		print " LISTA COMPRA TAXA RETENCAO conta 2.80.20.20.20"
		print j	

	return j

@frappe.whitelist()
def get_vendas_taxa_retencao():
	#locate account 34140000 por liquidar pelo Cliente
	j= frappe.db.sql(""" select name, description, account_head, parent  from `tabSales Taxes and Charges` where account_head like '3414%' and parenttype ='Sales Taxes and Charges Template' """,as_dict=True)

	print " LISTA TAXA RETENCAO conta 3414"
	print j	
	if (j==[]):
		#Plano CONTIF
		j= frappe.db.sql(""" select name, description, account_head, parent  from `tabSales Taxes and Charges` where account_head like '2.80.20.20.30%' and parenttype ='Sales Taxes and Charges Template' """,as_dict=True)

		print " LISTA COMPRA TAXA RETENCAO conta 2.80.20.20.20"
		print j	

	return j

@frappe.whitelist()
def get_taxa_retencao():
	# POR REMOVER MAIS TARDE  **********************
	#locate account 34130000

	#Account 3413 ou 3414
	j= frappe.db.sql(""" select name, description, account_head, parent  from `tabSales Taxes and Charges` where account_head like '3413%' and parenttype ='Sales Taxes and Charges Template' """,as_dict=True)

	print " LISTA TAXA RETENCAO conta 3413"
	print j	
	if (j==[]):
		#Plano CONTIF
		j= frappe.db.sql(""" select name, description, account_head, parent  from `tabSales Taxes and Charges` where account_head like '2.80.20.20.30%' and parenttype ='Sales Taxes and Charges Template' """,as_dict=True)

		print " LISTA COMPRA TAXA RETENCAO conta 2.80.20.20.20"
		print j	

	return j

@frappe.whitelist()
def get_lista_retencoes():
	j= frappe.db.sql(""" SELECT name, descricao, percentagem, metade_do_valor from `tabRetencoes` """,as_dict=True)

	print " LISTA RETENCOES"
	print j	
	return j



@frappe.whitelist()
def get_lista_taxas_vendas():
	j= frappe.db.sql(""" select name, description  from `tabSales Taxes and Charges` """,as_dict=True)

	print " LISTA TAXES e CHARGES"
	print j	
	return j


@frappe.whitelist()
def get_supplier_retencao(fornecedor,fornclien = 'Supplier'):
	"""
		Looks for Supplier otherwise for Customer
	"""
	if (fornclien == 'Supplier'):
		j= frappe.db.sql(""" select name,que_retencao,retencao_na_fonte from `tabSupplier` where retencao_na_fonte=1 and name = %s """,fornecedor,as_dict=True)
	else:
		j= frappe.db.sql(""" select name,que_retencao,retencao_na_fonte from `tabCustomer` where retencao_na_fonte=1 and name = %s """,fornecedor,as_dict=True)


	print (fornclien," com RETENCAO")
	print j	
	return j





# 
# convert number to words 
# 
def in_words_pt(integer, in_million=True): 
	""" 
	Returns string in words for the given integer. 
	""" 
	n=int(integer) 
 	known = {0: 'zero', 1: 'um', 2: 'dois', 3: 'três', 4: 'quarto', 5: 'cinco', 6: 'seis', 7: 'sete', 8: 'oito', 9: 'novo', 10: 'dez', 11: 'onze', 12: 'doze', 13: 'treze', 14: 'catorze', 15: 'quinze', 16: 'dezaseis', 17: 'dezasete', 18: 'dezoito',
19: 'dezanove', 20: 'vinte', 30: 'trinta', 40: 'quarenta', 50: 'cinquenta', 60: 'sessenta', 70: 'setenta', 80: 'oitenta', 90: 'noventa'} 


	def psn(n, known, xpsn): 
		import sys; 
		if n in known: return known[n] 
		bestguess, remainder = str(n), 0 

 
		if n<=20: 
			webnotes.errprint(sys.stderr) 
			webnotes.errprint(n) 
			webnotes.errprint("Como isto aconteceu?") 
			assert 0 
		elif n < 100: 
			bestguess= xpsn((n//10)*10, known, xpsn) + '-' + xpsn(n%10, known, xpsn) 
			return bestguess 
		elif n < 1000: 
			bestguess= xpsn(n//100, known, xpsn) + ' ' + 'cem' 
			remainder = n%100 
		else: 
			if in_million: 
				if n < 1000000: 
					bestguess= xpsn(n//1000, known, xpsn) + ' ' + 'mil' 
					remainder = n%1000 
				elif n < 1000000000: 
					bestguess= xpsn(n//1000000, known, xpsn) + ' ' + 'milhões' 
					remainder = n%1000000 
				else: 
					bestguess= xpsn(n//1000000000, known, xpsn) + ' ' + 'bilhões' 
					remainder = n%1000000000 
			else: 
				if n < 100000: 
					bestguess= xpsn(n//1000, known, xpsn) + ' ' + 'mil' 
					remainder = n%1000 
				elif n < 10000000: 
					bestguess= xpsn(n//100000, known, xpsn) + ' ' + 'cem mil' 
					remainder = n%100000 
				else: 
					bestguess= xpsn(n//10000000, known, xpsn) + ' ' + 'dez milhões' 
					remainder = n%10000000 
		if remainder: 
			if remainder >= 100: 
				comma = ',' 
			else: 
				comma = '' 
			return bestguess + comma + ' ' + xpsn(remainder, known, xpsn) 
		else: 
			return bestguess 


	return psn(n, known, psn) 

@frappe.whitelist()
def get_sample_data():

	return frappe.db.sql("""select * from `tabJournal Entry` """, as_dict=False)

@frappe.whitelist()
def get_escola_ginasio():

	#print frappe.db.get_value("Modulo Ginasio",None,"mod_escola_ginasio")
	print frappe.get_value("Modulo Ginasio",None,"mod_escola_ginasio")
	return frappe.get_value("Modulo Ginasio",None,"mod_escola_ginasio")
	#return frappe.db.get_value("Modulo Ginasio",None,"mod_escola_ginasio")


@frappe.whitelist()
def get_escola_config():


	print frappe.get_value("School Settings",None,"current_academic_year")
	print frappe.get_value("School Settings",None,"current_academic_term")
	return frappe.get_value("School Settings",None,"current_academic_year"), frappe.get_value("School Settings",None,"current_academic_term")

@frappe.whitelist()
def get_cursos(programa):
	return frappe.db.sql('''select course, course_name from `tabProgram Course` where parent = %s''', (programa), as_dict=1)


@frappe.whitelist()
def set_fee_pago(propina,fatura):

	pago = frappe.get_doc('Fees',propina)
	print 'propina paga'
	print pago.outstanding_amount
	
	factura = frappe.get_doc('Sales Invoice',fatura) #self.format_as_links(ss.name)[0]

	if pago.outstanding_amount:
		#PAID
		if pago.grand_total:
			frappe.db.set_value("Fees", propina, "paid_amount", pago.grand_total)
		else:
			frappe.db.set_value("Fees", propina, "paid_amount", pago.total_amount)
		frappe.db.set_value("Fees", propina, "outstanding_amount", 0)
		frappe.db.set_value("Fees", propina, "sales_invoice", fatura)
#		pago.paid_amount = pago.total_amount
#		pago.outstanding_amount = 0
#		pago.save()




@frappe.whitelist()
def get_programa_enroll(aluno):

	print frappe.model.frappe.get_all('Program Enrollment',filters={'student':aluno},fields=['name','student_name','program'])

	print ('segundo ')

	print frappe.db.sql(""" select p.name,p.student,p.student_name,p.program, f.parent,f.fee_structure,f.amount from `tabProgram Fee` f JOIN `tabProgram Enrollment` p on f.parent = p.name where p.student = %s; """, (aluno),as_dict=False)

	return frappe.db.sql(""" select p.name,p.student,p.student_name,p.program, f.parent,f.fee_structure,f.amount from `tabProgram Fee` f JOIN `tabProgram Enrollment` p on f.parent = p.name where p.student = %s; """, (aluno),as_dict=True)



@frappe.whitelist()
def estudante_enroll(source_name):
	"""Creates a Student Record and returns a Program Enrollment.

	:param source_name: Student Applicant.
	"""
	frappe.publish_realtime('enroll_student_progress', {"progress": [1, 4]}, user=frappe.session.user)
	student = get_mapped_doc("Student Applicant", source_name,
		{"Student Applicant": {
			"doctype": "Student",
			"field_map": {
				"name": "student_applicant"
			}
		}}, ignore_permissions=True)

	student.save()

	frappe.db.set_value('Student',student.name,'_user_tags',student.title[0])
	frappe.db.commit()


	#Cria Customer	
	cliente = get_mapped_doc("Student Applicant", source_name,
		{"Student Applicant": {
			"doctype": "Customer",
			"field_map": {
				"name": "student_applicant"
			}
		}}, ignore_permissions=True)

	cliente.customer_name = student.title
	cliente.customer_group = 'Individual'
	cliente.territory = 'Angola'
	cliente.language = 'pt'
	print "ALUNO GENDER"
	print _(student.gender)

	cliente.save()

	frappe.db.set_value('Customer',cliente.name,'_user_tags',student.title[0])
	frappe.db.commit()
	

	contacto = frappe.new_doc("Contact")
	contacto.name = student.title
	contacto.first_name = student.first_name	
	contacto.middle_name = student.middle_name	
	contacto.last_name = student.last_name	
	contacto.gender = student.gender
	contacto.email_id = student.student_email_id
	contacto.mobile_no = student.student_mobile_number
	#contacto.parent

	contacto.status = 'Passive'
	contacto.save()


	contacto_link = frappe.new_doc('Dynamic Link')
	contacto_link.parent = contacto.name
	contacto_link.parentfield ='links'
	contacto_link.parenttype ='Contact'
	contacto_link.link_title = student.title
	contacto_link.link_doctype ='Customer'
	contacto_link.link_name = student.title

	contacto_link.save()


	program_enrollment = frappe.new_doc("Program Enrollment")
	program_enrollment.student = student.name
	program_enrollment.student_name = student.title
	program_enrollment.program = frappe.db.get_value("Student Applicant", source_name, "program")
	frappe.publish_realtime('enroll_student_progress', {"progress": [4, 4]}, user=frappe.session.user)	
	return program_enrollment


@frappe.whitelist()
def update_email_group(doctype, name):
	if not frappe.db.exists("Email Group", name):
		email_group = frappe.new_doc("Email Group")
		email_group.title = name
		email_group.save()
	email_list = []
	students = []
	if doctype == "Student Group":
		students = get_student_group_students(name)
	for stud in students:
		email = frappe.db.get_value("Student", stud.student, "student_email_id")
		print email
		if email:
			email_list.append(email)	
	add_subscribers(name, email_list)

@frappe.whitelist()
def get_student_group_students(student_group, include_inactive=0):
	"""Returns List of student, student_name in Student Group.

	:param student_group: Student Group.
	"""
	if include_inactive:
		students = frappe.get_list("Student Group Student", fields=["student", "student_name"] ,
			filters={"parent": student_group}, order_by= "group_roll_number")
	else:
		students = frappe.get_list("Student Group Student", fields=["student", "student_name"] ,
			filters={"parent": student_group, "active": 1}, order_by= "group_roll_number")
	return students

@frappe.whitelist()
def css_per_user(username=frappe.session.user):
	""" Should load the CSS created on app theme  per user
	
	:param username: currently logged or logging.
	"""

	print 'css per user ', username

	#should look for user folder with CSS and load if not use starndard CSS
	#assets/css/username/.css
	
	#assets/angola_erp/css/erpnext/bootstrap.css
	
	"""	body {
		  font-family: "Helvetica Neue", Helvetica, Arial, "Open Sans", sans-serif;
		  font-size: 10px;
		  line-height: 1.42857143;
		  color: #36414c;
		  background-color: #ff5858;
		}
	"""		
	#script = open ("./assets/angola_erp/js/carregarCSS.js","r")
	#script_content = script.read()

	#script.close()

	#js.exec(script_content)
	

@frappe.whitelist()
def get_versao_erp():
	""" Due to School renamed to Education ....
	
	"""

	print frappe.get_attr("erpnext"+".__version__")

	return frappe.get_attr("erpnext"+".__version__")

@frappe.whitelist()
def cancel_gl_entry_fee(fee_number):
	"""Cancel the GL Entry made by FEE... ONLY if user makes SALES INVOICE LATER FOR ALL GROUP OF Fees...

	:param fee_number.
	"""

	print "Cancela GL ENTRY NO FEE"
	print "Cancela GL ENTRY NO FEE"
	frappe.db.sql('''UPDATE `tabGL Entry` set docstatus = 2 where voucher_no = %s''', (fee_number), as_dict=1)

	print "APAGA GL ENTRY NO FEE"
	print "APAGA GL ENTRY NO FEE"
	frappe.db.sql('''DELETE from `tabGL Entry` where voucher_no = %s''', (fee_number), as_dict=1)


@frappe.whitelist()
def get_dominios_activos():
	"""Returns Active domains .... 

	:param .
	"""

	print "DOMINIOS ACTIVOS"
	print "DOMINIOS ACTIVOS"
	print "DOMINIOS ACTIVOS"
	print "DOMINIOS ACTIVOS"

	tmp = frappe.get_single('Domain Settings').active_domains

	#frappe.get_single('Domain Settings')

	if tmp:
		return tmp #frappe.cache().get_value('active_domains',tmp)
	else:
		return None


@frappe.whitelist()
def get_cliente_address(cliente):

	clientes = frappe.get_doc("Customer",cliente)
	if clientes:
		link1 = frappe.get_all('Dynamic Link',filters={'link_doctype':'Customer','link_name':cliente,'parenttype':'Address'}, fields=['parent'])
		if link1:
			endereco = frappe.get_doc('Address',link1[0].parent)
			return endereco


@frappe.whitelist()
def get_contracto_numero(matricula):

	link1 =  frappe.model.frappe.get_all('Contractos Rent',filters={'matricula':matricula,'docstatus':1,'status_contracto':'Activo'},fields=['contracto_numero','local_de_saida','local_previsto_entrada','data_de_saida','devolucao_prevista'])
	if link1:
		return link1

@frappe.whitelist()
def get_all_contracto_numero():

	link1 =  frappe.model.frappe.get_all('Contractos Rent',filters={'matricula':['like', '%'],'docstatus':1},fields=['matricula','contracto_numero','local_de_saida','local_previsto_entrada','data_de_saida','devolucao_prevista','kms_out','combustivel','deposito_out'])
	if link1:
		return link1
				


@frappe.whitelist()
def checkin_ficha_tecnica(source_name, target_doc = None):

	#Copy a Ficha Tecnica para o mesmo....
	fichatecnica = get_mapped_doc("Ficha Tecnica da Viatura", source_name,
		{"Ficha Tecnica da Viatura": {
			"doctype": "Ficha Tecnica da Viatura",
			"field_map": {
				"name": "name",

			}
		}}, target_doc,ignore_permissions=True)

	return fichatecnica


@frappe.whitelist()
def actualiza_ficha_tecnica(source_name):

	ficha = frappe.db.sql("""select name, matricula_veiculo, entrada_ou_saida_viatura from `tabFicha Tecnica da Viatura` WHERE entrada_ou_saida_viatura = "Saida" and matricula_veiculo = %s """, (source_name), as_dict=False)

	if ficha:
		print(ficha[0][0])
		ficha1 = frappe.get_doc("Ficha Tecnica da Viatura",ficha[0][0])
	
		print('aquiaaaaaaa')

		ficha1.status_viatura = "Devolvida"
		ficha1.save()		


@frappe.whitelist()
def get_termos(source_name):
	termos = frappe.db.sql("""select name, terms from `tabTerms and Conditions` WHERE name = %s """, (source_name), as_dict=False)
	print(termos)
 	if termos:
		return termos


def get_invoiced_qty_map(delivery_note):
	"""returns a map: {dn_detail: invoiced_qty}"""
	invoiced_qty_map = {}

	for dn_detail, qty in frappe.db.sql("""select dn_detail, qty from `tabSales Invoice Item`
		where delivery_note=%s and docstatus=1""", delivery_note):
			if not invoiced_qty_map.get(dn_detail):
				invoiced_qty_map[dn_detail] = 0
			invoiced_qty_map[dn_detail] += qty

	return invoiced_qty_map


@frappe.whitelist()
def make_factura_venda(source_name):
	invoiced_qty_map = get_invoiced_qty_map(source_name)
	
	somaitems = []

	def set_missing_values(source, target):
		target.is_pos = 0
		target.ignore_pricing_rule = 1
		target.run_method("set_missing_values")
		target.run_method("set_po_nos")

		if len(target.get("items")) == 0:
			frappe.throw(_("All these items have already been invoiced"))

		#MAYBE CORRE NO FIM target.run_method("calculate_taxes_and_totals")

		# set company address
		target.update(get_company_address(target.company))
		if target.company_address:
			target.update(get_fetch_values("Sales Invoice", 'company_address', target.company_address))	

	def update_item(source_doc, target_doc, source_parent):
		print(source_doc.item_code)
		#print(source_doc.base_rate)
		#print(target_doc.item_code)
		idx = 0
		adicionar = False

		target_doc.qty = source_doc.qty - invoiced_qty_map.get(source_doc.name, 0)
		#target_doc.base_net_amount = source_doc.base_rate
		if source_doc.serial_no and source_parent.per_billed > 0:
			target_doc.serial_no = get_delivery_note_serial_no(source_doc.item_code,
				target_doc.qty, source_parent.name)

	#Deve criar primeiro a Factura e depois ir buscar os Itens aos poucos...
	print('TARGET DOC')
	#print(target_doc)
	print('SOURCE DOC')
	print(source_name)

	print('Factura ====')
	print(doc)

#	return doc
		
	source_parent =  frappe.model.frappe.get_all('Delivery Note Item',filters={'parent':source_name,'docstatus':1},fields=['name'])

	for xx in source_parent:
		print('DENTRO DO LOOP')
		print(xx)
		print(source_parent)

		doc1 = get_mapped_doc('Delivery Note Item', xx.name, {
			"Delivery Note Item": {
				"doctype": "Sales Invoice Item",
				"name": "dn_detail",
				"parent": "delivery_note",
				"so_detail": "so_detail",
				"against_sales_order": "sales_order",
				"serial_no": "serial_no",
				"cost_center": "cost_center"
			}
		})
		
	print('ITEMS ====')
	print(doc1)


	return doc1

	doc = get_mapped_doc("Delivery Note", source_name, 	{
		"Delivery Note": {
			"doctype": "Sales Invoice",
			"validation": {
				"docstatus": ["=", 1]
			}
		},
		"Delivery Note Item": {
			"doctype": "Sales Invoice Item",
			"field_map": {
				"name": "dn_detail",
				"parent": "delivery_note",
				"so_detail": "so_detail",
				"against_sales_order": "sales_order",
				"serial_no": "serial_no",
				"cost_center": "cost_center"
			},
			"postprocess": update_item,
			"filter": lambda d: abs(d.qty) - abs(invoiced_qty_map.get(d.name, 0))<=0
		},

		"Sales Taxes and Charges": {
			"doctype": "Sales Taxes and Charges",
			"add_if_empty": True
		},
		"Sales Team": {
			"doctype": "Sales Team",
			"field_map": {
				"incentives": "incentives"
			},
			"add_if_empty": True
		}
	}, target_doc, set_missing_values)

#		"Delivery Note Item": {
#			"doctype": "Sales Invoice Item",
#			"field_map": {
#				"name": "dn_detail",
#				"parent": "delivery_note",
#				"so_detail": "so_detail",
#				"against_sales_order": "sales_order",
#				"serial_no": "serial_no",
#				"cost_center": "cost_center"
#			},
#			"postprocess": update_item,
#			"filter": lambda d: abs(d.qty) - abs(invoiced_qty_map.get(d.name, 0))<=0
#		},


	print ("make_sales_invoice")
	print ("make_sales_invoice")
	print ("make_sales_invoice")
	print doc



		


	return doc


#+++
@frappe.whitelist()
def make_factura_venda1(source_name):
	#invoiced_qty_map = get_invoiced_qty_map(source_name)
	
	#somaitems = []

	def set_missing_values(source, target):
		target.is_pos = 0
		target.ignore_pricing_rule = 1
		target.run_method("set_missing_values")
		target.run_method("set_po_nos")

		if len(target.get("items")) == 0:
			frappe.throw(_("All these items have already been invoiced"))

		#MAYBE CORRE NO FIM target.run_method("calculate_taxes_and_totals")

		# set company address
		target.update(get_company_address(target.company))
		if target.company_address:
			target.update(get_fetch_values("Sales Invoice", 'company_address', target.company_address))	

	def update_item(source_doc, target_doc, source_parent):
		print(source_doc.item_code)
		#print(source_doc.base_rate)
		#print(target_doc.item_code)
		idx = 0
		adicionar = False

		target_doc.qty = source_doc.qty - invoiced_qty_map.get(source_doc.name, 0)
		#target_doc.base_net_amount = source_doc.base_rate
		if source_doc.serial_no and source_parent.per_billed > 0:
			target_doc.serial_no = get_delivery_note_serial_no(source_doc.item_code,
				target_doc.qty, source_parent.name)

	#Deve criar primeiro a Factura e depois ir buscar os Itens aos poucos...
	print('TARGET DOC')
	#print(target_doc)
	print('SOURCE DOC')
	print(source_name)

	print('Factura ====')
#	print(doc)

#	return doc
		
#	source_parent =  frappe.model.frappe.get_all('Delivery Note Item',filters={'parent':source_name,'docstatus':1},fields=['name'])
	source_parent =  frappe.model.frappe.get_all('Delivery Note Item',filters={'parent':source_name,'docstatus':1},fields=['*'])
	print(source_parent)

	return source_parent

	for xx in source_parent:
		print('DENTRO DO LOOP')
		print(xx)
		print(source_parent)
		doc1
		doc1 = get_mapped_doc('Delivery Note Item', xx.name, {
			"Delivery Note Item": {
				"doctype": "Sales Invoice Item",
				"name": "dn_detail",
				"parent": "delivery_note",
				"so_detail": "so_detail",
				"against_sales_order": "sales_order",
				"serial_no": "serial_no",
				"cost_center": "cost_center"
			}
		})
		
	print('ITEMS ====')
	print(doc1)


	return doc1

	doc = get_mapped_doc("Delivery Note", source_name, 	{
		"Delivery Note": {
			"doctype": "Sales Invoice",
			"validation": {
				"docstatus": ["=", 1]
			}
		},
		"Delivery Note Item": {
			"doctype": "Sales Invoice Item",
			"field_map": {
				"name": "dn_detail",
				"parent": "delivery_note",
				"so_detail": "so_detail",
				"against_sales_order": "sales_order",
				"serial_no": "serial_no",
				"cost_center": "cost_center"
			},
			"postprocess": update_item,
			"filter": lambda d: abs(d.qty) - abs(invoiced_qty_map.get(d.name, 0))<=0
		},

		"Sales Taxes and Charges": {
			"doctype": "Sales Taxes and Charges",
			"add_if_empty": True
		},
		"Sales Team": {
			"doctype": "Sales Team",
			"field_map": {
				"incentives": "incentives"
			},
			"add_if_empty": True
		}
	}, target_doc, set_missing_values)

#		"Delivery Note Item": {
#			"doctype": "Sales Invoice Item",
#			"field_map": {
#				"name": "dn_detail",
#				"parent": "delivery_note",
#				"so_detail": "so_detail",
#				"against_sales_order": "sales_order",
#				"serial_no": "serial_no",
#				"cost_center": "cost_center"
#			},
#			"postprocess": update_item,
#			"filter": lambda d: abs(d.qty) - abs(invoiced_qty_map.get(d.name, 0))<=0
#		},


	print ("make_sales_invoice")
	print ("make_sales_invoice")
	print ("make_sales_invoice")
	print doc



		


	return doc


@frappe.whitelist()
def get_car_lastmile(matricula):
	### Returns last KM of the car registered...
	print('verifica lastmile')
	print(frappe.db.sql(""" select ultimo_km from `tabVehicle_lastmile` where matricula like %s order by data_registo DESC limit 1 """,(matricula),as_dict=False))
	return frappe.db.sql(""" select ultimo_km from `tabVehicle_lastmile` where matricula like %s order by data_registo DESC limit 1 """,(matricula),as_dict=False)

@frappe.whitelist()
def none(source_name, target_doc=None):
	print('NOnE')
	print(source_name)
	print('target')
	print(target_doc.encode('utf-8'))
	return source_name

@frappe.whitelist()
def get_dn_for_si(source_name=None, datafiltro=None):
	#source_name should be customer name

#	if source_name == None:
#		dn_for_si =  frappe.model.frappe.get_all('Delivery Note',filters={'docstatus':1,'status':'To Bill'},fields=['name','customer','posting_date'])

#	else:
		#removed doscstatus 1 due to returned invoices...
		#dn_for_si =  frappe.model.frappe.get_all('Delivery Note',filters={'customer':source_name,'docstatus':1,'status':'To Bill'},fields=['name','customer','posting_date'])

	if source_name =="":
		source_name = None

	if datafiltro =="":
		datafiltro = None

	if datafiltro != None:

		print('DATAFILTRO')
		print(datafiltro)
		print(datafiltro[2:datafiltro.find(',')-1])
		print(datafiltro[datafiltro.find(',')+2:len(datafiltro)-2])

		d1 = datafiltro[2:datafiltro.find(',')-1]
		d2 = datafiltro[datafiltro.find(',')+2:len(datafiltro)-2]

#			dn_for_si =  frappe.model.frappe.get_all('Delivery Note',filters={'customer':source_name,'status':'To Bill','posting_date': (">=", d1),'posting_date': ("<=", d2)},fields=['name','customer','posting_date','is_return','return_against'])


		dn_for_si =  frappe.model.frappe.get_all('Delivery Note',filters={'customer':source_name,'status':'To Bill','posting_date': ("between", [d1,d2])},fields=['name','customer','posting_date','is_return','return_against'])

		print(dn_for_si)
	else:
		dn_for_si =  frappe.model.frappe.get_all('Delivery Note',filters={'customer':source_name,'status':'To Bill'},fields=['name','customer','posting_date','is_return','return_against'])

	#Filter returned invoices ... and remove from selection
	#dn_for_si.sort(reverse=True)
	ret1 = []
	dn_for_si1 = []
	for ret in dn_for_si:
		if ret.return_against:
			print(ret.return_against)
			print(ret.name)  
			ret1.append(ret.return_against)
			ret1.append(ret.name)


	for ret1a in dn_for_si:
		#print('DN ',ret1a.name)
		if ret1a.name in ret1:
			print('PARA REMOVER')
			print(ret1a)
			print(ret1)
			dn_for_si.remove(ret1a)

	#Para ter a certeza que foi removido...
	for ret1a in dn_for_si:
		#print('DN ',ret1a.name)
		if ret1a.name in ret1:
			print('PARA REMOVER')
			print(ret1a)
			print(ret1)
			dn_for_si.remove(ret1a)


	return dn_for_si



@frappe.whitelist()
def get_all_enderecos(doctipo,partyname):

	print 'Todos Enderecos Address or Contact'
	print doctipo
	print partyname.encode('utf-8')
	#dadoscliente = frappe.model.frappe.get_all('Dynamic Link',filters={'link_doctype':doctipo,'link_name':partyname,'parenttype':'Address'},fields={'*'})
	dadoscliente = frappe.db.sql(""" select parent from `tabDynamic Link` where link_doctype like %s and link_name like %s and parenttype = 'Contact' """,(doctipo,partyname),as_dict=False)
	if dadoscliente:
		data1 = frappe.get_doc("Contact", dadoscliente[0][0])
		if data1:
			return data1
	else:
		dadoscliente = frappe.db.sql(""" select parent from `tabDynamic Link` where link_doctype like %s and link_name like %s and parenttype = 'Address' """,(doctipo,partyname),as_dict=False)
		if dadoscliente:
			data1 = frappe.get_doc("Address", dadoscliente[0][0])
			if data1:
				return data1


@frappe.whitelist()
def get_all_enderecos_a(doctipo,partyname):

	print 'Todos Enderecos Address ONLY!!!'
	print doctipo
	print partyname.encode('utf-8')
	dadoscliente = frappe.db.sql(""" select parent from `tabDynamic Link` where link_doctype like %s and link_name like %s and parenttype = 'Address' """,(doctipo,partyname),as_dict=False)
	if dadoscliente:
		data1 = frappe.get_doc("Address", dadoscliente[0][0])
		if data1:
			return data1
				

@frappe.whitelist()
def get_xml(args):
	from werkzeug.wrappers import Response
	response = Response()
	response.mimetype = 'text/xml'
	response.charset = 'utf-8'
	response.data = '<xml></xml>'

	print 'AAAAA'

	print response	

	return response


def convert_xml():
	

	print 'creating Header'

	head = ET.Element('Header')
	auditfileversion = ET.SubElement(head,'AuditFile Version')
	companyid = ET.SubElement(head,'Company ID')	
	taxregistrationnumber = ET.SubElement(head,'Tax Registration Number')
	taxaccountingbasis = ET.SubElement(head,'Tax Accounting Basis')

	companyname = ET.SubElement(head,'Company Name')
	businessname = ET.SubElement(companyname,'Business Name')
	companyaddress = ET.SubElement(companyname,'Company Address')
	buildingnumber = ET.SubElement(companyname,'Building Number')
	streetname = ET.SubElement(companyname,'Street Name')
	addressdetail = ET.SubElement(companyname,'Address Detail')
	city = ET.SubElement(companyname,'City')
	postalcode = ET.SubElement(companyname,'Postal Code')
	region = ET.SubElement(companyname,'Region')
	country = ET.SubElement(companyname,'Country')
	fiscalyear = ET.SubElement(companyname,'Fiscal Year')
	startdate = ET.SubElement(companyname,'Sart Date')
	enddate = ET.SubElement(companyname,'End Date')
	currencycode = ET.SubElement(companyname,'Currency Code')
	datecreated = ET.SubElement(companyname,'Date Created')
	taxentity = ET.SubElement(companyname,'Tax Entity')
	productcompanytaxid = ET.SubElement(head,'Product Company Tax ID')
	softwarevalidationnumber = ET.SubElement(head,'Software Validation Number')
	productid = ET.SubElement(head,'Product ID')
	productversion = ET.SubElement(head,'Product Version')
	headercomment = ET.SubElement(head,'Header Comment')
	telephone = ET.SubElement(companyname,'Telephone')
	fax = ET.SubElement(companyname,'Fax')
	email = ET.SubElement(companyname,'Email')
	website = ET.SubElement(companyname,'Website')

	# END OF HEADER
	#Set os textos dos campos acima ..... using TEXT
	
	#Still need to add DATA FOR HEADER

	#MasterFiles
	#GeneralLedgerAccounts
	masterfiles = ET.Element('MasterFiles')

	generalledgeraccounts = ET.SubElement(masterfiles,'GeneralLedgerAccounts')
	account = ET.SubElement(generalledgeraccounts,'Account')
	accountid = ET.SubElement(account,'AccountID')
	accountdescription = ET.SubElement(account,'AccountDescription')		
	openingcreditbalance = ET.SubElement(account,'Opening Debit Balance')
	openingdebitbalance = ET.SubElement(account,'Opening Credit Balance')
	closingdebitbalance = ET.SubElement(account,'Closing Debit Balance')
	closingdebitbalance = ET.SubElement(account,'Closing Credit Balance')
	groupingcategory = ET.SubElement(account,'GroupingCategory')
	groupingcode = ET.SubElement(account,'GroupingCode')

	#END OF GeneralLedgerAccounts

	#Still need to add DATA GeneralLedgerAccounts

	#Customers
	customers = ET.SubElement(masterfiles,'Customers')
	customer = ET.SubElement(customers,'Customer')
	customerid = ET.SubElement(customer,'CustomerID')
	accountid = ET.SubElement(customer,'AccountID')
	cutomertaxid = ET.SubElement(customer,'Customer Tax ID')
	companyname = ET.SubElement(customer,'Company Name')
	contact = ET.SubElement(customer,'Contact')
	#address
	address = ET.SubElement(customer,'Address')
	billingaddress = ET.SubElement(address,'Billing Address')
	streetname = ET.SubElement(address,'Street Name')
	addressdetail = ET.SubElement(address,'Address Detail')
	city = ET.SubElement(address,'City')
	postalcode = ET.SubElement(address,'PostalCode')
	region = ET.SubElement(address,'Region')
	country = ET.SubElement(address,'Country')
	shiptoaddress = ET.SubElement(address,'ShipToAddress')
	buildingnumber = ET.SubElement(address,'BuildingNumber')
	#address 1
	address1 = ET.SubElement(customer,'Address1')
	streetname = ET.SubElement(address1,'Street Name')
	addressdetail = ET.SubElement(address1,'Address Detail')
	city = ET.SubElement(address1,'City')
	postalcode = ET.SubElement(address1,'PostalCode')
	region = ET.SubElement(address1,'Region')
	country = ET.SubElement(address1,'Country')
	telephone = ET.SubElement(customer,'Telephone')
	fax = ET.SubElement(customer,'Fax')
	email = ET.SubElement(customer,'Email')
	website = ET.SubElement(customer,'Website')
	selfbillingindicator = ET.SubElement(customer,'SelfBillingIndicator')


	#END OF Customers

	#Still need to add DATA Customers

	#Suppliers
	suppliers = ET.SubElement(masterfiles,'Suppliers')
	supplier = ET.SubElement(suppliers,'Supplier')
	supplierid = ET.SubElement(supplier,'SuplierID')
	accountid = ET.SubElement(supplier,'AccountID')
	supliertaxid = ET.SubElement(supplier,'SuplierTaxID')
	companyname = ET.SubElement(supplier,'CompanyName')
	#address
	address = ET.SubElement(supplier,'Address')
	billingaddress = ET.SubElement(address,'Billing Address')
	streetname = ET.SubElement(address,'Street Name')
	addressdetail = ET.SubElement(address,'Address Detail')
	city = ET.SubElement(address,'City')
	postalcode = ET.SubElement(address,'PostalCode')
	region = ET.SubElement(address,'Region')
	country = ET.SubElement(address,'Country')
	shipfromaddress = ET.SubElement(address,'ShipFromAddress')
	buildingnumber = ET.SubElement(address,'BuildingNumber')
	#address 1
	address1 = ET.SubElement(supplier,'Address1')
	streetname = ET.SubElement(address1,'Street Name')
	addressdetail = ET.SubElement(address1,'Address Detail')
	city = ET.SubElement(address1,'City')
	postalcode = ET.SubElement(address1,'PostalCode')
	region = ET.SubElement(address1,'Region')
	country = ET.SubElement(address1,'Country')
	telephone = ET.SubElement(supplier,'Telephone')
	fax = ET.SubElement(supplier,'Fax')
	email = ET.SubElement(supplier,'Email')
	website = ET.SubElement(supplier,'Website')
	selfbillingindicator = ET.SubElement(supplier,'SelfBillingIndicator')

	#END OF Suppliers

	#Still need to add DATA Suppliers


	#Products

	products = ET.SubElement(masterfiles,'Products')
	product = ET.SubElement(products,'Product')
	producttype = ET.SubElement(product,'Product Type')
	productcode = ET.SubElement(product,'Product Code')
	productgroup = ET.SubElement(product,'Product Group')
	productdescription = ET.SubElement(product,'Product Description')
	productnumbercode = ET.SubElement(product,'Product Number Code')
	customsdetails = ET.SubElement(product,'Customs Details')
	unnumber = ET.SubElement(product,'UNNumber')

	#END OF Products

	#Still need to add DATA Products


	#TaxTable

	taxtable = ET.SubElement(masterfiles,'TaxTable')
	taxtableentry = ET.SubElement(taxtable,'TaxTableEntry')
	taxtype = ET.SubElement(taxtableentry,'Tax Type')
	taxcountryregion = ET.SubElement(taxtableentry,'Tax Country Region')
	taxcode = ET.SubElement(taxtableentry,'Tax Code')
	description = ET.SubElement(taxtableentry,'Description')
	taxexpirationdate = ET.SubElement(taxtableentry,'Tax Expiration Date')
	taxpercentage = ET.SubElement(taxtableentry,'Tax Percentage')
	taxamount = ET.SubElement(taxtableentry,'Tax Amount')

	#END OF TaxTable

	#Still need to add DATA TaxTable



	###### FECHA O MASTER FILES

	#GeneralLEdgerEntries
	generalledgerentries = ET.Element('GeneralLedgerEntries')
	numberofentries = ET.SubElement(generalledgerentries,'NumberOfEntries')
	totaldebit = ET.SubElement(generalledgerentries,'TotalDebit')
	totalcredit = ET.SubElement(generalledgerentries,'TotalCredit')
	journal = ET.SubElement(generalledgerentries,'Journal')
	journalid = ET.SubElement(journal,'JournalID')
	description = ET.SubElement(journal,'Description')
	#transaction
	transaction = ET.SubElement(journal,'Transaction')
	transactionid = ET.SubElement(transaction,'TransactionID')
	period = ET.SubElement(transaction,'Period')
	transactiondate = ET.SubElement(transaction,'TransactionDate')
	sourceid = ET.SubElement(transaction,'SourceID')
	description = ET.SubElement(transaction,'Description')
	docarchivalnumber = ET.SubElement(transaction,'DocArchivalNumber')
	transactiontype = ET.SubElement(transaction,'TransactionType')
	glpostingdate = ET.SubElement(transaction,'GLPostingDate')
	customerid = ET.SubElement(transaction,'CustomerID')
	supplierid = ET.SubElement(transaction,'SupplierID')
	#lines
	lines = ET.SubElement(generalledgerentries,'Lines')
	debitline = ET.SubElement(lines,'Debit Line')
	recordid = ET.SubElement(lines,'Record ID')
	accountid = ET.SubElement(lines,'Account ID')
	sourcedocumentid = ET.SubElement(lines,'Source Document ID')
	systementrydate = ET.SubElement(lines,'System Entry Date')
	description = ET.SubElement(lines,'Description')
	debitamount = ET.SubElement(lines,'Debit Amount')
	#lines 1
	lines1 = ET.SubElement(generalledgerentries,'Lines1')
	creditline = ET.SubElement(lines1,'Credit Line')
	recordid = ET.SubElement(lines1,'RecordID')
	accountid = ET.SubElement(lines1,'Account ID')
	sourcedocumentid = ET.SubElement(lines1,'Source Document ID')
	systementrydate = ET.SubElement(lines1,'System Entry Date')
	description = ET.SubElement(lines1,'description')
	creditamount = ET.SubElement(lines1,'CreditAmount')



	#END OF GeneralLEdgerEntries

	#Still need to add DATA GeneralLEdgerEntries



	#SalesInvoices
	salesinvoices = ET.Element('SalesInvoices')
	numberofentries = ET.SubElement(salesinvoices,'NumberOfEntries')
	totaldebit = ET.SubElement(salesinvoices,'TotalDebit')
	totalcredit = ET.SubElement(salesinvoices,'TotalCredit')
	#invoice
	invoice = ET.SubElement(salesinvoices,'Invoice')
	invoiceno = ET.SubElement(invoice,'InvoiceNo')
	#documentstatus
	documentstatus = ET.SubElement(invoice,'DocumentStatus')
	invoicestatus = ET.SubElement(documentstatus,'InvoiceStatus')
	invoicestatusdate = ET.SubElement(documentstatus,'InvoiceStatusDate')
	reason = ET.SubElement(documentstatus,'Reason')
	sourceid = ET.SubElement(documentstatus,'SourceID')
	sourcebilling = ET.SubElement(documentstatus,'SourceBilling')

	salesinvoicehash = ET.SubElement(invoice,'Hash')
	salesinvoicehashcontrol = ET.SubElement(invoice,'HashControl')
	period = ET.SubElement(invoice,'Period')
	invoicedate = ET.SubElement(invoice,'InvoiceDate')
	invoicetype = ET.SubElement(invoice,'InvoiceType')
	#specialRegimes
	specialregimes = ET.SubElement(invoice,'SpecialRegimes')
	selfbillingindicator = ET.SubElement(specialregimes,'SelfBillingIndicator')
	cashvatschemeindicator = ET.SubElement(specialregimes,'CashVATSchemeIndicator')
	thirdpartiesbillingindicator = ET.SubElement(specialregimes,'ThirdPartiesBillingIndicator')

	sourceid = ET.SubElement(invoice,'SourceID')
	eaccode = ET.SubElement(invoice,'EACCode')
	systementrydate = ET.SubElement(invoice,'SystemEntryDate')
	transactionid = ET.SubElement(invoice,'TransactionID')
	customerid = ET.SubElement(invoice,'CustomerID')
	#shipto
	shipto = ET.SubElement(invoice,'ShipTo')
	deliveryid = ET.SubElement(shipto,'DeliveryID')
	deliverydate = ET.SubElement(shipto,'DeliveryDate')
	warehouseid = ET.SubElement(shipto,'WarehouseID')
	locationid = ET.SubElement(shipto,'LocationID')
	#address
	address = ET.SubElement(shipto,'Address')	
	buildingnumber = ET.SubElement(address,'BuildingNumber')
	streetname = ET.SubElement(address,'StreetName')
	addressdetail = ET.SubElement(address,'AddressDetail')
	city = ET.SubElement(address,'City')
	postalcode = ET.SubElement(address,'PostalCode')
	region = ET.SubElement(address,'Region')
	country = ET.SubElement(address,'Country')
	#shipfrom
	shipfrom = ET.SubElement(invoice,'ShipFrom')
	deliveryid = ET.SubElement(shipfrom,'DeliveryID')
	deliverydate = ET.SubElement(shipfrom,'DeliveryDate')
	warehouseid = ET.SubElement(shipfrom,'WarehouseID')
	locationid = ET.SubElement(shipfrom,'LocationID')
	#address
	address = ET.SubElement(shipfrom,'Address')
	buildingnumber = ET.SubElement(address,'BuildingNumber')
	streetname = ET.SubElement(address,'StreetName')
	addressdetail = ET.SubElement(address,'AddressDetail')
	city = ET.SubElement(address,'City')
	postalcode = ET.SubElement(address,'PostalCode')
	region = ET.SubElement(address,'Region')
	country = ET.SubElement(address,'Country')

	movementendtime = ET.SubElement(invoice,'MovementEndTime')
	movementstarttime = ET.SubElement(invoice,'MovementStartTime')
	#line
	line = ET.SubElement(invoice,'Line')
	linenumber = ET.SubElement(line,'LineNumber')
	#orderreferences
	orderreferences = ET.SubElement(line,'OrderReferences')
	originatingon = ET.SubElement(orderreferences,'OriginatingON')
	orderdate = ET.SubElement(orderreferences,'OrderDate')
	productdate = ET.SubElement(line,'ProductDate')
	productdescription = ET.SubElement(line,'ProductDescription')
	quantity = ET.SubElement(line,'Quantity')
	unifofmeasure = ET.SubElement(line,'UnifOfMeasure')
	unitprice = ET.SubElement(line,'UnitPrice')
	taxbase = ET.SubElement(line,'TaxBase')
	taxpointdate = ET.SubElement(line,'TaxPointDate')
	#references
	references = ET.SubElement(line,'References')
	reference = ET.SubElement(references,'Reference')
	reason = ET.SubElement(references,'Reason')
	description = ET.SubElement(references,'Description')
	#productserialnumber
	productserialnumber = ET.SubElement(line,'ProductSerialNumber')
	serialnumber = ET.SubElement(productserialnumber,'SerialNumber')
	debitamount = ET.SubElement(line,'DebitAmount')
	creditamount = ET.SubElement(line,'CreditAmount')
	#tax
	tax = ET.SubElement(line,'Tax')
	taxtype = ET.SubElement(tax,'TaxType')
	taxcountryregion = ET.SubElement(tax,'TaxCountryRegion')
	taxcode = ET.SubElement(tax,'TaxCode')
	taxpercentage = ET.SubElement(tax,'TaxPercentage')
	taxamount = ET.SubElement(tax,'TaxAmount')
	taxexemptionreason = ET.SubElement(tax,'TaxExemptionReason')
	taxexemptioncode = ET.SubElement(tax,'TaxExemptionCode')
	settlementamount = ET.SubElement(tax,'SettlementAmount')
	#customsinformation
	customsinformation = ET.SubElement(line,'CustomsInformation')
	arcno = ET.SubElement(customsinformation,'ARCNo')
	iecamount = ET.SubElement(customsinformation,'IECAmount')
	#documenttotals
	documenttotals = ET.SubElement(line,'DocumentTotals')
	taxpayable = ET.SubElement(documenttotals,'TaxPayable')
	nettotal = ET.SubElement(documenttotals,'NetTotal')
	grosstotal = ET.SubElement(documenttotals,'GrossTotal')
	#currency
	currency = ET.SubElement(line,'Currency')
	currencycode = ET.SubElement(currency,'CurrencyCode')
	currencyamount = ET.SubElement(currency,'CurrencyAmount')
	exchangerate = ET.SubElement(currency,'ExchangeRate')
	#settlement
	settlement = ET.SubElement(line,'Settlement')
	settlementdiscount = ET.SubElement(settlement,'SettlementDiscount')
	settlementamount = ET.SubElement(settlement,'SettlementAmount')
	settlementdate = ET.SubElement(settlement,'SettlementDate')
	paymentterms = ET.SubElement(settlement,'PaymentTerms')
	#payment
	payment = ET.SubElement(line,'Payment')
	paymentmechanism = ET.SubElement(payment,'PaymentMechanism')
	paymentamount = ET.SubElement(payment,'PaymentAmount')
	paymentdate = ET.SubElement(payment,'PaymentDate')
	#witholdingtax
	withholdingtax = ET.SubElement(line,'WithholdingTax')
	withholdingtaxtype = ET.SubElement(withholdingtax,'WithholdingTaxType')
	withholdingtaxdescription = ET.SubElement(withholdingtax,'WithholdingTaxDescription')
	withholdingtaxamount = ET.SubElement(withholdingtax,'WithholdingTaxAmount')


	#END OF SAlesInvoice

	#Still need to add DATA SAlesInvoice


	#MovementOfGoods
	movementofgoods = ET.Element('MovementOfGoods')
	numberofmovementlines = ET.SubElement(movementofgoods,'NumberOfMovimentLines')
	totalquantityissued = ET.SubElement(movementofgoods,'TotalQuantityIssued')
	stockmovement = ET.SubElement(movementofgoods,'StockMovement')
	documentnumber = ET.SubElement(movementofgoods,'DocumentNumber')
	documentstatus = ET.SubElement(movementofgoods,'DocumentStatus')
	movementstatus = ET.SubElement(movementofgoods,'MovementStatus')
	movementstatusdate = ET.SubElement(movementofgoods,'MovementStatusDate')
	reason = ET.SubElement(movementofgoods,'Reason')
	sourceid = ET.SubElement(movementofgoods,'SourceID')
	sourcebilling = ET.SubElement(movementofgoods,'SourceBilling')
	movementofgoodshash = ET.SubElement(movementofgoods,'Hash')
	movementofgoodshashcontrol = ET.SubElement(movementofgoods,'HashControl')
	period = ET.SubElement(movementofgoods,'Period')
	movementdate = ET.SubElement(movementofgoods,'MovementDate')
	movementtype = ET.SubElement(movementofgoods,'MovementType')
	systementrydate = ET.SubElement(movementofgoods,'SystemEntryDate')
	transactionid = ET.SubElement(movementofgoods,'TransactionID')
	customerid = ET.SubElement(movementofgoods,'CustomerID')
	supplierid = ET.SubElement(movementofgoods,'SupplierID')
	sourceid = ET.SubElement(movementofgoods,'SourceID')
	eaccode = ET.SubElement(movementofgoods,'EACCode')
	movementcomments = ET.SubElement(movementofgoods,'MovementComments')
	shipto = ET.SubElement(movementofgoods,'ShipTo')
	deliveryid = ET.SubElement(movementofgoods,'DeliveryID')
	deliverydate = ET.SubElement(movementofgoods,'DeliveryDate')
	warehouseid = ET.SubElement(movementofgoods,'WarehouseID')
	locationid = ET.SubElement(movementofgoods,'LocationId')
	address = ET.SubElement(movementofgoods,'Address')
	buildingnumber = ET.SubElement(movementofgoods,'BuildingNumber')
	streetname = ET.SubElement(movementofgoods,'StreetName')
	addressdetail = ET.SubElement(movementofgoods,'AddressDetail')
	city = ET.SubElement(movementofgoods,'City')
	postalcode = ET.SubElement(movementofgoods,'PostalCode')
	region = ET.SubElement(movementofgoods,'Region')
	country = ET.SubElement(movementofgoods,'Country')
	shipfrom = ET.SubElement(movementofgoods,'ShipFrom')
	deliveryid = ET.SubElement(movementofgoods,'DeliveryID')
	deliverydate = ET.SubElement(movementofgoods,'DeliveryDate')
	warehouseid = ET.SubElement(movementofgoods,'WarehouseID')
	locationid = ET.SubElement(movementofgoods,'LocationID')
	address = ET.SubElement(movementofgoods,'Address')
	buildingnumber = ET.SubElement(movementofgoods,'BuildingNumber')
	streetname = ET.SubElement(movementofgoods,'StreetName')
	addressdetail = ET.SubElement(movementofgoods,'AddressDetail')
	city = ET.SubElement(movementofgoods,'City')
	postalcode = ET.SubElement(movementofgoods,'PostalCode')
	region = ET.SubElement(movementofgoods,'Region')
	country = ET.SubElement(movementofgoods,'Country')
	movementendtime = ET.SubElement(movementofgoods,'MovementEndTime')
	movementstarttime = ET.SubElement(movementofgoods,'MovementStartTime')
	codigoidentificacaodocumento = ET.SubElement(movementofgoods,'CodigoIdentificacaoDocumento')
	line = ET.SubElement(movementofgoods,'Line')
	linenumber = ET.SubElement(movementofgoods,'LineNumber')
	orderreferences = ET.SubElement(movementofgoods,'OrderReferences')
	originatingon = ET.SubElement(movementofgoods,'OriginatingON')
	orderdate = ET.SubElement(movementofgoods,'OrderDate')
	productcode = ET.SubElement(movementofgoods,'ProductCode')
	productdescription = ET.SubElement(movementofgoods,'ProductDescription')
	quantity = ET.SubElement(movementofgoods,'Quantity')
	unitofmeasure = ET.SubElement(movementofgoods,'UnifOfMeasure')
	unitprice = ET.SubElement(movementofgoods,'UnitPrice')
	description = ET.SubElement(movementofgoods,'Description')
	productserialnumber = ET.SubElement(movementofgoods,'ProductSerialNumber')
	serialnumber = ET.SubElement(movementofgoods,'SerialNumber')
	debitamount = ET.SubElement(movementofgoods,'DebitAmount')
	creditamount = ET.SubElement(movementofgoods,'creditAmount')
	tax = ET.SubElement(movementofgoods,'Tax')
	taxtype = ET.SubElement(movementofgoods,'TaxType')
	taxcountryregion = ET.SubElement(movementofgoods,'TaxCountryRegion')
	taxcode = ET.SubElement(movementofgoods,'TaxCode')
	taxpercentage = ET.SubElement(movementofgoods,'TaxPercentage')
	taxexemptionreason = ET.SubElement(movementofgoods,'TaxExemptionReason')
	taxexemptioncode = ET.SubElement(movementofgoods,'TaxExemptionCode')
	settlementamount = ET.SubElement(movementofgoods,'SettlementAmount')

	#customsinformation
	customsinformation = ET.SubElement(movementofgoods,'CustomsInformation')
	arcno = ET.SubElement(customsinformation,'ARCNo')
	iecamount = ET.SubElement(customsinformation,'IECAmount')
	#documenttotals
	documenttotals = ET.SubElement(movementofgoods,'DocumentTotals')
	taxpayable = ET.SubElement(documenttotals,'TaxPayable')
	nettotal = ET.SubElement(documenttotals,'NetTotal')
	grosstotal = ET.SubElement(documenttotals,'GrossTotal')
	#currency
	currency = ET.SubElement(movementofgoods,'Currency')
	currencycode = ET.SubElement(currency,'CurrencyCode')
	currencyamount = ET.SubElement(currency,'CurrencyAmount')
	exchangerate = ET.SubElement(currency,'ExchangeRate')


	#END OF MovementOfGoods

	#Still need to add DATA MovementOfGoods


	#WorkingDocuments
	workingdocuments = ET.Element('WorkingDocuments')
	numberofentries = ET.SubElement(workingdocuments,'NumberOfEntries')
	totaldebit = ET.SubElement(workingdocuments,'TotalDebit')
	totalcredit = ET.SubElement(workingdocuments,'TotalCredit')
	workdocument = ET.SubElement(workingdocuments,'WorkDocument')
	documentnumber = ET.SubElement(workingdocuments,'DocumentNumber')
	codigounicodocumento = ET.SubElement(workingdocuments,'CodigoUnicoDocumento')
	documentstatus = ET.SubElement(workingdocuments,'DocumentStatus')
	workstatus = ET.SubElement(workingdocuments,'WorkStatus')
	workstatusdate = ET.SubElement(workingdocuments,'WorkStatusDate')
	reason = ET.SubElement(workingdocuments,'Reason')
	sourceid = ET.SubElement(workingdocuments,'SourceID')
	sourcebilling = ET.SubElement(workingdocuments,'SourceBilling')
	workingdocumentshash = ET.SubElement(workingdocuments,'Hash')
	workingdocumentshashcontrol = ET.SubElement(workingdocuments,'HashControl')
	period = ET.SubElement(workingdocuments,'Period')
	workdate = ET.SubElement(workingdocuments,'WorkDate')
	worktype = ET.SubElement(workingdocuments,'WorkType')
	sourceid = ET.SubElement(workingdocuments,'SourceID')
	eaccode = ET.SubElement(workingdocuments,'EACCode')
	systementrydate = ET.SubElement(workingdocuments,'SystemEntryDate')
	transactionid = ET.SubElement(workingdocuments,'TransactionID')

	customerid = ET.SubElement(workingdocuments,'CustomerID')
	#line
	line = ET.SubElement(workingdocuments,'Line')
	linenumber = ET.SubElement(line,'LineNumber')
	orderreferences = ET.SubElement(line,'OrderReferences')
	originatingon = ET.SubElement(orderreferences,'OriginatingON')
	orderdate = ET.SubElement(orderreferences,'OrderDate')

	productcode = ET.SubElement(line,'ProductCode')
	productdescription = ET.SubElement(line,'ProductDescription')
	quantity = ET.SubElement(line,'Quantity')
	unitofmeasure = ET.SubElement(line,'UnifOfMeasure')
	unitprice = ET.SubElement(line,'UnitPrice')
	taxbase = ET.SubElement(line,'TaxBase')
	taxpointdate = ET.SubElement(line,'TaxPointDate')
	#references
	references = ET.SubElement(line,'References')
	reference = ET.SubElement(references,'Reference')
	reason = ET.SubElement(references,'Reason')
	description = ET.SubElement(references,'Description')
	#productserialnumber
	productserialnumber = ET.SubElement(line,'ProductSerialNumber')
	serialnumber = ET.SubElement(productserialnumber,'SerialNumber')
	debitamount = ET.SubElement(line,'DebitAmount')
	creditamount = ET.SubElement(line,'CreditAmount')
	#tax
	tax = ET.SubElement(line,'Tax')
	taxtype = ET.SubElement(tax,'TaxType')
	taxcountryregion = ET.SubElement(tax,'TaxCountryRegion')
	taxcode = ET.SubElement(tax,'TaxCode')
	taxpercentage = ET.SubElement(tax,'TaxPercentage')
	taxamount = ET.SubElement(tax,'TaxAmount')
	taxexemptionreason = ET.SubElement(tax,'TaxExemptionReason')
	taxexemptioncode = ET.SubElement(tax,'TaxExemptionCode')

	settlementamount = ET.SubElement(tax,'SettlementAmount')
	#customsinformation
	customsinformation = ET.SubElement(line,'CustomsInformation')
	arcno = ET.SubElement(customsinformation,'ARCNo')
	iecamount = ET.SubElement(customsinformation,'IECAmount')
	#documenttotals
	documenttotals = ET.SubElement(workingdocuments,'DocumentTotals')
	taxpayable = ET.SubElement(documenttotals,'TaxPayable')
	nettotal = ET.SubElement(documenttotals,'NetTotal')
	grosstotal = ET.SubElement(documenttotals,'GrossTotal')
	#currency
	currency = ET.SubElement(documenttotals,'Currency')
	currencycode = ET.SubElement(currency,'CurrencyCode')
	currencyamount = ET.SubElement(currency,'CurrencyAmount')
	exchangerate = ET.SubElement(currency,'ExchangeRate')


	#END OF WorkingDocuments

	#Still need to add DATA WorkingDocuments


	#Payments
	payments = ET.Element('Payments')
	numberofentries = ET.SubElement(payments,'NumberOfEntries')
	totaldebit = ET.SubElement(payments,'TotalDebit')
	totalcredit = ET.SubElement(payments,'TotalCredit')
	#payment
	payment = ET.SubElement(payments,'Payment')
	paymentrefno = ET.SubElement(payment,'PaymentRefNo')
	period = ET.SubElement(payment,'Period')
	transactionid = ET.SubElement(payment,'TransactionID')
	transactiondate = ET.SubElement(payment,'TransactionDate')
	paymenttype = ET.SubElement(payment,'PaymentType')
	description = ET.SubElement(payment,'Description')
	systemid = ET.SubElement(payment,'SystemID')
	documentstatus = ET.SubElement(payment,'DocumentStatus')
	paymentstatus = ET.SubElement(documentstatus,'PaymentStatus')	
	paymentstatusdate = ET.SubElement(documentstatus,'PaymentStatusDate')
	reason = ET.SubElement(documentstatus,'Reason')
	sourceid = ET.SubElement(documentstatus,'SourceID')
	sourcepayment = ET.SubElement(documentstatus,'SourcePayment')
	paymentmethod = ET.SubElement(payment,'PaymentMethod')
	paymentmechanism = ET.SubElement(paymentmethod,'PaymentMechanism')
	paymentamount = ET.SubElement(paymentmethod,'PaymentAmount')
	paymentdate = ET.SubElement(paymentmethod,'PaymentDate')
	sourceid = ET.SubElement(payment,'SourceID')
	systementrydate = ET.SubElement(payment,'SystemEntryDate')
	customerid = ET.SubElement(payment,'CustomerID')

	#line
	line = ET.SubElement(payment,'Line')
	linenumber = ET.SubElement(line,'LineNumber')
	sourcedocumentid = ET.SubElement(line,'SourceDocumentID')
	originatingon = ET.SubElement(sourcedocumentid,'OriginatingON')
	invoicedate = ET.SubElement(sourcedocumentid,'InvoiceDate')
	description = ET.SubElement(sourcedocumentid,'Description')

	settlementamount = ET.SubElement(line,'SettlementAmount')
	debitamount = ET.SubElement(line,'DebitAmount')
	creditamount = ET.SubElement(line,'CreditAmount')
	#tax
	tax = ET.SubElement(line,'Tax')
	taxtype = ET.SubElement(tax,'TaxType')
	taxcountryregion = ET.SubElement(tax,'TaxCountryRegion')
	taxcode = ET.SubElement(tax,'TaxCode')
	taxpercentage = ET.SubElement(tax,'TaxPercentage')
	taxamount = ET.SubElement(tax,'TaxAmount')
	taxexemptionreason = ET.SubElement(line,'TaxExemptionReason')
	taxexemptioncode = ET.SubElement(line,'TaxExemptionCode')
	#documenttotals
	documenttotals = ET.SubElement(payment,'DocumentTotals')
	taxpayable = ET.SubElement(documenttotals,'TaxPayable')
	nettotal = ET.SubElement(documenttotals,'NetTotal')
	grosstotal = ET.SubElement(documenttotals,'GrossTotal')
	#settlement
	settlement = ET.SubElement(documenttotals,'Settlement')
	settlementamount = ET.SubElement(settlement,'SettlementAmount')
	#currency
	currency = ET.SubElement(documenttotals,'Currency')
	currencycode = ET.SubElement(currency,'CurrencyCode')
	currencyamount = ET.SubElement(currency,'CurrencyAmount')
	exchangerate = ET.SubElement(currency,'ExchangeRate')
	#witholdingtax
	withholdingtax = ET.SubElement(payment,'WithholdingTax')
	withholdingtaxtype = ET.SubElement(withholdingtax,'WithholdingTaxType')
	withholdingtaxdescription = ET.SubElement(withholdingtax,'WithholdingTaxDescription')
	withholdingtaxamount = ET.SubElement(withholdingtax,'WithholdingTaxAmount')


	#END OF Payments

	#Still need to add DATA Payments


	#Invoices
	invoices = ET.Element('Invoices')
	numberofentries = ET.SubElement(invoices,'NumberOfEntries')
	invoicedate = ET.SubElement(invoices,'InvoiceDate')
	period = ET.SubElement(invoices,'Period')
	invoicetype = ET.SubElement(invoices,'InvoiceType')
	sourceid = ET.SubElement(invoices,'SourceID')
	supplierid = ET.SubElement(invoices,'SupplierID')
	invoiceno = ET.SubElement(invoices,'InvoiceNo')
	documenttotals = ET.SubElement(invoices,'DocumentTotals')
	inputtax = ET.SubElement(invoices,'InputTax')
	taxbase = ET.SubElement(invoices,'TaxBase')
	grosstotal = ET.SubElement(invoices,'GrossTotal')
	deductibletax = ET.SubElement(invoices,'DeductibleTax')
	deductiblepercentage = ET.SubElement(invoices,'DeductiblePercentage')
	currencycode = ET.SubElement(invoices,'CurrencyCode')
	currencyamount = ET.SubElement(invoices,'CurrencyAmount')
	operationtype = ET.SubElement(invoices,'OperationType')

	#END OF Invoices

	#Still need to add DATA Invoices


	print 'Convert XML'

	data = ET.Element('root')
	row = ET.SubElement(data,'row')
	#Campos do file CSV....
	cust = ET.SubElement(row,'customer_name')
	custtype = ET.SubElement(row,'customer_type')

	custgroup = ET.SubElement(row,'customer_group')

	cust.text= 'Virgilio Luis'

	custtype.text = 'Individual'

	custgroup.text = 'Funcionarios'

	#record the data...	
	mydata = ET.tostring(data, encoding='utf8')

	myfile = open("/tmp/clientes.xml","w")

	myfile.write(mydata)

	print 'file created'

@frappe.whitelist()
def gerar_saft_ao():
	#read from source ...
	empresa = frappe.get_doc('Company', '2MS - Comercio e Representacoes, Lda')	#Should get as arg or based on default...
	emp_enderecos = get_all_enderecos("Company",empresa.name)
	print 'ENdereco Empresa'
	print emp_enderecos

	AnoFiscal = frappe.db.sql(""" select year, year_start_date, year_end_date, disabled from `tabFiscal Year` where year = %s """,(datetime.today().year
),as_dict=True)

	print 'AnoFiscal'
	print AnoFiscal 
	print datetime.today().year

	#create Header

	data = ET.Element('AuditFile')
	print 'creating Header'
	head = ET.SubElement(data,'Header')

	auditfileversion = ET.SubElement(head,'AuditFileVersion')
	auditfileversion.text = '1.0'

	companyid = ET.SubElement(head,'CompanyID')	
	companyid.text = empresa.name

	taxregistrationnumber = ET.SubElement(head,'TaxRegistrationNumber')
	taxregistrationnumber.text = empresa.tax_id

	taxaccountingbasis = ET.SubElement(head,'TaxAccountingBasis')
	taxaccountingbasis.text = "I"	#I contab. integrada c/Factur, C - Contab, F - Fact, Q - bens, services, Fact.

	companyname = ET.SubElement(head,'CompanyName')
	companyname.text = empresa.name

	businessname = ET.SubElement(companyname,'BusinessName')
	businessname.text = empresa.name

	companyaddress = ET.SubElement(companyname,'CompanyAddress')
	buildingnumber = ET.SubElement(companyname,'BuildingNumber')

	streetname = ET.SubElement(companyname,'StreetName')
	streetname.text = emp_enderecos.address_line1

	addressdetail = ET.SubElement(companyname,'AddressDetail')
	addressdetail.text = emp_enderecos.address_line1

	city = ET.SubElement(companyname,'City')
	city.text = emp_enderecos.city
	
	postalcode = ET.SubElement(companyname,'PostalCode')
	postalcode.text = emp_enderecos.pincode

	region = ET.SubElement(companyname,'Region')
	region.text = emp_enderecos.state

	country = ET.SubElement(companyname,'Country')
	country.text = "AO"	#default

	fiscalyear = ET.SubElement(companyname,'FiscalYear')
	fiscalyear.text = AnoFiscal[0].year

	print 'Ano Inicio'
	print AnoFiscal[0].year_start_date

	startdate = ET.SubElement(companyname,'SartDate')
	startdate.text = AnoFiscal[0].year_start_date.strftime("%Y-%m-%d %H:%M:%S")

	enddate = ET.SubElement(companyname,'EndDate')
	enddate.text = AnoFiscal[0].year_end_date.strftime("%Y-%m-%d %H:%M:%S")

	currencycode = ET.SubElement(companyname,'CurrencyCode')
	currencycode.text = "AOA"	#default

	datecreated = ET.SubElement(companyname,'DateCreated')
	datecreated.text = frappe.utils.nowdate()	#XML created

	taxentity = ET.SubElement(companyname,'TaxEntity')
	taxentity.text = "Global"	#default

	productcompanytaxid = ET.SubElement(head,'ProductCompanyTaxID')
	productcompanytaxid.text = "5417537802"	#TeorLogico

	
	softwarevalidationnumber = ET.SubElement(head,'SoftwareValidationNumber')
	softwarevalidationnumber.text = 0	#TeorLogico for now

	productid = ET.SubElement(head,'ProductID')
	productid.text = "AngolaERP / TeorLogico"	#TeorLogico

	productversion = ET.SubElement(head,'ProductVersion')
	productid.text = str(get_versao_erp())

	print get_versao_erp()

	headercomment = ET.SubElement(head,'HeaderComment')

	telephone = ET.SubElement(companyname,'Telephone')
	telephone.text = emp_enderecos.phone

	fax = ET.SubElement(companyname,'Fax')
	productid.text = emp_enderecos.fax

	email = ET.SubElement(companyname,'Email')
	productid.text = emp_enderecos.email_id

	website = ET.SubElement(companyname,'Website')
	productid.text = empresa.website


	# END OF HEADER

	#MASTER Files
	masterfiles = ET.SubElement(data,'MasterFiles')
	#Customers
	customers = ET.SubElement(masterfiles,'Customers')

	#masterfiles = ET.Element('MasterFiles')

	#create Customer
	clientes = frappe.db.sql(""" select * from `tabCustomer` where docstatus = 0 """,as_dict=True)

	adicionacliente = True

	#Faz loop
	for cliente in clientes:
		contascliente = frappe.db.sql(""" select * from `tabParty Account` where parenttype = 'Customer' and parentfield = 'accounts' and parent = %s and company = %s """,(cliente.name, empresa.name), as_dict=True)
		print 'account cliente'
		print cliente.name
		print contascliente

		if not contascliente:
			#test to see if exists ... but on diff company

			contascliente = frappe.db.sql(""" select * from `tabParty Account` where parenttype = 'Customer' and parentfield = 'accounts' and parent = %s """,(cliente.name), as_dict=True)
			print 'outra empresa'
			print contascliente
			if contascliente:
				#Outra empresa..
				adicionacliente = False
			else:
				adicionacliente = True
		
		
		if adicionacliente == True:
			print 'Add cliente'
			print 'Add cliente'
			print 'Add cliente'
			#Customers
			#customers = ET.SubElement(masterfiles,'Customers')
			customer = ET.SubElement(customers,'Customer')
			customerid = ET.SubElement(customer,'CustomerID')
			customerid.text = cliente.name

			accountid = ET.SubElement(customer,'AccountID')



			if not contascliente:
					contascliente = frappe.db.sql(""" select * from `tabAccount` where name like '31121000%%' and company = %s """,(empresa.name), as_dict=True)
					print contascliente
					accountid.text = contascliente[0].account_name
#				else:
#					accountid.text = "Desconhecido"				
			else:

				accountid.text = contascliente[0].account


			customertaxid = ET.SubElement(customer,'CustomerTaxID')
			customertaxid.text = cliente.tax_id

			companyname = ET.SubElement(customer,'CompanyName')
			companyname.text = cliente.customer_name

			contact = ET.SubElement(customer,'Contact')

			#address
			address = ET.SubElement(customer,'Address')

			billingaddress = ET.SubElement(address,'BillingAddress')
			cliente_endereco = get_all_enderecos_a("Customer",cliente.name)
			if cliente_endereco:
				print cliente_endereco.address_line1
				billingaddress.text = cliente_endereco.address_line1

			streetname = ET.SubElement(address,'StreetName')
			if cliente_endereco:
				streetname.text = cliente_endereco.address_line1

			addressdetail = ET.SubElement(address,'AddressDetail')
			if cliente_endereco:				
				addressdetail.text = cliente_endereco.address_line1

			else:
				addressdetail.text = "Desconhecido"	#default

			city = ET.SubElement(address,'City')
			if cliente_endereco:
				city.text = cliente_endereco.city

			postalcode = ET.SubElement(address,'PostalCode')
			if cliente_endereco:
				postalcode.text = cliente_endereco.pincode

			region = ET.SubElement(address,'Region')

			country = ET.SubElement(address,'Country')
			if cliente_endereco:
				country.text = cliente_endereco.country

			#address 1
			shiptoaddress = ET.SubElement(address,'ShipToAddress')

			buildingnumber = ET.SubElement(shiptoaddress,'BuildingNumber')
			streetname = ET.SubElement(shiptoaddress,'StreetName')
			addressdetail = ET.SubElement(shiptoaddress,'AddressDetail')
			city = ET.SubElement(shiptoaddress,'City')
			postalcode = ET.SubElement(shiptoaddress,'PostalCode')
			region = ET.SubElement(shiptoaddress,'Region')
			country = ET.SubElement(shiptoaddress,'Country')


			telephone = ET.SubElement(customer,'Telephone')
			if cliente_endereco:
				telephone.text = cliente_endereco.phone

			fax = ET.SubElement(customer,'Fax')
			if cliente_endereco:
				fax.text = cliente_endereco.fax

			email = ET.SubElement(customer,'Email')
			if cliente_endereco:
				email.text = cliente_endereco.email_id

			website = ET.SubElement(customer,'Website')

			selfbillingindicator = ET.SubElement(customer,'SelfBillingIndicator')
			selfbillingindicator.text = 0	#default

		#END OF Customers

	#create Suppliers


	#Suppliers
	suppliers = ET.SubElement(masterfiles,'Suppliers')
	fornecedores = frappe.db.sql(""" select * from `tabSupplier` where docstatus = 0 """,as_dict=True)

	adicionafornecedor = True

	for fornecedor in fornecedores:
		contasfornecedor = frappe.db.sql(""" select * from `tabParty Account` where parenttype = 'Supplier' and parentfield = 'accounts' and parent = %s and company = %s """,(fornecedor.name, empresa.name), as_dict=True)
		print 'account fornecedor'
		print fornecedor.name
		print contasfornecedor

		if not contasfornecedor:
			#test to see if exists ... but on diff company

			contasfornecedor = frappe.db.sql(""" select * from `tabParty Account` where parenttype = 'Supplier' and parentfield = 'accounts' and parent = %s """,(fornecedor.name), as_dict=True)
			print 'outra empresa'
			print contasfornecedor
			if contasfornecedor:
				#Outra empresa..
				adicionafornecedor = False
			else:
				adicionafornecedor = True
		
		
		if adicionafornecedor == True:
			print 'Add Fornecedor'
			print 'Add Fornecedor'
			print 'Add Fornecedor'



			supplier = ET.SubElement(suppliers,'Supplier')
			supplierid = ET.SubElement(supplier,'SuplierID')
			supplierid.text = fornecedor.name

		
			accountid = ET.SubElement(supplier,'AccountID')

			if not contasfornecedor:
					contasfornecedor = frappe.db.sql(""" select * from `tabAccount` where name like '31121000%%' and company = %s """,(empresa.name), as_dict=True)
					print contasfornecedor
					accountid.text = contasfornecedor[0].account_name
#				else:
#					accountid.text = "Desconhecido"				
			else:

				accountid.text = contasfornecedor[0].account


			supliertaxid = ET.SubElement(supplier,'SuplierTaxID')
			supliertaxid.text = fornecedor.tax_id

			companyname = ET.SubElement(supplier,'CompanyName')
			companyname.text = fornecedor.supplier_name

			#address
			address = ET.SubElement(supplier,'Address')
			billingaddress = ET.SubElement(address,'BillingAddress')

			fornecedor_endereco = get_all_enderecos_a("Supplier",fornecedor.name)
			if fornecedor_endereco:
				print fornecedor_endereco.address_line1
				billingaddress.text = fornecedor_endereco.address_line1

			streetname = ET.SubElement(address,'StreetName')
			if fornecedor_endereco:
				streetname.text = fornecedor_endereco.address_line1


			addressdetail = ET.SubElement(address,'AddressDetail')
			if fornecedor_endereco:
				addressdetail.text = fornecedor_endereco.address_line1

			city = ET.SubElement(address,'City')
			if fornecedor_endereco:
				city.text = fornecedor_endereco.city


			postalcode = ET.SubElement(address,'PostalCode')
			if fornecedor_endereco:
				postalcode.text = fornecedor_endereco.pincode

			region = ET.SubElement(address,'Region')
			if fornecedor_endereco:
				region.text = fornecedor_endereco.region

			country = ET.SubElement(address,'Country')
			if fornecedor_endereco:
				countr.text = fornecedor_endereco.country

			#address 1
			shipfromaddress = ET.SubElement(address,'ShipFromAddress')
			buildingnumber = ET.SubElement(shipfromaddress,'BuildingNumber')

			address1 = ET.SubElement(shipfromaddress,'Address1')
			streetname = ET.SubElement(shipfromaddress,'StreetName')
			addressdetail = ET.SubElement(shipfromaddress,'AddressDetail')
			city = ET.SubElement(shipfromaddress,'City')
			postalcode = ET.SubElement(shipfromaddress,'PostalCode')
			region = ET.SubElement(shipfromaddress,'Region')
			country = ET.SubElement(shipfromaddress,'Country')

			telephone = ET.SubElement(supplier,'Telephone')
			if fornecedor_endereco:
				telephone.text = fornecedor_endereco.phone

			fax = ET.SubElement(supplier,'Fax')
			if fornecedor_endereco:
				fax.text = fornecedor_endereco.fax

			email = ET.SubElement(supplier,'Email')
			if fornecedor_endereco:
				email.text = fornecedor_endereco.email_id

			website = ET.SubElement(supplier,'Website')
			website.text = fornecedor.website

			selfbillingindicator = ET.SubElement(supplier,'SelfBillingIndicator')
			selfbillingindicator.text = 0 #default

	#END OF Suppliers


	#create Products / Services
	#Products


	products = ET.SubElement(masterfiles,'Products')

	produtos = frappe.db.sql(""" select * from `tabItem` where docstatus = 0 """,as_dict=True)

	for produto in produtos:
	
		product = ET.SubElement(products,'Product')
		producttype = ET.SubElement(product,'ProductType')
		if produto.is_stock_item:
			producttype.text = "P" #Produto
		else:
			producttype.text = "S" #Servico

		
		productcode = ET.SubElement(product,'ProductCode')
		productcode.text = produto.item_code

		productgroup = ET.SubElement(product,'ProductGroup')
		productgroup.text = produto.item_group

		productdescription = ET.SubElement(product,'ProductDescription')
		productdescription.text = produto.item_name

		productnumbercode = ET.SubElement(product,'ProductNumberCode')
		productnumbercode.text = produto.barcode

		customsdetails = ET.SubElement(product,'CustomsDetails')
		unnumber = ET.SubElement(product,'UNNumber')

	#END OF Products


	#create Retencoes...
	#TaxTable

	
	taxtable = ET.SubElement(masterfiles,'TaxTable')
	retencoes = frappe.db.sql(""" select * from `tabRetencoes` where docstatus = 0 """,as_dict=True)

	for retencao in retencoes:

		taxtableentry = ET.SubElement(taxtable,'TaxTableEntry')
		taxtype = ET.SubElement(taxtableentry,'TaxType')
		if "IPC" in retencao.name:
			taxtype.text = "NS"
		elif "SELO" in retencao.name:
			taxtype.text = "IS"
		elif "IVA" in retencao.name:
			taxtype.text = "IVA"
		else:
			taxtype.text = "NS"

		taxcountryregion = ET.SubElement(taxtableentry,'TaxCountryRegion')


		taxcode = ET.SubElement(taxtableentry,'TaxCode')
		if "IPC" in retencao.name:
			taxcode.text = "NS"
		elif "SELO" in retencao.name:
			taxcode.text = "ISE"
		elif "IVA" in retencao.name:
			taxcode.text = "ISE"
		else:
			taxcode.text = "NS"

		description = ET.SubElement(taxtableentry,'Description')
		description.text = retencao.descricao

		taxexpirationdate = ET.SubElement(taxtableentry,'TaxExpirationDate')
		taxexpirationdate.text = retencao.data_limite

		taxpercentage = ET.SubElement(taxtableentry,'TaxPercentage')
		taxpercentage.text = str(retencao.percentagem)+"0"

		taxamount = ET.SubElement(taxtableentry,'TaxAmount')
		taxamount.text = 0

	#END OF TaxTable

	#create Sales Invoices


	#SalesInvoices
	salesinvoices = ET.SubElement(data,'SalesInvoices')
	#still need to filter per user request by MONTH or dates filter...
	#Default CURRENT MONTH
	print 'mes inicial ', get_first_day(datetime.today())
	print 'mes fim ', get_last_day(datetime.today())

	primeirodiames = get_first_day(datetime.today())
	ultimodiames = get_last_day(datetime.today())

	facturas = frappe.db.sql(""" select count(name) from `tabSales Invoice` where company = %s and posting_date >= %s and posting_date <= %s """,(empresa.name,primeirodiames,ultimodiames), as_dict=True)

	print facturas
	print int(facturas[0]['count(name)'])


	numberofentries = ET.SubElement(salesinvoices,'NumberOfEntries')
	numberofentries.text = str(int(facturas[0]['count(name)']))

	##### POR FAZER
	totaldebit = ET.SubElement(salesinvoices,'TotalDebit')

	totalcredit = ET.SubElement(salesinvoices,'TotalCredit')

	####### POR FAZER


	#invoice
	facturas = frappe.db.sql(""" select * from `tabSales Invoice` where company = %s and posting_date >= %s and posting_date <= %s """,(empresa.name,primeirodiames,ultimodiames), as_dict=True)

	for factura in facturas:
		print factura.name
		print factura.creation
		print factura.modified

		invoice = ET.SubElement(salesinvoices,'Invoice')

		invoiceno = ET.SubElement(invoice,'InvoiceNo')
		invoiceno.text = str(factura.name)

		#documentstatus
		documentstatus = ET.SubElement(invoice,'DocumentStatus')
		invoicestatus = ET.SubElement(documentstatus,'InvoiceStatus')
		if factura.status =="Paid" and factura.docstatus == 1:
			invoicestatus.text = "F"	#Facturado
		elif factura.status =="Cancelled" and factura.docstatus == 2:
			invoicestatus.text = "A"	#Anulado

		else:
			invoicestatus.text = "N"	#Normal


		invoicestatusdate = ET.SubElement(documentstatus,'InvoiceStatusDate')
		invoicestatusdate.text = factura.modified.strftime("%Y-%m-%d %H:%M:%S")	#ultima change

		reason = ET.SubElement(documentstatus,'Reason')
		sourceid = ET.SubElement(documentstatus,'SourceID')
		sourceid.text = factura.modified_by	#User

		sourcebilling = ET.SubElement(documentstatus,'SourceBilling')
		sourcebilling.text = "P"	#Default

		salesinvoicehash = ET.SubElement(invoice,'Hash')
		salesinvoicehash.text = 0	#por rever...

		salesinvoicehashcontrol = ET.SubElement(invoice,'HashControl')
		salesinvoicehashcontrol.text = 0	#por rever

		period = ET.SubElement(invoice,'Period')
		period.text = str(factura.modified.month)	#last modified month

		invoicedate = ET.SubElement(invoice,'InvoiceDate')
		invoicedate.text = factura.posting_date.strftime("%Y-%m-%d %H:%M:%S")	#posting date

		invoicetype = ET.SubElement(invoice,'InvoiceType')
		invoicedate.text = "FT"	#default sales invoice

		#specialRegimes
		specialregimes = ET.SubElement(invoice,'SpecialRegimes')
		selfbillingindicator = ET.SubElement(specialregimes,'SelfBillingIndicator')
		selfbillingindicator.text = 0	#default 

		cashvatschemeindicator = ET.SubElement(specialregimes,'CashVATSchemeIndicator')
		cashvatschemeindicator.text = 0	#default 

		thirdpartiesbillingindicator = ET.SubElement(specialregimes,'ThirdPartiesBillingIndicator')
		thirdpartiesbillingindicator.text = 0	#default 

		sourceid = ET.SubElement(invoice,'SourceID')
		sourceid.text = factura.owner	#created by

		eaccode = ET.SubElement(invoice,'EACCode')

		systementrydate = ET.SubElement(invoice,'SystemEntryDate')
		systementrydate.text = factura.creation.strftime("%Y-%m-%d %H:%M:%S")	#creation date

		transactionid = ET.SubElement(invoice,'TransactionID')
		entradasgl =  frappe.db.sql(""" select * from `tabGL Entry` where voucher_type ='sales invoice' and company = %s and voucher_no = %s """,(empresa.name,factura.name), as_dict=True)
		if entradasgl:
			transactionid.text = entradasgl[0].name	#entrada GL;single invoice can generate more than 2GL

		customerid = ET.SubElement(invoice,'CustomerID')
		customerid.text = factura.customer	#cliente

		#shipto
		shipto = ET.SubElement(invoice,'ShipTo')
		deliveryid = ET.SubElement(shipto,'DeliveryID')
		deliverydate = ET.SubElement(shipto,'DeliveryDate')
		warehouseid = ET.SubElement(shipto,'WarehouseID')
		locationid = ET.SubElement(shipto,'LocationID')
		#address
		address = ET.SubElement(shipto,'Address')	
		buildingnumber = ET.SubElement(address,'BuildingNumber')
		streetname = ET.SubElement(address,'StreetName')
		addressdetail = ET.SubElement(address,'AddressDetail')
		city = ET.SubElement(address,'City')
		postalcode = ET.SubElement(address,'PostalCode')
		region = ET.SubElement(address,'Region')
		country = ET.SubElement(address,'Country')
		#shipfrom
		shipfrom = ET.SubElement(invoice,'ShipFrom')
		deliveryid = ET.SubElement(shipfrom,'DeliveryID')
		deliverydate = ET.SubElement(shipfrom,'DeliveryDate')
		warehouseid = ET.SubElement(shipfrom,'WarehouseID')
		locationid = ET.SubElement(shipfrom,'LocationID')
		#address
		address = ET.SubElement(shipfrom,'Address')
		buildingnumber = ET.SubElement(address,'BuildingNumber')
		streetname = ET.SubElement(address,'StreetName')
		addressdetail = ET.SubElement(address,'AddressDetail')
		city = ET.SubElement(address,'City')
		postalcode = ET.SubElement(address,'PostalCode')
		region = ET.SubElement(address,'Region')
		country = ET.SubElement(address,'Country')

		movementendtime = ET.SubElement(invoice,'MovementEndTime')
		movementstarttime = ET.SubElement(invoice,'MovementStartTime')

		#line
		line = ET.SubElement(invoice,'Line')
		facturaitems = frappe.db.sql(""" select * from `tabSales Invoice Item` where parent = %s """,(factura.name), as_dict=True)
		
		for facturaitem in facturaitems:

			linenumber = ET.SubElement(line,'LineNumber')
			linenumber.text = str(facturaitem.idx)


			#orderreferences
			orderreferences = ET.SubElement(line,'OrderReferences')
			originatingon = ET.SubElement(orderreferences,'OriginatingON')
			orderdate = ET.SubElement(orderreferences,'OrderDate')

			productcode = ET.SubElement(line,'ProductCode')
			productcode.text = facturaitem.item_code

			productdescription = ET.SubElement(line,'ProductDescription')
			productdescription.text = facturaitem.item_name

			quantity = ET.SubElement(line,'Quantity')
			quantity.text = str(facturaitem.qty)


			unifofmeasure = ET.SubElement(line,'UnifOfMeasure')
			unifofmeasure.text = facturaitem.uom

			unitprice = ET.SubElement(line,'UnitPrice')
			unitprice.text = str(facturaitem.rate)+"0"

			taxbase = ET.SubElement(line,'TaxBase')
			taxbase.text = str(facturaitem.net_rate)+"0"

			taxpointdate = ET.SubElement(line,'TaxPointDate')
			taxpointdate.text = facturaitem.delivery_note	#DN

			#references
			references = ET.SubElement(line,'References')
			reference = ET.SubElement(references,'Reference')
			reason = ET.SubElement(references,'Reason')

			description = ET.SubElement(line,'Description')
			description.text = facturaitem.item_description

			#productserialnumber
			productserialnumber = ET.SubElement(line,'ProductSerialNumber')
			serialnumber = ET.SubElement(productserialnumber,'SerialNumber')
			serialnumber.text = facturaitem.serial_no

			debitamount = ET.SubElement(line,'DebitAmount')
			debitamount.text = str(facturaitem.amount)+"0"

			creditamount = ET.SubElement(line,'CreditAmount')

		#tax
		tax = ET.SubElement(line,'Tax')
		taxtype = ET.SubElement(tax,'TaxType')
		taxcountryregion = ET.SubElement(tax,'TaxCountryRegion')
		taxcode = ET.SubElement(tax,'TaxCode')
		taxpercentage = ET.SubElement(tax,'TaxPercentage')
		taxamount = ET.SubElement(tax,'TaxAmount')
		taxexemptionreason = ET.SubElement(tax,'TaxExemptionReason')
		taxexemptioncode = ET.SubElement(tax,'TaxExemptionCode')
		settlementamount = ET.SubElement(tax,'SettlementAmount')

		#customsinformation
		customsinformation = ET.SubElement(line,'CustomsInformation')
		arcno = ET.SubElement(customsinformation,'ARCNo')
		iecamount = ET.SubElement(customsinformation,'IECAmount')
		#documenttotals
		documenttotals = ET.SubElement(line,'DocumentTotals')
		taxpayable = ET.SubElement(documenttotals,'TaxPayable')
		nettotal = ET.SubElement(documenttotals,'NetTotal')
		grosstotal = ET.SubElement(documenttotals,'GrossTotal')
		#currency
		currency = ET.SubElement(line,'Currency')
		currencycode = ET.SubElement(currency,'CurrencyCode')
		currencyamount = ET.SubElement(currency,'CurrencyAmount')
		exchangerate = ET.SubElement(currency,'ExchangeRate')
		#settlement
		settlement = ET.SubElement(line,'Settlement')
		settlementdiscount = ET.SubElement(settlement,'SettlementDiscount')
		settlementamount = ET.SubElement(settlement,'SettlementAmount')
		settlementdate = ET.SubElement(settlement,'SettlementDate')
		paymentterms = ET.SubElement(settlement,'PaymentTerms')
		#payment
		payment = ET.SubElement(line,'Payment')
		paymentmechanism = ET.SubElement(payment,'PaymentMechanism')
		paymentamount = ET.SubElement(payment,'PaymentAmount')
		paymentdate = ET.SubElement(payment,'PaymentDate')
		#witholdingtax
		withholdingtax = ET.SubElement(line,'WithholdingTax')
		withholdingtaxtype = ET.SubElement(withholdingtax,'WithholdingTaxType')
		withholdingtaxdescription = ET.SubElement(withholdingtax,'WithholdingTaxDescription')
		withholdingtaxamount = ET.SubElement(withholdingtax,'WithholdingTaxAmount')


	#END OF SAlesInvoice


	#create WorkingDocuments...

	#create Payments



	#record the data...	
	mydata = ET.tostring(data, encoding='utf8')

	myfile = open("/tmp/clientes.xml","w")

	myfile.write(mydata)

	print 'file created'

	#END OF SAFT_AO

@frappe.whitelist()
def convert_csv_xml(ficheiro="csv_xml.csv", delimiter1 = None, site="http://127.0.0.1:8000"):

	#delimiter default , but added ;
	if delimiter1 == None:
		delimiter1 = str(u',').encode('utf-8') 
	if delimiter1 == ';':
		delimiter1 = str(u';').encode('utf-8') 	
	
	if not "tmp" in ficheiro:
		ficheiro = "/tmp/" + ficheiro	

	linhainicial = False
	colunas = []

	with open (ficheiro) as csvfile:
			readCSV = csv.reader(csvfile, delimiter = delimiter1)	

			for row in readCSV:
				if "DocType:" in row[0]:
					print row[1]	#Doctype name

				if "Column Name:" in row[0]:
					print len(row)	#Fields count
					for cols in row:	#Fields name print.
						print cols
						colunas.append(cols)
					#print row[1]	# 1st Fields...


				if linhainicial == True:	
					#Data starts here ....
#					print "Data starts here ...."
					for idx, cols in enumerate(row):
						#print idx
						#print cols
						print colunas[idx]
						print cols

				if "Start entering data below this line" in row[0]:
					print row
					linhainicial = True

			#testing ....
			convert_xml()



@frappe.whitelist()
def test_xs():
	from lxml import etree as ET
	from lxml.builder import ElementMaker

	NS_DC = "http://purl.org/dc/elements/1.1/"
	NS_OPF = "http://www.idpf.org/2007/opf"
	SCHEME = ET.QName(NS_OPF, 'scheme')
	FILE_AS = ET.QName(NS_OPF, "file-as")
	ROLE = ET.QName(NS_OPF, "role")
	opf = ElementMaker(namespace=NS_OPF, nsmap={"opf": NS_OPF, "dc": NS_DC})
	dc = ElementMaker(namespace=NS_DC)
#	validator = ET.RelaxNG(ET.parse("/tmp/opf-schema.xml"))

	tree = (
	    opf.package(
		{"unique-identifier": "uuid_id", "version": "2.0"},
		opf.metadata(
		    dc.identifier(
		        {SCHEME: "uuid", "id": "uuid_id"},
		        "d06a2234-67b4-40db-8f4a-136e52057101"),
		    dc.creator({FILE_AS: "Homes, A. M.", ROLE: "aut"}, "A. M. Homes"),
		    dc.title("My Book"),
		    dc.language("en"),
		),
		opf.manifest(
		    opf.item({"id": "foo", "href": "foo.pdf", "media-type": "foo"})
		),
		opf.spine(
		    {"toc": "uuid_id"},
		    opf.itemref({"idref": "uuid_id"}),
		),
		opf.guide(
		    opf.reference(
		        {"href": "cover.jpg", "title": "Cover", "type": "cover"})
		),
	    )
	)
#	validator.assertValid(tree)

	print(ET.tostring(tree, pretty_print=True).decode('utf-8'))



def get_first_day(dt, d_years=0, d_months=0):
    # d_years, d_months are "deltas" to apply to dt
    y, m = dt.year + d_years, dt.month + d_months
    a, m = divmod(m-1, 12)
    return date(y+a, m+1, 1)

def get_last_day(dt):
    return get_first_day(dt, 0, 1) + timedelta(-1)
