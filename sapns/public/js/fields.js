var fields = {
        check_regex: function(field, regex) {
            if (!regex) {
                var regex = field.attr('regex');
            }
            
            var text = field.val();
            if (regex && text) {
                try {
                    regex = new RegExp(regex.trim());
                    if (regex.test(text)) {
                        field.css('color', '').attr('_ok', 1);
                    }
                    else {
                        field.css('color', 'red').attr('_ok', '');
                    }
                }
                catch(e) {
                    field.css('color', '').attr('_ok', 1);
                }
            }
        },
        num_field_keydown: function (fld, e, is_int) {
            var k = e.which;
            var current_text = fld.val();
            var one_dot = current_text.search(/\./) != -1;
            if ((k < 48 || k > 57) && // numbers
                (k < 96 || k > 105) && // numbers
                (current_text.length > 0 || k != 109) && // - (minus sign)
                (current_text.length > 0 || k != 107) && // + (plus sign)
                (current_text.length > 0 || k != 61) && // + (plus sign)
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
        num_field_change: function(fld, is_int, no_sign) {
            var current_text = fld.val();
            if (current_text.trim()) {
                if (!no_sign) {
                    if (is_int) {
                        var pat = /^\s*(-|\+)?\d+\s*$/g
                    }
                    else {
                        var pat = /^\s*(-|\+)?\d+(\.\d*)?$/g
                    }
                }
                else {
                    if (is_int) {
                        var pat = /^\s*\d+\s*$/g
                    }
                    else {
                        var pat = /^\s*\d+(\.\d*)?$/g
                    }
                }
                
                var ok = pat.test(current_text);
                if (ok) {
                    fld.css('color', '');
                }
                else {
                    fld.css('color', 'red');
                }
            }
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