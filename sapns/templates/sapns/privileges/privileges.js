function attr_access_change() {

    var attr_p = $(this).parent();
    
    var data_in = $('#classes_list').data('data_in');
    data_in.id_attribute = attr_p.attr('id_attr');
    data_in.id_attr_p = attr_p.attr('id_attr_p');
    data_in.access = $(this).val();
    
    $.ajax({
        url: "{{tg.url('/dashboard/privileges/attrp_update')}}",
        data: data_in,
        success: function(data) {
            if (data.status) {
            }
        }
    });
}

function init_attr_events() {
    // attr_access (select) 
    $('.attr_row select').change(attr_access_change);
}

function action_granted_change() {
    
    var action_p = $(this).parent();
    
    var data_in = $('#classes_list').data('data_in');
    data_in.id_action = action_p.attr('id_action');
    data_in.granted = $(this).val();
    
    $.ajax({
        url: "{{tg.url('/dashboard/privileges/actionp_update')}}",
        data: data_in,
        success: function(data) {
            if (data.status) {
            }
        }
    });
}

function init_action_events() {
    // action_granted (select) 
    $('.action_row select').change(action_granted_change);
}

function load_privileges(id_class) {

    var data_in = $('#classes_list').data('data_in');
    data_in.id_class = id_class;
    
    // attributes 
    $('#attr_list').html("<p>{{_('Loading')}}...</p>");
    $.ajax({
        url: "{{tg.url('/dashboard/privileges/attributes')}}",
        data: data_in, 
        success: function(data) {
            $('#attr_list').html(data);
            init_attr_events();
        }
    });
    
    // actions 
    $('#actions_list').html("<p>{{_('Loading')}}...</p>");
    $.ajax({
        url: "{{tg.url('/dashboard/privileges/actions')}}",
        data: data_in,
        success: function(data) {
            $('#actions_list').html(data);
            init_action_events();
        }
    });
}
    
function init_classes_events() {
    // class name click 
    $('.class_name').click(function() {
        $('.class_row').removeClass('class_row_selected');
        $(this).parent().addClass('class_row_selected');                
        
        load_privileges($(this).parent().attr('id_class'));
    });
    
    // class select 
    $('.class_row select').change(function() {
        
        var data_in = $.extend(true, 
                $('#classes_list').data('data_in'), 
                {
                    id_class: $(this).parent().attr('id_class'),
                    granted: $(this).val()
                }
        );
        
        //if (get_role_user(data_in)) { 
        $.ajax({
            url: "{{tg.url('/dashboard/privileges/classp_update')}}",
            data: data_in,
            success: function(data) {
                if (data.status) {
                }
            }
        });
        //}
    });
}
    
function load_classes(id_role, id_user) {
    
    $('#classes_list').html("<p>{{_('Loading')}}...</p>");
    
    var data_in = $('#classes_list').data('data_in');
    
    $.ajax({
        url: "{{tg.url('/dashboard/privileges/classes')}}",
        data: data_in,
        success: function(data) {
            $('#classes_list').html(data);
            init_classes_events();
            // Select the first class 
            $('.class_name:first').click();
        }
    });
}

// attr_ selects 
function change_all_selects(access) {
    $(this).parent().parent().find('select').each(function() {
        if ($(this).val() != access) {
            $(this).val(access);
            this.attr_access_change = attr_access_change;
            this.attr_access_change();
        }
    });            
}

// actions selects 
function change_all_actions_selects(granted) {
    $(this).parent().parent().find('select').each(function() {
        if ($(this).val() != granted ) {
            $(this).val(granted);
            this.action_granted_change = action_granted_change;
            this.action_granted_change();
        }
    });
}

function set_empty() {
    $('#classes_list').html('');
    $('#attr_list').html('');
    $('#actions_list').html('');
}

$(document).ready(function() {

    // role selector 
    /*
    $('#role_selector').sapnsSelector({
        name: 'role',
        title: "{{_('Role')}}",
        rc: 'sp_roles',
        rc_title: "{{_('Roles')}}",
        onChange: function(value) {
            if (value != '') {
                $('#user_selector').sapnsSelector('setValue', '', true);
                load_classes();
            }
            else {
                set_empty();
            }
        }
    });
    */
    
    // user selector 
    /*
    $('#user_selector').sapnsSelector({
        name: 'user',
        title: "{{_('User')}}",
        rc: 'sp_users',
        rc_title: "{{_('Users')}}",
        dialog: { results: 0 },
        onChange: function(value) {
            if (value != '') {
                $('#role_selector').sapnsSelector('setValue', '', true);
                load_classes();
            }
            else {
                set_empty();
            }
        }
    });
    */
    
    $('#btn_denied').click(function() {
        this.change_all_selects = change_all_selects;
        this.change_all_selects('denied');
    });
    
    $('#btn_readonly').click(function() {
        this.change_all_selects = change_all_selects;
        this.change_all_selects('read-only');
    });

    $('#btn_readwrite').click(function() {
        this.change_all_selects = change_all_selects;
        this.change_all_selects('read/write');
    });
    
    $('#btn_yes').click(function() {
        this.change_all_actions_selects = change_all_actions_selects;
        this.change_all_actions_selects('true');
    });
    
    $('#btn_no').click(function() {
        this.change_all_actions_selects = change_all_actions_selects;
        this.change_all_actions_selects('false');
    });
    
    var data_in = {
            id_role: "{{id_role or ''}}",
            id_user: "{{id_user or ''}}"
    };
    
    $('#classes_list').data('data_in', data_in);
    load_classes();
});