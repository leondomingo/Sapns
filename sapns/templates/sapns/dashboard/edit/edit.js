$(function() {

    var sbm = new SidebarMessages();

    function go_back() {
        var form_ = $('<form/>', {
            method: 'post',
            action: "{{came_from}}",
        });

        form_.appendTo('body').submit().remove();
    }
    
    $('#sp-back').hide();
    
    $('#back-button').click(function() {
        go_back();
    });
    
    $('.sp-edit-field:first').find('input:first').focus();      
    
    $('#save-button').click(function() {
        
        $('.ui-tooltip').remove();
        
        var params = { id: "{{id}}" },
            required_attrs = [];
        
        // text 
        $('.sp-text-field').each(function() {
            var field = $(this).parents('.sp-edit-field'),
                name = field.attr('name'),
                required = field.hasClass('required'),
                value = $.trim($(this).val()),
                ok = !$(this).hasClass('sp-field-error');

            if (required && value === '' || !ok) {
                required_attrs.push($(this));
            }
            
            params['fld_'+name] = value;
        });
        
        // integer
        $('.sp_integer_field').each(function() {
            var field = $(this).parents('.sp-edit-field'),
                name = field.attr('name'),
                required = field.hasClass('required'),
                value = $.trim($(this).val()),
                ok = !$(this).hasClass('sp-field-error');
                    
            if (required && value == '' || !ok) {
                required_attrs.push($(this));
            }
            
            params['fld_'+name] = value;
        });
        
        // float
        $('.sp_float_field').each(function() {
            var field = $(this).parents('.sp-edit-field'),
                name = field.attr('name'),
                required = field.hasClass('required'),
                value = $.trim($(this).val()),
                ok = !$(this).hasClass('sp-field-error');
                    
            if (required && value == '' || !ok) {
                required_attrs.push($(this));
            }
            
            params['fld_'+name] = value;
        });
        
        // url
        $('.url_field_text').each(function() {
            var field = $(this).parents('.sp-edit-field'),
                name = field.attr('name'),
                required = field.hasClass('required'),
                value = $.trim($(this).val());
                    
            if (required == 'true' && value == '') {
                required_attrs.push($(this));
            }
            
            params['fld_'+name] = value;
        });
        
        // checkbox 
        $('.sp-checkbox-field').each(function() {
            var name = $(this).parents('.sp-edit-field').attr('name');
            params['fld_'+name] = $(this).prop('checked');
        });

        // date 
        $('.sp-date-field').each(function() {
            
            var value = $.trim($(this).val()),
                field = $(this).parents('.sp-edit-field'), 
                name = field.attr('name'),
                required = field.hasClass('required'),
                ko = $(this).hasClass('sp-field-error');
            
            if (required && value === '') {
                required_attrs.push($(this));
            }
            
            params['fld_'+name] = value;
        });
        
        // time
        $('.sp-time-field').each(function() {
            var field = $(this).parents('.sp-edit-field'),
                name = field.attr('name'),
                required = field.hasClass('required'),
                value = $.trim($(this).val()),
                ko = $(this).hasClass('sp-field-error');
                    
            if (required && value === '' || ko) {
                required_attrs.push($(this));
            }
            
            params['fld_'+name] = value;
        });

        // datetime - date
        $('.sp-datetime-field.sp-date-field').each(function() {

            var value = $.trim($(this).val()),
                field = $(this).parents('.sp-edit-field'), 
                name = field.attr('name'),
                required = field.hasClass('required'),
                ko = $(this).hasClass('sp-field-error');
            
            if (required && value === '' || ko) {
                required_attrs.push($(this));
            }
            
            params['fld_'+name] = value;
        });

        // datetime - time
        $('.sp-datetime-field.sp-time-field').each(function() {
            var field = $(this).parents('.sp-edit-field'),
                name = field.attr('name'),
                required = field.hasClass('required'),
                value = $.trim($(this).val()),
                ko = $(this).hasClass('sp-field-error'),
                date_value = params['fld_' + name];
                    
            if (required && value === '' || ko || date_value === '' && value !== '') {
                required_attrs.push($(this));
            }

            if (date_value && value === '') {
                value = '00:00';
            }

            params['fld_'+name] += ' ' + value;
        });
        
        // select fields
        $('.sp-select-field').each(function() {
            
            var field = $(this).parents('.sp-edit-field'),
                name = field.attr('name'),
                required = field.hasClass('required'),
                sel_value = $(this).attr('value');
                    
            if (required && sel_value == '') {
                required_attrs.push($(this));
            }
            
            params['fld_'+name] = sel_value;
        });
        
        if (required_attrs.length > 0) {
            
            $('#save-button').qtip({
                content: { text: "{{_('Check required fields!')}}" },
                show: {
                    target: false,
                    ready: true                            
                },
                hide: {
                    event: false
                },
                position: {
                    at: "right top",
                    my: "left bottom"
                },
                style: "ui-tooltip-red ui-tooltip-rounded"
            });
            
            for (var i=0, l=required_attrs.length; i<l; i++) {
                required_attrs[i].qtip({
                    content: { text: "{{_('this field is required')}}" },
                    show: {
                        target: false,
                        ready: true                            
                    },
                    hide: {
                        event: false
                    },
                    position: {
                        at: "right top",
                        my: "left bottom"
                    },
                    style: "ui-tooltip-red ui-tooltip-rounded"                        
                });
            }
        }
        else {
            // save
            var id_message = sbm.show({ message: "{{_('Wait, please...')}}", hide_after: 0, modal: true });

            $.ajax({
                url: "{{tg.url('/dashboard/save/%s/' % cls)}}",
                type: "post",
                data: params,
                success: function(res) {
                    sbm.hide({ id: id_message });

                    if (res.status) {
                        go_back();
                    }
                    else {
                        if (res.message) {
                            alert(res.message);
                        }
                        else {
                            alert('Error!');
                        }
                    }
                },
                error: function() {
                    sbm.hide({ id: id_message });
                    alert('Error!');
                }
            });
        }
    });
    
    sapns_date_field('.sp-date-field');
    
    // show related class
    $('#rel-classes-show').click(function() {
        
        var option = $('#rel-classes-sel option:selected'),
            action = "/dashboard/list/" + option.attr('cls');
        
        var params = '';
        params += '<input type="hidden" name="parent_id" value="{{id}}">\n';
        params += '<input type="hidden" name="ch_attr" value="' + option.attr('ch_attr') + '">\n';
           
        $('#rel-classes-form').attr('action', action).html(params).submit();
    });
    
    // execute action 
    $('#action-go').click(function() {
        var id = $('#actions-sel').attr('row_id'),
            url = $('#actions-sel option:selected').val();
        
        if (url[url.length-1] != '/') {
            url += '/';
        }
        
        url += id;
        
        $('#action-form').attr('action', url).submit();
        $('#actions-sel option:first').prop('selected', true);
    });
    
    var selectors = $('.sp_selector');
    for (var i=0, l=selectors.length; i<l; i++) {
        var s = $(selectors[i]),
            attr_name = s.attr('attr_name'),
            attr_value = s.attr('attr_value'),
            attr_title = s.attr('attr_title'),
            attr_rc = s.attr('attr_rc'),
            attr_rc_title = s.attr('attr_rc_title'),
            read_only = s.parent().parent().hasClass('readonly');
        
        s.sapnsSelector({
            name: attr_name,
            value: attr_value,
            title: attr_title,
            rc: attr_rc,
            rc_title: attr_rc_title,
            read_only: read_only
        });
    }
    
    SapnsFields.init('.sp_integer_field, .sp_float_field, .sp-text-field, .sp-date-field, .sp-time-field', 'blur');

    $('.sp-datetime-field.sp-date-field').blur(function() {
        var time_field = $(this).siblings('.sp-time-field');
        if ($(this).val() !== '' && $.trim(time_field.val()) === '') {
            time_field.val('00:00');
        }
    });
    
    $('.url_field_btn').click(function() {
        var url = $(this).parent().find('.url_field_text').val();
        if (url.trim()) {
            $('<form method="get" action="' + url + '" target="_blank"></form>').
                appendTo('body').submit().remove();
        }
    });
    
    $('.created').click(function() {
        $.ajax({
            url: "{{tg.url('/dashboard/logs/search/')}}",
            data: {
                table_name: "{{cls}}",
                row_id: "{{id}}"
            },
            success: function(content) {
                $('#edit-dialog').html(content).dialog({
                    title: "Logs",
                    width: 1100,
                    height: 600,
                    resizable: false,
                    modal: true,
                    buttons: {
                        "{{_('Close')}}": function() {
                            $('#edit-dialog').dialog('close');
                        }
                    }
                });
            }
        });
    });
});
