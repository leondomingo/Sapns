/* Sapns selector */

(function($) {

    // SapnsSelector (constructor)
    function SapnsSelector(settings) {
        
        var _settings = $.extend(true, {
            name: 'sapns_selector_' + Math.floor(Math.random()*999999),
            value: '',
            title: '',
            rc: '',
            rc_title: settings.rc.toUpperCase(),
            read_only: false,
            title_url: "{{tg.url('/dashboard/title/')}}",
            edit_url: "{{tg.url('/dashboard/edit/')}}",
            onChange: null,
            onClick: null,
            dialog: {
                width: 1100,
                height: 'auto',
            },
            grid: {
                cls: settings.rc,
                rp: 25,
                pag_n: 1,
                with_pager: true,
                pager_options: [{
                    val: 25,
                    desc: '25',
                    sel: true
                },
                {
                    val: 100,
                    desc: '100',
                    sel: false
                },
                {
                    val: 500,
                    desc: '500',
                    sel: false
                }],
                allow_multiselect: false,
                height: 380,
                exportable: false,
                select_first: true,
                search_params: {
                    url: settings.search_url,
                    data: settings.search_data
                },
                with_filters: false
            }
        }, settings);
        
        $.extend(true, this, _settings);
    }
    
    // setValue
    SapnsSelector.prototype.setValue = function(value, no_callback) {
        
        var self = this;
        
        if (!self.read_only) {
            var change = self.value != value,
                old_value = self.value;
    
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
        
        var self = this,
            id = "#st_" + self.name,
            value = self.value;
        
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
        
        $('#st_' + self.name).prop('disabled', value);
        $('#sb_' + self.name).prop('disabled', value);
        $('#rb_' + self.name).prop('disabled', value);
        self.read_only = value;
    }
    
    SapnsSelector.prototype.dialog_name = function() {
        var self = this;
        return '#sp-selector-dialog-' + self.name;
    }
    
    $.fn.sapnsSelector = function(arg1, arg2, arg3) {
        
        if (typeof(arg1) === "object") {
            
            var self = this,
                sapnsSelector = new SapnsSelector(arg1),
                // select text
                select_text = '<input id="st_' + sapnsSelector.name + '" class="sp-select-text" type="text" readonly value=""';
            
            if (self.is('[readonly]') || self.is('[disabled]')) {
                sapnsSelector.read_only = true;
                select_text += ' disabled';
            }
            
            select_text += '>';
            
            self.append(select_text);
            
            // double-click to edit the selected object (if there's any)
            self.find('#st_' + sapnsSelector.name).dblclick(function() {
                
                if (!sapnsSelector.isReadonly) {
                    var cls = sapnsSelector.getClass(),
                        id = sapnsSelector.getValue();
                    if (id != '') {
                        var url_edit = sapnsSelector.edit_url;
                        
                        if (url_edit[url_edit.length-1] != '/') {
                            url_edit += '/';
                        }
                        
                        url_edit += sprintf('%s/%s', cls, id);
                        
                        var form_edit =
                            '<form action="' + url_edit + '" method="post" target="_blank">\
                                <input type="hidden" name="came_from" value="">\
                            </form>';
                            
                        $(form_edit).appendTo('body').submit().remove();
                    }
                }
            });
            
            // select_button
            var title = "{{_('Set value')}}",
                select_button = '<button id="sb_' + sapnsSelector.name + '" class="sp-select-button" title="' + title + '"';
            
            if (sapnsSelector.read_only) {
                select_button += ' disabled';
            }
            
            select_button += '>...</button>';
            
            self.append(select_button);

            self.find('#sb_' + sapnsSelector.name).click(function() {
                
                if (!sapnsSelector.isReadonly) {
                    
                    if (sapnsSelector.onClick) {
                        sapnsSelector.onClick(sapnsSelector.value);
                    }
                    else {
                        // dialog title
                        var dialog_title = sapnsSelector.rc_title;
                        if (typeof(sapnsSelector.rc_title) === 'function') {
                            dialog_title = sapnsSelector.rc_title();
                        }
                        
                        var dialog_name_ = sapnsSelector.dialog_name().replace('#', '');
                        
                        $(sapnsSelector.dialog_name()).remove();
                        $('<div id="' + dialog_name_ + '"><div class="sapnsGrid"></div></div>').appendTo('body');
                        $(sapnsSelector.dialog_name() + ' .sapnsGrid').sapnsGrid(sapnsSelector.grid);
                        
                        // show search dialog
                        $(sapnsSelector.dialog_name()).dialog({
                            title: dialog_title,
                            width: sapnsSelector.dialog.width,
                            height: sapnsSelector.dialog.height,
                            resizable: false,
                            modal: true,
                            buttons: {
                                "{{_('Ok')}}": function() {
                                    // get the id of the selected row
                                    var new_value = $(sapnsSelector.dialog_name() + ' .sapnsGrid').sapnsGrid('getSelectedIds')[0],
                                        current_value = sapnsSelector.getValue();
                                    
                                    sapnsSelector.setValue(new_value);
                                    if (current_value != new_value) {
                                        sapnsSelector.setTitle();
                                    }
                                    
                                    $(sapnsSelector.dialog_name()).dialog('destroy').remove();
                                },
                                "{{_('Cancel')}}": function() {
                                    $(sapnsSelector.dialog_name()).dialog('destroy').remove();
                                }
                            }
                        });
                    }
                }
            });
            
            sapnsSelector.setTitle();
            
            // remove button
            var remove_button = '<button id="rb_' + sapnsSelector.name + '" class="sp-empty-button"',
                title = "{{_('Remove value')}}";
            
            if (sapnsSelector.read_only) {
                remove_button += ' disabled ';
            }
            
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
        else if (typeof(arg1) === "string") {
            
            var sapnsSelector = this.data('sapnsSelector');
            
            // setValue(arg2)
            // $(element).sapnsSelector("setValue", 123);
            // $(element).sapnsSelector("setValue", null);
            if (arg1 === "setValue") {
                var current_value = sapnsSelector.getValue();
                sapnsSelector.setValue(arg2, arg3);
                if (current_value != arg2) {
                    sapnsSelector.setTitle();
                }
            }
            // getValue()
            else if (arg1 === "getValue") {
                return sapnsSelector.value;
            }
            // getTitle()
            else if (arg1 === "getTitle") {
                return sapnsSelector.title;
            }
            // getClass()
            else if (arg1 === "getClass") {
                return sapnsSelector.rc;
            }
            else if (arg1 === "setReadonly") {
                sapnsSelector.setReadonly(arg2);
            }
            else if (arg1 === "isReadonly") {
                return sapnsSelector.read_only;
            }
            // TODO: other sapnsSelector methods
        }
        
        return this;
    };
}) (jQuery);