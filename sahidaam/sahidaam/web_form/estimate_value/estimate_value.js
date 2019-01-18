frappe.ready(function() {
	// bind events here'



jQuery.fn.btnClick=function(){


		frappe.call({
			method:'sahidaam.api.getConditionParameter',
			args:{'model':$('[data-fieldname="device"]') .val()},
			callback:function(r){
				cond_obj=[]
				r.message.data.forEach(function(d1) {
					cond_json={}
					cond_json["condition"]=d1.condition
					cond_json["check"]=$("input[type='radio'][name='"+d1.condition.replace(/\s/g,'')+"']:checked").val();
					cond_obj.push(cond_json)
				})
				console.log(cond_obj);

				frappe.call({
					method:'sahidaam.api.getEstimateValue',
					args:{'model':$('[data-fieldname="device"]') .val(),'parameter_obj':cond_obj},
					callback:function(r){
						
						if(r.message.status==200){
							console.log(r.message.data)
							alert("Estimate Value Is :"+r.message.data)

						}

					}



				})
				

			}
			})



}

	

	setTimeout(() => {

$('select[data-fieldname="device"]').on('change', function() {
		$(".cnq").empty()
		frappe.call({
			method:'sahidaam.api.getConditionParameter',
			args:{'model':$('[data-fieldname="device"]') .val()},
			callback:function(r){

				if(r.message){
					cond_que=''
					r.message.data.forEach(function(d) {
						console.log(d.condition.replace(/\s/g,''))
						
						cond_que=cond_que+'<P>'+d.condition+'</p><input type="radio" name='+d.condition.replace(/\s/g,'')+' value="Yes">Yes&nbsp;&nbsp;<input type="radio" name='+d.condition.replace(/\s/g,'')+' value="No" checked>No';
					

					})
				cond_que=cond_que+'<br/><br/><button id="cp">Check Price</button>'
				cond_que=cond_que+"<script type='text/javascript'>$('#cp').on('click',function(){ $(this).btnClick()})"
				$(".cnq").append(cond_que)	

					

				}
			}

		})
		}); 	





	
		$('.btn-form-submit').hide();
	},1000)



	



	
})
