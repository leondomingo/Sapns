/* Sapns selector */

(function($) {

	// SapnsSelector (constructor)
	function SapnsSelector(settings) {
		
		function set(this_object, key, value, obj) {
			
			if (obj == undefined) {
				obj = settings;
			}

			if (obj[key] == undefined) {
				this_object[key] = value;
			}
			else {
				this_object[key] = obj[key];
			}
			
			return;
		}
		
		set(this, 'fname', null);
		set(this, 'name', '');
		set(this, 'value', null);
		set(this, 'title', '');
		set(this, 'rc', '');
		set(this, 'rc_title', '');
		set(this, 'read_only', false);
		set(this, 'url_title', "{{tg.url('/dashboard/title/')}}");
	    set(this, 'url_search', "{{tg.url('/dashboard/search/')}}");
	    
	    set(this, 'dialog', {});
	    
	    set(this.dialog, 'width', 950, this.dialog);
	    set(this.dialog, 'height', 550, this.dialog);
	    set(this.dialog, 'results', 25, this.dialog);
	}

	// getTitle
	SapnsSelector.prototype.getTitle = function() {
		
		var sapnsSelector = this;
		var id = "#st_" + this.name
		
		if (this.value && this.rc) {
			$.ajax({
				url: sapnsSelector.url_title,
				data: {
					cls: this.rc,
					id: this.value
				},
				success: function(data) {
					if (data.status) {
						$(id).val(data.title);
					}
				}
			});
		}
		else {
			$(id).val('');
		}
	}

	// click_search
	SapnsSelector.prototype.click_search = function(q) {
		
		var sapnsSelector = this;
		var dialog_name = "#dialog-" + this.name;
		
		if (q == undefined) {
	        q = $(dialog_name + ' .sp-search-text').val();
	    }

		$.ajax({
	        url: this.url_search,
	        type: 'post',
	        dataType: 'html',
	        data: {
	            cls: this.rc,
	            q: q,
	            rp: this.dialog.results, // {# maximun number of results in the select dialog #} 
	        },
	        success: function(res) {
	            $(dialog_name).html(res);
	            
	            $(dialog_name + ' .sp-search-button').click(function() {
	                sapnsSelector.click_search();
	            });
	            
	            $(dialog_name + ' .sp-search-text').keypress(function(event) {
	                sapnsSelector.search_kp(event);
	            }).val(q).focus();
	        },
	        error: function(f, status, error) {
	            alert('error!');
	            sapnsSelector.click_search();
	            // {# $(dialog_name).dialog('close'); #} 
	        }
	    });
	}

	// search_kp
	SapnsSelector.prototype.search_kp = function(event) {
	    if (event.which == 13) {
	        this.click_search();
	    }
	}

	// remove
	SapnsSelector.prototype.remove = function() {
		this.value = null;
		this.getTitle();
	}

	$.fn.sapnsSelector = function(callerSettings) {
		
        if (!callerSettings.fname) {
        	
        	this.sapnsSelector = new SapnsSelector(callerSettings);
        	var sapnsSelector = this.sapnsSelector;
        	
			// dialog
			this.append('<div id="dialog-' + sapnsSelector.name + '" style="display: none;"></div>'); 

			// select text
			var select_text = '<input id="st_' + sapnsSelector.name + '"' + 
				' class="sp-select-text"' + 
				' type="text" readonly' + 
				' value=""';
			
			if (sapnsSelector.read_only) {
				select_text += ' disabled';
			}
			
			select_text += '>';
			
			this.append(select_text);
			
			// select_button
			var select_button = '<button id="sb_' + sapnsSelector.name + '"' +
				' class="sp-button sp-select-button" ' +
				' title=\'Set a value for "' + sapnsSelector.title + '"\'' +
				' style="font-weight: bold;"';
			
			if (sapnsSelector.read_only) {
				select_button += ' disabled';
			}
			
			select_button += '>...</button>';
			
			this.append(select_button);
			
			this.find('#sb_' + sapnsSelector.name).click(function() {

				$('#dialog-' + sapnsSelector.name).dialog({
	                title: sapnsSelector.rc_title,
	                width: sapnsSelector.dialog.width,
	                height: sapnsSelector.dialog.height,
	                resizable: false,
	                modal: true,
	                buttons: {
	                    "{{_('Ok')}}": function() {
	                        // {# get the id of the selected row #} 
	                        var id_selected = '';
	                        $('#dialog-' + sapnsSelector.name + ' .sp-grid .sp-grid-rowid').each(function() {
	                            if ($(this).attr('checked') == true) {
	                                id_selected = $(this).attr('id_row');
	                            }
	                        });
	                        
	                        if (id_selected != '') {
	                        	sapnsSelector.value = id_selected;
	                        	sapnsSelector.getTitle();
	                        }
	                        else {
	                        	$('#st_' + sapnsSelector.name).val('');
	                        }
	                        
	                        sapnsSelector.value = id_selected;
	                        
	                        $('#dialog-' + sapnsSelector.name).dialog('close');
	                    },
	                    "{{_('Cancel')}}": function() {
	                        $('#dialog-' + sapnsSelector.name).dialog('close');
	                    }
	                }
	            });
	            
	            sapnsSelector.click_search('');
	        });
			
			sapnsSelector.getTitle();
			
			// remove button
			var remove_button = '';
			if (!sapnsSelector.read_only) {
				remove_button += '<button id="rb_' + sapnsSelector.name + '"' +
					' class="sp-button sp-empty button"' +
					' title=\'Remove value of "' + sapnsSelector.title + '"\'' +
					' style="font-weight: bold; color: red;">X</button>';
			}
		
			this.append(remove_button);
			
			this.find('#rb_' + sapnsSelector.name).click(function() {
				sapnsSelector.remove();
			});
		}
		else if (callerSettings.fname == 'getTitle') {
			this.sapnsSelector.getTitle();
		}
        
		return this;
	};
}) (jQuery);