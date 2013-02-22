$(function() {
    
    var view_id = "{{view.view_id}}",
        view_name = "{{view.name or ''}}";
        
    function return_() {
        var came_from = "{{came_from}}",
        url = came_from.split('?')[0],
        params = (came_from.split('?')[1] || '').split('&');
    
        var params_ = '';
        for (var i=0, l=params.length; i<l; i++) {
            var p = params[i];
            if (p !== '') {
                p_name = p.split('=')[0],
                p_value = p.split('=')[1];
            
                params_ += '<input type="hidden" name="' + p_name + '" value="' + p_value + '">';
            }
        }
        
        var f = '<form action="' + url + '">' + params_ + '</form>';
        $(f).appendTo('body').submit().remove();            
    }
    
    $('#sp-edit-view-ok').click(function() {
        var title = $('#sp-view-title').val();
        if (!title) {
            alert("{{_('You must specify a title')}}");
            return;
        }
        
        var class_id = $('#sp-view-table').sapnsSelector('getValue');
        if (!class_id) {
            alert("{{_('You must specify a base table')}}");
            return;
        }
        
        if (!view_name) {
            alert("{{_('You have to add some columns to the view')}}");
            return;
        }
        
        var user_id = ''; //$('#sp-view-user').sapnsSelector('getValue');
        
        // TODO: mostrar sidebar-message modal=true 
        
        $.ajax({
            url: "{{tg.url('/dashboard/views/view_save/')}}",
            data: {
                view_id: view_id,
                view_name: view_name,
                id: "{{view.id or ''}}",
                title: title,
                name: "{{view.name or ''}}",
                class_id: class_id,
                user_id: user_id
            },
            success: function(res) {
                // TODO: ocultar sidebar-message 
                if (res.status) {
                    return_();
                }
                else {
                    alert('Error!');
                }
            },
            error: function() {
                // TODO: ocultar sidebar-message 
                alert('Error!');
            }
        });
    });
    
    $('#sp-edit-view-cancel').click(function() {
        return_();
    });
    
    function reload_attributes(class_id, path) {
        $.ajax({
            url: "{{tg.url('/dashboard/views/attributes_list/')}}",
            data: {
                class_id: class_id,
                path: path
            },
            success: function(res) {
                if (res.status) {
                    $('#sp-edit-view-attr-list').html(res.attributes);
                    $('#sp-edit-view-attr-list .attribute').disableSelection();
                }
                else {
                    alert('Error!');
                }
            },
            error: function() {
                alert('Error!');
            }
        });
    }
    
    function reload_cols() {
        $('#sp-edit-view-cols').html('');
        $.ajax({
            url: "{{tg.url('/dashboard/views/view_cols/')}}",
            data: { view_id: view_id },
            success: function(content) {
                $('#sp-edit-view-cols').html(content);
            },
            error: function() {
                $('#sp-edit-view-cols').html('<div>Error!</div>');
            }
        });
    }
    
    $('#sp-view-table').sapnsSelector({
        rc: 'sp_classes', rc_title: "{{_('Classes')}}",
        onChange: function(class_id) {
            $('#sp-edit-view-classes').jstree({
                json_data: {
                    ajax: {
                        url: "{{tg.url('/dashboard/views/classes/')}}",
                        data: function(node) {
                            return {
                                class_id0: class_id,
                                class_id: $(node).attr('class_id'),
                                path: $(node).attr('path')
                            };
                        }
                    }
                },
                core: { animation: 0 },
                themes: {
                    theme: 'classic',
                    url: "{{tg.url('/js/jstree/themes/classic/style.css')}}"
                },
                ui: { select_limit: 1 },
                types: { valid_children: ['classes'] },
                plugins: ['themes', 'json_data', 'types', 'ui']
            });                
            
            reload_attributes(class_id, '');
            
            $('#sp-edit-view-classes').bind('select_node.jstree', function(e, obj) {
                var nodo = obj.rslt.obj;
                reload_attributes(nodo.attr('class_id'), nodo.attr('path'));
            });
        }
    });
    
    $('#sp-view-table').sapnsSelector('setValue', "{{view.class_id or ''}}");
    
    $('#sp-view-user').sapnsSelector({
        rc: 'sp_users', rc_title: "{{_('Users')}}"
    });
    
    function show_grid() {
        $('#sp-edit-view-list .grid').remove();
        $('#sp-edit-view-list').append('<div class="grid"></div>');
        $('#sp-edit-view-list .grid').sapnsGrid({
            cls: view_name,
            q: '',
            rp: 25,
            search_params: {
                url: "{{tg.url('/dashboard/views/grid/')}}"
            },
            hide_check: true,
            height: parseInt($('#sp-edit-view-list').css('height').replace('px', '')) - 65
        });            
    }
    
    $('#sp-edit-view-cols').sortable({
        placeholder: 'placeholder',
        stop: function() {
            var data_ = {};
            $('#sp-edit-view-cols .column').each(function(i) {
                data_['atr_' + i] = $(this).attr('path');
            });
            
            data_.view_id = view_id;
            data_.view_name = view_name;
            
            $.ajax({
                url: "{{tg.url('/dashboard/views/reorder_attributes/')}}",
                data: data_,
                success: function(res) {
                    if (res.status) {
                        if (res.view_name !== '') {
                            view_name = res.view_name;
                            show_grid();
                        }                            
                    }
                    else {
                        $('#sp-edit-view-cols').sortable('cancel');
                    }
                },
                error: function() {
                    $('#sp-edit-view-cols').sortable('cancel');
                }
            });
        }
    });
    
    var s_ = '#sp-edit-view-attr-list .attribute .col-attr.add';
    $(document).off('click', s_).on('click', s_, function() {
        var path = $(this).parent().attr('path');
        
        $.ajax({
            url: "{{tg.url('/dashboard/views/add_attribute/')}}",
            data: { view_id: view_id, attribute_path: path, view_name: view_name },
            success: function(res) {
                if (res.status) {
                    if (res.attribute.title) {
                        reload_cols();
                        
                        if (res.view_name !== '') {
                            view_name = res.view_name;
                            show_grid();
                        }
                    }
                }
                else {
                    alert('Error!');
                }
            },
            error: function() {
                alert('Error!');
            }
        });
    });
    
    var s_ = '#sp-edit-view-cols .column .title';
    $(document).off('dblclick', s_).on('dblclick', s_, function() {
        var path = $(this).parent().attr('path'),
            on_progress = false;
        
        $.ajax({
            url: "{{tg.url('/dashboard/views/edit_attribute/')}}",
            data: { view_id: view_id, view_name: view_name, path: path },
            success: function(content) {
                $('#sp-edit-view-dialog').remove();
                $('<div id="sp-edit-view-dialog" style="display:none"></div>').appendTo('body');
                $('#sp-edit-view-dialog').html(content).dialog({
                    title: path,
                    modal: true,
                    resizable: false,
                    width: 600,
                    height: 'auto',
                    buttons: {
                        "{{_('Ok')}}": function() {
                            if (!on_progress) {
                                on_progress = true;
                                
                                edit_attribute_save(function(res) {
                                    view_name = res.view_name
                                    reload_cols();
                                    show_grid();
                                    $('#sp-edit-view-dialog').dialog('close');
                                },
                                function() {
                                    on_progress = false;
                                });
                            }
                        },
                        "{{_('Cancel')}}": function() {
                            if (!on_progress) {
                                $('#sp-edit-view-dialog').dialog('close');
                            }
                        }
                    }
                });
            }
        });
    });
    
    var s_ = '#sp-edit-view-cols .column .close';
    $(document).off('click', s_).on('click', s_, function() {
        var path = $(this).parent().attr('path');
        
        $.ajax({
            url: "{{tg.url('/dashboard/views/remove_attribute/')}}",
            data: { view_id: view_id, view_name: view_name, path: path },
            success: function(res) {
                if (res.status) {
                    view_name = res.view_name;
                    
                    reload_cols();
                    show_grid();
                }
                else {
                    alert('Error!');
                }
            },
            error: function() {
                alert('Error!');
            }
        });
    });
    
    if (view_name) {
        reload_cols();
        show_grid();
    }
    
    $('#sp-view-title').focus();
});