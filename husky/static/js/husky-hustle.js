var labelType, useGradients, nativeTextSupport, animate;
var noAlert = true;
var isOpen  = false;
var timeOut = 12000;
var formID  = '';
var tID     = '';
var shown   = [ ];

$('.remove_item').live('click', removeItem);
$('.add_item').live('click', addItem);
$('.cancel_button').live('click', cancelForm);
$('.submit_button').live('click', submitForm);
$('.submit_form').live('click', submitFormAction);
$('.submit').live('click', submitThisForm);
$('.submit_edit').live('click', submitFormEdit);
$('.set-paid').live('click', setPaid);
$('.set-all-reminders').live('click', setAllReminders);
$('.disconnect').live('click', disconnectSocial);
$('.post-to-social').live('click', postToSocial);
$('.show-edit').live('click', showEdit);
$('.send-email').live('click', sendEmail);
$('.pre-set-amount').live('click', setPreSetAmount);
$('.to-principle').live('click', setPreSetAmount);
$('.to-teacher').live('change', setPreSetAmount);
$('.run-calculations').live('click', runCalculations);
$('.tooltip').live('click', showTooltip);
$('#link_to').live('click', linkToParent);
$('body').keyup(cancelOverlay);

$(document).ready(
	function () {
		if ($('a.closeEl')) $('a.closeEl').bind('click', toggleContent);
	}
);

var toggleContent = function(e)
{
	var targetContent = $('div.itemContent', this.parentNode.parentNode);
	if (targetContent.css('display') == 'none') {
		targetContent.slideDown(300);
		$(this).html('<img src="/static/images/btn_collapse.gif" border="0" alt="collapse" title="collapse" />');
	} else {
		targetContent.slideUp(300);
		$(this).html('<img src="/static/images/btn_expand.gif" border="0" alt="expand" title="expand" />');
	}
	return false;
};


/* Overlay Functions */
function clearMessage(out) {
	if (!out) out = timeOut;
	tID = setTimeout(function(){ $('#message').html(''); }, out);
}

function showOverlay(overlay) {
	if (tID) clearTimeout(tID);
	if (!overlay) overlay = 'overlay';
	$('#'+overlay).css('display', 'block');
	$('#'+overlay).height($(document).height());
	$('#message').css('color','#000000');
	$('#message').css('margin-left','10px');
	$('#message').css('font-weight','bold');
	$('#message').html('Loading...Please Wait!');
}

function showOverlayTop(event) {
	$('.background-cover-top').css({
		display: 'block',
		width: '100%',
		height: $(document).height(),
		opacity: 0,
		'z-index': 1050
	}).animate({opacity: 0.5, backgroundColor: '#000'});
}

function hideOverlay(overlay, out) {
	if (!overlay) overlay = 'overlay';
	$('#'+overlay).css('display', 'none');
	clearMessage(out);
}

function showOverlayBox(overlay, layer) {
	//if box is not set to open then don't do anything
	if (isOpen === false) return;
	// set the properties of the overlay box, the left and top positions
	$(overlay).css({
		display: 'block',
		left: ($(window).width() - $(overlay).width())/2,
		top: 50,
		position: 'absolute'
	});
	// set the window background for the overlay. i.e the body becomes darker
	if (layer) {
		$('.background-cover-top').css({
			display: 'block',
			width: '100%',
			height: $(document).height()
		});
		$(overlay).css({ 'z-index': $(overlay).css('z-index')+layer });
	} else {
		$('.background-cover').css({
			display: 'block',
			width: '100%',
			height: $(document).height()
		});
	}
}

function doOverlayOpen(overlay, layer) {
	formID  = overlay;
	overlay = '#overlay-box-'+overlay;
	//set status to open
	isOpen = true;
	showOverlayBox(overlay, layer);
	if (layer) {
		$('.background-cover-top').css({opacity: 0}).animate({opacity: 0.5, backgroundColor: '#000'});
	} else {
		$('.background-cover').css({opacity: 0}).animate({opacity: 0.5, backgroundColor: '#000'});
	}
	// dont follow the link : so return false.
	return false;
}

function doOverlayClose(overlay, layer) {
	overlay = '#overlay-box-'+overlay;
	//set status to closed
	isOpen = false;
	$(overlay).css('display', 'none');
	// now animate the background to fade out to opacity 0
	// and then hide it after the animation is complete.
	if (layer) {
		$('.background-cover-top').animate( {opacity: 0}, 'fast', null, function() { $(this).hide(); } );
		$(overlay).css({ 'z-index': $(overlay).css('z-index')-layer });
	} else {
		$('.background-cover').animate( {opacity: 0}, 'fast', null, function() { $(this).hide(); } );
	}
}

