$(function() {
    $('#copy_from').sapnsSelector({
        rc: 'sp_users', rc_title: "{{_('Users')}}"
    });
    
    $('#display_name').focus();
    
    SapnsFields.init('#user_name, #email_address, #password', 'change');
    
    $('#cancel_user_btn').click(function() {
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
    });
    
    $('#save_user_btn').click(function() {
        
        // display_name 
        var display_name = $('#display_name').val();
        if (!display_name) {
            alert('{{_("\"Display name\" is required")}}');
            $('#display_name').focus();
            return;
        }
        
        // user_name 
        var user_name = $('#user_name').val(),
            user_name_ok = !$('#user_name').hasClass('sp-field-error');
        if (!user_name || !user_name_ok) {
            alert('{{_("\"User name\" is required")}}');
            $('#user_name').focus();
            return;
        }
        
        // email_address 
        var email_address = $('#email_address').val(),
            email_address_ok = !$('#email_address').hasClass('sp-field-error');
        if (!email_address || !email_address_ok) {
            alert('{{_("\"E-mail address\" is required")}}');
            $('#email_address').focus();
            return;
        }
        
        // password 
        var password = $('#password').val(),
            password_ok = !$('#password').hasClass('sp-field-error');
        // {% if not user.user_id %}
        if (!password) {
            alert('{{_("\"Password\" is required")}}');
            $('#password').focus();
            return;
        }
        // {% endif %} 
        
        if (!password_ok) {
            alert('{{_("\"Password\" is required")}}');
            $('#password').focus();
            return;
        }
        
        var password2 = $('#password2').val();
        if (password != '' && password != password2) {
            alert("{{_('Passwords must be equal')}}");
            return;
        }
        else {
            
            var copy_from = '';
            // {% if not user.user_id %} 
            copy_from = $('#copy_from').sapnsSelector('getValue');
            if (!copy_from) {
                alert("{{_('A user to copy from must be specified')}}");
                return;
            }
            // {% endif %}
            
            $.ajax({
                url: "{{tg.url('/dashboard/users/save/')}}",
                data: {
                    id: "{{user.user_id}}",
                    display_name: display_name,
                    user_name: user_name,
                    email_address: email_address,
                    password: password,
                    copy_from: copy_from,
                },
                success: function(data) {
                    if (data.status) {
                        $('#form_exit').submit();
                    }
                    else if (data.message) {
                        alert(data.message);
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
    });
});