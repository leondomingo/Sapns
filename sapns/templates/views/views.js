$(document).ready(function() {
	
	$('#btn_add_column').click(function() {
		//alert('Adding a column!')
		
		var new_column = 
			'<tr class="column_item">\n' +
			'<td class="">{{_('Title')}}</td>\n' +
			'<td><input class="sp_column_title" type="text"/></td>\n' +
			"<td class=''>{{_('Definition')}}</td>\n" +
			'<td><input class="sp_column_definition" type="text"/></td>\n' +
			"<td class=''>{{_('Alias')}}</td>\n" +
			'<td><input class="sp_column_alias" type="text"/></td>\n' +
			'<td class="">{{_('Align')}}</td>\n' +
			'<td><select>' +
			'<option value="center">center</option>\n' +
			'<option value="left">left</option>\n' +
			'<option value="right">right</option>\n' +
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
	
	$('#btn_add_relation').click(function() {
		//alert('Adding a relation!')
		
		var new_relation = 
			'<tr class="relation_item">\n' +
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
	
	$('#btn_add_filter').click(function() {
		//alert('Adding a filter!')
		
		var new_filter = 
			'<tr class="filter_item">\n' +
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

	$('#btn_add_order').click(function() {
		//alert('Adding an order!')
		
		var new_order = 
			'<tr class="order_item">\n' +
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
	
	$('#btn_save_view').click(function() {
		alert('Saving view...')
		
		// TODO: collect data
		// order
		var order_items = [];
		$('.sp_order_definition').each(function(i) {
			order_items[i] = $(this).val();
		});
		
		alert(JSON.stringify(order_items));
	});
});