/* Sapns grid */

(function($) {

    // SapnsGrid (constructor)
    function SapnsGrid(settings) {
        
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
        
        /*
         * caption=caption, 
         * name=cls, 
         * cls=cls_.name,
         * search_url=url('/dashboard/list/'),
         * cols=cols, 
         * data=data,
         * actions=actions, pag_n=pag_n, rp=rp, pos=pos,
         * totalp=totalp, total=ds.count, total_pag=total_pag
         */
        
        set(this, 'caption', '');
        if (typeof(this.caption) == 'function') {
            this.caption = this.caption();
        }
        set(this, 'name', 'grid_' + Math.floor(Math.random()*999999));
        set(this, 'cls', null);
        set(this, 'with_search', true);
        set(this, 'search_url', "{{tg.url('/dashboard/list/')}}");
        set(this, 'show_ids', false);
        set(this, 'came_from', '');
        set(this, 'link', '');
        set(this, 'q', '');
        set(this, 'ch_attr', '');
        set(this, 'parent_id', '');
        set(this, 'data', {});
        if (typeof(this.data) == 'function') {
            this.data = this.data();
        }
        
        set(this, 'actions', []);
        if (typeof(this.actions) == 'function') {
            this.actions = this.actions();
        }
        
        set(this, 'exportable', true);
        
        set(this, 'with_pager', true);
        set(this, 'pag_n', 1);
        set(this, 'rp', 10);
        set(this, 'pos', 0);
        set(this, 'totalp', 0);
        set(this, 'total', 0);
        set(this, 'total_pag', 0);
        
        /*
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
        */
    }
    
    // setValue
    SapnsGrid.prototype.setValue = function(value, no_callback) {
        var change = this.value != value;
        var old_value = this.value;

        this.value = value;
        if (change && this.onChange && !no_callback) {
            this.onChange(value, old_value);
        }
    }
    
    // getValue
    SapnsGrid.prototype.getValue = function() {
        return this.value;
    }

    // click_search
    SapnsGrid.prototype.click_search = function(q) {
        
        var sapnsSelector = this;
        var dialog_name = "#dialog-" + this.name;
        
        if (q == undefined) {
            q = $(dialog_name + ' .sp-search-text').val();
        }
        
        // search params
        var params = {
                cls: this.rc,
                q: q,
                rp: this.dialog.results
        };
        
        if (this.search_params != null) {
            if (typeof(this.search_params) == 'object') {
                for (k in this.search_params) {
                    params[k] = this.search_params[k];
                }
            }
            else if (typeof(this.search_params) == 'function') {
                params.search_params = this.search_params;
                params.search_params();
            }
        }

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
    SapnsGrid.prototype.search_kp = function(event) {
        if (event.which == 13) {
            this.click_search();
        }
    }

    $.fn.sapnsGrid = function(arg1, arg2, arg3) {
        
        if (typeof(arg1) == "object") {
            
            var g = new SapnsGrid(arg1);
            
            this.append('<div id="grid-dialog" style="display: none;"></div>');
            
            var g_content = '';            
            g_content += '<div class="sp-grid-container" id="' + g.name + '" cls="' + g.cls + '">';
            
            if (g.caption) {
                g_content += '<div class="sp-grid-caption">' + g.caption + '</div>';
            }
            
            if (g.with_search) {
                
                g_content += '<div>';
                g_content += '<div style="float: left;">' +
                    '<form class="sp-search-form" method="post" action="' + g.search_url + g.cls + '">' +
                        '<input type="hidden" name="caption" value="' + g.caption + '">' +
                        '<input type="hidden" name="show_ids" value="' + g.show_ids + '">' +
                        '<input type="hidden" name="came_from" value="' + g.came_from + '">' +
                        '<input class="sp-search-txt" name="q" type="text" value="' + g.q + '">' +
                        '<input type="hidden" name="ch_attr" value="' + g.ch_attr + '">' +
                        '<input type="hidden" name="parent_id" value="' + g.parent_id + '">' +
                        "<input class=\"sp-button sp-search-btn\" type=\"button\" value=\"{{_('Search...')}}\">" +
                    '</form></div>'

                if (g.link) {
                    g_content += 
                        '<div style="padding-left: 20px;">' +
                        "<button id='link-shortcut' class='sp-button' style='float: left;'>{{_('Create a shortcut')}}</button>" +
                        '<div style="font-size: 9px; margin-top: 7px; width: 100px; float: left;">' +
                            "<a id='this-search' href='" + g.link + "' target='_blank'>[{{_('this search')}}]</a>" +
                        '</div>' +
                        '<div id="link-shortcut-dialog" style="display: none;">' +
                            "<p>{{_('Do you want to create a shortcut for this search?')}}</p>" +
                            "<label>{{_('Shortcut title')}}:</label>" +
                            "<input id='link-shortcut-title' type='text' value='({{_('title')}})'>" +
                        '</div>' +
                    '</div>';
                }
                g_content += '</div>';
                
            }
            
            this.append(g_content);
            
            var g_table = 
                '<div style="overflow: auto; clear: left;">' +
                '<table class="sp-grid">' +
                    '<tr>' +
                    '<td class="sp-col-title">#</td>';
            
            //console.log(JSON.stringify(g));
            for (var i=0, l=g.data.cols.length; i<l; i++) {
                var col = g.data.cols[i];
                //console.log(col);
                var wd = col.width;
                if (!wd) {
                    wd = 60;
                }
                
                g_table += '<td class="sp-col-title" style="width: ' + wd + 'px;">' + col.title + '</td>';
            }
            
            g_table += '</tr>';
            
            var data = g.data.data;
            if (typeof(data) == 'function') {
                data = data();
            }
            
            var ld = data.length;
            //console.log(ld);
            if (ld > 0) {
            for (var i=0; i<ld; i++) {
                
                var row = data[i];
                
                g_table += '<tr class="sp-grid-row">' +
                    '<td title="' + (i+1) + '"><input class="sp-grid-rowid" type="checkbox" id_row="' + row[0] + '"></td>';
                
                for (var j=0, lr=row.length; j<lr; j++) {
                    var col = g.data.cols[j];
                    var al = col.align;
                    if (!al) {
                        al = 'center';
                    }
                    
                    var wd = col.width;
                    if (!wd) {
                        wd = 60;
                    }
                    
                    var cell = row[j];
                    if (!cell) {
                        cell = '';
                    }
                    
                    g_table += '<td class="sp-grid-cell" style="text-align: ' + al + '; width: ' + wd + 'px;"';
                    
                    if (cell) {
                        g_table += 'title="' + cell + '"';
                    }
                    else {
                        g_table += 'title="({{_("empty")}})"';
                    }
                    
                    g_table += 'clickable="true">';
                    
                    if (cell.length > 30) {
                        g_table += (cell+'').substr(0, 30) + '...';
                    }
                    else {
                        g_table += cell;
                    }
                    
                    g_table += '</td>';
                }
                
                g_table += '</tr>';
            }
            }
            else {
                g_table += 
                    '<tr class="sp-grid-row" style="width: 100%;">' +
                        '<td class="sp-grid-cell sp-grid-noresults"' + 
                            ' colspan="' + (g.data.cols.length+1) + '">{{_("No results")}}</td>' +
                    '</tr>';
            }
            
            g_table += '</table></div>';
            
            this.append(g_table);
            
            // pager
            var g_pager = '';
            if (g.with_pager) {
            }
            
            this.append(g_pager);
            
            // actions
            var g_actions = '';
            var act_f = [];
            if (g.actions.length > 0) {
                g_actions += '<div class="sp-grid-actions-title">{{_("Actions")}}:</div>';
                for (var i=0, l=g.actions.length; i<l; i++) {
                    
                    var act = g.actions[i];
                    
                    var req_id = act.require_id;
                    if (req_id === undefined) {
                        req_id = true;
                    }
                    
                    if (typeof(act.type) === 'string') {
                        g_actions += '<div style="float: left;">' +
                            '<form class="action-form" method="post" action0="' + act.url + '">' +
                            '<input type="hidden" name="cls" value="' + g.cls + '">' +
                            '<input type="hidden" name="came_from" value="' + g.link + '">';
                        
                        if (g.parent_id) {
                            g_actions += '<input type="hidden" name="_' + g.ch_attr + '" value="' + g.parent_id + '">';
                        }
    
                        g_actions += '<input class="sp-button sp-grid-action" type="button" value="' + act.title + '"' +
                            ' title="' + act.url + '" url="' + act.url + '" action-type="' + act.type + '"' +
                            ' require_id="' + req_id + '" >';
                        
                        g_actions += '</form></div>';
                    }
                    else {
                        g_actions += 
                            '<div style="float: left;">' +
                                '<button id="' + act.type.id + '" class="sp-button sp-grid-action" ' +
                                    ' require_id="' + req_id + '" >' + act.title + '</button>' +
                            '</div>';
                        
                        act_f.push(act.type);
                    }
                }
            }
            
            // export
            if (g.exportable) {
                g_actions += 
                    '<div id="grid-export" style="background-color: none; height: 25px; margin-left: 0px;">' +
                    '<select id="select-export" class="sp-button sp-grid-action" style="height: 20px;">' +
                        '<option value="">({{_("Export")}})</option>' +
                        '<option value="csv">CSV</option>' +
                        '<option value="excel">Excel</option>' +
                    '</select>' +
                    '</div>';
            }
            
            this.append(g_actions);
            
            // assign functions to actions
            for (var i=0, l=act_f.length; i<l; i++) {
                $('#' + act_f[i].id).data('_func', act_f[i].f);
                
                $('#' + act_f[i].id).click(function() {
                    if ($(this).attr('require_id') == 'true') {
                     // TODO: obtener id seleccionado y pasárselo a la función
                        var selected_id = 123;
                        $(this).data('_func')(selected_id);
                    }
                    else {
                        $(this).data('_func')();
                    }
                });
            }
            
            this.data('sapnsGrid', g);
        }
        else if (typeof(arg1) == "string") {
            
            var sapnsGrid = this.data('sapnsGrid');
            
            // setValue(arg2)
            // $(element).sapnsSelector("setValue", 123);
            // $(element).sapnsSelector("setValue", null);
            if (arg1 == "setValue") {
                sapnsSelector.setValue(arg2, arg3);
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

{% macro js_select_row(_) %}
{# This function is in its own macro because the select dialog doesn't need more
   than just this function #}
<script type="text/javascript">
    $(document).ready(function() {
        // {# select a row #} 
        $('.sp-grid-cell').click(function() {
            if ($(this).attr('clickable') == 'true') {
                var row_id = $(this).parent().find('.sp-grid-rowid');
                $('.sp-grid-rowid').each(function() {
                	if ($(this) != row_id) {
                		$(this).attr('checked', false);
                	}
                });
                
                if (row_id.attr('checked') == true) {
                    row_id.attr('checked', false);
                }
                else {
                    row_id.attr('checked', true);
                }
            }
        });
    });
</script>
{% endmacro %}

{% macro js_functions(_) %}
<script type="text/javascript">
    $(document).ready(function() {
    	
    	$('.sp-grid-cell').qtip({
    		content: {
    			text: true
    		},
    		position: {
    		    my: "left top",
    		    at: "bottom center"
    		},
    		style: "ui-tooltip-dark ui-tooltip-rounded"
    	});
    	
    	// {# default DELETE action #} 
    	function delete_action(button, selected_row, id) {
    		
    		var cls = button.parent().find('input[name=cls]').val();
    		var url = button.attr('url');
    		
    		var delete_html = 
    			"<p id='delete-question'>{{_('Do you really want to delete this record?')}}</p>" +
    			"<p id='object-title'></p>";
    			
    		var error_html =
    			"<p id='delete-error-title'>{{_('Oops, something went wrong...')}}</p>" +
    			"<div id='delete-error-message'></div>";
    		
    	    $('#grid-dialog').html(delete_html);
    			
    	    // {# get object's title #} 
    	    var title = '';
    		$.ajax({
    			url: "/dashboard/title",
    			type: "get",
    			dataType: "json",
    			data: {
    				cls: cls,
    				id: id,    		
    			},
    			success: function(res) {
    				if (res.status) {
    					$('#grid-dialog #object-title').html(res.title);
    				}
    			},
    		    error: function() {
    		    	// {# alert('error!'); #} 
    		    }
    		});

    		$('#grid-dialog').dialog({
    			width: 650,
    			height: 210,
    			resizable: false,
    			modal: true,
    			title: "{{_('Delete')}}",
    			buttons: {
    				"{{_('Ok')}}": function() {
    					$.ajax({
    						url: url,
    						type: "get",
    						dataType: "json",
    						data: {
    							cls: cls,
    							id: id,
    						},
    						success: function(res) {
    							if (res.status) {
    								selected_row.remove();
      							    $('#grid-dialog').dialog('close');
    							}
    							else {
    								$('#grid-dialog').dialog('close');
    								
    								var message = "<p style='color: gray;'>" + res.message + "</p>";

    								if (res.rel_tables != undefined && res.rel_tables.length > 0) {
    									message += "<div>{{_('For your information this object is related with other objects in the following classes:')}}</div>";
    									message += "<ul>";
    									
    									for (var i=0; i<res.rel_tables.length; i++) {
    										var title = res.rel_tables[i].class_title;
    										var attr_title = res.rel_tables[i].attr_title;
    										message += '<li><span style="font-weight: bold;">' + title + '</span>' + 
    										  ' (<span style="color: gray;">' + attr_title + '</span>)</li>';
    									}
    									
    									message += "</ul>";
    								}
    								
    								// {# load message #} 
    								$('#grid-dialog').html(error_html).find('#delete-error-message').html(message);
    								
    								// {# show error dialog #} 
                                    $('#grid-dialog').dialog({
                                    	width: 700,
                                        height: 250,
                                        buttons: {"{{_('Close')}}": function() {
                                            $('#grid-dialog').dialog('close');
                                        }}
                                    });
    							}
    						},
    						error: function() {
    							$('#grid-dialog').dialog('close');
    							$('#grid-dialog').html(error_html).dialog({
    								buttons: {
    									"{{_('Close')}}": function() {
    										$('#grid-dialog').dialog('close');
    									}
    								}
    							});
    						},
    					});
    				},
    				"{{_('Cancel')}}": function() {
    					$('#grid-dialog').dialog('close');
    				}
    			}
    		});
    	}
    	
    	function selected_id(grid) {
            // {# get the id of the selected row #} 
            var selected_row = null;
            var id_selected = null;
            $('#' + grid + ' .sp-grid-row ').each(function() {
                var rowid = $(this).find('.sp-grid-rowid');
                if (rowid.attr('checked') == true) {
                    id_selected = rowid.attr('id_row');
                    selected_row = $(this);
                }
            });
            
            return selected_row;
    	}
    	
        function search(button) {
            
            // {# parent grid of this search #} 
            var grid_id = button.parent().parent().parent().parent().attr('id');

            // {# results per page #} 
            var rp = $('#' + grid_id + ' .sp-grid-rp').val();
            
            // {# Add params to the form #} 
            var params = 
                '<input name="rp" type="hidden" value="' + rp + '">';
                
            $('#' + grid_id + ' .sp-search-form').append(params);
            
            // {# submit the search #} 
            $('#' + grid_id + ' .sp-search-form').submit();
        }
    	
    	// {# Link auto-submit with "Search..." button #} 
    	$('.sp-search-form .sp-search-txt').keypress(function(event) {
    		// {# Pressed ENTER (13) in text search box #} 
    		if (event.which == 13) {
    			var grid_id = $(this).parent().parent().attr('id');
    			search($('#' + grid_id + ' .sp-search-btn'));
    		}
    	});

    	// {# Clicking on search button #} 
    	$('.sp-search-form .sp-search-btn').click(function() {
    		search($(this));
    	});
    	
    	// {# Clicking on an action #} 
    	$('.sp-grid-action').click(function(event) {
    	    
            // {# parent grid of this action #} 
            var grid_id = $(this).parent().parent().parent().parent().attr('id');

            // action form 
            var form = $(this).parent();
            
            // child attribute 
            var ch_attr = $('#' + grid_id + ' .sp-search-form input[name=ch_attr]').val();
            /*if (ch_attr != '') {
                var parent_id = $('#' + grid_id + ' .sp-search-form input[name=parent_id]').val();
                form.append('<input type="hidden"' +
                    ' name="_' + ch_attr + '" value="' + parent_id + '">');
            }*/
            
            // if CTRL is pressed open in a new tab 
            form.attr('target', '');
            if (event.ctrlKey) {
                form.attr('target', '_blank');
                // $(form).find('input[name=came_from]').val(''); 
            }
            
            if ($(this).attr('require_id') == 'true') {
        		
        		// {# get the id of the selected row #}
        		var selected_row = selected_id(grid_id);
        		
        		// {# if there's a selected row, go to the corresponding location #} 
        		if (selected_row != null) {
        			
        			var id_selected = selected_row.find('.sp-grid-rowid').attr('id_row');
        			
        			if($(this).attr('action-type') == 'delete') {
        				delete_action($(this), selected_row, id_selected);
        			}
        			else {
        				// "process" actions 
        				if ($(this).attr('action-type') == 'process') {
        					// build the url like this:  
        					//  "/foo/bar/123" 
        					//  where "/foo/bar/" is the url of the action and 
        					//  "123" is the id of the selected row 
        					form.attr('action', form.attr('action0') + id_selected);
        				}
        				else {
        					// other "action types" 
        					form.attr('action', form.attr('action0'));
        					var id_param = form.find('input[name=id]').first();
        					if (id_param.length == 0) {
        						form.append('<input type="hidden" ' + 
        						    ' name="id" value="' + id_selected + '">');
        					}
        					else {
        						id_param.val(id_selected);
        					}
        				}

                        // submit action form 
          			    form.submit();
        			}
        		}
        		else {
        			$('#grid-dialog').
        			    html("<p style='text-align: center'>{{_('You must select a row before click on this action')}}</p>"). 
        			    dialog({
        			    	resizable: false,
        	                height: 100,
        	                width: 450,
        	                modal: true        			    	
        			    });
        		}
    		}
    		else {
    			form.attr('action', form.attr('action0')).submit();
    		}
    	});
    	
    	// {# Changing results per page #} 
    	$('.sp-grid-rp').change(function() {
    		var grid_id = $(this).parent().parent().attr('id');
    		search($('#' + grid_id + ' .sp-search-btn'));
    	});
    	
    	// {# show related class #} 
    	$('#rel-classes-show').click(function() {
    		
    		var grid = $(this).parent().parent();
    		var id_selected = selected_id(grid.attr('id'));    		
    		
    		if (id_selected != null) {
    			
    			id_selected = id_selected.find('.sp-grid-rowid').attr('id_row');
    			
    			var option = $('#rel-classes-sel option:selected');
    			
    			var action = "/dashboard/list/" + option.attr('cls');
    			
    			var params = '';
    			params += '<input type="hidden" name="ch_attr" ' +
    			    'value="' + option.attr('ch_attr') + '">\n';
    			    
    			params += '<input type="hidden" name="parent_id" ' + 
    			    'value="' + id_selected + '">\n';
    			    
    			$('#rel-classes-form').attr('action', action).html(params).submit();
    		}
    	});
    	
    	// {# export button #} 
    	$('#select-export').change(function() {
    		var fmt = $(this).val();
    		
    		if (fmt == '') {
    			// nothing selected 
    			return;
    		}
    		
    		var grid = $(this).parent().parent().parent();
    		
    		var cls = grid.attr('cls');
    		var q = grid.find('.sp-search-form input[name=q]').val();
    		
    	    //<input type="hidden" name="ch_attr" value="{{ch_attr or ''}}"> 
    	    var ch_attr = grid.find('.sp-search-form input[name=ch_attr]').val();
    	    //<input type="hidden" name="parent_id" value="{{parent_id or ''}}"> 
    	    var parent_id = grid.find('.sp-search-form input[name=parent_id]').val();
    		
    	    if (fmt == 'csv') {
    			var type = 'csv';
    			var url = '/dashboard/tocsv';
    		}
    		else if (fmt == 'excel') {
    			var type = 'excel';
    			var url = '/dashboard/toxls';
    		}
    		// TODO other formats...
    		
    		var form_html =
    			'<form action="' + url + '" method="get" >' +
    			    '<input type="hidden" name="cls" value="' + cls + '">' +
    			    '<input type="hidden" name="q" value="' + q + '">' +
    			    '<input type="hidden" name="ch_attr" value="' + ch_attr + '">' +
    			    '<input type="hidden" name="parent_id" value="' + parent_id + '">' +
    			'</form>';
    			
    		$(form_html).appendTo('body').submit().remove();
    		
    		// reset the select 
    		$(this).find('option:first').attr('selected', true);
    	});
    	
    	// create a shortcut from this search 
    	$('#link-shortcut').click(function() {
    		$('#link-shortcut-title').val('').focus();
    		$('#link-shortcut-dialog').dialog({
    			title: "{{_('Create a shortcut for this search')}}",
    			modal: true,
    			width: 450,
    			height: 200,
    			resizable: false,
    			buttons: {
    				"{{_('Ok')}}": function() {
    					var title = $('#link-shortcut-title').val();
    					if (title != '') {
    						
    						$.ajax({
    							url: "/dashboard/sc/from_list",
    							data: {
    								title: title,
    								link: $('#this-search').attr('href')
    							},
    							dataType: "json",
    							type: "get",
    							success: function(data) {
    								if (!data.status) {
    								    alert(data.message);
    								}
    								
    								$('#link-shortcut-dialog').dialog('close');
    							}
    						});
    					}
    				},
    				"{{_('Cancel')}}": function () {
    					$('#link-shortcut-dialog').dialog('close');
    				}
    			}
    		});
    	});
    });
</script>
{% endmacro %}

