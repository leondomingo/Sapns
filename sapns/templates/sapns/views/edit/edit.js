$(function() {
    
    var view_id = "{{view.view_id}}",
        view_name = '',
        query = '{{view.query or ""}}';

    var sbm = new SidebarMessages();
        
    function return_() {
        var f = '<form method="post" action="{{came_from}}"></form>';
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
        
        if (!view_name && "{{view.name or ''}}" === '') {
            alert("{{_('You have to add some columns to the view')}}");
            return;
        }
        
        var user_id = '', //$('#sp-view-user').sapnsSelector('getValue');
            query = $('#sp-edit-view-list .grid').sapnsGrid('getQuery');
        
        var id_message = sbm.show({ message: "{{_('Wait, please...')}}", hide_after: 0, modal: true });

        $.ajax({
            url: "{{tg.url('/dashboard/views/view_save/')}}",
            data: {
                view_id: view_id,
                view_name: view_name,
                id: "{{view.id or ''}}",
                title: title,
                name: "{{view.name or ''}}",
                class_id: class_id,
                user_id: user_id,
                query: query
            },
            success: function(res) {
                sbm.hide({ id: id_message });

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
        $.ajax({
            url: "{{tg.url('/dashboard/views/delete/')}}",
            data: { view_id: view_id, view_name: view_name },
            success: function(res) {
                if (res.status) {
                    return_();
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
    
    function reload_attributes(class_id, path, rel) {
        var id_message = sbm.show({ message: "{{_('Wait, please...')}}", hide_after: 0, modal: true });
        $.ajax({
            url: "{{tg.url('/dashboard/views/attributes_list/')}}",
            data: {
                class_id: class_id,
                path: path,
                rel: rel
            },
            success: function(res) {
                sbm.hide({ id: id_message });

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
        var id_message = sbm.show({ message: "{{_('Wait, please...')}}", hide_after: 0, modal: true });
        $('#sp-edit-view-cols').html('');
        $.ajax({
            url: "{{tg.url('/dashboard/views/view_cols/')}}",
            data: { view_id: view_id },
            success: function(content) {
                sbm.hide({ id: id_message });

                $('#sp-edit-view-cols').html(content);
                $('#sp-edit-view-cols .filter').disableSelection();
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
                reload_attributes(nodo.attr('class_id'), nodo.attr('path'), nodo.attr('rel'));
            });
        }
    });
    
    $('#sp-view-table').sapnsSelector('setValue', "{{view.class_id or ''}}");
    
    $('#sp-view-user').sapnsSelector({
        rc: 'sp_users', rc_title: "{{_('Users')}}"
    });
    
    function show_grid(cls) {
        
        if (cls !== undefined) {
            cls = "{{view.name}}";
        }
        else {
            cls = view_name;
            query = '';
            if ($('#sp-edit-view-list .grid').length) {
                query = $('#sp-edit-view-list .grid').sapnsGrid('getQuery');
            }
        }
        
        $('#sp-edit-view-list .grid').remove();
        $('#sp-edit-view-list').append('<div class="grid"></div>');
        $('#sp-edit-view-list .grid').sapnsGrid({
            cls: cls,
            q: query,
            rp: 25,
            search_params: {
                url: "{{tg.url('/dashboard/views/grid/')}}",
                data: { view_id: view_id }
            },
            hide_check: true,
            height: parseInt($('#sp-edit-view-list').css('height').replace('px', '')) - 65,
            with_filters: false,
            resize: {
                after: function(col_num) {
                    console.log(col_num);
                }
            }
        });            
    }
    
    $('#sp-edit-view-cols').sortable({
        placeholder: 'placeholder',
        items: '.column',
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
    
    // add field
    var s_add_field = '#sp-edit-view-attr-list .attribute .col-attr.add';
    $(document).off('click', s_add_field).on('click', s_add_field, function() {
        var path = $(this).parents('.attribute').attr('path');
        
        var id_message = sbm.show({ message: "{{_('Wait, please...')}}", hide_after: 0, modal: true });
        $.ajax({
            url: "{{tg.url('/dashboard/views/add_attribute/')}}",
            data: { view_id: view_id, attribute_path: path, view_name: view_name },
            success: function(res) {
                sbm.hide({ id: id_message });

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

    function edit_filter(path, pos) {
        var on_progress = false;

        var id_message = sbm.show({ message: "{{_('Wait, please...')}}", hide_after: 0, modal: true });
        $.ajax({
            url: "{{tg.url('/dashboard/views/edit_filter/')}}",
            data: { view_id: view_id, view_name: view_name, attribute_path: path, pos: pos },
            success: function(res) {
                sbm.hide({ id: id_message });

                if (res.status) {
                    $('#sp-edit-filter-dialog').remove();
                    $('<div id="sp-edit-filter-dialog" style="display:none"></div>').appendTo('body');
                    $('#sp-edit-filter-dialog').html(res.content).dialog({
                        title: "{{_('Advanced filter')}}",
                        modal: true,
                        resizable: false,
                        closeOnEscape: false,
                        width: 850,
                        height: 150,
                        buttons: {
                            "{{_('Ok')}}": function() {
                                if (!on_progress) {
                                    on_progress = true;
                                    filter_save(function(res) {
                                        $('#sp-edit-filter-dialog').dialog('close');
                                        reload_cols();

                                        if (res.view_name !== '') {
                                            view_name = res.view_name;
                                            show_grid();
                                        }
                                    },
                                    function() {
                                        on_progress = false;
                                    });
                                }
                            },
                            "{{_('Cancel')}}": function() {
                                if (!on_progress) {
                                    $('#sp-edit-filter-dialog').dialog('close');
                                }
                            }
                        }
                    });
                }
                else {}
            },
            error: function() {}
        });
    }

    // add (advanced) filter
    var s_add_filter = '#sp-edit-view-attr-list .attribute .col-attr.add-filter';
    $(document).off('click', s_add_filter).on('click', s_add_filter, function() {
        var path = $(this).parents('.attribute').attr('path');
        edit_filter(path);
    });

    // edit filter
    var s_edit_filter = '#sp-edit-view-cols .filter .title';
    $(document).off('dblclick', s_edit_filter).on('dblclick', s_edit_filter, function() {
        var pos = $(this).parents('.filter').attr('pos'), path;

        edit_filter(path, pos);
    });

    var s_column_edit = '#sp-edit-view-cols .column .title';
    $(document).off('dblclick', s_column_edit).on('dblclick', s_column_edit, function() {
        var path = $(this).parent().attr('path'),
            on_progress = false;
        
        var id_message = sbm.show({ message: "{{_('Wait, please...')}}", hide_after: 0, modal: true });
        $.ajax({
            url: "{{tg.url('/dashboard/views/edit_attribute/')}}",
            data: { view_id: view_id, view_name: view_name, path: path },
            success: function(content) {
                sbm.hide({ id: id_message });
                
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
    
    // remove column
    var s_column_close = '#sp-edit-view-cols .column .close';
    $(document).off('click', s_column_close).on('click', s_column_close, function() {
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

    // remove filter
    var s_filter_close = '#sp-edit-view-cols .filter .close';
    $(document).off('click', s_filter_close).on('click', s_filter_close, function() {
        var pos = $(this).parents('.filter').attr('pos');
        
        $.ajax({
            url: "{{tg.url('/dashboard/views/remove_filter/')}}",
            data: { view_id: view_id, view_name: view_name, pos: pos },
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
    
    if ("{{view.name or ''}}") {
        reload_cols();
        show_grid("{{view.name}}");
    }
    
    $('#sp-view-title').focus();
});
