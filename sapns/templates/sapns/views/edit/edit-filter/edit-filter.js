function filter_save(callback, callback_error) {
    var operator = $('#sp-edit-filter-operator').val(),
        value = $('#sp-edit-filter-value').val(),
        null_value = $('#sp-edit-filter-null-value').val();

    $.ajax({
        url: "{{tg.url('/dashboard/views/edit_filter_/')}}",
        data: {
            view_name: "{{filter.view_name}}",
            filter_id: "{{filter.id}}",
            operator: operator,
            value: value,
            null_value: null_value,
            pos: "{{filter.pos}}"
        },
        success: function(res) {
            if (res.status) {
                callback(res);
            }
            else {
                alert('Error!');
                callback_error();
            }
        },
        error: function() {
            alert('Error!');
            callback_error();
        }
    });
}

$(function() {
    $('#sp-edit-filter-operator').val("{{filter.operator or ''}}").focus();

    $('#sp-edit-filter-date-functions').change(function() {
        $('#sp-edit-filter-value').val($(this).val());
        $(this).val('');
    });

    var s_filter_value = '#sp-edit-filter-value';
    $(document).off('keypress', s_filter_value).on('keypress', s_filter_value, function(e) {
        if (e.which === 13) {
            // INTRO
            $(this).parents('.ui-dialog').find('.ui-dialog-buttonset button:first').click();
        }
    });
});