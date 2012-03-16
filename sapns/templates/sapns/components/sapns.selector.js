/* Sapns selector */

function load_script(src) {
    //console.log('Loading from: ' + src);
    var fileref = document.createElement('script');
    fileref.setAttribute("type", "text/javascript");
    fileref.setAttribute("src", src);
    document.getElementsByTagName("head")[0].appendChild(fileref)
}

try {
    sprintf;
}
catch (e) {
    load_script("{{tg.url('/js/sprintf.min.js')}}");
}

(function($) {

    // SapnsSelector (constructor)
    function SapnsSelector(settings) {
        
        function set(this_object, key, value, obj) {
            
            if (obj == undefined) {
                obj = settings;
            }

            if (obj[key] == undefined) {
                this_object[key] = value;
            }
            else {
                this_object[key] = obj[key];
            }
            
            return;
        }
        
        set(this, 'name', 'sel_' + Math.floor(Math.random()*999999));
        set(this, 'value', '');
        set(this, 'title', '');
        set(this, 'rc', '');
        set(this, 'rc_title', '');
        set(this, 'read_only', false);
        set(this, 'title_url', "{{tg.url('/dashboard/title/')}}");
        set(this, 'search_url', "{{tg.url('/dashboard/search/')}}");
        set(this, 'search_params', null);
        set(this, 'edit_url', "{{tg.url('/dashboard/edit/')}}");
        set(this, 'onChange', null);
        
        set(this, 'dialog', {});
        
        set(this.dialog, 'width', 1100, this.dialog);
        set(this.dialog, 'height', 600, this.dialog);
        set(this.dialog, 'results', 25, this.dialog);
    }
    
    // setValue
    SapnsSelector.prototype.setValue = function(value, no_callback) {
        
        var self = this;
        
        if (!self.read_only) {
            var change = self.value != value;
            var old_value = self.value;
    
            self.value = value;
            if (change && self.onChange && !no_callback) {
                self.onChange(value, old_value);
            }
        }
    }
    
    // getValue
    SapnsSelector.prototype.getValue = function() {
        return this.value;
    }

    // setTitle
    SapnsSelector.prototype.setTitle = function() {
        
        var self = this;
        var id = "#st_" + self.name
        var value = self.value;
        
        if (value && self.rc) {
            $.ajax({
                url: self.title_url,
                data: {
                    cls: self.rc,
                    id: self.value
                },
                success: function(data) {
                    if (data.status) {
                        $(id).val(data.title).parent().attr('value', value);
                        self.title = data.title;
                    }
                }
            });
        }
        else {
            $(id).val('').parent().attr('value', '');
            self.title = '';
        }
    }
    
    // getTitle
    SapnsSelector.prototype.getTitle = function() {
        return this.title;
    }
    
    // getClass
    SapnsSelector.prototype.getClass = function() {
        return this.rc;
    }
    
    // search
    SapnsSelector.prototype.search = function(q) {
        
        var self = this;
        var dialog_name = "#dialog_" + self.name;
        
        if (q == undefined) {
            q = $(dialog_name + ' .sp-search-text').val();
        }
        
        // search params
        var params = {
                cls: self.rc,
                q: q,
                rp: self.dialog.results
        };
        
        if (self.search_params != null) {
            if (typeof(self.search_params) == 'object') {
                params = $.extend(true, params, self.search_params);
            }
            else if (typeof(self.search_params) == 'function') {
                params.search_params = self.search_params;
                params.search_params();
            }
        }

        // search
        $.ajax({
            url: this.search_url,
            //type: 'post',
            dataType: 'html',
            data: params,
            success: function(res) {
                $(dialog_name).html(res);
            },
            error: function(f, status, error) {
                alert('error!');
                sapnsSelector.search();
                // $(dialog_name).dialog('close'); 
            }
        });
    }

    // search_kp
    SapnsSelector.prototype.search_kp = function(event) {
        if (event.which == 13) {
            this.search();
        }
    }

    // remove
    SapnsSelector.prototype.remove = function() {
        this.setValue('');
        this.setTitle();
    }
    
    // setEnabled
    SapnsSelector.prototype.setReadonly = function(value) {
        
        var self = this;
        
        if (value === undefined) {
            value = true;
        }
        
        $('#st_' + self.name).attr('disabled', value);
        $('#sb_' + self.name).attr('disabled', value);
        $('#rb_' + self.name).attr('disabled', value);
        self.read_only = value;
    }

    $.fn.sapnsSelector = function(arg1, arg2, arg3) {
        
        if (typeof(arg1) == "object") {
            
            var sapnsSelector = new SapnsSelector(arg1);
            
            // dialog
            this.append('<div id="dialog_' + sapnsSelector.name + '" style="display: none;"></div>'); 

            // select text
            var select_text = 
                '<input id="st_' + sapnsSelector.name + '"' + 
                ' class="sp-select-text" type="text" readonly value=""';
            
            if (this.attr('readonly') || this.attr('disabled')) {
                sapnsSelector.read_only = true;
            }
            
            if (sapnsSelector.read_only) {
                select_text += ' disabled';
            }
            
            select_text += '>';
            
            this.append(select_text);
            
            // double-click to edit the selected object (if there's any)
            this.find('#st_' + sapnsSelector.name).dblclick(function() {
                
                if (!sapnsSelector.isReadonly) {
                    var cls = sapnsSelector.getClass();
                    var id = sapnsSelector.getValue();
                    if (id != '') {
                        var url_edit = sapnsSelector.edit_url;
                        
                        if (url_edit[url_edit.length-1] != '/') {
                            url_edit += '/';
                        }
                        
                        url_edit += sprintf('%s/%s', cls, id);
                        
                        var form_edit =
                            '<form action="' + url_edit + '" method="post" target="_blank">' +
                                '<input type="hidden" name="came_from" value="">' +
                            '</form>';
                            
                        $(form_edit).appendTo('body').submit().remove();
                    }
                }
            });
            
            // select_button
            var title = sprintf('{{_("Set a value for [%s]")}}', sapnsSelector.title);
            var select_button = 
                '<button id="sb_' + sapnsSelector.name + '"' +
                ' class="sp-select-button" ' +
                ' title="' + title + '"'
            
            if (sapnsSelector.read_only) {
                select_button += ' disabled';
            }
            
            select_button += '>...</button>';
            
            this.append(select_button);

            this.find('#sb_' + sapnsSelector.name).click(function() {
                
                if (!sapnsSelector.isReadonly) {
                    
                    // dialog title
                    var dialog_title = sapnsSelector.rc_title;
                    if (typeof(sapnsSelector.rc_title) == 'function') {
                        dialog_title = sapnsSelector.rc_title();
                    }
                    
                    // show search dialog
                    $('#dialog_' + sapnsSelector.name).dialog({
                        title: dialog_title,
                        width: sapnsSelector.dialog.width,
                        height: sapnsSelector.dialog.height,
                        resizable: false,
                        modal: true,
                        buttons: {
                            "{{_('Ok')}}": function() {
                                // get the id of the selected row
                                
                                var id_selected = $('#dialog_' + sapnsSelector.name + ' .sapns_grid').sapnsGrid('getSelectedIds')[0];
                                
                                sapnsSelector.setValue(id_selected);
                                sapnsSelector.setTitle();
                                
                                $('#dialog_' + sapnsSelector.name).dialog('close');
                            },
                            "{{_('Cancel')}}": function() {
                                $('#dialog_' + sapnsSelector.name).dialog('close');
                            }
                        }
                    });
                    
                    sapnsSelector.search('');
                }
            });
            
            sapnsSelector.setTitle();
            
            // remove button
            var remove_button = '<button id="rb_' + sapnsSelector.name + '" class="sp-empty-button"';
            
            if (sapnsSelector.read_only) {
                remove_button += ' disabled ';
            }
            
            var title = sprintf("{{_('Remove value of [%s]')}}", sapnsSelector.title);
            remove_button += ' title="' + title + '">x</button>';

            this.append(remove_button);
            
            this.find('#rb_' + sapnsSelector.name).click(function() {
                if (!sapnsSelector.isReadonly) {
                    sapnsSelector.remove();
                }
            });
            
            //this.sapnsSelector = sapnsSelector;
            this.data('sapnsSelector', sapnsSelector);
        }
        else if (typeof(arg1) == "string") {
            
            var sapnsSelector = this.data('sapnsSelector');
            
            // setValue(arg2)
            // $(element).sapnsSelector("setValue", 123);
            // $(element).sapnsSelector("setValue", null);
            if (arg1 == "setValue") {
                sapnsSelector.setValue(arg2, arg3);
                sapnsSelector.setTitle();
            }
            // getValue()
            else if (arg1 == "getValue") {
                return sapnsSelector.value;
            }
            // getTitle()
            else if (arg1 == "getTitle") {
                return sapnsSelector.title;
            }
            // getClass()
            else if (arg1 == "getClass") {
                return sapnsSelector.rc;
            }
            else if (arg1 == "setReadonly") {
                sapnsSelector.setReadonly(arg2);
            }
            else if (arg1 == "isReadonly") {
                return sapnsSelector.read_only;
            }
            // TODO: other sapnsSelector methods
        }
        
        return this;
    };
}) (jQuery);