# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import frappe
import math
import datetime
from frappe import msgprint
from frappe.utils import money_in_words, flt
from erpnext.setup.utils import get_company_currency
from erpnext.hr.doctype.process_payroll.process_payroll import get_month_details
from erpnext.hr.doctype.employee.employee import get_holiday_list_for_employee


def validate(doc,method):
#	get_edc(doc, method)
	gross_pay = 0
	net_pay = 0
	tot_ded = 0
	tot_cont = 0

	#Salva Payment Days e recalcula o IRT, INSS

	j= frappe.db.sql(""" SELECT count(status) from `tabAttendance` where employee = %s and status = 'Absent' and month(att_date) = %s and year(att_date) = %s and docstatus=1 """,(doc.employee,doc.month,doc.fiscal_year), as_dict=True)
	print doc.employee
	print doc.payment_days - j[0]['count(status)']
	
	doc.numero_de_faltas = j[0]['count(status)']
	doc.payment_days = doc.payment_days - j[0]['count(status)']

	for desconto in frappe.db.sql(""" SELECT * from `tabSalary Detail` where parent = %s """,doc.name, as_dict=True):
		dd = frappe.get_doc("Salary Detail",desconto.name)
		print "valor ", dd.amount
		print "default ", dd.default_amount
		dd.amount = desconto.default_amount
		dd.save()

#	if not (len(doc.get("earnings")) or len(doc.get("deductions"))):
		# get details from salary structure
#		print "BUSCA SALARY STRUCTURE"
#		doc.get_emp_and_leave_details()
#	else:
#		print "BUSCA SALARY STRUCTURE com LEAVE"
#		doc.get_leave_details(lwp = doc.leave_without_pay)

	print "MEU TESTE"
	print "MEU TESTE"
	print "MEU TESTE"
	print "MEU TESTE"
	print "MEU TESTE"
	print "MEU TESTE"
	print "MEU TESTE"
	print "MEU TESTE"
	print "MEU TESTE"
	print "MEU TESTE"
	print "MEU TESTE"

	return

	m = get_month_details(doc.fiscal_year, doc.month)
	msd = m.month_start_date
	med = m.month_end_date
	emp = frappe.get_doc("Employee", doc.employee)
	
	tdim, twd = get_total_days(doc,method, emp, msd, med, m)
	
	get_loan_deduction(doc,method, msd, med)
	get_expense_claim(doc,method)
	holidays = get_holidays(doc, method, msd, med, emp)
	
	lwp, plw = get_leaves(doc, method, msd, med, emp)
	
	doc.leave_without_pay = lwp
		
	doc.posting_date = m.month_end_date
	wd = twd - holidays #total working days
	doc.total_days_in_month = tdim
	att = frappe.db.sql("""SELECT sum(overtime), count(name) FROM `tabAttendance` 
		WHERE employee = '%s' AND att_date >= '%s' AND att_date <= '%s' 
		AND status = 'Present' AND docstatus=1""" \
		%(doc.employee, msd, med),as_list=1)

	half_day = frappe.db.sql("""SELECT count(name) FROM `tabAttendance` 
		WHERE employee = '%s' AND att_date >= '%s' AND att_date <= '%s' 
		AND status = 'Half Day' AND docstatus=1""" \
		%(doc.employee, msd, med),as_list=1)
	
	t_hd = flt(half_day[0][0])
	t_ot = flt(att[0][0])
	doc.total_overtime = t_ot
	tpres = flt(att[0][1])

	ual = twd - tpres - lwp - holidays - plw - (t_hd/2)
	
	if ual < 0:
		frappe.throw(("Unauthorized Leave cannot be Negative for Employee {0}").\
			format(doc.employee_name))
	
	paydays = tpres + (t_hd/2) + plw + math.ceil((tpres+(t_hd/2))/wd * holidays)
	pd_ded = flt(doc.payment_days_for_deductions)
	doc.payment_days = paydays
	
