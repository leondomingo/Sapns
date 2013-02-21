// Internet Explorer lacks of "Array.indexOf" function
if(!Array.indexOf) {
	Array.prototype.indexOf = function(obj) {
		for(var i=0; i<this.length; i++){
			if(this[i] == obj) {
				return i;
			}
		}
		return -1;
	}
}

$(document).ready(function() {
	
	function item_up(button, item_class, f) {
		//alert($(this).attr('class'));
		var pos = button.parent().parent().attr('pos');
		//alert('pos=' + pos);
		pos = pos*1;
		
		var prev_pos = pos - 1;
		
		if (pos > 0) {
			// get the previous item in the list
			var prev_item = $('.' + item_class + ':eq(' + prev_pos + ')');
			prev_item.attr('pos', pos);
			button.parent().parent().attr('pos', prev_pos);
			
			f();
		}
	}
	
	function item_down(button, item_class, f) {
		var pos = button.parent().parent().attr('pos');
		pos = pos*1;
		
		var next_pos = pos + 1;
		
		var max = $('.' + item_class + ':last').attr('pos')*1;
		if (pos < max) {
			// get the next item in the list
			var next_item = $('.' + item_class + ':eq(' + next_pos + ')');
			next_item.attr('pos', pos);
			button.parent().parent().attr('pos', next_pos);
			
			f();
		}
	}

	function apply_new_order0(item_type, handler_up, handler_down, handler_remove) {
		
		//alert(item_class + '-' + list_id);
		
		var new_order = [];
		$('.' + item_type + '_item').each(function(){
			var pos = $(this).attr('pos')*1;
			new_order[pos] = $(this);
			$(this).remove();
		});
		
		for (var i=0; i<new_order.length; i++) {
			$('#' + item_type + '_list').append(new_order[i]);
			
			// recover click events
			$('.' + item_type + '_item:last .btn_up_' + item_type).bind('click', handler_up);
			$('.' + item_type + '_item:last .btn_down_' + item_type).bind('click', handler_down);
			$('.' + item_type + '_item:last .btn_remove_' + item_type).bind('click', handler_remove);
		}
	}
	
	function update_order(item_class) {
		$('.' + item_class).each(function(i) {
			$(this).attr('pos', i);			
		});
	}
	
	// columns
	function remove_column() {
		$(this).parent().parent().remove();
		update_order('column_item');
	}

	function column_up() {
		item_up($(this), 'column_item', apply_new_order_column);
	}
	
	function column_down() {
		item_down($(this), 'column_item', apply_new_order_column);
	}

	function apply_new_order_column(){
		apply_new_order0('column', column_up, column_down, remove_column);
	}

	$('#btn_add_column').click(function() {
		
		var last_pos = $('.column_item:last').attr('pos');
		if (last_pos == undefined) {
			last_pos = 0;
		}
		else {
			last_pos = (last_pos*1) + 1;
		}
		
		var new_column = 
			'<tr class="column_item" pos="' + last_pos + '">\n' +
	        '<td class="sp-label-field">' + "{{_('Title')}}" + '</td>\n' +
	        '<td><input class="sp-text-field sp_column_title" type="text"/></td>\n' +
	        '<td class="sp-label-field ">' + "{{_('Definition')}}" + '</td>\n' +
	        '<td><input class="sp-text-field sp_column_definition" type="text"/></td>\n' +
	        '<td class="sp-label-field">' + "{{_('Alias')}}" + '</td>\n' +
	        '<td><input class="sp-text-field sp_column_alias" type="text"/></td>\n' +
	        '<td class="sp-label-field">' + "{{_('Align')}}" + '</td>\n' +
	        '<td>\n' +
	        '<select class="sp-button sp_column_align">\n' +
	            '<option value="center">' + "{{_('center')}}" +  '</option>\n' +
	            '<option value="left">' + "{{_('left')}}" + '</option>\n' +
	            '<option value="right">' + "{{_('right')}}" + '</option>\n' +
	        '</select>\n' +
	        '</td>\n' +
	        '<td><input class="sp-button btn_remove_column" type="button" value="' + "{{_('Remove column')}}" + '"/></td>\n' +
	        '<td><input class="sp-button btn_up_column" type="button" value="' + "{{_('Up')}}" + '"/></td>\n' +
	        '<td><input class="sp-button btn_down_column" type="button" value="' + "{{_('Down')}}" + '"/></td>\n' +
			'</tr>\n';
		
		$('#column_list').append(new_column);
		$('#column_list:last .btn_remove_column').click(remove_column);
		
		$('#column_list:last .sp_column_definition').focus();
	});
	
	$('.btn_remove_column').click(remove_column);
	$('.btn_up_column').click(column_up);
	$('.btn_down_column').click(column_down);
	
	// relations
	function remove_relation() {
		$(this).parent().parent().remove();
		update_order('relation_item');
	}

	function relation_up() {
		item_up($(this), 'relation_item', apply_new_order_relation);
	}
	
	function relation_down() {
		item_down($(this), 'relation_item', apply_new_order_relation);
	}

	function apply_new_order_relation(){
		apply_new_order0('relation', relation_up, relation_down, remove_relation);
	}
	
	$('#btn_add_relation').click(function() {
		
		var last_pos = $('.relation_item:last').attr('pos');
		if (last_pos == undefined) {
			last_pos = 0;
		}
		else {
			last_pos = (last_pos*1) + 1;
		}
		
		var new_relation = 
			'<tr class="relation_item" pos="' + last_pos + '">\n' +
	        '<td class="sp-label-field">' + "{{_('Table')}}" + '</td>\n' +
	        '<td><input class="sp-text-field sp_relation_table" type="text"/></td>\n' +
	        '<td class="sp-label-field">' + "{{_('Alias')}}" + '</td>\n' +
	        '<td><input class="sp-text-field sp_relation_alias" type="text"/></td>\n' +
	        '<td class="sp-label-field">' + "{{_('Condition')}}" + '</td>\n' +
	        '<td><input class="sp-text-field sp_relation_condition" type="text"/></td>\n' +
	        '<td><input class="sp-button btn_remove_relation" type="button" value="' + "{{_('Remove relation')}}" + '"/></td>\n' +
	        '<td><input class="sp-button btn_up_relation" type="button" value="' + "{{_('Up')}}" + '"/></td>\n' +
	        '<td><input class="sp-button btn_down_relation" type="button" value="' + "{{_('Down')}}" + '"/></td>\n' +
			'</tr>\n'
		
		$('#relation_list').append(new_relation);
		$('#relation_list:last .btn_remove_relation').click(remove_relation);
		$('#relation_list:last .btn_up_relation').click(relation_up);
		$('#relation_list:last .btn_down_relation').click(relation_down);
		
		$('#relation_list:last .sp_relation_table').focus();
	});
	
	$('.btn_remove_relation').click(remove_relation);
	$('.btn_up_relation').click(relation_up);
	$('.btn_down_relation').click(relation_down);
	
	// filters
	function remove_filter() {
		$(this).parent().parent().remove();
		update_order('filter_item');
	}

	function filter_up() {
		item_up($(this), 'filter_item', apply_new_order_filter);
	}
	
	function filter_down() {
		item_down($(this), 'filter_item', apply_new_order_filter);
	}

	function apply_new_order_filter(){
		apply_new_order0('filter', filter_up, filter_down, remove_filter);
	}
	
	$('#btn_add_filter').click(function() {
		
		var last_pos = $('.filter_item:last').attr('pos');
		if (last_pos == undefined) {
			last_pos = 0;
		}
		else {
			last_pos = (last_pos*1) + 1;
		}
		
		var new_filter = 
			'<tr class="filter_item" pos="' + last_pos + '">\n' +
	        '<td class="sp-label-field sp_filter_lbl">' + "{{_('Definition')}}" + '</td>\n' +
	        '<td><textarea class="sp-text-field sp_filter_definition"></textarea></td>\n' +
	        '<td><input class="sp-button btn_remove_filter" type="button" value="' + "{{_('Remove filter')}}" + '"/></td>\n' +
	        '<td><input class="sp-button btn_up_filter" type="button" value="' + "{{_('Up')}}" + '"/></td>\n' +
	        '<td><input class="sp-button btn_down_filter" type="button" value="' + "{{_('Down')}}" + '"/></td>\n' +
			'</tr>\n'
		
		$('#filter_list').append(new_filter);
		$('#filter_list:last .btn_remove_filter').click(remove_filter);
		$('#filter_list:last .btn_up_filter').click(filter_up);
		$('#filter_list:last .btn_down_filter').click(filter_down);

		$('#filter_list:last .sp_filter_definition').focus();
	});
	
	$('.btn_remove_filter').click(remove_filter);
	$('.btn_up_filter').click(filter_up);
	$('.btn_down_filter').click(filter_down);
	
	// order
	function remove_order() {
		$(this).parent().parent().remove();
		update_order('order_item');
	}
	
	function apply_new_order(){
		apply_new_order0('order', order_up, order_down, remove_order);
	}
	
	function order_up() {
		item_up($(this), 'order_item', apply_new_order);
	}
	
	function order_down() {
		item_down($(this), 'order_item', apply_new_order);
	}
	
	$('#btn_add_order').click(function() {
		
		var last_pos = $('.order_item:last').attr('pos');
		if (last_pos == undefined) {
			last_pos = 0;
		}
		else {
			last_pos = (last_pos*1) + 1;
		}
		
		var new_order = 
			'<tr class="order_item" pos="' + last_pos + '">\n' +
			'<td class="sp-label-field sp_order_lbl">' + "{{_('Definition')}}" + '</td>\n' +
			'<td><input class="sp-text-field sp_order_definition" type="text"/></td>\n' +
			'<td><input class="sp-button btn_remove_order" type="button" value="' + "{{_('Remove order')}}" + '"/></td>\n' +
			'<td><input class="sp-button btn_up_order" type="button" value="' + "{{_('Up')}}" + '"/></td>\n' +
			'<td><input class="sp-button btn_down_order" type="button" value="' + "{{_('Down')}}" + '"/></td>\n' +			
			'</tr>\n'
		
		$('#order_list').append(new_order);
		
		$('#order_list:last .btn_remove_order').click(remove_order);
		$('#order_list:last .btn_up_order').click(order_up);
		$('#order_list:last .btn_down_order').click(order_down);
		
		$('#order_list:last .sp_order_definition').focus();
	});
	
	$('.btn_remove_order').click(remove_order);
	$('.btn_up_order').click(order_up);
	$('.btn_down_order').click(order_down);
	
	// "Save view" button
	$('#btn_save_view').click(function() {
		
		var error = false;
		
		// view (header)
		
		// title
		$('#view_title').removeClass('sp_field_error');
		if ($('#view_title').val() != '') { 
			$('#form_view input[name=title]').val($('#view_title').val());
		}
		else {
			error = true;
			$('#view_title').addClass('sp_field_error');
		}
		
		// code
		$('#view_code').removeClass('sp_field_error');
		if ($('#view_code').val() != '') {
			$('#form_view input[name=code]').val($('#view_code').val());
		}
		else {
			error = true;
			$('#view_code').addClass('sp_field_error');
		}
		
		// columns
		$('.sp_column_definition').removeClass('sp_field_error')
		$('.sp_column_alias').removeClass('sp_field_error');

		var column_items = [];
		var column_aliases = [];
		
		$('.column_item').each(function(i) {
			var item = {
				title: $(this).find('.sp_column_title').val(),
				definition: $(this).find('.sp_column_definition').val(),
				alias: $(this).find('.sp_column_alias').val(),
				align: $(this).find('.sp_column_align').val()
			};
			
			// check for already-used aliases
			var this_alias = item.alias.toLowerCase();

			if (this_alias != '') {
				if (column_aliases.indexOf(this_alias) == -1) {
					column_aliases.push(this_alias);
				}
				else {
					error = true;
					$(this).find('.sp_column_alias').addClass('sp_field_error');
				}
			}

			// "definition" can not be empty
			if (item.definition == '') {
				error = true;
				$(this).find('.sp_column_definition').addClass('sp_field_error');
			}
			
			column_items[i] = item;
		});
		
		$('#form_view input[name=columns]').val(JSON.stringify(column_items));
		
		// relations
		var relation_items = [];
		var table_aliases = [];
		
		$('#view_table').removeClass('sp_field_error');
		relation_items[0] = {
			table: $('#view_table').val(),
			alias: $('#view_table_alias').val(),
			condition: null
		};
		
		var this_alias = $('#view_table_alias').val().toLowerCase();
		if (this_alias != '') {
			table_aliases.push(this_alias);
		}
		
		if (relation_items[0].table == '') {
			error = true;
			$('#view_table').addClass('sp_field_error');
		}
		
		$('.sp_relation_table').removeClass('sp_field_error');
		$('.sp_relation_alias').removeClass('sp_field_error');
		$('.sp_relation_condition').removeClass('sp_field_error');
		
		$('.relation_item').each(function(i) {
			
			var item = {
				table: $(this).find('.sp_relation_table').val(),
				alias: $(this).find('.sp_relation_alias').val(),
				condition: $(this).find('.sp_relation_condition').val()
			};
			
			var this_alias = $(this).find('.sp_relation_alias').val().toLowerCase();
			if (this_alias != '') {
				if (table_aliases.indexOf(this_alias) == -1) {
					table_aliases.push(this_alias);
				}
				else {
					error = true;
					$(this).find('.sp_relation_alias').addClass('sp_field_error');
				}
			}
			
			// table
			if (item.table == '') {
				error = true;
				$(this).find('.sp_relation_table').addClass('sp_field_error');
			}
			
			// condition
			if (item.condition == '') {
				error = true;
				$(this).find('.sp_relation_condition').addClass('sp_field_error');
			}
			
			relation_items[i+1] = item;
		});
		
		$('#form_view input[name=relations]').val(JSON.stringify(relation_items));
		
		// filters
		var filter_items = [];
		$('.sp_filter_definition').removeClass('sp_field_error');
		$('.sp_filter_definition').each(function(i) {
			filter_items[i] = $(this).val();
			if ($(this).val() == '') {
				error = true;
				$(this).addClass('sp_field_error');
			}
		});
		
		$('#form_view input[name=filters]').val(JSON.stringify(filter_items));
		
		// order
		var order_items = [];
		$('.sp_order_definition').removeClass('sp_field_error');
		$('.sp_order_definition').each(function(i) {
			order_items[i] = $(this).val();
			
			if ($(this).val() == '') {
				error = true;
				$(this).addClass('sp_field_error');
			}
		});
		
		$('#form_view input[name=order]').val(JSON.stringify(order_items));
		
		// Submit the view form
		if (!error) {
			$('#form_view').submit();
		}
		else {
			$('#views-dialog').
			    html("<p>{{_('Please, check the information you have entered')}}</p>").
			    dialog({
				    title: "{{_('Warning')}}",
				    modal: true,
				    resizable: false,
				    width: 400,
				    height: 180,
				    buttons: {
					    "{{_('Close')}}": function() {
						    $('#views-dialog').dialog('close');
					    }
				    }
			    });
		}
	});
});
