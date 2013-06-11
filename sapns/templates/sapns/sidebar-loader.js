// Load sidebar (don't wait for document load) 
$.ajax({
    url: "{{tg.url('/dashboard/sidebar/')}}",
    data: {came_from: "{{came_from or ''}}"},
    cache: true, 
    dataType: 'html',
    success: function(content) {
        $('.sp_sidebar').html(content).sortable({
            item: '.item_sb_sortable',
            axis: 'y',
            cancel: '.item_home',
            placeholder: 'item_sb_dragging',
            stop: function() {
                var order = [];
                $('.item_sb_sortable').each(function() {
                    order.push($(this).attr('shortcut_id')*1);
                });
                
                $.ajax({
                    url: "{{tg.url('/dashboard/sc/reorder/')}}",
                    data: { order: JSON.stringify(order) },
                    success: function(res) {
                        if (!res.status) {
                            $('.sp_sidebar').html(content).sortable('cancel');
                        }
                    },
                    error: function() {
                        $('.sp_sidebar').html(content).sortable('cancel');
                    }
                });
            }
        });
    }
});