#	if doc.change_deductions == 0:
#		doc.payment_days_for_deductions = doc.payment_days
	
#	doc.unauthorized_leaves = ual 
	
	ot_ded = round(8*ual,1)
	if ot_ded > t_ot:
		ot_ded = (int(t_ot/8))*8
	doc.overtime_deducted = ot_ded
	d_ual = int(ot_ded/8)
	
	#Calculate Earnings
	chk_ot = 0 #Check if there is an Overtime Rate
	for d in doc.earnings:
		if d.salary_component == "Overtime Rate":
			chk_ot = 1
			
	for d in doc.earnings:
		earn = frappe.get_doc("Salary Component", d.salary_component)
		if earn.depends_on_lwp == 1:
			d.depends_on_lwp = 1
		else:
			d.depends_on_lwp = 0
		
		if earn.based_on_earning:
			for d2 in doc.earnings:
				#Calculate Overtime Value
				if earn.earning == d2.salary_component:
					d.default_amount = flt(d2.amount) * t_ot
					d.amount = flt(d2.amount) * (t_ot - ot_ded)
		else:
			if d.depends_on_lwp == 1 and earn.books == 0:
				if chk_ot == 1:
					d.amount = round(flt(d.default_amount) * (paydays+d_ual)/tdim,0)
				else:
					d.amount = round(flt(d.default_amount) * (paydays)/tdim,0)
			elif d.depends_on_lwp == 1 and earn.books == 1:
				d.amount = round(flt(d.default_amount) * flt(doc.payment_days_for_deductions)/ tdim,0)
			else:
				d.amount = d.default_amount
		
		if earn.only_for_deductions <> 1:
			gross_pay += flt(d.amount)

	if gross_pay < 0:
		doc.arrear_amount = -1 * gross_pay
	gross_pay += flt(doc.arrear_amount) + flt(doc.leave_encashment_amount)
	
	#Calculate Deductions
	for d in doc.deductions:
		#Check if deduction is in any earning's formula
		chk = 0
		for e in doc.earnings:
			earn = frappe.get_doc("Salary Component", e.salary_component)
			for form in earn.deduction_contribution_formula:
				if d.salary_component == form.salary_component:
					chk = 1
					d.amount = 0
		if chk == 1:
			for e in doc.earnings:
				earn = frappe.get_doc("Salary Component", e.salary_component)
				for form in earn.deduction_contribution_formula:
					if d.salary_component == form.salary_component:
						d.default_amount = flt(e.default_amount) * flt(form.percentage)/100
						d.amount += flt(e.amount) * flt(form.percentage)/100
			d.amount = round(d.amount,0)
			d.default_amount = round(d.default_amount,0)
		elif d.salary_component <> 'Loan Deduction':
			str = frappe.get_doc("Salary Structure", doc.salary_structure)
			for x in str.deductions:
				if x.salary_component == d.salary_component:
					d.default_amount = x.amount
					d.amount = d.default_amount

		tot_ded +=d.amount
	
	#Calculate Contributions
	for c in doc.contributions:
		#Check if contribution is in any earning's formula
		chk = 0
		for e in doc.earnings:
			earn = frappe.get_doc("Salary Component", e.salary_component)
			for form in earn.deduction_contribution_formula:
				if c.salary_component == form.salary_component:
					chk = 1
		if chk == 1:
			c.amount = round((flt(c.default_amount) * flt(doc.payment_days_for_deductions)/tdim),0)
		tot_cont += c.amount
	
	doc.gross_pay = gross_pay
	doc.total_deduction = tot_ded
	doc.net_pay = doc.gross_pay - doc.total_deduction
	doc.rounded_total = myround(doc.net_pay, 10)
		
	company_currency = get_company_currency(doc.company)
	doc.total_in_words = money_in_words(doc.rounded_total, company_currency)
	doc.total_ctc = doc.gross_pay + tot_cont


	
