/* Sapns selector */

(function($) {
	
	var settings;
	
	$.fn.sapnsSelector = function(callerSettings) {
		
		function getTitle() {
			if (settings.value && settings.rc) {
				$.ajax({
					url: settings.url_title,
					data: {
						cls: settings.rc,
						id: settings.value
					},
					success: function(data) {
						if (data.status) {
							$('#st_' + settings.name).val(data.title);
						}
					}
				});
			}
		}
		
		function click_search (q) {
			
			if (q == undefined) {
                q = $('#dlg-' + settings.name + ' .sp-search-text').val();
            }
            
            $.ajax({
                url: settings.url_search,
                type: 'post',
                dataType: 'html',
                data: {
                    cls: settings.rc,
                    q: q,
                    rp: settings.dialog.results, // {# maximun number of results in the select dialog #} 
                },
                success: function(res) {
                    $('#dlg-' + settings.name).html(res);
                    
                    $('#dlg-' + settings.name + ' .sp-search-button').click(function() {
                        click_search();
                    });
                    
                    $('#dlg-' + settings.name + ' .sp-search-text').keypress(function(event) {
                        search_kp(event);
                    }).val(q).focus();
                },
                error: function(f, status, error) {
                    alert('error!');
                    click_search();
                    // {# $('#edit-dialog').dialog('close'); #} 
                }
            });
        }
		
        function search_kp(event) {
            if (event.which == 13) {
                click_search();
            }
        }

        if (!callerSettings.fname) {
			
			// name, value, rel_title, title, rc, rc_title, read_only=False) %}
			settings = $.extend({
				fname: null,
				name: '',
				value: null,
				rel_title: '',
				title: '',
				rc: '',
				rc_title: '',
				read_only: false,
				url_title: "{{tg.url('/dashboard/title/')}}",
				url_search: "{{tg.url('/dashboard/search/')}}",
			}, callerSettings||{});
			
			// settings.dialog
			settings.dialog = $.extend({
				width: 950,
				height: 550,
				results: 25
			}, callerSettings.dialog||{});
			
			// dialog
			this.append('<div id="dlg-' + settings.name + '" style="display: none;"></div>'); 

			// select text
			var select_text = '<input id="st_' + settings.name + '"' + 
				' class="sp-select-text"' + 
				' type="text" readonly' + 
				' value="' + settings.rel_title + '"';
			
			if (settings.read_only) {
				select_text += ' disabled';
			}
			
			select_text += '>';
			
			this.append(select_text);
			
			// select_button
			var select_button = '<button id="sb_' + settings.name + '"' +
				' class="sp-button sp-select-button" ' +
				' title=\'Set a value for "' + settings.title + '"\'' +
				' style="font-weight: bold;"';
			
			if (settings.read_only) {
				select_button += ' disabled';
			}
			
			select_button += '>...</button>';
			
			this.append(select_button);
			
			this.find('#sb_' + settings.name).click(function() {

				$('#dlg-' + settings.name).dialog({
	                title: settings.rc_title,
	                width: settings.dialog.width,
	                height: settings.dialog.height,
	                resizable: false,
	                modal: true,
	                buttons: {
	                    "{{_('Ok')}}": function() {
	                        // {# get the id of the selected row #} 
	                        var id_selected = '';
	                        $('#dlg-' + settings.name + ' .sp-grid .sp-grid-rowid').each(function() {
	                            if ($(this).attr('checked') == true) {
	                                id_selected = $(this).attr('id_row');
	                            }
	                        });
	                        
	                        if (id_selected != '') {
	                            $.ajax({
	                                url: settings.url_title,
	                                type: "get",
	                                dataType: "json",
	                                data: {
	                                    cls: settings.rc,
	                                    id: id_selected
	                                },
	                                success: function(res) {
	                                    if (res.status) {
	                                        $('#st_' + settings.name).val(res.title);
	                                    }
	                                },
	                                error: function() {
	                                }
	                            });
	                        }
	                        else {
	                        	$('#st_' + settings.name).val('');
	                        }
	                        
	                        settings.value = id_selected;
	                        
	                        $('#dlg-' + settings.name).dialog('close');
	                    },
	                    "{{_('Cancel')}}": function() {
	                        $('#dlg-' + settings.name).dialog('close');
	                    }
	                }
	            });
	            
	            click_search('');
	        });
			
			// remove button
			var remove_button = '';
			if (!settings.read_only) {
				remove_button += '<button id="rb_' + settings.name + '"' +
					' class="sp-button sp-empty button"' +
					' title=\'Remove value of "' + settings.title + '"\'' +
					' style="font-weight: bold; color: red;">X</button>';
			}
		
			this.append(remove_button);
		}
		else if (callerSettings.fname == 'getTitle') {
			getTitle();
		}
        
        // get object's title (if "value" is defined)
        getTitle();
		
		return this;
	};
}) (jQuery);