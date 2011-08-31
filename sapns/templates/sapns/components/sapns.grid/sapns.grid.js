/* Sapns grid */

(function($) {

    // SapnsGrid (constructor)
    function SapnsGrid(settings) {
        
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
        
        set(this, 'caption', '');
        if (typeof(this.caption) == 'function') {
            this.caption = this.caption();
        }
        set(this, 'name', 'grid_' + Math.floor(Math.random()*999999));
        set(this, 'cls', '');
        set(this, 'with_search', true);
        set(this, 'search_func', function(q, rp, pos) {
            var self = this;
            return {
                url: "{{tg.url('/dashboard/test_search/')}}",
                data: {
                    cls: self.cls,
                    q: q,
                    rp: rp,
                    pos: pos
                },
                _success: function(g, resp) {
                    if (resp.status) {
                        if (resp.cols) {
                            g.cols = resp.cols;
                        }
                        g.data = resp.data;
                        g.loadData();
                    }
                }
            };
        });
        
        set(this, 'show_ids', false);
        set(this, 'link', '');
        set(this, 'q', '');
        set(this, 'ch_attr', '');
        set(this, 'parent_id', '');
        set(this, 'cols', []);
        set(this, 'data', {});
        
        set(this, 'default_', {});
        set(this.default_, 'col_width', 60, this.default_);
        set(this.default_, 'col_align', 'center', this.default_);
        set(this.default_, 'empty_value', '', this.default_);
        
        set(this, 'actions', []);
        if (typeof(this.actions) == 'function') {
            this.actions = this.actions();
        }
        
        set(this, 'exportable', true);
        
        set(this, 'with_pager', true);
        set(this, 'pag_n', 1);
        set(this, 'rp', 10);
        set(this, 'pos', 0);
        set(this, 'totalp', 0);
        set(this, 'total', 0);
        set(this, 'total_pag', 0);
    }

    // getSelectedIds
    SapnsGrid.prototype.getSelectedIds = function() {
        var self = this;
        var selected_ids = [];
        $('#' + self.name + ' .sp-grid-row').each(function() {
            var rowid = $(this).find('.sp-grid-rowid');
            if (rowid.attr('checked') == true) {
                selected_ids.push(rowid.attr('id_row'));
            }
        });
        
        return selected_ids;
    }
    
    // loadData
    SapnsGrid.prototype.loadData = function() {
        
        var self = this;
        var g_table = 
            '<table class="sp-grid">' +
            '<tr><td class="sp-col-title">#</td>';
        
        var cols = self.cols;
        if (typeof(cols) == 'function') {
            cols = cols();
        }
        
        for (var i=0, l=cols.length; i<l; i++) {
            var col = cols[i];
            var wd = col.width;
            if (!wd) {
                wd = self.default_.col_width;
            }
            
            g_table += '<td class="sp-col-title" style="width: ' + wd + 'px;">' + col.title + '</td>';
        }

        g_table += '</tr>';
        
        var data = self.data;
        if (typeof(data) == 'function') {
            data = data();
        }
        
        var ld = data.length;
        if (ld > 0) {
        for (var i=0; i<ld; i++) {
            
            var row = data[i];
            
            g_table += 
                '<tr class="sp-grid-row">' +
                '<td title="' + (i+1) + '"><input class="sp-grid-rowid" type="checkbox" id_row="' + row[0] + '"></td>';
            
            for (var j=0, lr=cols.length; j<lr; j++) {
                var col = cols[j];
                var al = col.align;
                if (!al) {
                    al = self.default_.col_align;
                }
                
                var wd = col.width;
                if (!wd) {
                    wd = self.default_.col_width;
                }
                
                var cell = row[j];
                if (!cell) {
                    cell = self.default_.empty_value;
                }
                
                g_table += '<td class="sp-grid-cell" style="text-align: ' + al + '; width: ' + wd + 'px;"';
                
                if (cell) {
                    g_table += 'title="' + cell + '"';
                }
                else {
                    g_table += 'title="({{_("empty")}})"';
                }
                
                g_table += 'clickable="true">';
                
                if (cell.length > 30) {
                    g_table += (cell+'').substr(0, 30) + '...';
                }
                else {
                    g_table += cell;
                }
                
                g_table += '</td>';
            }
            
            g_table += '</tr>';
        }
        }
        else {
            g_table += 
                '<tr class="sp-grid-row" style="width: 100%;">' +
                    '<td class="sp-grid-cell sp-grid-noresults"' + 
                        ' colspan="' + (cols.length+1) + '">{{_("No results")}}</td>' +
                '</tr>';
        }
        
        $('#' + self.name).find('.sp-grid-parent').html(g_table);
    }
    
    // search
    SapnsGrid.prototype.search = function(q) {
        var self = this;
        self.q = q;
        
        var data = self.search_func(self.q, self.rp, self.pos);
        if (data) {
            if (data.length === undefined) {
                // it's an object
                $.ajax(data);
            }
            else {
                // it's an array
                self.data = data;
                self.loadData();
            }
        }
    }
    
    SapnsGrid.prototype._loadActions = function(actions) {
        
        var g = this;
        var g_actions = '';
        var act_f = []
        
        if (actions.length > 0) {
            g_actions += '<div class="sp-grid-actions-title">{{_("Actions")}}:</div>';
            for (var i=0, l=actions.length; i<l; i++) {
                
                var act = actions[i];
                
                var req_id = act.require_id;
                if (req_id === undefined) {
                    req_id = true;
                }
                
                if (typeof(act.type) === 'string') {
                    g_actions += 
                        '<div style="float: left;">' +
                            '<form class="action-form" method="post" action0="' + act.url + '">' +
                            '<input type="hidden" name="cls" value="' + g.cls + '">' +
                            '<input type="hidden" name="came_from" value="' + g.link + '">';
                    
                    if (g.parent_id) {
                        g_actions += '<input type="hidden" name="_' + g.ch_attr + '" value="' + g.parent_id + '">';
                    }

                    g_actions += '<input class="sp-button sp-grid-action standard_action" type="button" value="' + act.title + '"' +
                        ' title="' + act.url + '" url="' + act.url + '" action-type="' + act.type + '"' +
                        ' require_id="' + req_id + '" >';
                    
                    g_actions += '</form></div>';
                }
                else {
                    g_actions += 
                        '<div style="float: left;">' +
                            '<button id="' + act.type.id + '" class="sp-button sp-grid-action" ' +
                                ' require_id="' + req_id + '" >' + act.title + '</button>' +
                        '</div>';
                    
                    act_f.push(act.type);
                }
            }
        }
        
        // assign functions to actions
        for (var i=0, l=act_f.length; i<l; i++) {
            $('#' + act_f[i].id).data('_func', act_f[i].f);
            
            $('#' + act_f[i].id).live('click', function() {
                if ($(this).attr('require_id') == 'true') {
                    var selected_ids = g.getSelectedIds();
                    if (selected_ids.length > 0) {
                        $(this).data('_func')(selected_ids[0]);
                    }
                }
                else {
                    $(this).data('_func')();
                }
            });
        }        
        
        return g_actions;
    }
    
    SapnsGrid.prototype.loadActions = function() {
        
        var g = this;
        var g_actions = '';
        
        var actions;
        if (!g.actions) {
            actions = g.actions_func();
            if (actions) {
                if (actions.length === undefined) {
                    // it's an object
                    // TODO: llamar a "g._loadActions(...)" en el "success"
                    /*
                    function wrapper_success (data) {
                        var actions = actions.success(data);
                        g._loadActions(actions);                        
                    };
                    
                    actions.success = wrapper_success;
                    */
                    
                    $.ajax(actions);
                }
                else {
                    // it's an array
                    g.actions = actions;
                    g_actions += g._loadActions(g.actions);
                }
            }
        }
        else {
            //actions = g.actions;
            g_actions += g._loadActions(g.actions);
        }
        
        
        // export
        if (g.exportable) {
            g_actions += 
                '<div id="grid-export" style="background-color: none; height: 25px; margin-left: 0px;">' +
                '<select id="select-export" class="sp-button sp-grid-action" style="height: 20px;">' +
                    '<option value="">({{_("Export")}})</option>' +
                    '<option value="csv">CSV</option>' +
                    '<option value="excel">Excel</option>' +
                '</select></div>';
        }

        // standard actions
        $('.standard_action').live('click', function(event) {
            
            // action form 
            var form = $(this).parent();
            
            // child attribute 
            var ch_attr = $('#' + g.name + ' .sp-search-form input[name=ch_attr]').val();
            
            // if CTRL is pressed open in a new tab 
            form.attr('target', '');
            if (event.ctrlKey) {
                form.attr('target', '_blank');
            }
            
            var url = $(this).attr('url');
            var action_type = $(this).attr('action-type')
            console.log(action_type + ': ' + url);
            if ($(this).attr('require_id') == 'true') {
                var selected_ids = g.getSelectedIds();
                if (selected_ids.length > 0) {
                    // edit
                    if (action_type == 'edit') {
                        g.std_edit(selected_ids[0], url);
                    }
                    // delete
                    else if (action_type == 'delete') {
                        g.std_delete(selected_ids, url);
                    }
                }
                else {
                    // new
                    if (action_type == 'new') {
                        g.std_new(url);
                    }
                }
            }
            else {
                $(this).data('_func')();
            }
        });
        
        $('#' + g.name + ' .actions').html(g_actions);
    }
    
    // std_new
    SapnsGrid.prototype.std_new = function() {
        console.log('std_new');
        var self = this;
        return;
    }
    
    // std_edit
    SapnsGrid.prototype.std_edit = function(id) {
        console.log('std_edit');
        var self = this;
        
        console.log(id);
        
        return;
    }
    
    // std_delete
    SapnsGrid.prototype.std_delete = function(ids) {

        console.log('std_delete');
        var self = this;
        
        var cls = self.cls;
        
        return;
        
        var url = button.attr('url');
        
        var delete_html = 
            "<p id='delete-question'>{{_('Do you really want to delete this record?')}}</p>" +
            "<p id='object-title'></p>";
            
        var error_html =
            "<p id='delete-error-title'>{{_('Oops, something went wrong...')}}</p>" +
            "<div id='delete-error-message'></div>";
        
        $('#grid-dialog').html(delete_html);
            
        // {# get object's title #} 
        var title = '';
        $.ajax({
            url: "/dashboard/title",
            type: "get",
            dataType: "json",
            data: {
                cls: cls,
                id: id,         
            },
            success: function(res) {
                if (res.status) {
                    $('#grid-dialog #object-title').html(res.title);
                }
            },
            error: function() {
                // {# alert('error!'); #} 
            }
        });

        $('#grid-dialog').dialog({
            width: 650,
            height: 210,
            resizable: false,
            modal: true,
            title: "{{_('Delete')}}",
            buttons: {
                "{{_('Ok')}}": function() {
                    $.ajax({
                        url: url,
                        type: "get",
                        dataType: "json",
                        data: {
                            cls: cls,
                            id: id,
                        },
                        success: function(res) {
                            if (res.status) {
                                selected_row.remove();
                                $('#grid-dialog').dialog('close');
                            }
                            else {
                                $('#grid-dialog').dialog('close');
                                
                                var message = "<p style='color: gray;'>" + res.message + "</p>";

                                if (res.rel_tables != undefined && res.rel_tables.length > 0) {
                                    message += "<div>{{_('For your information this object is related with other objects in the following classes:')}}</div>";
                                    message += "<ul>";
                                    
                                    for (var i=0; i<res.rel_tables.length; i++) {
                                        var title = res.rel_tables[i].class_title;
                                        var attr_title = res.rel_tables[i].attr_title;
                                        message += '<li><span style="font-weight: bold;">' + title + '</span>' + 
                                          ' (<span style="color: gray;">' + attr_title + '</span>)</li>';
                                    }
                                    
                                    message += "</ul>";
                                }
                                
                                // {# load message #} 
                                $('#grid-dialog').html(error_html).find('#delete-error-message').html(message);
                                
                                // {# show error dialog #} 
                                $('#grid-dialog').dialog({
                                    width: 700,
                                    height: 250,
                                    buttons: {"{{_('Close')}}": function() {
                                        $('#grid-dialog').dialog('close');
                                    }}
                                });
                            }
                        },
                        error: function() {
                            $('#grid-dialog').dialog('close');
                            $('#grid-dialog').html(error_html).dialog({
                                buttons: {
                                    "{{_('Close')}}": function() {
                                        $('#grid-dialog').dialog('close');
                                    }
                                }
                            });
                        },
                    });
                },
                "{{_('Cancel')}}": function() {
                    $('#grid-dialog').dialog('close');
                }
            }
        });
    }

    $.fn.sapnsGrid = function(arg1, arg2, arg3) {
        
        if (typeof(arg1) == "object") {
            
            var g = new SapnsGrid(arg1);
            this.data('sapnsGrid', g);
            
            this.append('<div id="grid-dialog" style="display: none;"></div>');
            
            var g_content = '';            
            g_content += '<div class="sp-grid-container" id="' + g.name + '" cls="' + g.cls + '">';
            
            if (g.caption) {
                g_content += '<div class="sp-grid-caption">' + g.caption + '</div>';
            }
            
            if (g.with_search) {
                
                g_content += 
                    '<div><div style="float: left;">' +
                    /*
                    '<form class="sp-search-form" method="post" action="' + g.search_url + g.cls + '">' +
                        '<input type="hidden" name="caption" value="' + g.caption + '">' +
                        '<input type="hidden" name="show_ids" value="' + g.show_ids + '">' +
                        '<input type="hidden" name="came_from" value="' + g.came_from + '">' +*/
                        '<input class="sp-search-txt" name="q" type="text" value="' + g.q + '">' +
                        /*
                        '<input type="hidden" name="ch_attr" value="' + g.ch_attr + '">' +
                        '<input type="hidden" name="parent_id" value="' + g.parent_id + '">' +
                        */
                        '<button class="sp-button sp-search-btn">{{_("Search...")}}</button></div>';                     
                    //'</form></div>'
                        
                $('#' + g.name + ' .sp-search-btn').live('click', function() {
                    g.search($('#' + g.name + ' .sp-search-txt').val());
                });
                
                $('#' + g.name + ' .sp-search-txt').live('keypress', function(event) {
                    // "Intro" key pressed
                    if (event.which == 13) {
                        g.search($(this).val());
                    }
                });

                if (g.link) {
                    g_content += 
                        '<div style="padding-left: 20px;">' +
                        "<button id='link-shortcut' class='sp-button' style='float: left;'>{{_('Create a shortcut')}}</button>" +
                        '<div style="font-size: 9px; margin-top: 7px; width: 100px; float: left;">' +
                            "<a id='this-search' href='" + g.link + "' target='_blank'>[{{_('this search')}}]</a>" +
                        '</div>' +
                        '<div id="link-shortcut-dialog" style="display: none;">' +
                            "<p>{{_('Do you want to create a shortcut for this search?')}}</p>" +
                            "<label>{{_('Shortcut title')}}:</label>" +
                            "<input id='link-shortcut-title' type='text' value='({{_('title')}})'>" +
                        '</div></div>';
                }
                g_content += '</div>';
            }
            
            var g_table = '<div class="sp-grid-parent" style="overflow: auto; clear: left;"></div>';
            
            // if the row is selected, then mark the checkbox
            $('.sp-grid-cell').live('click', function() {
                if ($(this).attr('clickable') == 'true') {
                    var row_id = $(this).parent().find('.sp-grid-rowid');
                    $('.sp-grid-rowid').each(function() {
                        if ($(this) != row_id) {
                            $(this).attr('checked', false);
                        }
                    });
                    
                    if (row_id.attr('checked') == true) {
                        row_id.attr('checked', false);
                    }
                    else {
                        row_id.attr('checked', true);
                    }
                }
            });
            
            try {
                $('.sp-grid-cell').qtip({
                    content: {
                        text: true
                    },
                    position: {
                        my: "left top",
                        at: "bottom center"
                    },
                    style: "ui-tooltip-dark ui-tooltip-rounded"
                });
            } catch (e) {
                // qtip2 is not loaded
            }
            
            // pager
            var g_pager = '';
            if (g.with_pager) {
            }
            
            this.append(g_content+g_table+g_pager+'<div class="actions"></div></div>');
            
            g.loadActions();

            g.search(g.q)
        }
        else if (typeof(arg1) == "string") {
            
            console.log([arg1, arg2, arg3].join(', '));
            
            var grid = this.data('sapnsGrid');
            
            // setValue(arg2)
            // $(element).sapnsSelector("setValue", 123);
            // $(element).sapnsSelector("setValue", null);
            if (arg1 == "loadData") {
                g.loadData();
            }
            else if (arg1 == "search") {
                var q = '';
                if (arg2) {
                    q = arg2;
                }
                
                g.search(q);
            }
            // getSelectedIds
            else if (arg1 == "getSelectedIds") {
                return g.getSelectedIds();
            }
            else if (arg1 == "delete") {
                g.std_delete();
            }
            // TODO: other sapnsSelector methods
        }
        
        return this;
    };
}) (jQuery);