# TO CLEAN WHAT IS USED AND NOT 
	def validate_dates(self):
		if date_diff(self.end_date, self.start_date) < 0:
			frappe.throw(_("To date cannot be before From date"))
			
	def calculate_component_amounts(self):
		if not getattr(self, '_salary_structure_doc', None):
			self._salary_structure_doc = frappe.get_doc('Salary Structure', self.salary_structure)

		data = self.get_data_for_eval()
		for key in ('earnings', 'deductions'):
			for struct_row in self._salary_structure_doc.get(key):
				amount = self.eval_condition_and_formula(struct_row, data)	
				if amount:
					self.update_component_row(struct_row, amount, key)
					
					
	def update_component_row(self, struct_row, amount, key):
		component_row = None
		for d in self.get(key):
			if d.salary_component == struct_row.salary_component:
				component_row = d
		
		if not component_row:
			self.append(key, {
				'amount': amount,
				'default_amount': amount,
				'depends_on_lwp' : struct_row.depends_on_lwp,
				'salary_component' : struct_row.salary_component
			})
		else:
			component_row.amount = amount
	
	def eval_condition_and_formula(self, d, data):
		try:
			if d.condition:
				if not eval(d.condition, None, data):
					return None	
			amount = d.amount
			if d.amount_based_on_formula:
				if d.formula:
					amount = eval(d.formula, None, data)
				data[d.abbr] = amount
			return amount
			
		except NameError as err:
		    frappe.throw(_("Name error: {0}".format(err)))
		except SyntaxError as err:
		    frappe.throw(_("Syntax error in formula or condition: {0}".format(err)))
		except:
		    frappe.throw(_("Error in formula or condition"))
		    raise	
	
	def get_data_for_eval(self):
		'''Returns data for evaluating formula'''
		data = frappe._dict()
		
		for d in self._salary_structure_doc.employees:
			if d.employee == self.employee:
				data.base, data.variable = d.base, d.variable
	
		data.update(frappe.get_doc("Employee", self.employee).as_dict())
		data.update(self.as_dict())

		# set values for components
		salary_components = frappe.get_all("Salary Component", fields=["salary_component_abbr"])
		for salary_component in salary_components:
			data[salary_component.salary_component_abbr] = 0
			
		return data
		

	def get_emp_and_leave_details(self):
		'''First time, load all the components from salary structure'''
		print " ESTOU NO MEU CARREGA!!!!!!"
		if self.employee:
			self.set("earnings", [])
			self.set("deductions", [])

			self.set_month_dates()
			self.validate_dates()
			joining_date, relieving_date = frappe.db.get_value("Employee", self.employee,
				["date_of_joining", "relieving_date"])

			self.get_leave_details(joining_date, relieving_date)
			struct = self.check_sal_struct(joining_date, relieving_date)

			if struct:
				self._salary_structure_doc = frappe.get_doc('Salary Structure', struct)
				self.salary_slip_based_on_timesheet = self._salary_structure_doc.salary_slip_based_on_timesheet or 0
				self.set_time_sheet()
				self.pull_sal_struct()

	def set_time_sheet(self):
		if self.salary_slip_based_on_timesheet:
			self.set("timesheets", [])
			timesheets = frappe.db.sql(""" select * from `tabTimesheet` where employee = %(employee)s and start_date BETWEEN %(start_date)s AND %(end_date)s and (status = 'Submitted' or
				status = 'Billed')""", {'employee': self.employee, 'start_date': self.start_date, 'end_date': self.end_date}, as_dict=1)

			for data in timesheets:
				self.append('timesheets', {
					'time_sheet': data.name,
					'working_hours': data.total_hours
				})

	def set_month_dates(self):
		if self.month and not self.salary_slip_based_on_timesheet:
			m = get_month_details(self.fiscal_year, self.month)
			self.start_date = m['month_start_date']
			self.end_date = m['month_end_date']

	def check_sal_struct(self, joining_date, relieving_date):
		st_name = frappe.db.sql("""select parent from `tabSalary Structure Employee`
			where employee=%s
			and parent in (select name from `tabSalary Structure`
				where is_active = 'Yes'
				and (from_date <= %s or from_date <= %s)
				and (to_date is null or to_date >= %s or to_date >= %s))
			""",(self.employee, self.start_date, joining_date, self.end_date, relieving_date))
			
		if st_name:
			if len(st_name) > 1:
				frappe.msgprint(_("Multiple active Salary Structures found for employee {0} for the given dates")
					.format(self.employee), title=_('Warning'))
			return st_name and st_name[0][0] or ''
		else:
			self.salary_structure = None
			frappe.msgprint(_("No active or default Salary Structure found for employee {0} for the given dates")
				.format(self.employee), title=_('Salary Structure Missing'))	

	def pull_sal_struct(self):
		from erpnext.hr.doctype.salary_structure.salary_structure import make_salary_slip
		make_salary_slip(self._salary_structure_doc.name, self)

		if self.salary_slip_based_on_timesheet:
			self.salary_structure = self._salary_structure_doc.name
			self.hour_rate = self._salary_structure_doc.hour_rate
			self.total_working_hours = sum([d.working_hours or 0.0 for d in self.timesheets]) or 0.0
			self.add_earning_for_hourly_wages(self._salary_structure_doc.salary_component)
			
			
			
	def process_salary_structure(self):
		'''Calculate salary after salary structure details have been updated'''
		self.pull_emp_details()
		self.get_leave_details()
		self.calculate_net_pay()

	def add_earning_for_hourly_wages(self, salary_component):
		default_type = False
		for data in self.earnings:
			if data.salary_component == salary_component:
				data.amount = self.hour_rate * self.total_working_hours
				default_type = True
				break

		if not default_type:
			earnings = self.append('earnings', {})
			earnings.salary_component = salary_component
			earnings.amount = self.hour_rate * self.total_working_hours

	def pull_emp_details(self):
		emp = frappe.db.get_value("Employee", self.employee, ["bank_name", "bank_ac_no"], as_dict=1)
		if emp:
			self.bank_name = emp.bank_name
			self.bank_account_no = emp.bank_ac_no


	def get_leave_details(self, joining_date=None, relieving_date=None, lwp=None):
		if not self.fiscal_year:
			# if default fiscal year is not set, get from nowdate
			self.fiscal_year = get_fiscal_year(nowdate())[0]

		if not self.month:
			self.month = "%02d" % getdate(nowdate()).month
			self.set_month_dates()

		if not joining_date:
			joining_date, relieving_date = frappe.db.get_value("Employee", self.employee,
				["date_of_joining", "relieving_date"])

		holidays = self.get_holidays_for_employee(self.start_date, self.end_date)

		working_days = date_diff(self.end_date, self.start_date) + 1
		if not cint(frappe.db.get_value("HR Settings", None, "include_holidays_in_total_working_days")):
			working_days -= len(holidays)
			if working_days < 0:
				frappe.throw(_("There are more holidays than working days this month."))

		if not lwp:
			lwp = self.calculate_lwp(holidays, working_days)
		self.total_days_in_month = working_days
		self.leave_without_pay = lwp
		payment_days = flt(self.get_payment_days(joining_date, relieving_date)) - flt(lwp)
		self.payment_days = payment_days > 0 and payment_days or 0

		print ("Numero faltas ",self.numero_de_faltas)

	def get_payment_days(self, joining_date, relieving_date):
		start_date = getdate(self.start_date)

		if joining_date:
			if joining_date > getdate(self.start_date):
				start_date = joining_date
			elif joining_date > getdate(self.end_date):
				return

		end_date = getdate(self.end_date)
		if relieving_date:
			if relieving_date > start_date and relieving_date < getdate(self.end_date):
				end_date = relieving_date
			elif relieving_date < getdate(self.start_date):
				frappe.throw(_("Employee relieved on {0} must be set as 'Left'")
					.format(relieving_date))

		payment_days = date_diff(end_date, start_date) + 1

		if not cint(frappe.db.get_value("HR Settings", None, "include_holidays_in_total_working_days")):
			holidays = self.get_holidays_for_employee(start_date, end_date)
			payment_days -= len(holidays)

		return payment_days

	def get_holidays_for_employee(self, start_date, end_date):
		holiday_list = get_holiday_list_for_employee(self.employee)
		holidays = frappe.db.sql_list('''select holiday_date from `tabHoliday`
			where
				parent=%(holiday_list)s
				and holiday_date >= %(start_date)s
				and holiday_date <= %(end_date)s''', {
					"holiday_list": holiday_list,
					"start_date": start_date,
					"end_date": end_date
				})

		holidays = [cstr(i) for i in holidays]

		return holidays
	
	def calculate_lwp(self, holidays, working_days):
		lwp = 0
		holidays = "','".join(holidays)
		for d in range(working_days):
			dt = add_days(cstr(getdate(self.start_date)), d)
			leave = frappe.db.sql("""
				select t1.name, t1.half_day
				from `tabLeave Application` t1, `tabLeave Type` t2
				where t2.name = t1.leave_type
				and t2.is_lwp = 1
				and t1.docstatus = 1
				and t1.employee = %(employee)s
				and CASE WHEN t2.include_holiday != 1 THEN %(dt)s not in ('{0}') and %(dt)s between from_date and to_date
				WHEN t2.include_holiday THEN %(dt)s between from_date and to_date
				END
				""".format(holidays), {"employee": self.employee, "dt": dt})
			if leave:
				lwp = cint(leave[0][1]) and (lwp + 0.5) or (lwp + 1)
		return lwp	

	def check_existing(self):
		if not self.salary_slip_based_on_timesheet:
			ret_exist = frappe.db.sql("""select name from `tabSalary Slip`
						where month = %s and fiscal_year = %s and docstatus != 2
						and employee = %s and name != %s""",
						(self.month, self.fiscal_year, self.employee, self.name))
			if ret_exist:
				self.employee = ''
				frappe.throw(_("Salary Slip of employee {0} already created for this period").format(self.employee))
		else:
			for data in self.timesheets:
				if frappe.db.get_value('Timesheet', data.time_sheet, 'status') == 'Payrolled':
					frappe.throw(_("Salary Slip of employee {0} already created for time sheet {1}").format(self.employee, data.time_sheet))

	def sum_components(self, component_type, total_field):
		for d in self.get(component_type):
			if cint(d.depends_on_lwp) == 1 and not self.salary_slip_based_on_timesheet:
				d.amount = rounded((flt(d.amount) * flt(self.payment_days)
					/ cint(self.total_days_in_month)), self.precision("amount", component_type))
			elif not self.payment_days and not self.salary_slip_based_on_timesheet:
				d.amount = 0
			elif not d.amount:
				d.amount = d.default_amount
			self.set(total_field, self.get(total_field) + flt(d.amount))

	def calculate_net_pay(self):
		if self.salary_structure:
			self.calculate_component_amounts()

		disable_rounded_total = cint(frappe.db.get_value("Global Defaults", None, "disable_rounded_total"))

		self.gross_pay = flt(self.arrear_amount) + flt(self.leave_encashment_amount)
		self.total_deduction = 0

		self.sum_components('earnings', 'gross_pay')
		self.sum_components('deductions', 'total_deduction')

		self.net_pay = flt(self.gross_pay) - flt(self.total_deduction)
		self.rounded_total = rounded(self.net_pay,
			self.precision("net_pay") if disable_rounded_total else 0)

	def on_submit(self):
		if self.net_pay < 0:
			frappe.throw(_("Net Pay cannot be less than 0"))
		else:
			self.set_status()
			self.update_status(self.name)
			if(frappe.db.get_single_value("HR Settings", "email_salary_slip_to_employee")):
				self.email_salary_slip()

	def on_cancel(self):
		self.set_status()
		self.update_status()

	def email_salary_slip(self):
		receiver = frappe.db.get_value("Employee", self.employee, "prefered_email")

		if receiver:
			subj = 'Salary Slip - from {0} to {1}, fiscal year {2}'.format(self.start_date, self.end_date, self.fiscal_year)
			frappe.sendmail([receiver], subject=subj, message = _("Please see attachment"),
				attachments=[frappe.attach_print(self.doctype, self.name, file_name=self.name)], reference_doctype= self.doctype, reference_name= self.name)
		else:
			msgprint(_("{0}: Employee email not found, hence email not sent").format(self.employee_name))

	def update_status(self, salary_slip=None):
		for data in self.timesheets:
			if data.time_sheet:
				timesheet = frappe.get_doc('Timesheet', data.time_sheet)
				timesheet.salary_slip = salary_slip
				timesheet.flags.ignore_validate_update_after_submit = True
				timesheet.set_status()
				timesheet.save()
				
	def set_status(self, status=None):
		'''Get and update status'''
		if not status:
			status = self.get_status()
		self.db_set("status", status)

	def get_status(self):
		if self.docstatus == 0:
			status = "Draft"
		elif self.docstatus == 1:
			status = "Submitted"
			if self.journal_entry:
				status = "Paid"
		elif self.docstatus == 2:
			status = "Cancelled"
		return status	

