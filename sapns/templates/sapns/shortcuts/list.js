$(function() {
    
    var sbm = new SidebarMessages(),
        sort_mode = false;
    
    function load_shortcuts() {
        $.ajax({
            url: "{{tg.url('/dashboard/sc/list_/')}}",
            data: {
                id_user: "{{user.id}}",
                sc_parent: "{{this_shortcut.id or ''}}"
            },
            success: function(content) {
                $('#sp-shortcut-list').html(content).removeClass('sort-mode');
                
                // {% if h.is_manager() or h.allowed('dashboard-management') %} 
                if (!sort_mode) {
                    $('.sp-shortcut').draggable({
                        helper: 'clone',
                        start: function() {
                            $('#sp-shortcut-list').addClass('on-dragging');
                            $('#sp-shortcut-options').slideDown();
                        },
                        stop: function() {
                            $('#sp-shortcut-options').slideUp(function() {
                                $('#sp-shortcut-list').removeClass('on-dragging');
                            });
                        }
                    });
                    
                    // sidebar 
                    $('.sp_sidebar').droppable({
                        accept: '.sp-shortcut',
                        hoverClass: 'activo',
                        drop: function(e, ui) {
                            
                            var img = '';
                            // list 
                            if (ui.draggable.hasClass('list')) {
                                img = '<img src="{{tg.url("/images/sapns/icons/list.png")}}"> '; 
                            }
                            // view 
                            else if (ui.draggable.hasClass('view')) {
                                img = '<img src="{{tg.url("/images/sapns/icons/view.png")}}"> ';
                            }
                            // process 
                            else if (ui.draggable.hasClass('process')) {
                                img = '<img src="{{tg.url("/images/sapns/icons/process.png")}}"> ';
                            }
                            // report
                            else if (ui.draggable.hasClass('report')) {
                                img = '<img src="{{tg.url("/images/sapns/icons/print.png")}}"> ';
                            }
                            // group 
                            else if (ui.draggable.hasClass('group')) {
                                img = '<img src="{{tg.url("/images/sapns/icons/group.png")}}"> ';
                            }
                            
                            $.ajax({
                                url: "{{tg.url('/dashboard/sc/bookmark/')}}",
                                data: {
                                    user_id: "{{user.id}}",
                                    id_shortcut: ui.draggable.attr('shortcut_id')
                                },
                                success: function(res) {
                                    if (res.status) {
                                        var new_shortcut = '<div class="item_sb item_sb_sortable" shortcut_id="' + res.shortcut.id + '">\
                                            <a href="' + res.shortcut.url + '">\
                                            <span class="text_sb" title="' + res.shortcut.title + '">' + img + res.shortcut.title + '</span>\
                                            </a></div>' 
                                        
                                        $('.sp_sidebar').append(new_shortcut);
                                    }
                                },
                                error: function() {}
                            });
                        }
                    });
                    
                    // move into a group 
                    $('.sp-shortcut.group').droppable({
                        accept: '.sp-shortcut',
                        hoverClass: 'activo',
                        drop: function(e, ui) {
                            var id_group = $(this).attr('shortcut_id');
                            $.ajax({
                                url: "{{tg.url('/dashboard/sc/move/')}}",
                                data: {
                                    id_shortcut: ui.draggable.attr('shortcut_id'),
                                    id_group: id_group
                                },
                                success: function(res) {
                                    if (res.status) {
                                        ui.draggable.fadeOut(function() {
                                            ui.draggable.remove();
                                        });
                                    }
                                    else {
                                        // Error 
                                    }
                                },
                                error: function() {}
                            });
                        }
                    });
                    
                    // edit 
                    $('#sp-shortcut-options .edit').droppable({
                        accept: '.sp-shortcut',
                        hoverClass: 'accept',
                        drop: function(e, ui) {
                            var shortcut_id = ui.draggable.attr('shortcut_id');
                            edit_shortcut(shortcut_id);
                        }
                    });
                    
                    // users 
                    $('#sp-shortcut-options .users').droppable({
                        accept: '.sp-shortcut.list, .sp-shortcut.process, .sp-shortcut.report, .sp-shortcut.view',
                        hoverClass: 'accept',
                        drop: function(e, ui) {
                            share_shortcut(ui.draggable.attr('shortcut_id'));
                        }
                    });
                    
                    // roles 
                    $('#sp-shortcut-options .roles').droppable({
                        accept: '.sp-shortcut.list, .sp-shortcut.process, .sp-shortcut.report, .sp-shortcut.view',
                        hoverClass: 'accept',
                        drop: function(e, ui) {
                            share_shortcut_roles(ui.draggable.attr('shortcut_id'));
                        }
                    });
                    
                    // up 
                    $('#sp-shortcut-options .up').droppable({
                        accept: '.sp-shortcut',
                        hoverClass: 'accept',
                        drop: function(e, ui) {
                            $.ajax({
                                url: "{{tg.url('/dashboard/sc/move/')}}",
                                data: {
                                    id_shortcut: ui.draggable.attr('shortcut_id'),
                                    id_group: "{{sc_parent}}"
                                },
                                success: function(res) {
                                    if (res.status) {
                                        ui.draggable.fadeOut(function() {
                                            ui.draggable.remove();
                                        });
                                    }
                                    else {
                                        // Error 
                                    }
                                }
                            });
                        }
                    });
                    
                    // delete 
                    $('#sp-shortcut-options .delete').droppable({
                        accept: '.sp-shortcut',
                        hoverClass: 'accept',
                        drop: function(e, ui) {
                            var shortcut_id = ui.draggable.attr('shortcut_id');
                            var action_type = ui.draggable.attr('action_type');
                            var cls = ui.draggable.attr('cls');
                            
                            $('#delete-confirmation').dialog({
                                modal: true,
                                resizable: false,
                                width: 450,
                                buttons: {
                                    "{{_('Ok')}}": function() {
                                        $.ajax({
                                            url: "{{tg.url('/dashboard/sc/delete/')}}",
                                            data: { id_shortcut: shortcut_id },
                                            success: function(res) {
                                                if (res.status) {
                                                    $('#delete-confirmation').dialog('close');
                                                    // delete shortcut (right pane) 
                                                    ui.draggable.fadeOut();
                                                    
                                                    // delete shortcut from sidebar (left pane), if it exists 
                                                    $('.sp_sidebar').find('div[shortcut_id=' + shortcut_id + ']').fadeOut();
                                                }
                                            },
                                            error: function() {
                                                alert('Error!');
                                                $('#delete-confirmation').dialog('close');
                                            }
                                        });
                                    },
                                    "{{_('Cancel')}}": function() {
                                        $('#delete-confirmation').dialog('close');
                                    }
                                }
                            });
                        }
                    });
                }
                else {
                    $('#sp-shortcut-list').addClass('sort-mode').sortable({
                        stop: function() {
                            var sort = [];
                            $('#sp-shortcut-list .sp-shortcut').each(function() {
                                sort.push($(this).attr('shortcut_id')*1);
                            });
                            
                            $.ajax({
                                url: "{{tg.url('/dashboard/sc/reorder/')}}",
                                data: { order: JSON.stringify(sort) },
                                success: function(res) {
                                    if (!res.status) {
                                        $('#sp-shortcut-list').sortable('cancel');
                                    }
                                },
                                error: function() {
                                    $('#sp-shortcut-list').sortable('cancel');
                                }
                            });
                        }
                    });
                }
                // {% endif %} 
            }
        });
    }
    
    load_shortcuts();
    
    function edit_shortcut(id_shortcut) {
        var en_proceso = false, id_message;

        var dlg = new SapnsDialog('sp-shortcut-new-dialog', function() {
            id_message = sbm.show({ message: "{{_('Wait, please...')}}", hide_after: 0 });
        }, function() {
            sbm.hide({ id: id_message, velocity: 1500 });
        });

        dlg.load({
            url: "{{tg.url('/dashboard/sc/edit/')}}",
            data: {
                user_id: "{{user.id}}",
                id_shortcut: id_shortcut,
                id_parent: "{{this_shortcut.id or ''}}"
            },
            html_load: true,
            success: function() {
                
                dlg.dialog({
                    title: "{{_('New shortcut')}}",
                    width: 700,
                    height: 'auto',
                    buttons: {
                        "{{_('Ok')}}": function() {
                            if (!en_proceso) {
                                en_proceso = true;
                                sp_shortcut_new(function(res) {
                                    dlg.close();
                                    load_shortcuts();
                                },
                                function() {
                                    en_proceso = false;
                                });
                            }
                        },
                        "{{_('Cancel')}}": function() {
                            if (!en_proceso) {
                                dlg.close();
                            }
                        }
                    }
                });
            }
        });
    }
    
    $('#sp-shortcut-new').click(function() {
        edit_shortcut();
    });
    
    $('#sp-shortcut-sort').click(function() {
        sort_mode = !sort_mode;
        if (sort_mode) {
            $('#sp-shortcut-sort').qtip({
                content: { text: "{{_('Click again when you finish placing your shortcuts')}}" },
                position: {
                    at: 'left top',
                    my: 'right bottom'
                },
                show: { ready: true },
                hide: false,
                style: 'ui-tooltip-tipped'
            });
        }
        else {
            $('.ui-tooltip.ui-tooltip-tipped').remove();
        }
        
        load_shortcuts();
    });
    
    var s_ = '.sp-no-shortcuts span.here'; 
    $(document).off('click', s_).on('click', s_, function() {
        edit_shortcut();
    });
    
    // share with users 
    function share_shortcut(shortcut_id) {
        
        var message_id, on_progress = false;

        var dlg = new SapnsDialog('sp-shortcut-share-users-dialog', function() {
            id_message = sbm.show({ message: "{{_('Wait, please...')}}", hide_after: 0 });
        }, function() {
            sbm.hide({ id: id_message, velocity: 1500 });
        });

        dlg.load({
            url: "{{tg.url('/dashboard/sc/share_users/')}}",
            data: { shortcut_id: shortcut_id },
            html_load: true,
            success: function() {
                dlg.dialog({
                    title: "{{_('Share with users')}}",
                    width: 600,
                    height: 'auto',
                    buttons: {
                        "{{_('Ok')}}": function() {
                            if (!on_progress) {
                                on_progress = true;
                                
                                share_users(function() {
                                    dlg.close();
                                },
                                function() {
                                    on_progress = false;
                                });
                            }
                        },
                        "{{_('Cancel')}}": function() {
                            if (!on_progress) {
                                dlg.close();
                            }
                        }
                    }
                });                    
            }
        });
    }
    
    // share with roles 
    function share_shortcut_roles(shortcut_id) {
        
        var message_id, on_progress = false;

        var dlg = new SapnsDialog('sp-shortcut-share-roles-dialog', function() {
            id_message = sbm.show({ message: "{{_('Wait, please...')}}", hide_after: 0 });
        }, function() {
            sbm.hide({ id: id_message, velocity: 1500 });
        });

        dlg.load({
            url: "{{tg.url('/dashboard/sc/share_roles/')}}",
            data: { shortcut_id: shortcut_id },
            html_load: true,
            success: function() {
                dlg.dialog({
                    title: "{{_('Share with roles')}}",
                    width: 600,
                    height: 'auto',
                    buttons: {
                        "{{_('Ok')}}": function() {
                            if (!on_progress) {
                                on_progress = true;
                                
                                share_roles(function() {
                                    dlg.close();
                                },
                                function() {
                                    on_progress = false;
                                });
                            }
                        },
                        "{{_('Cancel')}}": function() {
                            if (!on_progress) {
                                dlg.close();
                            }
                        }
                    }
                });
            }
        });
    }
});
