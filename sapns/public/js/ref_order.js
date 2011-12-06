function ref_order(url) {
    $('#save_ref_order').click(function() {
        
        var atributos = [];
        var i = 0;
        $('.attr_included').each(function() {
            
            var pos = null;
            if ($(this).attr('checked')) {
                pos = $(this).parent().parent().parent().attr('pos');
            }
            
            i++;
            
            atributos.push({
                id: $(this).parent().parent().parent().attr('id_attr'),
                order: pos
            });
        });
        
        $.ajax({
            url: url, 
            data: {
                attributes: JSON.stringify(atributos)
            },
            success: function(res) {
                if (res.status) {
                    $('#form_ref_order').submit();
                }
                else {
                    alert('Error!');
                }
            }   
        });
    });
    
    function new_order() {
        var new_order = [];
        $('.ref_attr').each(function(){
            var pos = $(this).attr('pos')*1;
            new_order[pos] = $(this);
            $(this).remove();
        });
        
        // apply new order 
        
        for (var i=0; i<new_order.length; i++) {
            $('#ref_list').append(new_order[i]);
            
            // recover click events 
            $('.ref_attr:last .reforder_up').click(function() { ref_up($(this)); });
            $('.ref_attr:last .reforder_down').click(function() { ref_down($(this)); });
            
            if($('.ref_attr:last').attr('modified') == 'true') {
                $('.ref_attr:last').effect('highlight', {color: 'yellow'}, 500);
            }
            
            $('.ref_attr:last').attr('modified', 'false');
        }
    }
    
    function ref_up (button) {
        var pos = button.parent().parent().parent().attr('pos')*1;
        if (pos > 0) {
            
            // update order 
            var prev_pos = pos - 1;
            var prev_item = $('.ref_attr:eq(' + prev_pos + ')');
            prev_item.attr('pos', pos);
            button.parent().parent().parent().attr('pos', prev_pos);
            button.parent().parent().parent().attr('modified', 'true');
            
            // create new order 
            new_order();
        }
    }
    
    function ref_down (button) {
        var pos = button.parent().parent().parent().attr('pos')*1;
        var max = $('.ref_attr:last').attr('pos')*1;
        if (pos < max) {
            
            // update order 
            var next_pos = pos + 1;
            var next_item = $('.ref_attr:eq(' + next_pos + ')');
            next_item.attr('pos', pos);
            button.parent().parent().parent().attr('pos', next_pos);
            button.parent().parent().parent().attr('modified', 'true');
            
            // create new order 
            new_order();
        }
    }
    
    $('.reforder_up').click(function() { ref_up($(this)); });
    $('.reforder_down').click(function() { ref_down($(this)); });
}