function doOverlaySwap(close_overlay, open_overlay) {
	// close the current overlay
	overlay = '#overlay-box-'+close_overlay;
	//set status to closed
	isOpen = false;
	$(overlay).css('display', 'none');
	// open the next overlay
	overlay = '#overlay-box-'+open_overlay;
	//set status to open
	isOpen = true;
	showOverlayBox(overlay);
	return false;
}


/* Main Functions */
function reloadPage(event, id) {
	var url = window.location.href.replace( '#', '' );
	window.location = url;
}

function showFormDonate(event, id) {
	$('#overlay-box-add').dialog({
		closeOnEscape: true,
		minWidth: 600,
		minHeight: 100,
		modal: true,
		dialogClass: 'tooltip',
		resizable: false,
		close: function(event, ui) { cancelForm(); }
	});
}

function showFormTeacher(event, id) {
	$('#overlay-box-teacher').dialog({
		closeOnEscape: true,
		minWidth: 600,
		minHeight: 100,
		modal: true,
		dialogClass: 'tooltip',
		resizable: false,
		close: function(event, ui) { cancelForm(); }
	});
}

function showEdit(event) {
	var reg  = new RegExp( '(\\w+)_(\\w+)_(\\d+)' );
	var got  = this.id.match( reg );
	var edit = got[1];
	var form = got[2];
	var id   = got[3];
	if (form == 'sponsor') {
		$('.submit_sponsor').attr('id', 'submit_sponsor_'+id);
		$('#sponsor').show();
		$('#sponsor input').each(
			function () {
				var text = $('#row'+id+' td[abbr="'+this.name+'"]').text();
				if (this.name == 'per_lap') {
					if (text == 'yes') {
						$('#per_lap_yes').attr('checked', true);
					} else {
						$('#per_lap_no').attr('checked', true);
					}
				} else if (text) {
					$(this).val( text );
				}
			}
		);
	} else {
		$('#'+form+'_'+id).show();
	}
	$('#overlay-box-edit').dialog({
		closeOnEscape: true,
		minWidth: 600,
		minHeight: 100,
		modal: true,
		dialogClass: 'tooltip',
		resizable: false,
		close: function(event, ui) { $('.form-edit').hide(); }
	});
}

function showBarChart(type) {
	$.getJSON('/admin/reports/' + type, initBarChart);
}

function showTooltip(event) {
	var id = this.id.replace( '_tooltip', '' );
	$('#tooltip_'+id).dialog({
		closeOnEscape: true,
		minWidth: 500,
		minHeight: 100,
//		modal: true
		dialogClass: 'tooltip',
		resizable: false
	});
}

function addItem(event) {
	var id  = this.id.replace( 'add_', '' );
	var reg = new RegExp( '(\\w+)_(\\w+)' );
	var got = id.match( reg );
	var ids = 'items';
	if (got) ids = got[1] + '_' + got[2] + 's';
	$('#'+ids+' option:selected').each(function(){
		var option = $(this)[0].cloneNode(true);
		var value  = $(option).val();
		if (!$('#'+id+' option[value="' + value + '"]').val()) {
			$(option).appendTo('#'+id);
		}
	});
}

function removeItem(event) {
	var id  = this.id.replace( 'remove_', '' );
	$('#'+id+' option:selected').remove();
}

function submitForm(event) {
	var id = this.id.replace( 'submit_', '' );
	var form = $('#'+ id +'_form');
	var params = form.serialize();
	var action = form.attr('action');
	if (id === 'email') {
		if (!$('#email_addresses').val()) {
			alert('You must provide email addresses');
			return false;
		}
	}
	if (id === 'reminder') {
		$('.set-reminder').each(
			function () {
				if ($(this).attr('checked') == 'checked') {
					params += '&donators=' + $(this).val();
				}
			}
		);
	}
	$.ajax(
		{
			url: action,
			type: 'post',
			dataType: 'json',
			data: params,
			timeout: 35000,
			success: reloadPage
		}
	);
	showOverlayTop();
	return false;
}

function submitFormAction(event) {
	var id = this.id.replace( 'submit_', '' );
	var form = $('#'+ id +'_form');
	showOverlayTop();
	setTimeout(function(){ form.submit(); }, 1000);
}

function submitThisForm() {
	var id  = this.id.replace( 'submit_', '' );
	var reg = new RegExp( '(\\w+)_(\\w+)' );
	var got = id.match( reg );
	if (got) {
		id = got[2];
		if (got[1] == 'parent') {
			$('#parent_only').val(1);
			$('#student_last_name').val('');
			$('#student_first_name').val('');
		} else {
			$('#parent_only').val(0);
			$('#parent_last_name').val('');
			$('#parent_first_name').val('');
		}
	}
	showOverlayTop();
	setTimeout(function(){ $('#form_'+ id).submit(); }, 1000);
}

