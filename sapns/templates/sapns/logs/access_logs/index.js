$(function() {
    var sbm = new SidebarMessages(),
        filters = [];

    function reload_logs() {
        var id_message = sbm.show({ message: "{{_('Wait, please...')}}", hide_after: 0 });

        $.ajax({
            url: "{{tg.url('/dashboard/logs/logs_list/')}}",
            data: { fields: JSON.stringify(filters) },
            success: function(content) {
                sbm.hide({ id: id_message });
                $('#access-logs-main .list').html(content);
            },
            error: function() {
                sbm.hide({ id: id_message });
                sbm.show({ message: "Error!", hide_after: 0 })
            }
        })
    }

    var s_col = '#access-logs-main .list .item .col';
    $(document).off('click', s_col).on('click', s_col, function() {
        var field_name = $(this).attr('field-name'),
            log_id = $(this).parents('.item').attr('log-id'),
            val = $(this).text();

        var f = { field_name: field_name, log_id: log_id, id: Math.floor(Math.random()*999999999) };
        filters.push(f);

        var filter = '<div class="filter" filter-id="' + f.id + '" title="' + val + '">' + val + '</div>'
        $('#access-logs-main .filters').append(filter);

        reload_logs();
    });

    var s_filter = '#access-logs-main .filters .filter';
    $(document).off('dblclick', s_filter).on('dblclick', s_filter, function() {
        var filter_id = $(this).attr('filter-id');
        for (var i=0, l=filters.length; i<l; i++) {
            var filter = filters[i];
            if (filter.id === filter_id*1) {
                if (i > 0) {
                    filters = filters.slice(0, i).concat(filters(i, filters.length));
                }
                else {
                    filters = filters.slice(1, filters.length);
                }

                $(this).remove();

                reload_logs();
                break;
            }
        }
    });

    reload_logs();
});
