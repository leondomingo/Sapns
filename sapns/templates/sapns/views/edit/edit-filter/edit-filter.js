function filter_save(callback, callback_error) {
    var operator = $('#sp-edit-filter-operator').val(),
        value = $('#sp-edit-filter-value').val();

    $.ajax({
        url: "{{tg.url('/dashboard/views/edit_filter_/')}}",
        data: {
            view_name: "{{filter.view_name}}",
            filter_id: "{{filter.id}}",
            operator: operator,
            value: value,
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
    $('#sp-edit-filter-operator').val("{{filter.value or ''}}").focus();
});