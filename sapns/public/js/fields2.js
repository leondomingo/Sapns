var SapnsFields = {
        init: function(selector, event, settings) {
            var self = this;
            
            if (settings === undefined) {
                settings = {};
            }
            
            $(selector)[event](function() {
                var settings_ = $.extend(true, { field: $(this) }, settings);
                self.check_regex(settings_);
            });
        },
        check_regex: function(settings) {
            
            var default_settings = {
                    regex_attr: 'regex',
                    class_error: 'sp-field-error',
                    class_ok: 'sp-field-ok'
            }
            
            var settings_ = $.extend(true, default_settings, settings),
                regex = settings_.field.attr(settings_.regex_attr);
            
            var text = settings_.field.val();
            if (regex && text) {
                try {
                    regex = new RegExp(regex.trim());
                    if (regex.test(text)) {
                        settings_.field.removeClass(settings_.class_error).
                            addClass(settings_.class_ok);
                    }
                    else {
                        settings_.field.addClass(settings_.class_error).
                            removeClass(settings_.class_ok);
                    }
                }
                catch(e) {
                    settings_.field.removeClass(settings_.class_error).
                        addClass(settings_.class_ok);
                }
            }
            else {
                settings_.field.removeClass(settings_.class_error).
                    removeClass(settings_.class_ok);
            }
        }
};