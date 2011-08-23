var fields = {
num_field_keydown: function (fld, e, is_int) {
    var k = e.which;
    var current_text = fld.val();
    var one_dot = current_text.search(/\./) != -1;
    if ((k < 48 || k > 57) && // numbers
        (k < 96 || k > 105) && // numbers
        (k != 190 || one_dot || is_int) && // dot (.)
        (k != 110 || one_dot || is_int) && // dot (.)
        k != 46 && // delete
        k != 8 && // backspace
        k != 9 && // tab
       (k < 37 || k > 40) && // cursor keys
       (k < 35 || k > 36)       
      ) {
        e.preventDefault();
    }
    //console.log(e.which);
},
time_field_keydown: function (e) {
    var k = e.which;
    if ((k < 48 || k > 57) &&
        (k < 96 || k > 105) &&
        k != 59 &&
        k != 46 &&
        k != 8 &&
        k != 9 &&
        (k < 37 || k > 40) &&
        (k < 35 || k > 36)
       ) {
        e.preventDefault();
        //console.log(k);
    }
},
time_field_change: function(fld) {
    var current_text = fld.val();
    if (current_text.trim()) {
        var pat = /^\s*\d{1,2}:\d{1,2}(:\d{1,2})?\s*$/g
        var ok = pat.test(current_text);
        if (ok) {
            fld.css('color', '');
        }
        else {
            fld.css('color', 'red');
        }
    }
}
};

/*$(document).ready(function() {
    $('.float_field').keydown(function(e) {
        num_field_keydown($(this), e, true);
    });

    $('.time_field').keydown(function(e) {
        time_field_keydown(e);
    }).change(function() {
        time_field_change($(this));
    });
});*/