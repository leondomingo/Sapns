function add_filter(callback, callback_error) {
    // TODO: comprobaciones
    var operator, value;

    $.ajax({
        url: "{{tg.url('/dashboard/views/add_filter_/')}}",
        data: { operator: operator, value: value },
        success: function(res) {
            if (res.status) {
    
            }
            else {}
        },
        error: function() {}
    });
}

$(function() {
    $('#sp-add-filter-field').focus();
});