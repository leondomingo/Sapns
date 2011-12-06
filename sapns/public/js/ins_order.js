function ins_order() {

    $('#save-ins-order').click(function() {
        
        var atributos = [];
        $('.ins-attr').each(function() {
            atributos.push({
                id: $(this).attr('id_attr'),
                title: $(this).find('.sp-text-field').val(),
                order: $(this).attr('pos'),
                required: $(this).find('.attr-required').attr('checked'),
                visible: $(this).find('.attr-visible').attr('checked')
            });
        });
        
        $('#form-ins-order input[name=title]').val($('#title-class').val());
        $('#form-ins-order input[name=attributes]').val(JSON.stringify(atributos));
        $('#form-ins-order').submit();
    });

    // when the "visible" check is unchecked, the attribute title's background turns gray 
    function color_visible(check) {
        if (check.attr('checked')) {
            check.parent().parent().find('.attr-title').
              find('.sp-text-field').css('background-color', 'white');
        }
        else {
            check.parent().parent().find('.attr-title').
              find('.sp-text-field').css('background-color', 'gray');
        }
    }

    // when the "required" check is checked, the attribute title's font turns bolder 
    function font_required(check) {
        if (check.attr('checked')) {
            check.parent().parent().find('.attr-title').
              find('.sp-text-field').css('font-weight', 'bold');
        }
        else {
            check.parent().parent().find('.attr-title').
              find('.sp-text-field').css('font-weight', 'normal');
        }
    }
    
    // apply style on attribute title depending on the checks 
    $('.attr-visible').click(function() {
        color_visible($(this));
    }).each(function() {
        color_visible($(this));
    });
    
    $('.attr-required').click(function() {
        font_required($(this));
    }).each(function() {
        font_required($(this));
    });
    
    function new_order() {
        var new_order = [];
        $('.ins-attr').each(function(){
            var pos = $(this).attr('pos')*1;
            new_order[pos] = $(this);
            $(this).remove();
        });
        
        // apply new order 
        
        for (var i=0; i<new_order.length; i++) {
            $('#ins_list').append(new_order[i]);
            
            // recover click events  
            $('.ins-attr:last .insorder-up').click(function() { ins_up($(this)); });
            $('.ins-attr:last .insorder-down').click(function() { ins_down($(this)); });
            $('.ins-attr:last .attr-visible').click(function() { color_visible($(this)); });
            $('.ins-attr:last .attr-required').click(function() { font_required($(this)); });
            
            if ($('.ins-attr:last').attr('modified') == 'true') {
                $('.ins-attr:last').effect('highlight', {color: 'yellow'}, 300);
            }
            
            $('.ins-attr:last').attr('modified', 'false');
        }
    }
    
    function ins_up (button) {
        var pos = button.parent().parent().parent().attr('pos')*1;
        if (pos > 0) {
            
            // update order 
            var prev_pos = pos - 1;
            var prev_item = $('.ins-attr:eq(' + prev_pos + ')');
            prev_item.attr('pos', pos);
            button.parent().parent().parent().attr('pos', prev_pos);
            button.parent().parent().parent().attr('modified', 'true');
            
            // create new order 
            new_order();
        }
    }
    
    function ins_down (button) {
        var pos = button.parent().parent().parent().attr('pos')*1;
        var max = $('.ins-attr:last').attr('pos')*1;
        if (pos < max) {
            
            // update order 
            var next_pos = pos + 1;
            var next_item = $('.ins-attr:eq(' + next_pos + ')');
            next_item.attr('pos', pos);
            button.parent().parent().parent().attr('pos', next_pos);
            button.parent().parent().parent().attr('modified', 'true');
            
            // create new order 
            new_order();
        }
    }
    
    $('.insorder-up').click(function() { ins_up($(this)); });
    $('.insorder-down').click(function() { ins_down($(this)); });
}