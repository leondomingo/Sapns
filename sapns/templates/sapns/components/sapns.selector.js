/* Sapns selector */

(function($) {

    // SapnsSelector (constructor)
    function SapnsSelector(settings) {
        var _settings = $.extend(true, {
            name: 'sel_' + Math.floor(Math.random()*999999),
            value: null,
            title: '',
            rc: '',
            rc_title: '',
            read_only: false,
            title_url: "{{tg.url('/dashboard/title/')}}",
            edit_url: "{{tg.url('/dashboard/edit/')}}",
            onChange: null,
            dialog: {
                width: 950,
                height: 550
            },
            grid: {
                cls: settings.rc,
                rp: 25,
                q: '',
                pag_n: 1,
                with_pager: false,
                height: 380,
                exportable: false,
                select_first: true,
                search_params: {
                    url: settings.search_url,
                    data: settings.search_data
                }
            }
        }, settings);

        $.extend(true, this, _settings);
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
            
            // select text
            var select_text = 
                '<input id="st_' + sapnsSelector.name + '"' + 
                ' class="sp-select-text"' + 
                ' type="text" readonly' + 
                ' value=""';
            
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
                        var form_edit =
                            '<form action="' + url_edit + '" method="post" target="_blank">\
                                <input type="hidden" name="cls" value="' + cls + '">\
                                <input type="hidden" name="id" value="' + id + '">\
                                <input type="hidden" name="came_from" value="">\
                            </form>';
                            
                        $(form_edit).appendTo('body').submit().remove();
                    }
                }
            });
            
            // select_button
            var title = sprintf('{{_("Set a value for [%s]")}}', sapnsSelector.title);
            var select_button = 
                '<button id="sb_' + sapnsSelector.name + '"' +
                ' class="sp-button sp-select-button" ' +
                ' title="' + title + '" ' +
                ' style="font-weight:bold"';
            
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
                    
                    var dialog_name = 'dialog_' + sapnsSelector.name,
                        dialog_id = '#' + dialog_name;
                    
                    $(dialog_id).remove();
                    $('<div id="' + dialog_name + '"><div class="sapnsGrid"></div></div>').appendTo('body');
                    $(dialog_id + ' .sapnsGrid').sapnsGrid(sapnsSelector.grid);
                    
                    // show search dialog
                    $(dialog_id).dialog({
                        title: dialog_title,
                        width: sapnsSelector.dialog.width,
                        height: sapnsSelector.dialog.height,
                        resizable: false,
                        modal: true,
                        close: function() {
                            $('#'+dialog_name).remove();
                        },
                        buttons: {
                            "{{_('Ok')}}": function() {
                                // get the id of the selected row
                                
                                var id_selected = $('#'+dialog_name + ' .sapnsGrid').sapnsGrid('getSelectedIds')[0];
                                
                                sapnsSelector.setValue(id_selected);
                                sapnsSelector.setTitle();
                                
                                $(dialog_id).dialog('destroy').remove();
                            },
                            "{{_('Cancel')}}": function() {
                                $(dialog_id).dialog('destroy').remove();
                            }
                        }
                    });
                }
            });
            
            sapnsSelector.setTitle();
            
            // remove button
            var remove_button =
                '<button id="rb_' + sapnsSelector.name + '"' +
                ' class="sp-button sp-empty-button"';
            
            if (sapnsSelector.read_only) {
                remove_button += ' disabled ';
            }
            
            var title = sprintf("{{_('Remove value of [%s]')}}", sapnsSelector.title);
            remove_button += 
                ' title="' + title + '" ' +
                ' style="font-weight: bold; color: red;">x</button>';

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