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
                        accept: '.sp-shortcut.list, .sp-shortcut.process, .sp-shortcut.view',
                        hoverClass: 'accept',
                        drop: function(e, ui) {
                            share_shortcut(ui.draggable.attr('shortcut_id'));
                        }
                    });
                    
                    // roles 
                    $('#sp-shortcut-options .roles').droppable({
                        accept: '.sp-shortcut.list, .sp-shortcut.process, .sp-shortcut.view',
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
        var en_proceso = false;
        var id_mensaje = sbm.show({ message: "{{_('Wait, please')}}...", hide_after: 0 });
        
        $.ajax({
            url: "{{tg.url('/dashboard/sc/edit/')}}",
            data: {
                user_id: "{{user.id}}",
                id_shortcut: id_shortcut,
                id_parent: "{{this_shortcut.id or ''}}"
            },
            success: function(content) {
                sbm.hide({ id: id_mensaje, velocity: 1500 });
                
                $('#sp-shortcut-new-dialog').remove();
                $('<div id="sp-shortcut-new-dialog" style="display:none"></div>').appendTo('body');
                $('#sp-shortcut-new-dialog').html(content).dialog({
                    title: "{{_('New shortcut')}}",
                    modal: true,
                    resizable: false,
                    width: 700,
                    height: 'auto',
                    buttons: {
                        "{{_('Ok')}}": function() {
                            if (!en_proceso) {
                                en_proceso = true;
                                sp_shortcut_new(function(res) {
                                    $('#sp-shortcut-new-dialog').dialog('close');
                                    load_shortcuts();
                                },
                                function() {
                                    en_proceso = false;
                                });
                            }
                        },
                        "{{_('Cancel')}}": function() {
                            if (!en_proceso) {
                                $('#sp-shortcut-new-dialog').dialog('close');
                            }
                        }
                    }
                });
            },
            error: function() {
                sbm.hide({ id: id_mensaje, velocity: 1500 });
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
        
        var message_id = sbm.show({ message: "{{_('Wait, please')}}...", hide_after: 0 });

        $.ajax({
            url: "{{tg.url('/dashboard/sc/share_users/')}}",
            data: { shortcut_id: shortcut_id },
            success: function(content) {
                
                sbm.hide({ id: message_id });
                
                var on_progress = false;
                
                $('#sp-shortcut-share-users-dialog').remove();
                $('<div id="sp-shortcut-share-users-dialog" style="display:none"></div>').appendTo('body');
                
                $('#sp-shortcut-share-users-dialog').html(content).dialog({
                    title: "{{_('Share with users')}}",
                    modal: true,
                    resizable: false,
                    width: 600,
                    height: 'auto',
                    buttons: {
                        "{{_('Ok')}}": function() {
                            if (!on_progress) {
                                on_progress = true;
                                
                                share_users(function() {
                                    $('#sp-shortcut-share-users-dialog').dialog('close');
                                },
                                function() {
                                    on_progress = false;
                                });
                            }
                        },
                        "{{_('Cancel')}}": function() {
                            if (!on_progress) {
                                $('#sp-shortcut-share-users-dialog').dialog('close');
                            }
                        }
                    }
                });                    
            },
            error: function() {
                sbm.hide({ id: message_id });
            }
        });
    }
    
    // share with roles 
    function share_shortcut_roles(shortcut_id) {
        
        var message_id = sbm.show({ message: "{{_('Wait, please')}}...", hide_after: 0 });

        $.ajax({
            url: "{{tg.url('/dashboard/sc/share_roles/')}}",
            data: { shortcut_id: shortcut_id },
            success: function(content) {
                
                sbm.hide({ id: message_id });
                
                var on_progress = false;
                
                $('#sp-shortcut-share-roles-dialog').remove();
                $('<div id="sp-shortcut-share-roles-dialog" style="display:none"></div>').appendTo('body');
                
                $('#sp-shortcut-share-roles-dialog').html(content).dialog({
                    title: "{{_('Share with roles')}}",
                    modal: true,
                    resizable: false,
                    width: 600,
                    height: 'auto',
                    buttons: {
                        "{{_('Ok')}}": function() {
                            if (!on_progress) {
                                on_progress = true;
                                
                                share_roles(function() {
                                    $('#sp-shortcut-share-roles-dialog').dialog('close');
                                },
                                function() {
                                    on_progress = false;
                                });
                            }
                        },
                        "{{_('Cancel')}}": function() {
                            if (!on_progress) {
                                $('#sp-shortcut-share-roles-dialog').dialog('close');
                            }
                        }
                    }
                });                    
            },
            error: function() {
                sbm.hide({ id: message_id });
            }
        });
    }
});
