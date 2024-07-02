var amount_set = "0.00";
var loan_month_set = 0;
var calculation_set = "0.00";
var total_int = "0.00";
var other_chargers = 0;

console.log('==============================',$('#other_chargers').val());
if($('#other_chargers') && $('#other_chargers').val()){
	console.log('---------------------------------------')
	other_chargers = $('#other_chargers').val();
	other_chargers = parseFloat(other_chargers);
}

if($('#calculation_set_get') && $('#calculation_set_get').val()){
	calculation_set = $('#calculation_set_get').val();
}

if($('#total_int_get') && $('#total_int_get').val()){
	total_int = $('#total_int_get').val();
}

if($('#loan_amount') && $('#loan_amount').val()){
	amount_set = $('#loan_amount').val();
}
if($('#get_loan_id') && $('#get_loan_id').val()){
	var get_loan_first = $('#get_loan_id').find(":selected").text();
			if (get_loan_first == 'Select Month'){
				loan_month_set = 0
				
			}
			else{
				loan_month_set = get_loan_first
				
			}
}

// if($('#ln_get_loan_id') && $('#ln_get_loan_id').val()){
// 	loan_month_set = $('#ln_get_loan_id').val();
// }

$("#loan_amount").keyup(function(){
    var prefix = ''
	var data = this.value     
    myString = data.replace(/\D/g,'');
    
    // var test = myString.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
    var test = myString;
    this.value = test
    if(this.value.indexOf(prefix) !== 0 ){
        this.value = prefix + this.value;
    }

});
$("#monthly_income").keyup(function(){
    var prefix = ''
    var data = this.value     
    myString = data.replace(/\D/g,'');
    
    // var test = myString.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
    var test = myString;
    this.value = test
    if(this.value.indexOf(prefix) !== 0 ){
        this.value = prefix + this.value;
    }
});

$(function(){
  $('#amount_set').html(amount_set)
  $('#loan_month_set').html(loan_month_set)
  $('#calculation_set').html(calculation_set)
  $('#total_int').html(total_int)

  other_chargers_lst = other_chargers - Math.floor(other_chargers)
  other_chargers = parseInt(other_chargers);
  // other_chargers = parseInt(other_chargers).toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
  $('#product_stmp_per_id').html(other_chargers+"."+other_chargers_lst.toFixed(2).split(".")[1])

  $('#product_stmp_per_id').html(parseFloat(other_chargers).toFixed(2))
});