function submitFormEdit(event) {
	var reg  = new RegExp( '\\w+_(\\w+)_(\\d+)' );
	var got  = this.id.match( reg );
	var params = $('#'+got[1]+'_'+got[2]).serialize();
	if (got[1] == 'sponsor') {
		params = $('#sponsor').serialize();
	}
	$.ajax(
		{
			url: '/edit/'+got[1],
			type: 'post',
			dataType: 'json',
			data: params,
			timeout: 15000,
			success: reloadPage
		}
	);
	showOverlayTop();
}

function cancelOverlay(e) {
	var keyCode;
	if (e === null) {
		keyCode = event.keyCode;
	} else { // mozilla
		keyCode = e.which;
	}
	if (keyCode == 27) {
		if (formID.match('_form')) {
			$('#'+formID+' .cancel_button').trigger('click');
		} else if (formID == 'edit') {
			$('.form-'+formID+' .cancel_button').trigger('click');
		} else {
			$('#'+formID+'_form .cancel_button').trigger('click');
		}
		cancelForm(formID, formID);
		formID  = '';
	}
}

function cancelForm(event, cssClass) {
	var id  = $(this).attr('id');
	var form;
	if (id && typeof(id) != 'object') {
		doOverlayClose(id);
		if (id == 'cancel_child' || id == 'cancel_profile') {
			$('.form-edit').hide();
		} else if (id == 'cancel_sponsor') {
			var sponsor_id = $('#id').val();
			$('#sponsor').hide();
			$('#sponsor input').each(
				function () {
					if (this.id) {
						var text = $('#row'+sponsor_id+' td[abbr="'+this.id+'"]').text();
						if (this.id == 'per_lap') {
							$(this).attr('checked', false);
						} else if (text) {
							$(this).attr('value', '');
						}
					}
				}
			);
		} else {
			form = id.replace( 'cancel_', '' );
			$('#'+form+'_form').hide();
		}
	} else if (id && typeof(id) === 'object' && id.name === 'id') {
		$('.input-field').each(
			function () {
				$(this).attr('value', '');
			}
		);
	} else if (this.id && typeof(this.id) != 'object') {
		form = this.id.replace( 'cancel_', '' );
		$('#'+form+'_form').hide();
	}
}

function populateMenu(data, type) {
	if (!type) type = '';
	if (data) {
		for (var i = 0; i < data.length; i++) {
			var option = new Option(data[i]['label'], data[i]['id']);
			$('#'+type).append(option);
		}
	}
}

function updatePage(data) {
	updateStatus(data);
	if (data['status'] != 200) return;
	cancelFormDetails(data['form']);
	path  = '/admin/index';
	path += '/limit/' + ($('#limit').val() ? $('#limit').val() : '10');
	path += '/offset/' + ($('#offset').val() ? $('#offset').val() : '0');
	setTimeout(function(){ top.location.href = path; }, 1200);
}

function updateStatus(data) {
	if (tID) clearTimeout(tID);
	var status_msg = $('#message');
	if (data['status'] != 200) {
		status_msg.css('color','red');
	} else {
		status_msg.css('color','green');
	}
	status_msg.html(data['status_message']);
	clearMessage();
}

function linkToParent(event) {
	alert('A request will be sent to the Parent to Link to your Account?');
}

function setPaid(event) {
	var id = this.id.replace( 'paid-', '' );
	if (confirm("Are you sure you want to reconcile this Donation as Paid?\n\nMark the Donation as Paid if your Sponsor has already paid.") === true) {
		$.getJSON('/paid/' + id, reloadPage);
	} else {
		$(this).attr('checked', false);
	}
}

function setAllReminders() {
	var checked = $(this).attr('checked');
	$('.set-reminder').each(
		function () {
			$(this).attr('checked', checked ? true : false);
		}
	);
}

function setPreSetAmount() {
	var value = $(this).val();
	if (this.className == 'to-principle') {
		if (value) {
			$('#id_first_name').attr('value', value);
			$('#id_first_name').attr('readonly', true);
			$('#id_first_name').show();
			$('#id_teacher').attr('disabled', true);
			$('#id_teacher').hide();
		} else {
			value = $('#id_teacher :selected').val();
			$('#id_first_name').attr('value', value);
			$('#id_first_name').hide();
			$('#id_teacher').attr('disabled', false);
			$('#id_teacher').show();
		}
	} else if (this.className == 'to-teacher') {
			value = $('#id_teacher :selected').val();
			$('#to_principle_teacher').attr('checked', true);
			$('#id_first_name').attr('value', value);
	} else {
		if (value) {
			$('#id_donation').attr('value', value);
			$('#id_donation').attr('readonly', true);
		} else {
			$('#id_donation').attr('value', '');
			$('#id_donation').attr('readonly', false);
		}
	}
}

