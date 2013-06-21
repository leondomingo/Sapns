$(function() {
    var sbm = new SidebarMessages(),
        filters = [],
        pag = 1;

    function reload_logs() {
        var id_message = sbm.show({ message: "{{_('Wait, please...')}}", hide_after: 0 });

        var rp = $('#access-logs-main .footer .rp').val()*1;
        $('#access-logs-main .footer .page-number').text(pag);

        $.ajax({
            url: "{{tg.url('/dashboard/logs/logs_list/')}}",
            data: { rp: rp, pag: pag, fields: JSON.stringify(filters) },
            success: function(res) {
                sbm.hide({ id: id_message });
                if (res.status) {
                    $('#access-logs-main .list').html(res.content).scrollTop(0);
                    $('#access-logs-main .fwd-pag button').prop('disabled', res.num_logs < rp);
                    $('#access-logs-main .rew-pag button').prop('disabled', pag === 1);
                }
                else {
                    sbm.show({ message: "Error!", hide_after: 0 });
                }
            },
            error: function() {
                sbm.hide({ id: id_message });
                sbm.show({ message: "Error!", hide_after: 0 });
            }
        })
    }

    var s_col = '#access-logs-main .list .item .col';
    $(document).off('click', s_col).on('click', s_col, function() {
        var field_name = $(this).attr('field-name'),
            log_id = $(this).parents('.item').attr('log-id'),
            val = $(this).attr('value') || $(this).text();

        if (field_name) {
            var f = { field_name: field_name, log_id: log_id, id: Math.floor(Math.random()*999999999), val: val };
            var encontrado = false;
            for (var i=0, l=filters.length; i<l; i++) {
                var f_ = filters[i];
                encontrado = field_name === f_.field_name && val === f_.val;
                if (encontrado) {
                    break;
                }
            }

            if (!encontrado) {
                filters.push(f);

                var filter = '<div class="filter" filter-id="' + f.id + '" title="' + val + '">' + val + '</div>'
                $('#access-logs-main .filters').append(filter);

                pag = 1
                reload_logs();
            }
        }
    });

    var s_col = '#access-logs-main .list .item .col.details';
    $(document).off('click', s_col).on('click', s_col, function() {
        var item = $(this).parents('.item');

        if (item.hasClass('open')) {
            item.removeClass('open');
        }
        else {
            item.addClass('open');
        }
    });

    var s_filter = '#access-logs-main .filters .filter';
    $(document).off('dblclick', s_filter).on('dblclick', s_filter, function() {
        var filter_id = $(this).attr('filter-id');
        for (var i=0, l=filters.length; i<l; i++) {
            var filter = filters[i];
            if (filter.id === filter_id*1) {
                if (i > 0) {
                    if (i === filters.length-1) {
                        filters = filters.slice(0, i);
                    }
                    else {
                        filters = filters.slice(0, i).concat(filters(i, filters.length));   
                    }
                }
                else {
                    filters = filters.slice(1, filters.length);
                }

                $(this).remove();

                pag = 1
                reload_logs();
                break;
            }
        }
    });

    $('#access-logs-main .rp').change(function() {
        reload_logs();
    });

    $('#access-logs-main .reload button').click(function() {
        reload_logs();
    });

    $('#access-logs-main .footer .rew-pag').click(function() {
        if (pag > 1) {
            pag--;
            reload_logs();
        }
    });

    $('#access-logs-main .footer .fwd-pag').click(function() {
        pag++;
        reload_logs();
    });

    reload_logs();
});
