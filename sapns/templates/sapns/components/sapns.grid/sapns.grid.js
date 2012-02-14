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
            } else {
                this_object[key] = obj[key];
            }

            return;
        }

        set(this, 'caption', '');
        if (typeof (this.caption) == 'function') {
            this.caption = this.caption();
        }
        set(this, 'name', 'grid_' + Math.floor(Math.random() * 999999));
        set(this, 'cls', '');
        set(this, 'with_search', true);
        set(this, 'search_params', {});
        set(this, 'show_ids', false);
        set(this, 'link', '');
        set(this, 'q', '');
        set(this, 'ch_attr', '');
        set(this, 'parent_id', '');
        set(this, 'cols', []);
        set(this, 'data', {});
        set(this, 'height', 500);
        set(this, 'url_base', '');
        set(this, 'multiselect', false);
        set(this, 'actions_inline', false);
        set(this, 'hide_check', false);
        set(this, 'hide_id', false);
        set(this, 'dblclick', null);
        set(this, 'select_first', false);
        set(this, 'onLoad', null);
        
        set(this, 'default_', {});
        set(this.default_, 'col_width', 60, this.default_);
        set(this.default_, 'col_align', 'center', this.default_);
        set(this.default_, 'empty_value', '', this.default_);

        set(this, 'actions', null);
        if (typeof (this.actions) == 'function') {
            this.actions = this.actions();
        }
        
        set(this, '_edit_default', {
            name: 'edit',
            url: '/dashboard/edit/',
            require_id: 'true',
            type: 'edit'
        });
        
        set(this, '_delete_default', {
            name: 'delete',
            url: '/dashboard/delete/',
            require_id: 'true',
            type: 'delete'
        });

        set(this, 'exportable', true);

        var formats = [{
            id: 'csv',
            title: 'CSV',
            url: "{{tg.url('/dashboard/tocsv')}}"
        },
        {
            id: 'excel',
            title: 'Excel',
            url: "{{tg.url('/dashboard/toxls')}}"
        }];
        
        set(this, 'exportable_formats', formats);

        set(this, 'with_pager', true);
        set(this, 'pag_n', 1);
        set(this, 'rp', 10);
        set(this, 'this_page', 0);
        set(this, 'total_count', 0);
        set(this, 'total_pag', 0);
        this.ajx_data = '{}';
    }

    // getSelectedIds
    SapnsGrid.prototype.getSelectedIds = function() {
        var self = this;
        var selected_ids = [];
        $('#' + self.name + ' .sp-grid-row').each(function() {
            var rowid = $(this).find('.sp-grid-rowid');
            if (rowid.attr('checked') == true) {
                selected_ids.push(rowid.attr('id_row') * 1);
            }
        });

        return selected_ids;
    }

    SapnsGrid.prototype.getAction = function(action_name) {
        var self = this;
        for (var i=0, l=self.actions.length; i < l; i++) {
            var act = self.actions[i];
            if (typeof(act.type) == 'object') {
                if (act.type.id == action_name) {
                    return act;
                }
            }
            else if (act.name == action_name) {
                return act;
            }
        }
    }

    // getRow
    SapnsGrid.prototype.getRow = function(id) {
        var self = this;
        var row = null;
        $('#' + self.name + ' .sp-grid-row').each(function() {
            var rowid = $(this).find('.sp-grid-rowid');
            if (rowid.attr('id_row') == id) {
                row = rowid.parent();
                return;
            }
        });

        return row;
    }

    // loadData
    SapnsGrid.prototype.loadData = function() {

        var self = this;
        
        var cols = self.cols;
        if (typeof(cols) == 'function') {
            cols = cols();
        }
        
        var g_wd = 23; // min-width: 20px;
        if (self.hide_check) {
            g_wd = -6;
        }

        for (var i=0, l=cols.length; i<l; i++) {
            var col = cols[i];
            
            if (self.hide_id && col.title == 'id') {
                continue;
            }
            
            g_wd += (col.width + 5);
        }
        
        var g_table = '<div class="sp-grid" style="width: ' + (g_wd+5) + 'px;">';
        
        var grid_header = '<div class="sp-grid-row">';
        
        if (!self.hide_check) {
            grid_header += '<div class="sp-col-title" style="width: 23px;">' + 
                '<input class="sp-grid-select-all" type="checkbox"/></div>';
        }
        
        if (self.actions_inline) {
            grid_header += '<div class="sp-col-title" style="%(actions_wd)s">*</div>';
        }
        
        for (var i=0, l=cols.length; i<l; i++) {
            var col = cols[i];
            var wd = col.width;
            if (!wd) {
                wd = self.default_.col_width;
            }

            if (self.hide_id && col.title == 'id') {
                continue;
            }
            
            grid_header += '<div class="sp-col-title" style="width: ' + wd + 'px;">' + col.title + '</div>\n';
        }

        grid_header += '</div>';
        
        var data = self.data;
        if (typeof (data) == 'function') {
            data = data();
        }

        var ld = data.length;
        if (ld > 0) {
            for (var i=0; i<ld; i++) {
                
                var row = data[i];
                
                var grid_row = '<div class="sp-grid-row">\n';
                
                if (!self.hide_check) {
                    var border_radius = '';
                    if (i == ld-1) {
                        border_radius = 'border-radius: 0 0 0 5px;';
                    }
                    
                    grid_row += '<div class="sp-grid-cell" title="' + (i+1) + '" style="width: 23px;' + border_radius + '">' +
                        '<input class="sp-grid-rowid" type="checkbox" id_row="' + row[0] + '"></div>';
                }
                
                if (self.actions_inline) {
                    
                    var actions_wd = 'width: 100px;';
                    if (!self.nonstd) {
                        actions_wd = 'width: 75px;';
                    }
                    
                    var _action_style = 'style="padding: 2px; margin-left: 5px; margin-right: 5px; border: 1px solid lightgray;"';
                    var _actions = 
                        '<div class="sp-grid-cell" style="%(actions_wd)s">\n' +
                        '<img class="inline_action edit_inline" title="{{_("Edit")}}" ' + 
                            'src="{{tg.url("/images/sapns/icons/edit.png")}}">\n' + 
                        '<img class="inline_action delete_inline" title="{{_("Delete")}}" ' + 
                            'src="{{tg.url("/images/sapns/icons/delete.png")}}">\n' + 
                        '<img class="inline_action docs_inline" title="{{_("Docs")}}" ' + 
                            'src="{{tg.url("/images/sapns/icons/docs.png")}}">\n';
                    
                    grid_row += sprintf(_actions, {actions_wd: actions_wd}) + self.nonstd + '\n';
                    grid_row += '</div>\n';
                }
                
                // grid_header
                if (i == 0) {
                    g_table += sprintf(grid_header, {actions_wd: actions_wd});
                }
                
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
                    
                    if (self.hide_id && col.title == 'id') {
                        continue;
                    }
                    
                    var width = '';
                    if (wd > 0) {
                        width = ' width: ' + wd + 'px;';
                    }
                    
                    var border_radius = '';
                    if ((self.hide_check && i == ld-1) && 
                            (!self.hide_id && j == 0 || self.hide_id && j == 1)) {
                        border_radius = 'border-radius: 0 0 0 5px;';
                    }
                    
                    if (i == ld-1 && j == lr-1) {
                        border_radius = 'border-radius: 0 0 5px 0;';
                    }
                    
                    grid_row += '<div class="sp-grid-cell" style="text-align: ' + al + ';' + width + border_radius + '"';
                    
                    if (cell) {
                        grid_row += 'title="' + cell.replace(/"/gi, "''") + '"';
                    }
                    else {
                        grid_row += 'title="({{_("empty")}})"';
                    }
                    
                    grid_row += 'clickable="true">' + cell + '</div>\n';
                }
                
                grid_row += '</div>\n';
                
                g_table += grid_row;
            }
        }
        else {
            var n = 1;
            var wd_ = g_wd;
            if (self.actions_inline) {
                n = 3;
                wd_ += 25;
            }

            g_table += 
                sprintf(grid_header, {actions_wd: actions_wd}) +
                '<div class="sp-grid-row">'
                    + '<div class="sp-grid-cell sp-grid-noresults" title="{{_("No results")}}" ' 
                        + 'style="width: ' + wd_ + 'px;" >{{_("No results")}}</div>' +
                '</div>';            
        }
        
        g_table += '</div>';
        
        $('#' + self.name).find('.sp-grid-parent').html(g_table);
        if (self.select_first && self.with_search && self.q && ld < 5 && ld > 0) {
            $('#' + self.name + ' .sp-grid-rowid:first').attr('checked', true);
        }
    }

    // search
    SapnsGrid.prototype.search = function(q, force, on_load) {
        var self = this;

        if (force == undefined) {
            force = false;
        }

        if (q == undefined) {
            q = self.q;
        }

        if (self.q != q || force) {
            self.pag_n = 1;
        }

        self.q = q;

        var loading = '<div style="padding: 10px; font-size: 15px; ' + 
            sprintf('font-weight: bold; color: gray; height: %(hg)dpx;">{{_("Loading")}}...</div>', {hg: self.height-50});
        
        $('#' + self.name).find('.sp-grid-parent').html(loading);

        var ajx = $.extend(true, {
            url: "{{tg.url('/dashboard/grid/')}}",
            data: {
                cls: self.cls,
                q: self.q,
                rp: self.rp,
                pag_n: self.pag_n,
                ch_attr: self.ch_attr,
                parent_id: self.parent_id
            },
            success: function(response) {
                if (response.status) {
                    
                    // this page
                    if (response.this_page) {
                        self.this_page = response.this_page;
                    }
                            
                    // total_count
                    if (response.total_count) {
                        self.total_count = response.total_count;
                    }
                    
                    
                    // total_pag
                    if (response.total_pag) {
                        self.total_pag = response.total_pag;
                    }
                    
                    // cols
                    if (response.cols) {
                        self.cols = response.cols;
                    }
                    
                    // actions
                    if (response.actions) {
                        self.actions = response.actions;
                    }
                    
                    // update pager
                    var pos = (self.pag_n - 1) * self.rp * 1;
                            
                    var params = {
                            curr_page: self.pag_n * 1,
                            total_page: self.total_pag * 1,
                            pos0: pos + 1,
                            pos1: pos + self.this_page
                    };
                            
                    var pag_desc = sprintf("{{_('Page %(curr_page)d of %(total_page)d / Showing rows %(pos0)d to %(pos1)d')}}", params);
                    
                    $('#' + self.name + ' .sp-grid-first-page').attr('title', "{{_('page 1')}}");
                    
                    // page-back
                    if (params.curr_page > 1) {
                        var prev_page = sprintf("{{_('page %(p)d')}}", {p: params.curr_page - 1});
                        $('#' + self.name + ' .sp-grid-page-back').attr('title', prev_page).attr('disabled', false);
                    } 
                    else {
                        $('#' + self.name + ' .sp-grid-page-back').attr('disabled', true);
                    }
                    
                    // page-forth
                    if (params.curr_page < params.total_page) {
                        var next_page = sprintf("{{_('page %(p)d')}}", {p: params.curr_page + 1});
                        $('#' + self.name + ' .sp-grid-page-forth').attr('title', next_page).attr('disabled', false);
                    } 
                    else {
                        $('#' + self.name + ' .sp-grid-page-forth').attr('disabled', true);
                    }
                    
                    
                    // last-page
                    var last_page = sprintf("{{_('page %(p)d')}}", {p: params.total_page});
                            
                    $('#' + self.name + ' .sp-grid-last-page').attr('title', last_page);
                    
                    $('#' + self.name + ' .sp-grid-pager-desc').html(pag_desc);
                    $('#' + self.name + ' .sp-grid-current-page').val(self.pag_n);

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
                        // console.log(e);
                        // qtip2 is not loaded
                    }
                    
                    self.data = response.data;
                    self.loadData();
                    
                    // onLoad
                    if (on_load) {
                        on_load(response);
                    }
                    
                    if (self.onLoad) {
                        self.onLoad(response);
                    }
                }
            }
        }, self.search_params);

        var curr_ajx_data = JSON.stringify(ajx.data);
        if (self.ajx_data) {
            if (self.ajx_data === curr_ajx_data && !force) {
                self.loadData();
            } else {
                $.ajax(ajx);
            }
        }

        self.ajx_data = curr_ajx_data;
    }

    SapnsGrid.prototype.warningSelectedId = function() {
        var self = this;

        $('#grid-dialog_' + self.name).html("<p style='text-align: center; font-style: italic;'>{{_('You must select a row before click on this action')}}</p>")
            .dialog({
                title: self.caption,
                resizable: false,
                height: 155,
                width: 450,
                modal: true,
                draggable: false,
                buttons: {
                    "{{_('Close')}}": function() {
                        $('#grid-dialog_' + self.name).dialog('close');
                    }
                }
            });

        $('.ui-icon-closethick').hide();
    }

    SapnsGrid.prototype._loadActions = function(actions) {

        var self = this;
        var g_actions = '';
        
        self.nonstd = '';
        
        var button_ = '<button id="%(id)s" class="sp-grid-button-action">%(title)s</button>';
        var option_ = '<option value="%(id)s">%(title)s</option>';

        if (actions.length > 0) {
            
            g_actions = '';
            for (var i=0, l=actions.length; i < l; i++) {
                
                var act = actions[i];

                var req_id = act.require_id;
                if (req_id === undefined) {
                    req_id = true;
                }

                if (typeof(act.type) === 'string' && act.type === 'new') {
                    var new_btn = '<img class="inline_action new_inline" ' 
                        + 'title="{{_("New")}}" src="{{tg.url("/images/sapns/icons/new.png")}}">';
                    $('#search_box').append(new_btn);
                }
                else if (!self.actions_inline) {
                    $('#'+self.name + ' .sp-grid-button-actions').show();
                    
                    var button_data;
                    
                    if (typeof(act.type) == 'object') {
                        button_data = {id: act.type.id, title: act.title};
                    }
                    else {
                        button_data = {id: act.name, title: act.title}; 
                    }
                    
                    $('#'+self.name + ' .sp-grid-button-actions').append(sprintf(button_, button_data));
                }
                else if (self.actions_inline) {
                    if (typeof(act.type) === 'string' && (act.type == 'edit' || act.type == 'delete' || act.type == 'docs')) {
                        continue;
                    }
                    else {
                        var option_data;
                        
                        if (typeof(act.type) == 'object') {
                            option_data = {id: act.type.id, title: act.title};
                        } 
                        else {
                            option_data = {id: act.name, title: act.title}
                        }
                        
                        self.nonstd += sprintf(option_, option_data);
                    }
                }
            }
            
            if (self.nonstd) {
                self.nonstd = '<select class="nonstd_actions">\n<option value=""></option>\n' 
                    + self.nonstd 
                    + '</select>\n';
            }
        }

        // export
        if (self.exportable) {

            var formats = self.exportable_formats;

            if (typeof(self.exportable) == 'object') {
                formats = self.exportable.formats;
            }

            var l = formats.length;
            if (l > 0) {
                var options = '';
                for (var i=0; i < l; i++) {
                    options += '<option value="' + formats[i].id + '">'
                            + formats[i].title + '</option>';
                }

                var s_export = '<div id="grid-export_'
                    + self.name
                    + '" style="height: 25px; float: left;">'
                    + '<select id="select-export" class="sp-button sp-grid-action" style="height: 20px;">'
                    + '<option value="">({{_("Export")}})</option>'
                    + options + '</select></div>';
                
                $('#search_box').append(s_export);
            }
        }

        return g_actions;
    }
    
    SapnsGrid.prototype.complete_actions = function() {
        
        var self = this;
        
        for (var i=0, l=self.actions.length; i<l; i++) {
            var act = self.actions[i];
            if (typeof(act.type) === 'string') {
                if (act.type === 'edit') {
                    self.actions[i] = $.extend(act, self._edit_default);
                }
                else if (act.type === 'delete') {
                    self.actions[i] = $.extend(act, self._delete_default);
                }
            }
        }
    }

    SapnsGrid.prototype.loadActions = function() {

        var self = this;
        var g_actions = '';

        if (self.actions != null) {
            if (self.actions.length === undefined) {
                // it's an object
                var ajx = $.extend(true, {
                    url: "{{tg.url('/dashboard/grid_actions/')}}",
                    type: "post",
                    data: {
                        cls: self.cls
                    },
                    success: function(response) {
                        if (response.status) {
                            self.actions = response.actions;
                        }
                        
                        self.complete_actions();
                        
                        $('#' + self.name + ' .actions').html(self._loadActions(self.actions));
                    }
                }, self.actions);

                $.ajax(ajx);
            } else {
                self.complete_actions();
                $('#' + self.name + ' .actions').html(self._loadActions(self.actions));
            }
        }

        // if the row is selected, then mark the checkbox
        $('#' + self.name + ' .sp-grid-cell').live('click', function(event) {
            if ($(this).attr('clickable') == 'true') {
                $('#'+self.name + ' .sp-grid-select-all').attr('checked', false);
                var row_id = $(this).parent().find('.sp-grid-rowid');
                $('#'+self.name + ' .sp-grid-rowid').each(function() {
                    var ctrl = event.ctrlKey || event.metaKey;
                    if ($(this) != row_id && !self.multiselect && !ctrl) {
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

        /*
         * if (self.dblclick) { $('#'+self.name + '
         * .sp-grid-cell').live('dblclick', function(event) {
         * //console.log('dbl-click'); if ($(this).attr('clickable') == 'true') {
         * var row_id = $(this).parent().find('.sp-grid-rowid'); $('#'+self.name + '
         * .sp-grid-rowid').each(function() { if ($(this) != row_id &&
         * !self.multiselect && !event.ctrlKey) { $(this).attr('checked',
         * false); } });
         * 
         * if (row_id.attr('checked') == true) { row_id.attr('checked', false); }
         * else { row_id.attr('checked', true); }
         * 
         * if (typeof(self.dblclick) == 'function') {
         * self.dblclick(row_id.attr('id_row')*1); } else { $('#'+self.name +
         * '_' + self.dblclick).click(); } } }); }
         */

        function form(action, target) {
            var came_from = '';
            if (target != '_blank') {
                var came_from = self.url_base
                        + '?q='
                        + encodeURI(self.q).replace('-', '%2D', 'g').replace(
                                '"', '%22', 'g').replace('+', '%2B', 'g')
                                .replace('#', '%23', 'g') + '&rp=' + self.rp
                        + '&pag_n=' + self.pag_n + '&ch_attr=' + self.ch_attr
                        + '&parent_id=' + self.parent_id;
            }

            var f = '<form type="post" action="' + action + '" target="'
                    + target + '">\n'
                    + '<input type="hidden" name="came_from" value="'
                    + came_from + '"/>\n';

            if (self.ch_attr) {
                f += '<input type="hidden" name="_' + self.ch_attr
                        + '" value="' + self.parent_id + '"/>\n';
            }

            f += '</form>\n';

            return f;
        }
        
        function _run_action(id, ids, act, ctrl) {
            
            if (typeof(act.type) === 'string') {
                
                var a = act.url;
                if (a[a.length - 1] != '/') {
                    a += '/';
                }
                
                var target = '';
                if (ctrl) {
                    target = '_blank';
                }
                
                if (act.type == 'process') {
                    if (act.require_id) {
                        if (id) {
                            a += id;
                        }
                        else {
                            self.warningSelectedId();
                            return;
                        }
                    } else {
                        if (id) {
                            a += id;
                        }
                    }
                }
                else if (act.type == 'new') {
                    a += sprintf('%s/', self.cls);
                }
                else if (act.type == 'delete') {
                    self.std_delete(ids, act.url);
                    return;
                }
                else {
                    if (act.require_id) {
                        if (id) {
                            a += sprintf('%s/%s', self.cls, id);
                        }
                        else {
                            self.warningSelectedId();
                            return;
                        }
                    } else {
                        if (id) {
                            a += sprintf('%s/%s', self.cls, id);
                        } 
                        else {
                            a += sprintf('%s/', self.cls);
                        }
                    }
                }

                $(form(a, target)).appendTo('body').submit().remove();
            }
            else {
                // typeof(act.type) === 'object'
                var selected_ids = ids;
                if (act.require_id) {
                    if (selected_ids.length > 0) {
                        // TODO: _runaction
                        act.type.f(selected_ids[0], selected_ids);
                    } 
                    else {
                        self.warningSelectedId();
                        return;
                    }
                } else {
                    if (selected_ids.length > 0) {
                        act.type.f(selected_ids[0], selected_ids);
                    } 
                    else {
                        act.type.f();
                    }
                }
            }
        }

        function run_action(item, action_name, ctrl) {
            var act = self.getAction(action_name);
            var id = item.parent().parent().find('.sp-grid-rowid').attr('id_row');
            _run_action(id, [], act, ctrl);
        }

        // new
        $('#' + self.name + ' .new_inline').live('click', function(event) {
            run_action($(this), 'new', event.ctrlKey || event.metaKey);
        });

        if (self.actions_inline) {
            
            // edit
            $('#' + self.name + ' .edit_inline').live('click', function(event) {
                run_action($(this), 'edit', event.ctrlKey || event.metaKey);
            });
    
            // delete
            $('#' + self.name + ' .delete_inline').live('click', function(event) {
                var ids = self.getSelectedIds();
                if (ids.length == 0) {
                    var id = $(this).parent().parent().find('.sp-grid-rowid').attr('id_row');
                    ids = [id];
                }
                
                var act = self.getAction('delete');
                self.std_delete(ids, act.url);
            });
    
            // docs
            $('#' + self.name + ' .docs_inline').live('click', function(event) {
                run_action($(this), 'docs');
            });
    
            // non-standard actions
            $('#' + self.name + ' .nonstd_actions').live('change', function(event) {
                var action_id = $(this).val();
                if (action_id) {
                    run_action($(this), action_id);
                }
            });
        }
        // !actions_inline
        else {
            $('#'+self.name + ' .sp-grid-button-action').live('click', function(event) {
                var act = self.getAction($(this).attr('id'));
                var selected_ids = self.getSelectedIds();
                _run_action(selected_ids[0], selected_ids, act, event.ctrlKey || event.metaKey);
            });
        }

        // export button
        $('#grid-export_' + self.name).live('change', function() {
            var fmt = $('#grid-export_' + self.name + ' option:selected').val();
            
            if (fmt == '') {
                // nothing selected
                return;
            }
            
            var formats = self.exportable_formats;
            
            var extra_params = '';
            if (typeof (self.exportable) == 'object') {
                
                formats = self.exportable.formats;

                if (self.exportable.data) {
                    for (k in self.exportable.data) {
                        var v = self.exportable.data[k];
                        if (typeof(v) == 'function') {
                            v = v();
                        }
                        extra_params += '<input type="hidden" name="' + k + '" value="' + v + '">';
                    }
                }
            }

            var url = '';
            for (var i=0, l=formats.length; i < l; i++) {
                if (formats[i].id == fmt) {
                    url = formats[i].url;
                    break;
                }
            }

            var form_export = '<form action="' + url + '" method="get" >' 
                + '<input type="hidden" name="cls" value="' + self.cls + '">' 
                + '<input type="hidden" name="q" value="' + self.q + '">' 
                + '<input type="hidden" name="ch_attr" value="' + self.ch_attr + '">' 
                + '<input type="hidden" name="parent_id" value="' + self.parent_id + '">' 
                + extra_params 
                + '</form>';

            $(form_export).appendTo('body').submit().remove();

            // reset the select
            $(this).find('option:first').attr('selected', true);
        });
    }

    // std_delete
    SapnsGrid.prototype.std_delete = function(ids, url) {

        var self = this;
        var cls = self.cls;

        var id = JSON.stringify(ids);

        var delete_html = "<p id='delete-question'>{{_('Do you really want to delete this record?')}}</p>"
                + "<p id='object-title'></p>";

        var error_html = "<p id='delete-error-title'>{{_('Oops, something went wrong...')}}</p>"
                + "<div id='delete-error-message'></div>";

        $('#grid-dialog_' + self.name).html(delete_html);

        // get object's title
        var title = '';
        $.ajax({
            url: "{{tg.url('/dashboard/title')}}",
            type: "get",
            dataType: "json",
            data: {
                cls: cls,
                id: id
            },
            success: function(res) {
                if (res.status) {
                    var title;
                    if (typeof (res.title) == 'string') {
                        title = res.title;
                    } else {
                        title = res.title.join(' | ');
                    }

                    $('#grid-dialog_' + self.name + ' #object-title').html(title);
                }
            },
            error: function() {
                // alert('error!');
            }
        });

        $('#grid-dialog_' + self.name).dialog({
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
                            id_: id
                        },
                        success: function(res) {
                            if (res.status) {
                                self.search(self.q, true);
                                $('#grid-dialog_' + self.name).dialog('close');
                            } 
                            else {
                                $('#grid-dialog_' + self.name).dialog('close');

                                var message = "<p style='color: gray;'>" + res.message + "</p>";

                                if (res.rel_tables != undefined && res.rel_tables.length > 0) {
                                    message += "<div>{{_('For your information this object is related with other objects in the following classes:')}}</div>";
                                    message += "<ul>";

                                    for (var i = 0; i < res.rel_tables.length; i++) {
                                        var title = res.rel_tables[i].class_title;
                                        var attr_title = res.rel_tables[i].attr_title;
                                        message += '<li><span style="font-weight: bold;">'
                                                + title
                                                + '</span>'
                                                + ' (<span style="color: gray;">'
                                                + attr_title
                                                + '</span>)</li>';
                                    }

                                    message += "</ul>";
                                }

                                // load message
                                $('#grid-dialog_'+ self.name).html(error_html)
                                    .find('#delete-error-message')
                                    .html(message);

                                // show error dialog
                                $('#grid-dialog_'+ self.name).dialog({
                                    width: 700,
                                    height: 250,
                                    buttons: {
                                        "{{_('Close')}}": function() {
                                            $('#grid-dialog_'+ self.name).dialog('close');
                                        }
                                    }
                                });
                            }
                        },
                        error: function() {
                            $('#grid-dialog_'+ self.name).dialog('close');
                            $('#grid-dialog_'+ self.name).html(error_html).dialog({
                                buttons: {
                                    "{{_('Close')}}": function() {
                                        $('#grid-dialog_'+ self.name).dialog('close');
                                    }
                                }
                            });
                        }
                    });
                },
                "{{_('Cancel')}}": function() {
                    $('#grid-dialog_' + self.name).dialog('close');
                }
            }
        });
    }
    
    SapnsGrid.prototype.selectAll = function(chk) {
        var self = this;
        if (chk === undefined) {
            chk = true;
        }
        
        $('#'+self.name + ' .sp-grid-rowid').attr('checked', chk);
    }

    $.fn.sapnsGrid = function(arg1, arg2, arg3) {

        if (typeof(arg1) == "object") {
            
            var g = new SapnsGrid(arg1);
            this.data('sapnsGrid', g);

            this.append(sprintf('<div id="grid-dialog_%(name)s" style="display: none;"></div>', {name: g.name}));

            var g_content = '';
            g_content += sprintf('<div class="sp-grid-container" id="%(name)s" cls="%(cls)s">', {name: g.name, cls: g.cls});

            if (g.caption) {
                g_content += sprintf('<div class="sp-grid-caption">%(caption)s</div>', {caption: g.caption});
            }

            if (g.with_search) {

                g_content += '<div><div id="search_box" style="float: left;">' +
                        '<input class="sp-search-txt" style="float: left;" name="q" type="text" value="">' +
                        '<img class="inline_action sp-search-btn" ' + 
                            'src="{{tg.url("/images/sapns/icons/search.png")}}" title="{{_("Search...")}}" style="margin-left: 5px;"></div>';

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
                    g_content += '<div style="padding-left: 20px;">'
                            + "<button id='link-shortcut' class='sp-button' style='float: left;'>{{_('Create a shortcut')}}</button>"
                            + '<div style="font-size: 9px; margin-top: 7px; width: 100px; float: left;">'
                            + "<a id='this-search' href='"
                            + g.link
                            + "' target='_blank'>[{{_('this search')}}]</a>"
                            + '</div>'
                            + '<div id="link-shortcut-dialog" style="display: none;">'
                            + "<p>{{_('Do you want to create a shortcut for this search?')}}</p>"
                            + "<label>{{_('Shortcut title')}}:</label>"
                            + "<input id='link-shortcut-title' type='text' value='({{_('title')}})'>"
                            + '</div></div>';
                }
                g_content += '</div>';
            }
            
            var g_table = 
                '<div class="sp-grid-parent" style="overflow: auto; clear: left; ' + 
                    'height: ' + (g.height+5) + 'px; background-color: transparent;"></div>';
            
            // pager
            var g_pager = '';
            if (g.with_pager) {
                g_pager += '<div class="sp-grid-pager">'
                        + '<div class="sp-grid-pager-desc"></div>';

                var sel_10 = '', sel_50 = '', sel_100 = '', sel_all = '';
                var sel = ' selected';
                var another_value = '';
                if (g.rp == 10) {
                    sel_10 = sel;
                } else if (g.rp == 50) {
                    sel_50 = sel;
                } else if (g.rp == 100) {
                    sel_100 = sel;
                } else if (g.rp == 0) {
                    sel_all = sel;
                } else {
                    another_value = '<option value="' + g.rp + '" selected>' + g.rp + '</option>';
                }

                g_pager += '<div style="float: left; clear: right; height: 25px; margin-top: 2px;"><select class="sp-button sp-grid-rp">'
                        + another_value
                        + '<option value="10"'
                        + sel_10
                        + '>10</option>'
                        + '<option value="50"'
                        + sel_50
                        + '>50</option>'
                        + '<option value="100"'
                        + sel_100
                        + '>100</option>'
                        + '<option value="0"'
                        + sel_all
                        + '>{{_("All")}}</option>'
                        + '</select>'
                        + '<button class="sp-button sp-grid-first-page" style="float: left;">|&lt;&lt;</button>'
                        + '<button class="sp-button sp-grid-page-back" style="float: left;">&lt;&lt;</button>'
                        + '<input class="sp-grid-current-page" type="text" style="text-align: center; font-size: 11px; margin-top: 3px;" readonly>'
                        + '<button class="sp-button sp-grid-page-forth" style="float: left;">&gt;&gt</button>'
                        + '<button class="sp-button sp-grid-last-page" style="float: left;">&gt;&gt|</button></div>';

                g_pager += '</div>';
                
                $('#' + g.name + ' .sp-grid-select-all').live('click', function() {
                    var chk = $(this).attr('checked');
                    g.selectAll(chk);
                });

                $('#' + g.name + ' .sp-grid-rp').live('change', function() {
                    g.rp = $(this).val();
                    g.pag_n = 1;
                    g.search(g.q);
                });

                $('#' + g.name + ' .sp-grid-first-page').live('click', function() {
                    g.pag_n = 1;
                    g.search(g.q);
                });

                $('#' + g.name + ' .sp-grid-page-back').live('click', function() {
                    if (g.pag_n > 1) {
                        g.pag_n -= 1;
                        g.search(g.q);
                    }
                });

                $('#' + g.name + ' .sp-grid-page-forth').live('click', function() {
                    if (g.pag_n < g.total_pag) {
                        g.pag_n *= 1
                        g.pag_n += 1;
                        g.search(g.q);
                    }
                });

                $('#' + g.name + ' .sp-grid-last-page').live('click', function() {
                    g.pag_n = g.total_pag;
                    g.search(g.q);
                });
            }
            
            var g_actions = '<div class="sp-grid-button-actions" style="display: none;"></div>';

            this.append(g_content + g_actions + g_table + g_pager + '</div>');

            g.loadActions();

            $('#' + g.name + ' .sp-search-txt').val(g.q);
            g.search(g.q)
        } 
        else if (typeof(arg1) == "string") {

            var self = this.data('sapnsGrid');

            // loadData
            if (arg1 == "loadData") {
                self.loadData();
            }
            // search
            // sapnsGrid('search', <string>/<bool>, [<function>])
            // sapnsGrid('search', 'john doe')
            // sapnsGrid('search', true)
            // a function is executed after data is loaded (before "general" onLoad)
            // sapnsGrid('search', true, function() {})
            // sapnsGrid('search', 'john doe', function() {})
            else if (arg1 == "search") {
                var q = '';

                if (typeof(arg2) == 'boolean') {
                    q = self.q;
                } else if (arg2) {
                    q = arg2;
                }

                if (self.with_search) {
                    $('#' + self.name + ' .sp-search-txt').val(q);
                }
                
                self.search(q, true, arg3);
            }
            // getSelectedIds
            else if (arg1 == "getSelectedIds") {
                return self.getSelectedIds();
            }
            // setRp
            else if (arg1 == "setRp") {
                self.rp = arg2;
                $('#'+self.name + ' .sp-grid-rp [value='+arg2+']').attr('selected', true);
            }
            // selectAll
            else if (arg1 == "selectAll") {
                self.selectAll();
            }
            // TODO: other sapnsGrid methods
        }

        return this;
    };
})(jQuery);