function sendEmail(event) {
	var id = this.id.replace( 'email-', '' );
	var msg = $('#message').text();
	msg = msg.replace( /{donate_url}/g, $('#donate-'+id).text() );
	msg = msg.replace( /{first_name}/g, $('#first_name-'+id).text() );
	$('#child_first_name').val( $('#first_name-'+id).text() );
	$('#custom_message').html( msg );
	$('#email_form').show();
	$('#overlay-box-email').dialog({
		closeOnEscape: true,
		minWidth: 790,
		minHeight: 400,
		modal: true,
		dialogClass: 'tooltip',
		resizable: false,
		close: function(event, ui) { cancelForm(event, ui); }
	});
}

function sendReminders(event) {
	var senders = false;
	$('.set-reminder').each(
		function () {
			if ($(this).attr('checked') == 'checked') {
				var id = this.id.replace( 'reminder-', '' );
				var text = $('#row'+id+' td[abbr="last_name"]').text();
				if (text == 'teacher') {
					$(this).attr('checked', false);
				} else {
					senders = true;
				}
			}
		}
	);
	if (senders) {
		$('#reminder_form').show();
		$('#overlay-box-reminder').dialog({
			closeOnEscape: true,
			minWidth: 790,
			minHeight: 400,
			modal: true,
			dialogClass: 'tooltip',
			resizable: false,
			close: function(event, ui) { cancelForm(event, ui); }
		});
	} else {
		alert('You must select sponsors to email.  You cannot send Reminders to Teachers.');
	}
}

function makePayment(event) {
	var payments = 0;
	var ids = [];
	$('.set-reminder').each(
		function () {
			if ($(this).attr('checked') == 'checked') {
				var id = this.id.replace( 'reminder-', '' );
				var text = $('#row'+id+' span[abbr="total"]').text();
				payments += parseFloat(text);
				ids.push(id);
			}
		}
	);
	if (payments) {
		if (confirm('You are about to make a payment for: $' + payments) === true) {
			window.location.href = '/payment/brooke-nguyen-408/' + ids.join(',') + '?amount=' + payments;
		}
	} else {
		alert('You must select sponsors to make payments for.');
	}
}

function disconnectSocial(event) {
	$.getJSON($(this).attr('src'), reloadPage);
	return false;
}

function runCalculations() {
	doOverlayOpen('none', 50);
	$.getJSON($(this).attr('href'), reloadPage);
	return false;
}

function postToSocial(event) {
	window.open($(this).attr('src'), '_social', 'height=200,width=550,resizable=yes,scrollbars=yes');
//	$('#post-iframe').attr('src', $(this).attr('src'));
//	doOverlayOpen('post');
}

function deleteSponsors(event) {
	if (confirm('Are you sure you want to delete the selected Sponsors?') === false) {
		return;
	}
	var params = $('#delete_form').serialize();
	$('.set-reminder').each(
		function () {
			if ($(this).attr('checked') == 'checked') {
				params += '&donators=' + $(this).val();
			}
		}
	);
	doOverlayOpen('none', 50);
	$.ajax(
		{
			url: '/delete/sponsor',
			type: 'post',
			dataType: 'json',
			data: params,
			timeout: 15000,
			success: reloadPage
		}
	);
}

(function() {
	var ua = navigator.userAgent,
		iStuff = ua.match(/iPhone/i) || ua.match(/iPad/i),
		typeOfCanvas = typeof HTMLCanvasElement,
		nativeCanvasSupport = (typeOfCanvas == 'object' || typeOfCanvas == 'function'),
		textSupport = nativeCanvasSupport && (typeof document.createElement('canvas').getContext('2d').fillText == 'function');
	labelType = (!nativeCanvasSupport || (textSupport && !iStuff))? 'Native' : 'HTML';
	nativeTextSupport = labelType == 'Native';
	useGradients = nativeCanvasSupport;
	animate = !(iStuff || !nativeCanvasSupport);
})();


function initBarChart(json){
	var barChart = new $jit.BarChart({
		injectInto: 'infovis',
		animate: true,
		orientation: 'vertical',
		barsOffset: 20,
		Margin: {
			top: 5,
			left: 5,
			right: 5,
			bottom: 5
		},
		labelOffset: 5,
		type: useGradients ? 'stacked:gradient' : 'stacked',
		showAggregates:true,
		showLabels:true,
		Label: {
			type: labelType,
			size: 13,
			family: 'Arial',
			color: 'white'
		},
		Tips: {
			enable: true,
			onShow: function(tip, elem, label) {
				tip.innerHTML = "<b>" + elem.name + "</b>: " + elem.value;
			}
		}
	});
	barChart.loadJSON(json);
}
