frappe.ready(function() {
	// bind events here'	
		form = frappe.web_form.field_group.fields_dict;
	setTimeout(() => {

$('select[data-fieldname="brand"]').on('change', function() {
			alert('hello')
		});
	form.device.set_input(['A','B']);
	
		$('.btn-form-submit').hide();
	},1000)
	
})
