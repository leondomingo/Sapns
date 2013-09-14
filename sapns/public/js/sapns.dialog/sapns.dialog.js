var SapnsDialog = (function(dialog_id, before_load, after_load) {

    var self = this;
    self.dialog_id = dialog_id;
    $('#'+self.dialog_id).remove();
    self.el = $('<div id="' + self.dialog_id + '" style="display:none"></div>').appendTo('body');

    self.load = function(params) {

        if (typeof(arguments[0]) === 'object') {
            /*
                params {
                    url
                    data (opcional)
                    success
                    error (opcional)
                }
            */

            if (params.data === undefined) {
                params.data = {};
            }

            if (params.error === undefined) {
                params.error = function() {};
            }

            if (before_load) {
                before_load();
            }

            if (params.html_load === undefined) {
                $.ajax({
                    url: params.url,
                    data: params.data,
                    success: function(res) {
                        if (after_load) {
                            after_load();
                        }

                        if (res.status) {
                            self.el.html(res.content);
                            params.success(res);
                        }
                        else {
                            params.error(res);
                        }
                    },
                    error: params.error
                });
            }
            else {
                $.ajax({
                    url: params.url,
                    data: params.data,
                    success: function(content) {
                        if (after_load) {
                            after_load();
                        }

                        self.el.html(content);
                        params.success();
                    },
                    error: params.error()
                });   
            }
        }
        else if (typeof(arguments[0]) === 'string') {
            /* 
                content
                onLoad (function) (opcional)
            */
            var content = arguments[0], on_load;

            if (arguments.length > 1) {
                on_load = arguments[1];
            }

            self.el.html(content);
            if (on_load) {
                on_load();
            }
        }
    }

    self.load_content = function(content) {
        $('#'+self.dialog_id).html(content);
        return self;
    }

    self.dialog = function(params) {
        params = $.extend({ modal: true, resizable: false, width: 'auto', height: 'auto' }, params);
        return self.el.dialog(params);
    }

    self.close = function() {
        return self.el.dialog('close');
    }
});