// Amount input Field Data Fill
var product_int_type = document.getElementById("product_interest_type_id")
var product_stamping_type = document.getElementById("product_stamping_type_id")
var product_stamp_duty_percentage = document.getElementById("product_stamp_duty_percentage_id")
// Simple Interest Calculation
if (product_int_type && product_int_type.value == 'simple'){
	$('#loan_amount').focusout(function(){
		var get_inte_rate = $('#interest_rate_id').text();
		var get_loan = $('#get_loan_id').find(":selected").text();
		total_int = 0
		get_amount = document.getElementById("loan_amount").value.replace(/\D/g,'');
		// if ( get_amount < 5000 || get_amount > 100000) {
	  	// 	get_amount='0'
	  	// 	this.value = get_amount	  		
		// }
		$('#amount_set').html(document.getElementById("loan_amount").value+".00")
		get_amount = parseFloat(get_amount);	  	
	  	var loan_amt_get = document.getElementById("loan_amount").value	  	
	  	if (loan_amt_get != '0' && get_loan != 'Select Month'){
	  		calculation = (get_amount*get_inte_rate)/100;
	  		calculation = calculation/12*get_loan;

			total_int = calculation
		  	calculation = (calculation + get_amount)/get_loan
		}
		else{
			calculation = 0
		}
    	total_int_lst = total_int - Math.floor(total_int)
    	calculation_lst = calculation - Math.floor(calculation)
    	total_int = parseInt(total_int).toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
    	calculation = parseInt(calculation).toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
		$('#calculation_set').html(calculation+"."+calculation_lst.toFixed(2).split(".")[1])
		$('#total_int').html(total_int+"."+total_int_lst.toFixed(2).split(".")[1])
		$('#total_int_get').val($('#total_int').text())
		$('#calculation_set_get').val($('#calculation_set').text())
		
		if($('#product_stmp_per_id') && $('#other_chargers')){			
			if(product_stamping_type && product_stamping_type.value == 'percentage'){
				total_stamp_duty = get_amount*product_stamp_duty_percentage.value/100
				$('#other_chargers').val(total_stamp_duty.toFixed(2))
				total_stamp_duty_lst = total_stamp_duty - Math.floor(total_stamp_duty)
				total_stamp_duty = parseInt(total_stamp_duty).toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
				$('#product_stmp_per_id').html(total_stamp_duty+"."+total_stamp_duty_lst.toFixed(2).split(".")[1])
			}
			else{
				$('#other_chargers').val(parseFloat(other_chargers).toFixed(2))

				other_chargers_lst = other_chargers - Math.floor(other_chargers)
				// other_chargers = parseInt(other_chargers).toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
				other_chargers = parseInt(other_chargers);
				$('#product_stmp_per_id').html(other_chargers+"."+other_chargers_lst.toFixed(2).split(".")[1])

			}
		}		
	});

	// Loan input Field Data Fill
	$('#get_loan_id').change(function(){
		var get_inte_rate = $('#interest_rate_id').text();
		if ($('#interest_rate_id').text()){
			get_inte_rate = $('#interest_rate_id').text()
			$('#interest_rate_get').val(get_inte_rate)
		}
		else{
			get_inte_rate = 0
			$('#interest_rate_get').val(get_inte_rate)
		}
		total_int = 0

		var get_loan = $('#get_loan_id').find(":selected").text();
		if (get_loan == 'Select Month'){
			get_loan = 0
			$('#loan_month_set').html(get_loan)
		}
		else{
			$('#loan_month_set').html(get_loan)
		}
		get_amount = document.getElementById("loan_amount").value.replace(/\D/g,'');
		get_amount = parseFloat(get_amount);

		var get_loan_month = $('#get_loan_id').find(":selected").text();
		if(document.getElementById("loan_amount").value && get_loan_month != 'Select Month'){
			// calculation = (get_amount*get_loan_month)/100;
			calculation = (get_amount*get_inte_rate)/100;
	  		calculation = calculation/12*get_loan;

			total_int = calculation
			calculation = (calculation + get_amount)/get_loan_month

		}
		else{
			calculation = 0
		}

    	total_int_lst = total_int - Math.floor(total_int)
    	calculation_lst = calculation - Math.floor(calculation)

    	// total_int = parseInt(total_int).toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
    	total_int = parseInt(total_int);
    	// calculation = parseInt(calculation).toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
    	calculation = parseInt(calculation);

		$('#calculation_set').html(calculation+"."+calculation_lst.toFixed(2).split(".")[1]);
		$('#total_int').html(total_int+"."+total_int_lst.toFixed(2).split(".")[1]);
		$('#total_int_get').val($('#total_int').text());
		$('#calculation_set_get').val($('#calculation_set').text())
		
		if($('#product_stmp_per_id') && $('#other_chargers')){
			
			if(product_stamping_type && product_stamping_type.value == 'percentage'){
				total_stamp_duty = get_amount*product_stamp_duty_percentage.value/100
				$('#other_chargers').val(total_stamp_duty.toFixed(2))
				total_stamp_duty_lst = total_stamp_duty - Math.floor(total_stamp_duty)
				total_stamp_duty = parseInt(total_stamp_duty);
				// total_stamp_duty = parseInt(total_stamp_duty).toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
				$('#product_stmp_per_id').html(total_stamp_duty+"."+total_stamp_duty_lst.toFixed(2).split(".")[1])
			}
			else{
				$('#other_chargers').val(parseFloat(other_chargers).toFixed(2))

				other_chargers_lst = other_chargers - Math.floor(other_chargers)
				other_chargers = parseInt(other_chargers).toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
				$('#product_stmp_per_id').html(other_chargers+"."+other_chargers_lst.toFixed(2).split(".")[1])

			}
		}

	});
}
// compound Interest Calculation
else{
	$('#loan_amount').focusout(function(){
		var get_inte_rate = $('#interest_rate_id').text();
		var get_loan = $('#get_loan_id').find(":selected").text();
		// if (get_loan == 'Select Month'){
		// 	get_loan = 0
		// }
		// amount get
		total_int = 0
		get_amount = document.getElementById("loan_amount").value.replace(/\D/g,'');
		// if ( get_amount < 5000 || get_amount > 100000) {
	  	// 	get_amount='0'
	  	// 	this.value = get_amount
	  		
		// }
		$('#amount_set').html(document.getElementById("loan_amount").value+".00")
		get_amount = parseFloat(get_amount);
	  	
	  	var loan_amt_get = document.getElementById("loan_amount").value
	  	
	  	if (loan_amt_get != '0' && get_loan != 'Select Month'){

	  		inte_rate_cal = ((get_inte_rate / 100) / 12);
			var monthly_cal = Math.pow(1 + inte_rate_cal, get_loan);
			monthlyPayment = (get_amount*monthly_cal*inte_rate_cal)/(monthly_cal-1);
			total_int = ((monthlyPayment * get_loan)-get_amount);

		}
		else{
			monthlyPayment = 0
		}

		total_int_lst = total_int - Math.floor(total_int)
		monthlyPayment_lst = monthlyPayment - Math.floor(monthlyPayment)

    	total_int = parseInt(total_int).toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
    	// monthlyPayment = parseInt(monthlyPayment).toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
    	monthlyPayment = parseInt(monthlyPayment);

		$('#calculation_set').html(monthlyPayment+"."+monthlyPayment_lst.toFixed(2).split(".")[1]);
		$('#total_int').html(total_int+"."+total_int_lst.toFixed(2).split(".")[1]);
		$('#total_int_get').val($('#total_int').text())
		$('#calculation_set_get').val($('#calculation_set').text())

		if($('#product_stmp_per_id') && $('#other_chargers')){
			
			if(product_stamping_type && product_stamping_type.value == 'percentage'){
				total_stamp_duty = get_amount*product_stamp_duty_percentage.value/100
				$('#other_chargers').val(total_stamp_duty.toFixed(2))
				total_stamp_duty_lst = total_stamp_duty - Math.floor(total_stamp_duty)
				// total_stamp_duty = parseInt(total_stamp_duty).toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
				total_stamp_duty = parseInt(total_stamp_duty);
				$('#product_stmp_per_id').html(total_stamp_duty+"."+total_stamp_duty_lst.toFixed(2).split(".")[1])
			}
			else{
				// $('#other_chargers').val(other_chargers.toFixed(2))	this code tempory not use		

				other_chargers_lst = other_chargers - Math.floor(other_chargers)
				other_chargers = parseInt(other_chargers);
				// other_chargers = parseInt(other_chargers).toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
				$('#product_stmp_per_id').html(other_chargers+"."+other_chargers_lst.toFixed(2).split(".")[1])

			}
		}

	});

	// Loan input Field Data Fill
	
	$('#get_loan_id').change(function(){
		var get_inte_rate = $('#interest_rate_id').text();
		if ($('#interest_rate_id').text()){
			get_inte_rate = $('#interest_rate_id').text()
			$('#interest_rate_get').val(get_inte_rate)
		}
		else{
			get_inte_rate = 0
			$('#interest_rate_get').val(get_inte_rate)
		}
		total_int = 0

		var get_loan = $('#get_loan_id').find(":selected").text();
		if (get_loan == 'Select Month'){
			get_loan = 0
			$('#loan_month_set').html(get_loan)
		}
		else{
			$('#loan_month_set').html(get_loan)
		}
		get_amount = document.getElementById("loan_amount").value.replace(/\D/g,'');
		get_amount = parseFloat(get_amount);

		var get_loan_month = $('#get_loan_id').find(":selected").text();
		if(document.getElementById("loan_amount").value && get_loan_month != 'Select Month'){
			inte_rate_cal = ((get_inte_rate / 100) / 12);
			var monthly_cal = Math.pow(1 + inte_rate_cal, get_loan);
			monthlyPayment = (get_amount*monthly_cal*inte_rate_cal)/(monthly_cal-1);
			total_int = ((monthlyPayment * get_loan)-get_amount);

		}
		else{
			monthlyPayment = 0
		}

		total_int_lst = total_int - Math.floor(total_int)
		monthlyPayment_lst = monthlyPayment - Math.floor(monthlyPayment)

    	total_int = parseInt(total_int).toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
    	monthlyPayment = parseInt(monthlyPayment).toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");

		$('#calculation_set').html(monthlyPayment+"."+monthlyPayment_lst.toFixed(2).split(".")[1]);
		$('#total_int').html(total_int+"."+total_int_lst.toFixed(2).split(".")[1]);
		$('#total_int_get').val($('#total_int').text());
		$('#calculation_set_get').val($('#calculation_set').text())
		
		if($('#product_stmp_per_id') && $('#other_chargers')){
			
			if(product_stamping_type && product_stamping_type.value == 'percentage'){
				total_stamp_duty = get_amount*product_stamp_duty_percentage.value/100
				$('#other_chargers').val(total_stamp_duty.toFixed(2))
				total_stamp_duty_lst = total_stamp_duty - Math.floor(total_stamp_duty)
				total_stamp_duty = parseInt(total_stamp_duty).toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
				$('#product_stmp_per_id').html(total_stamp_duty+"."+total_stamp_duty_lst.toFixed(2).split(".")[1])
			}
			else{
				// $('#other_chargers').val(other_chargers.toFixed(2))			

				other_chargers_lst = other_chargers - Math.floor(other_chargers)
				other_chargers = parseInt(other_chargers).toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
				$('#product_stmp_per_id').html(other_chargers+"."+other_chargers_lst.toFixed(2).split(".")[1])

			}
		}

	});
}