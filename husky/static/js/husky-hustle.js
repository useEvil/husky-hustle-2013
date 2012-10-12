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
$('.submit_edit').live('click', submitFormEdit);
$('.set-paid').live('click', setPaid);
$('.set-all-reminders').live('click', setAllReminders);
$('.disconnect').live('click', disconnectSocial);
$('.post-facebook').live('click', postToSocial);
$('.show-edit').live('click', showEdit);
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
	tID = setTimeout(function(){ $('#message').html('') }, out);
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

function hideOverlay(overlay, out) {
    if (!overlay) overlay = 'overlay';
    $('#'+overlay).css('display', 'none');
    clearMessage(out);
}

function showOverlayBox(overlay, layer) {
    //if box is not set to open then don't do anything
    if (isOpen == false) return;
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
	formID  = overlay
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
	window.location.reload();
}

function showFormDonate(event, id) {
	url = window.location.href;
	url = url.replace('account', 'donate');
	window.location.href = url;
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
				var text = $('#row'+id+' td[abbr="'+this.id+'"]').text();
				if (this.id == 'per_lap') {
					if (text == 'yes') $(this).attr('checked', true);
				} else if (text) {
					$(this).val( text );
				}
			}
		);
	} else {
		$('#'+form+'_'+id).show();
	}
	doOverlayOpen(edit);
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
	var params = $('#reminder_form').serialize();
	$('.set-reminder').each(
		function () {
			if ($(this).attr('checked') == 'checked') {
				params += '&donators=' + $(this).val();
			}
		}
	);
	$.ajax(
		{
			url: '/reminders',
			type: 'post',
			dataType: 'json',
			data: params,
			timeout: 15000,
			success: reloadPage,
		}
	);
	doOverlayOpen('none', 50);
}

function submitFormEdit(event) {
	var reg  = new RegExp( '\\w+_(\\w+)_(\\d+)' );
	var got  = this.id.match( reg );
	var params = $('#'+got[1]+'_'+got[2]).serialize();
	if (got[1] == 'sponsor') {
		params = $('#sponsor').serialize();
	}
	doOverlayOpen('none', 50);
	$.ajax(
		{
			url: '/edit/'+got[1],
			type: 'post',
			dataType: 'json',
			data: params,
			timeout: 15000,
			success: reloadPage,
		}
	);
}

function cancelOverlay(e) {
	var keyCode;
	if (e == null) {
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
	}
	cancelForm(formID, formID);
	formID  = '';
}

function cancelForm(event, cssClass) {
	var id  = $(this).attr('id');
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
			var form = id.replace( 'cancel_', '' );
			$('#'+form+'_form').hide();
		}
	} else if (typeof(this.id) != 'object') {
		var form = this.id.replace( 'cancel_', '' );
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
//	cancelUserForm();
	cancelFormDetails(data['form']);
	path  = '/admin/index';
	path += '/limit/' + ($('#limit').val() ? $('#limit').val() : '10');
	path += '/offset/' + ($('#offset').val() ? $('#offset').val() : '0');
	setTimeout(function(){ top.location.href = path }, 1200);
}

function updateStatus(data) {
	if (tID) clearTimeout(tID);
	var status_msg = $('#message');
	if (data['status'] != 200) {
		status_msg.css('color','red');
	} else {
		status_msg.css('color','green');
	}
	status_msg.html(data['message']);
	clearMessage();
}

function setPaid(event) {
	var id = this.id.replace( 'paid-', '' );
	$.getJSON('/paid/' + id);
}

function setAllReminders() {
	var checked = $(this).attr('checked');
	$('.set-reminder').each(
		function () {
			$(this).attr('checked', checked ? true : false);
		}
	);
}

function sendReminders(event) {
	var senders = false;
	$('.set-reminder').each(
		function () {
			if ($(this).attr('checked') == 'checked') {
				senders = true;
			}
		}
	);
	if (senders) {
		$('#reminder_form').show();
		doOverlayOpen('reminder');
	} else {
		alert('You must select sponsors to email.');
	}
}

function disconnectSocial(event) {
	$.getJSON($(this).attr('src'), reloadPage);
	return false;
}

function postToSocial(event) {
	window.open($(this).attr('src'), 'post-social', 'height=200,width=550,resizable=yes,scrollbars=yes')
//	$('#post-iframe').attr('src', $(this).attr('src'));
//	doOverlayOpen('post');
}

function deleteSponsors(event) {
	if (confirm('Are you sure you want to delete the selected Sponsors?') == false) {
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
			success: reloadPage,
		}
	);
}


