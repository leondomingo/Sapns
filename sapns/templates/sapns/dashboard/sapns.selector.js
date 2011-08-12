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
		
		set(this, 'name', '');
		set(this, 'value', '');
		set(this, 'title', '');
		set(this, 'rc', '');
		set(this, 'rc_title', '');
		set(this, 'read_only', false);
		set(this, 'title_url', "{{tg.url('/dashboard/title/')}}");
	    set(this, 'search_url', "{{tg.url('/dashboard/search/')}}");
	    set(this, 'search_params', null);
	    set(this, 'edit_url', "{{tg.url('/dashboard/edit/')}}");
	    set(this, 'onChange', null);
	    
	    set(this, 'dialog', {});
	    
	    set(this.dialog, 'width', 950, this.dialog);
	    set(this.dialog, 'height', 550, this.dialog);
	    set(this.dialog, 'results', 25, this.dialog);
	}
	
	// setValue
	SapnsSelector.prototype.setValue = function(value) {
	    var change = this.value != value;
		
		this.value = value;
		if (change && this.onChange) {
		    this.onChange(this);
		}
	}
	
	SapnsSelector.prototype.getValue = function() {
		return this.value;
	}

	// setTitle
	SapnsSelector.prototype.setTitle = function() {
		
		var sapnsSelector = this;
		var id = "#st_" + this.name
		var value = this.value;
		
		if (value && this.rc) {
			$.ajax({
				url: sapnsSelector.title_url,
				data: {
					cls: this.rc,
					id: this.value
				},
				success: function(data) {
					if (data.status) {
						$(id).val(data.title).parent().attr('value', value);
						sapnsSelector.title = data.title;
					}
				}
			});
		}
		else {
			$(id).val('').parent().attr('value', '');
			sapnsSelector.title = '';
		}
	}
	
	// getTitle
	SapnsSelector.prototype.getTitle = function() {
		return this.title;
	}
	
	// getClass
	SapnsSelector.prototype.getClass = function() {
		return this.rc;
	}
	
	// click_search
	SapnsSelector.prototype.click_search = function(q) {
		
		var sapnsSelector = this;
		var dialog_name = "#dialog-" + this.name;
		
		if (q == undefined) {
	        q = $(dialog_name + ' .sp-search-text').val();
	    }
		
		// search params
		var params = {};
		if (this.search_params != null) {
			params = this.search_params;
		}
		
		params.cls = this.rc;
		params.q = q;
		params.rp = this.dialog.results;

		// search
		$.ajax({
	        url: this.search_url,
	        type: 'post',
	        dataType: 'html',
	        data: params,
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
		this.setValue('');
		this.setTitle();
	}

	$.fn.sapnsSelector = function(arg1, arg2) {
		
        if (typeof(arg1) == "object") {
        	
        	var sapnsSelector = new SapnsSelector(arg1);
        	
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
			
			// double-click to edit the selected object (if there's any)
			this.find('#st_' + sapnsSelector.name).dblclick(function() {
	        	var cls = sapnsSelector.getClass();
	        	var id = sapnsSelector.getValue();
	        	if (id != '') {
	        		var url_edit = sapnsSelector.edit_url;
	        		var form_edit =
	        			'<form action="' + url_edit + '" method="post" target="_blank">' +
	        			    '<input type="hidden" name="cls" value="' + cls + '">' +   
	        			    '<input type="hidden" name="id" value="' + id + '">' +
	        			    '<input type="hidden" name="came_from" value="">' +
	        			'</form>';
	        			
	        		$(form_edit).appendTo('body').submit().remove();
	        	}
	        });
			
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
	                        
	                        sapnsSelector.setValue(id_selected);
	                        sapnsSelector.setTitle();
	                        
	                        $('#dialog-' + sapnsSelector.name).dialog('close');
	                    },
	                    "{{_('Cancel')}}": function() {
	                        $('#dialog-' + sapnsSelector.name).dialog('close');
	                    }
	                }
	            });
	            
	            sapnsSelector.click_search('');
	        });
			
			sapnsSelector.setTitle();
			
			// remove button
			var remove_button = '';
			if (!sapnsSelector.read_only) {
				remove_button += '<button id="rb_' + sapnsSelector.name + '"' +
					' class="sp-button sp-empty-button"' +
					' title=\'Remove value of "' + sapnsSelector.title + '"\'' +
					' style="font-weight: bold; color: red;">X</button>';
			}
		
			this.append(remove_button);
			
			this.find('#rb_' + sapnsSelector.name).click(function() {
				sapnsSelector.remove();
			});
			
			//this.sapnsSelector = sapnsSelector;
			this.data('sapnsSelector', sapnsSelector);
		}
		else if (typeof(arg1) == "string") {
			
			var sapnsSelector = this.data('sapnsSelector');
			
			// setValue(arg2)
			// $(element).sapnsSelector("setValue", 123);
			// $(element).sapnsSelector("setValue", null);
			if (arg1 == "setValue") {
				sapnsSelector.setValue(arg2);
				sapnsSelector.setTitle();
			}
			// getValue()
			else if (arg1 == "getValue") {
				return sapnsSelector.value;
			}
			// getTitle()
			else if (arg1 == "getTitle") {
				return sapnsSelector.title;
			}
			// getClass()
			else if (arg1 == "getClass") {
				return sapnsSelector.rc;
			}
			// TODO: other sapnsSelector methods
		}
        
		return this;
	};
}) (jQuery);