# END OF CLEAN TO BE DONE


def get_total_days(doc,method, emp, msd, med, month):
	tdim = month["month_days"] #total days in a month
	if emp.relieving_date is None:
		relieving_date = datetime.date(2099, 12, 31)
	else:
		relieving_date = emp.relieving_date

	if emp.date_of_joining >= msd:
		twd = (med - emp.date_of_joining).days + 1 #Joining DATE IS THE First WORKING DAY
	elif relieving_date <= med:
		twd = (emp.relieving_date - msd).days + 1 #RELIEVING DATE IS THE LAST WORKING DAY
	else:
		twd = month["month_days"] #total days in a month
	return tdim, twd
	
def get_leaves(doc, method, start_date, end_date, emp):
	#Find out the number of leaves applied by the employee only working days
	lwp = 0 #Leaves without pay
	plw = 0 #paid leaves
	diff = (end_date - start_date).days + 1
	for day in range(0, diff):
		date = start_date + datetime.timedelta(days=day)
		auth_leaves = frappe.db.sql("""SELECT la.name FROM `tabLeave Application` la
			WHERE la.status = 'Approved' AND la.docstatus = 1 AND la.employee = '%s'
			AND la.from_date <= '%s' AND la.to_date >= '%s'""" % (doc.employee, date, date), as_list=1)
		if auth_leaves:
			auth_leaves = auth_leaves[0][0]
			lap = frappe.get_doc("Leave Application", auth_leaves)
			ltype = frappe.get_doc("Leave Type", lap.leave_type)
			hol = get_holidays(doc,method, date, date, emp)
			if hol:
				pass
			else:
				if ltype.is_lwp == 1:
					lwp += 1
				else:
					plw += 1
	lwp = flt(lwp)
	plw = flt(plw)
	return lwp,plw
		
