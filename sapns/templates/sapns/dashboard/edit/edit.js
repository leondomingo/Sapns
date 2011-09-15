"{% import 'sapns/dashboard/datefield.js' as df %}";
$(document).ready(function() {
    
    $('#sp-back').hide();
    
    $('#back-button').click(function() {
        window.location = "{{came_from}}";
    });
    
    $('.sp-edit-field:first').find('input:first').focus();      
    
    $('#save-button').click(function() {
        
        $('.ui-tooltip').remove();
        
        var params = '';
        var required_attrs = [];
        
        // {# text #} 
        $('.sp-text-field').each(function() {
            var name = $(this).parent().parent().attr('name');
            var required = $(this).parent().parent().attr('required');
            var value = $(this).val();
                    
            if (required == 'true' && value == '') {
                required_attrs.push($(this));
            }
            
            params += 
                '<input type="hidden" name="fld_' + name + '" value="' + value + '">\n';
        });
        
        // integer
        $('.sp_integer_field').each(function() {
            var name = $(this).parent().parent().attr('name');
            var required = $(this).parent().parent().attr('required');
            var value = $(this).val();
                    
            if (required == 'true' && value == '') {
                required_attrs.push($(this));
            }
            
            params += 
                '<input type="hidden" name="fld_' + name + '" value="' + value + '">\n';
        });
        
        // float
        $('.sp_float_field').each(function() {
            var name = $(this).parent().parent().attr('name');
            var required = $(this).parent().parent().attr('required');
            var value = $(this).val();
                    
            if (required == 'true' && value == '') {
                required_attrs.push($(this));
            }
            
            params += 
                '<input type="hidden" name="fld_' + name + '" value="' + value + '">\n';
        });
        
        // {# url #} 
        $('.url_field_text').each(function() {
            var parent = $(this).parent().parent().parent();
            var name = parent.attr('name');
            var required = parent.attr('required');
            var value = $(this).val();
                    
            if (required == 'true' && value == '') {
                required_attrs.push($(this));
            }
            
            params +=
                '<input type="hidden" name="fld_' + name + '" value="' + value + '">\n';
        });
        
        // {# checkbox #} 
        $('.sp-checkbox-field').each(function() {
            var name = $(this).parent().parent().attr('name');
            params += 
                '<input type="hidden" name="fld_' + name + '" ' + 
                    'value="' + $(this).attr('checked') + '">\n';
        });

        // {# date #} 
        $('.sp-date-field').each(function() {
            
            var date_value = $(this).datepicker('getDate');
            var name = $(this).parent().parent().attr('name');
            
            if (date_value != null) {
                var year = date_value.getFullYear()
                var month = date_value.getMonth() + 1;
                var day = date_value.getDate();
            
                date_value = year + '-' + month + '-' + day;
            }
            else {
                date_value = '';
            }
            
            var required = $(this).parent().parent().attr('required');
                    
            if (required == 'true' && date_value == '') {
                required_attrs.push($(this));
            }
            
            params += 
                '<input type="hidden" name="fld_' + name + '" ' + 
                    'value="' + date_value + '">\n';
        });
        
        // {# time #} 
        $('.sp-time-field').each(function() {
            var name = $(this).parent().parent().attr('name');
            var required = $(this).parent().parent().attr('required');
            var value = $(this).val();
                    
            if (required == 'true' && value == '') {
                required_attrs.push($(this));
            }
            
            params += 
                '<input type="hidden" name="fld_' + name + '" ' + 
                    'value="' + value + '">\n';
        });
        
        // {# select fields #} 
        $('.sp-select-field').each(function() {
            
            var name = $(this).parent().parent().attr('name');
            var required = $(this).parent().parent().attr('required');
            var sel_value = $(this).attr('value');
                    
            if (required == 'true' && sel_value == '') {
                required_attrs.push($(this));
            }
            
            params += 
                '<input type="hidden" name="fld_' + name + '" value="' + sel_value + '">\n';
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
            
            for (var i=0; i<required_attrs.length; i++) {
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
            $('#edit-form').append(params).submit();
        }
    });
    
    // {# create datepickers 
    // with specific date format and options #} 
    {{ df.date_field(tg, _, '.sp-date-field') }}
    
    // {# show related class #} 
    $('#rel-classes-show').click(function() {
        
        var option = $('#rel-classes-sel option:selected');
        var action = "/dashboard/list/" + option.attr('cls');
        
        var params = '';
        params += '<input type="hidden" name="parent_id" value="{{id}}">\n';
        params += '<input type="hidden" name="ch_attr" value="' + option.attr('ch_attr') + '">\n';
           
        $('#rel-classes-form').attr('action', action).html(params).submit();
    });
    
    // execute action 
    $('#action-go').click(function() {
        var id = $('#actions-sel').attr('row_id');
        var url = $('#actions-sel option:selected').val();
        
        if (url[url.length-1] != '/') {
            url += '/';
        }
        
        url += id;
        
        $('#action-form').attr('action', url).submit();
        $('#actions-sel option:first').attr('selected', true);
    });
    
    var selectors = $('.sp_selector');
    for (var i=0, l=selectors.length; i<l; i++) {
        var s = $(selectors[i]);
        var attr_name = s.attr('attr_name');
        var attr_value = s.attr('attr_value');
        var attr_title = s.attr('attr_title');
        var attr_rc = s.attr('attr_rc');
        var attr_rc_title = s.attr('attr_rc_title');
        var read_only = s.parent().parent().attr('read_only');
        
        s.sapnsSelector({
            name: attr_name,
            value: attr_value,
            title: attr_title,
            rc: attr_rc,
            rc_title: attr_rc_title,
            read_only: read_only == 'true'
        });
    }
    
    $('.sp_float_field').keydown(function(e) {
        fields.num_field_keydown($(this), e);
    });
    
    $('.sp_integer_field').keydown(function(e) {
        fields.num_field_keydown($(this), e, true);
    });
    
    $('.sp-time-field').keydown(function(e) {
        fields.time_field_keydown(e);
    }).change(function() {
        fields.time_field_change($(this));
    });
    
    $('.url_field_btn').click(function() {
        var url = $(this).parent().find('.url_field_text').val();
        if (url.trim()) {
            $('<form method="get" action="' + url + '" target="_blank"></form>').
                appendTo('body').submit().remove();
        }
    });
});