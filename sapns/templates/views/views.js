$(document).ready(function() {
	
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
			'<td class="">{{_('Title')}}</td>\n' +
			'<td><input class="sp_column_title" type="text"/></td>\n' +
			'<td class="">{{_('Definition')}}</td>\n' +
			'<td><input class="sp_column_definition" type="text"/></td>\n' +
			'<td class="">{{_('Alias')}}</td>\n' +
			'<td><input class="sp_column_alias" type="text"/></td>\n' +
			'<td class="">{{_('Align')}}</td>\n' +
			'<td><select class="sp_column_align">' +
			'<option value="center">{{_('center')}}</option>\n' +
			'<option value="left">{{_('left')}}</option>\n' +
			'<option value="right">{{_('right')}}</option>\n' +
			'</select>' +
			'</td>\n' +			
			'<td><input class="btn_remove_column" type="button" value="{{_('Remove column')}}"/></td>\n' +
			'<td><input class="btn_up_column" type="button" value="{{_('Up')}}"/></td>\n' +
			'<td><input class="btn_down_column" type="button" value="{{_('Down')}}"/></td>\n' +
			'</tr>\n'
		
		$('#column_list').append(new_column);
		$('#column_list .column_item:last .btn_remove_column').click(function() {
			$(this).parent().parent().remove();
		});
		
		$('#column_list .column_item:last .sp_column_definition').focus();
	});
	
	$('.btn_remove_column').click(function() {
		$(this).parent().parent().remove();
	});
	
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
			"<td class='sp_relation_lbl'>{{_('Table')}}</td>\n" +
			'<td>\n' +
			'<input class="sp_relation_table" type="text"/>\n' +
			'</td>\n' +
			"<td class='sp_relation_lbl'>{{_('Alias')}}</td>\n" +
			'<td>\n' +
			'<input class="sp_relation_alias" type="text"/>\n' +
			'</td>\n' +
			"<td class='sp_relation_lbl'>{{_('Condition')}}</td>\n" +
			'<td>\n' +
			'<input class="sp_relation_condition" type="text"/>\n' +
			'</td>\n' +
			'<td>\n' + 
			'<input class="btn_remove_relation" type="button" value="{{_('Remove relation')}}"/>\n' +
			'</td>\n' +
			'<td>\n' + 
			'<input class="btn_up_relation" type="button" value="{{_('Up')}}"/>\n' +
			'</td>\n' +
			'<td>\n' + 
			'<input class="btn_down_relation" type="button" value="{{_('Down')}}"/>\n' +
			'</td>\n' +
			'</tr>\n'
		
		$('#relation_list').append(new_relation);
		$('#relation_list .relation_item:last .btn_remove_relation').click(function() {
			$(this).parent().parent().remove();
		});
		
		$('#relation_list .relation_item:last .sp_relation_table').focus();
	});
	
	$('.btn_remove_relation').click(function() {
		$(this).parent().parent().remove();
	});
	
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
			"<td class='sp_filter_lbl'>{{_('Definition')}}</td>\n" +
			'<td>\n' +
			'<input class="sp_filter_definition" type="text"/>\n' +
			'</td>\n' +
			'<td>\n' + 
			'<input class="btn_remove_filter" type="button" value="{{_('Remove filter')}}"/>\n' +
			'</td>\n' +
			'<td>\n' + 
			'<input class="btn_up_filter" type="button" value="{{_('Up')}}"/>\n' +
			'</td>\n' +
			'<td>\n' + 
			'<input class="btn_down_filter" type="button" value="{{_('Down')}}"/>\n' +
			'</td>\n' +
			'</tr>\n'
		
		$('#filter_list').append(new_filter);
		$('#filter_list .filter_item:last .btn_remove_filter').click(function() {
			$(this).parent().parent().remove();
		});
		
		$('#filter_list .filter_item:last .sp_filter_definition').focus();
	});
	
	$('.btn_remove_filter').click(function() {
		$(this).parent().parent().remove();
	});

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
			"<td class='sp_order_lbl'>{{_('Definition')}}</td>\n" +
			'<td>\n' +
			'<input class="sp_order_definition" type="text"/>\n' +
			'</td>\n' +
			'<td>\n' + 
			'<input class="btn_remove_order" type="button" value="{{_('Remove order')}}"/>\n' +
			'</td>\n' +
			'<td>\n' + 
			'<input class="btn_up_order" type="button" value="{{_('Up')}}"/>\n' +
			'</td>\n' +
			'<td>\n' + 
			'<input class="btn_down_order" type="button" value="{{_('Down')}}"/>\n' +
			'</td>\n' +
			'</tr>\n'
		
		$('#order_list').append(new_order);
		$('#order_list .order_item:last .btn_remove_order').click(function() {
			$(this).parent().parent().remove();
		});
		
		$('#order_list .order_item:last .sp_order_definition').focus();
	});
	
	$('.btn_remove_order').click(function() {
		$(this).parent().parent().remove();
	});
	
	
	$('.btn_up_order').click(function(){
		var pos = $(this).parent().parent().attr('pos');
		pos = pos*1;
		
		var prev_pos = pos - 1;
		
		if (pos > 0) {
			// get the previous item in the list
			var prev_item = $('.order_item:eq(' + prev_pos + ')');
			prev_item.remove();
		}
	});
	
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
					column_aliases[column_aliases.length] = this_alias;
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
			table_aliases[table_aliases.length] = this_alias;
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
					table_aliases[table_aliases.length] = this_alias;
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
			// Warning!
			alert('{{_('Please, check the information you have entered')}}');
		}
	});
});