def get_holidays(doc,method, start_date, end_date,emp):
	if emp.relieving_date is None:
		relieving_date = datetime.date(2099, 12, 31)
	else:
		relieving_date = emp.relieving_date
	
	if emp.date_of_joining > start_date:
		start_date = emp.date_of_joining
	
	if relieving_date < end_date:
		end_date = relieving_date
	
	holiday_list = get_holiday_list_for_employee(doc.employee)
	holidays = frappe.db.sql("""SELECT count(name) FROM `tabHoliday` WHERE parent = '%s' AND 
		holiday_date >= '%s' AND holiday_date <= '%s'""" %(holiday_list, \
			start_date, end_date), as_list=1)
	
	holidays = flt(holidays[0][0]) #no of holidays in a month from the holiday list
	return holidays
	
def get_loan_deduction(doc,method, msd, med):
	existing_loan = []
	for d in doc.deductions:
		existing_loan.append(d.employee_loan)
		
	#get total loan due for employee
	query = """SELECT el.name, eld.name, eld.emi, el.deduction_type, eld.loan_amount
		FROM 
			`tabEmployee Loan` el, `tabEmployee Loan Detail` eld
		WHERE
			eld.parent = el.name AND
			el.docstatus = 1 AND el.posting_date <= '%s' AND
			eld.employee = '%s'""" %(med, doc.employee)
		
	loan_list = frappe.db.sql(query, as_list=1)

	for i in loan_list:
		emi = i[2]
		total_loan = i[4]
		if i[0] not in existing_loan:
			#Check if the loan has already been deducted
			query = """SELECT SUM(ssd.amount) 
				FROM `tabSalary Detail` ssd, `tabSalary Slip` ss
				WHERE ss.docstatus = 1 AND
					ssd.parent = ss.name AND
					ssd.employee_loan = '%s' and ss.employee = '%s'""" %(i[0], doc.employee)
			deducted_amount = frappe.db.sql(query, as_list=1)

			if total_loan > deducted_amount[0][0]:
				#Add deduction for each loan separately
				#Check if EMI is less than balance
				balance = flt(total_loan) - flt(deducted_amount[0][0])
				if balance > emi:
					doc.append("deductions", {
						"idx": len(doc.deductions)+1, "depends_on_lwp": 0, "default_amount": emi, \
						"employee_loan": i[0], "salary_component": i[3], "amount": emi
					})
				else:
					doc.append("deductions", {
						"idx": len(doc.deductions)+1, "d_depends_on_lwp": 0, "default_amount": balance, \
						"employee_loan": i[0], "salary_component": i[3], "amount": balance
					})
	for d in doc.deductions:
		if d.employee_loan:
			total_given = frappe.db.sql("""SELECT eld.loan_amount 
				FROM `tabEmployee Loan` el, `tabEmployee Loan Detail` eld
				WHERE eld.parent = el.name AND eld.employee = '%s' 
				AND el.name = '%s'"""%(doc.employee, d.employee_loan), as_list=1)
			
			deducted = frappe.db.sql("""SELECT SUM(ssd.amount) 
				FROM `tabSalary Detail` ssd, `tabSalary Slip` ss
				WHERE ss.docstatus = 1 AND ssd.parent = ss.name 
				AND ssd.employee_loan = '%s' and ss.employee = '%s'"""%(d.employee_loan, doc.employee), as_list=1)
			balance = flt(total_given[0][0]) - flt(deducted[0][0])
			if balance < d.amount:
				frappe.throw(("Max deduction allowed {0} for Loan Deduction {1} \
				check row # {2} in Deduction Table").format(balance, d.employee_loan, d.idx))

def get_expense_claim(doc,method):
	m = get_month_details(doc.fiscal_year, doc.month)
	#Get total Expense Claims Due for an Employee
	query = """SELECT ec.name, ec.employee, ec.total_sanctioned_amount, ec.total_amount_reimbursed
		FROM `tabExpense Claim` ec
		WHERE ec.docstatus = 1 AND ec.approval_status = 'Approved' AND
			ec.total_amount_reimbursed < ec.total_sanctioned_amount AND
			ec.posting_date <= '%s' AND ec.employee = '%s'""" %(m.month_end_date, doc.employee)
	
	
	ec_list = frappe.db.sql(query, as_list=1)
	for i in ec_list:
		existing_ec = []
		for e in doc.earnings:
			existing_ec.append(e.expense_claim)
		
		if i[0] not in existing_ec:
			#Add earning claim for each EC separately:
			doc.append("earnings", {
				"idx": len(doc.earnings)+1, "depends_on_lwp": 0, "default_amount": (i[2]-i[3]), \
				"expense_claim": i[0], "salary_component": "Expense Claim", "amount": (i[2]- i[3])
			})

def get_edc(doc,method):
	#Earning Table should be replaced if there is any change in the Earning Composition
	#Change can be of 3 types in the earning table
	#1. If a user removes a type of earning
	#2. If a user adds a type of earning
	#3. If a user deletes and adds a type of another earning
	#Function to get the Earnings, Deductions and Contributions (E,D,C)

	m = get_month_details(doc.fiscal_year, doc.month)
	emp = frappe.get_doc("Employee", doc.employee)
	joining_date = emp.date_of_joining
	if emp.relieving_date:
		relieving_date = emp.relieving_date
	else:
		relieving_date = '2099-12-31'
	
	struct = frappe.db.sql("""SELECT name FROM `tabSalary Structure Employee` WHERE employee = %s AND
		is_active = 'Yes' AND (from_date <= %s OR from_date <= %s) AND
		(to_date IS NULL OR to_date >= %s OR to_date >= %s)""", 
		(doc.employee, m.month_start_date, joining_date, m.month_end_date, relieving_date))
	if struct:
		sstr = frappe.get_doc("Salary Structure", struct[0][0])
		print struct[0][0]
	else:
		frappe.throw("No active Salary Structure for this period")
		
	contri_amount = 0

	existing_ded = []
	
	dict = {}	
	for d in doc.deductions:
		dict['salary_component'] = d.salary_component
		dict['idx'] = d.idx
		dict['default_amount'] = d.default_amount
		existing_ded.append(dict.copy())
	
	doc.contributions = []
	doc.earnings = []
	
	earn = 0
	#Update Earning Table if the Earning table is empty
	if doc.earnings:
		pass
	else:
		earn = 1
	
	chk = 0
	for e in  sstr.earnings:
		for ern in doc.earnings:
			if e.salary_component == ern.salary_component and e.idx == ern.idx:
				chk = 1
		if chk == 0:
			doc.earnings = []
			get_from_str(doc, method)
			
	
	if earn == 1:
		doc.earnings = []
		for e in sstr.earnings:
			doc.append("earnings",{
				"salary_component": e.salary_component,
				"default_amount": e.amount,
				"amount": e.amount,
				"idx": e.idx
			})
			
	ded = 0
	if doc.deductions:
		pass
	else:
		ded = 1

	for d in doc.deductions:
		found = 0
		for dss in sstr.deductions:
			if d.salary_component == dss.salary_component and d.idx == dss.idx and found == 0:
				found = 1
		if found == 0 and ded == 0:
			if d.salary_component <> "Loan Deduction":
				ded = 1
				
	if ded == 1:
		doc.deductions = []
		for d in sstr.deductions:
			doc.append("deductions",{
				"salary_component": d.salary_component,
				"default_amount": d.amount,
				"amount": d.amount,
				"d.idx": d.idx
			})
	
	for c in sstr.contributions:
		contri = frappe.get_doc("Salary Component", c.salary_component)
		for e in doc.earnings:
			earn = frappe.get_doc("Salary Component", e.salary_component)
			for cont in earn.deduction_contribution_formula:
				if c.salary_component == cont.salary_component:
					contri_amount += round(cont.percentage * e.amount/100,0)
			
		doc.append("contributions",{
			"salary_component": c.salary_component,
			"default_amount": c.amount,
			"amount": contri_amount
			})

def get_from_str(doc,method):
	pass	
def myround(x, base=5):
    return int(base * round(float(x)/base))



def unlink_ref_doc_from_salary_slip(ref_no):
	linked_ss = frappe.db.sql_list("""select name from `tabSalary Slip`
	where journal_entry=%s and docstatus < 2""", (ref_no))
	if linked_ss:
		for ss in linked_ss:
			ss_doc = frappe.get_doc("Salary Slip", ss)
			frappe.db.set_value("Salary Slip", ss_doc.name, "status", "Submitted")
			frappe.db.set_value("Salary Slip", ss_doc.name, "journal_entry", "")
