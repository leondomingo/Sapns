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
        set(this, 'search_params', {});
        set(this, 'show_ids', false);
        set(this, 'link', '');
        set(this, 'q', '');
        set(this, 'ch_attr', '');
        set(this, 'parent_id', '');
        set(this, 'cols', []);
        set(this, 'data', {});
        set(this, 'height', 500); //470);
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
        if (typeof(this.actions) == 'function') {
            this.actions = this.actions();
        }
        
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
                selected_ids.push(rowid.attr('id_row')*1);
            }
        });
        
        return selected_ids;
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
        
        var l = cols.length,
            g_wd = 23;
        for (var i=0; i<l; i++) {
            var col = cols[i];
            g_wd += col.width;
        }
        
        g_wd += l*5;
        
        var g_table = '<div class="sp-grid" style="width: ' + (g_wd+15) + 'px;">';
        
        if (!self.hide_check) {
            g_table += '<div class="sp-grid-row"><div class="sp-col-title" style="width: 23px;">' + 
                '<input class="sp-grid-select-all" type="checkbox"/></div>';
        }
        
        if (self.actions_inline) {
            g_table += '<div class="sp-col-title">*</div>';
        }
        
        for (var i=0, l=cols.length; i<l; i++) {
            var col = cols[i],
                wd = col.width;
            if (!wd) {
                wd = self.default_.col_width;
            }
            
            if (self.hide_id && col.title == 'id') {
                continue;
            }
            
            g_table += '<div class="sp-col-title" style="width: ' + wd + 'px;">' + col.title + '</div>';
        }

        g_table += '</div>';
        
        var data = self.data;
        if (typeof(data) == 'function') {
            data = data();
        }
        
        var ld = data.length;
        if (ld > 0) {
            for (var i=0; i<ld; i++) {
                
                var row = data[i];
                
                g_table += '<div class="sp-grid-row">';
                
                if (!self.hide_check) {
                    var border_radius = '';
                    if (i == ld-1) {
                        border_radius = 'border-radius: 0 0 0 5px;';
                    }
                    
                    g_table += '<div class="sp-grid-cell" title="' + (i+1) + '" style="width: 23px;' + border_radius + '">' + 
                        '<input class="sp-grid-rowid" type="checkbox" id_row="' + row[0] + '"></div>';
                }
                
                if (self.actions_inline) {
                    var _action_style = 'style="padding: 2px; margin-left: 5px; margin-right: 5px; border: 1px solid lightgray;"';
                    g_table +=
                        '<div class="sp-grid-cell" style="font-size: 10px; width: 35px;">' +
                            '<a class="edit_inline" href="#" title="edit" ' + _action_style + '>E</a>' + 
                            '<a class="delete_inline" href="#" title="delete" ' + _action_style + '>D</a>' + 
                            '<a class="docs_inline" href="#" title="docs" ' + _action_style + '>D</a>' +
                        '</div>';
                }
                
                for (var j=0, lr=cols.length; j<lr; j++) {
                    var col = cols[j],
                        al = col.align;
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
                    
                    g_table += '<div class="sp-grid-cell" style="text-align: ' + al + ';' + width + border_radius + '"';
                    
                    if (cell) {
                        g_table += 'title="' + cell.replace(/"/gi, "''") + '"';
                    }
                    else {
                        g_table += 'title="({{_("empty")}})"';
                    }
                    
                    g_table += 'clickable="true">' + cell + '</div>';
                }
                
                g_table += '</div>';
            }
        }
        else {
            var n = 1;
            if (self.actions_inline) {
                n = 3;
            }
            g_table += 
                '<div class="sp-grid-row">'
                    + '<div class="sp-grid-cell sp-grid-noresults" title="{{_("No results")}}" ' 
                        + 'style="width: ' + g_wd + 'px;" >{{_("No results")}}</div>' +
                '</div>';
        }
        
        g_table += '</div>';
        
        $('#' + self.name).find('.sp-grid-parent').html(g_table);
        if (self.select_first && self.with_search && self.q && ld < 5 && ld > 0) {
            $('#'+self.name + ' .sp-grid-rowid:first').attr('checked', true);
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
            'font-weight: bold; color: gray;">{{_("Loading")}}...</div>';
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
                    var pos = (self.pag_n-1) * self.rp*1;

                    var params = {
                            curr_page: self.pag_n*1,
                            total_page: self.total_pag*1,
                            pos0: pos+1,
                            pos1: pos+self.this_page
                    };
                    
                    var pag_desc = sprintf("{{_('Page %(curr_page)d of %(total_page)d / Showing rows %(pos0)d to %(pos1)d')}}", params);
                    
                    $('#' + self.name + ' .sp-grid-first-page').attr('title', "{{_('page 1')}}");
                    
                    // page-back
                    if (params.curr_page > 1) {
                        var prev_page = sprintf("{{_('page %(p)d')}}", {p: params.curr_page-1});
                        $('#' + self.name + ' .sp-grid-page-back').
                            attr('title', prev_page).
                            attr('disabled', false);
                    }
                    else {
                        $('#' + self.name + ' .sp-grid-page-back').attr('disabled', true);
                    }
                    
                    // page-forth
                    if (params.curr_page < params.total_page) {
                        var next_page = sprintf("{{_('page %(p)d')}}", {p: params.curr_page+1}); 
                        $('#' + self.name + ' .sp-grid-page-forth').
                            attr('title', next_page).
                            attr('disabled', false);
                    }
                    else {
                        $('#' + self.name + ' .sp-grid-page-forth').attr('disabled', true);
                    }
                    
                    // last-page
                    var last_page = sprintf("{{_('page %(p)d')}}", {p: params.total_page});
                    $('#' + self.name + ' .sp-grid-last-page').attr('title', last_page);
                    
                    $('#' + self.name + ' .sp-grid-pager-desc').html(pag_desc);
                    $('#' + self.name + ' .sp-grid-current-page').val(self.pag_n);
                    
                    self.data = response.data;
                    self.loadData();
                    
                    // qtip2
                    try {
                        $('.sp-grid-cell').qtip({
                            content: {
                                text: true
                            },
                            position: {
                                my: "top left",
                                at: "bottom center"
                            },
                            style: "ui-tooltip-rounded"
                        });
                    } catch (e) {
                        //console.log(e);
                        //qtip2 is not loaded
                    }                    
                    
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
            }
            else {
                $.ajax(ajx);
            }
        }
        
        self.ajx_data = curr_ajx_data;
    }
    
    SapnsGrid.prototype.warningSelectedId = function() {
        var self = this;
        
        $('#grid-dialog_' + self.name).
        html("<p style='text-align: center; font-style: italic;'>{{_('You must select a row before click on this action')}}</p>"). 
        dialog({
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
        
        if (actions.length > 0) {
            //g_actions += '<div class="sp-grid-actions-title">{{_("Actions")}}:</div>';
            g_actions = '';
            for (var i=0, l=actions.length; i<l; i++) {
                
                var act = actions[i];
                
                var req_id = act.require_id;
                if (req_id === undefined) {
                    req_id = true;
                }
                
                if (typeof(act.type) === 'string') {
                    var a = '<div style="float: left;">';
                    a += '<button class="sp-button sp-grid-action standard_action" ' +
                        ' id="' + self.name + '_' + act.name + '"' +
                        ' title="' + act.url + '" url="' + act.url + '" action-type="' + act.type + '"' +
                        ' require_id="' + req_id + '" >' + act.title + '</button></div>';
                    
                    if (act.type === 'new') {
                        $('#search_box').append(a);
                    }
                    else {
                        g_actions += a;
                    }
                }
                else {
                    g_actions += 
                        '<div style="float: left;">' +
                            '<button id="' + act.type.id + '" class="sp-button sp-grid-action" ' +
                                ' require_id="' + req_id + '" >' + act.title + '</button>' +
                        '</div>';
                }
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
                for (var i=0; i<l; i++) {
                    options += '<option value="' + formats[i].id + '">' + formats[i].title + '</option>';
                }
                
                g_actions += 
                    '<div id="grid-export_' + self.name + '" style="position: absolute; background-color: none; height: 25px; right: 0px;">' +
                    '<select id="select-export" class="sp-button sp-grid-action" style="height: 20px;">' +
                        '<option value="">({{_("Export")}})</option>' +
                        options +
                    '</select></div>';
            }
        }

        return g_actions;
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
                        
                        $('#' + self.name + ' .actions').html(self._loadActions(self.actions));
                        
                    }
                }, 
                self.actions);
                
                $.ajax(ajx);
            }
            else {
                $('#' + self.name + ' .actions').html(self._loadActions(self.actions));
                
                if (self.actions.length == 0 && !self.exportable) {
                    $('#' + self.name + ' .actions').css('min-height', '0px');
                }
                
                // assign functions to actions
                for (var i=0, l=self.actions.length; i<l; i++) {
                    
                    var act = self.actions[i];
                    
                    if (typeof(act.type) == 'object') {
                        $('#' + act.type.id).data('_func', act.type.f);
                        
                        $('#' + act.type.id).live('click', function() {
                            if ($(this).attr('require_id') == 'true') {
                                var selected_ids = self.getSelectedIds();
                                if (selected_ids.length > 0) {
                                    $(this).data('_func')(selected_ids[0], selected_ids);
                                }
                                else {
                                    self.warningSelectedId();
                                }
                            }
                            else {
                                var selected_ids = self.getSelectedIds();
                                if (selected_ids.length > 0) {
                                    $(this).data('_func')(selected_ids[0], selected_ids);
                                }
                                else {
                                    $(this).data('_func')();
                                }
                            }
                        });
                    }
                }
            }
        }
        
        // if the row is selected, then mark the checkbox
        $('#'+self.name + ' .sp-grid-cell').live('click', function(event) {
            //console.log('click');
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
        if (self.dblclick) {
            $('#'+self.name + ' .sp-grid-cell').live('dblclick', function(event) {
                //console.log('dbl-click');
                if ($(this).attr('clickable') == 'true') {
                    var row_id = $(this).parent().find('.sp-grid-rowid');
                    $('#'+self.name + ' .sp-grid-rowid').each(function() {
                        if ($(this) != row_id && !self.multiselect && !event.ctrlKey) {
                            $(this).attr('checked', false);
                        }
                    });
                    
                    if (row_id.attr('checked') == true) {
                        row_id.attr('checked', false);
                    }
                    else {
                        row_id.attr('checked', true);
                    }
                    
                    if (typeof(self.dblclick) == 'function') {
                        self.dblclick(row_id.attr('id_row')*1);
                    }
                    else {
                        $('#'+self.name + '_' + self.dblclick).click();
                    }
                }
            });
        }
        */
        
        // standard actions
        $('#'+self.name + ' .standard_action').live('click', function(event) {
            
            function form(action, target) {
                var came_from = '';
                if (target != '_blank') {
                    var came_from = self.url_base + '?q=' + encodeURI(self.q).
                    replace('-', '%2D', 'g').replace('"', '%22', 'g').
                    replace('+', '%2B', 'g').replace('#', '%23', 'g') + 
                        '&rp=' + self.rp + '&pag_n=' + self.pag_n +
                        '&ch_attr=' + self.ch_attr + '&parent_id=' + self.parent_id;
                }
                
                var f = 
                    '<form type="post" action="' + action + '" target="' + target + '">' +
                        '<input type="hidden" name="came_from" value="' + came_from + '">';
                
                if (self.ch_attr) {
                    f += '<input type="hidden" name="_' + self.ch_attr + '" value="' + self.parent_id + '">';
                }
                    
                f += '</form>';
                
                return f;
            }
            
            // child attribute 
            var ch_attr = self.ch_attr;
            
            // if CTRL or CMD (Mac) is pressed open in a new tab 
            var target = '';
            if (event.ctrlKey || event.metaKey) {
                target = '_blank';
            }
            
            var url = $(this).attr('url');
            var action_type = $(this).attr('action-type')
            var _func = $(this).attr('_func');
            //console.log(action_type + ': ' + url + ' ' + _func);
            if (!_func) {
                
                var a = $(this).attr('url');
                if (a[a.length-1] != '/') {
                    a += '/';
                }
                
                var selected_ids = self.getSelectedIds();
                
                // with selection
                if ($(this).attr('require_id') == 'true') {
                                        
                    if (selected_ids.length > 0) {
                        // delete (std)
                        if (action_type == 'delete') {
                            self.std_delete(selected_ids, url);
                        }
                        // non-standard actions
                        else if (action_type == 'process') {
                            if (selected_ids.length == 1) {
                                a += selected_ids[0];
                                $(form(a, target)).appendTo('body').submit().remove();
                            }
                            else {
                                // multiselect
                                var a0 = a;
                                for(var i=0, l=selected_ids.length; i<l; i++) {
                                    $(form(a0 + selected_ids[i], '_blank')).appendTo('body').submit().remove();
                                }
                            }
                        }
                        // standard actions
                        else {
                            // edit, docs, ...
                            if (selected_ids.length == 1) {
                                a += sprintf('%s/%s', self.cls, selected_ids[0]+'');
                                $(form(a, target)).appendTo('body').submit().remove();
                            }
                            else {
                                // multiselect
                                a += sprintf('%s/', self.cls);
                                var a0 = a;
                                for(var i=0, l=selected_ids.length; i<l; i++) {
                                    $(form(a0 + selected_ids[i], '_blank')).appendTo('body').submit().remove();
                                } 
                            }
                        }
                    }
                    else {
                        self.warningSelectedId();
                    }
                }
                // selection is not required
                else {
                    // new (standard)
                    if (action_type == 'new') {
                        a += sprintf('%s/', self.cls);
                        $(form(a, target)).appendTo('body').submit().remove();
                    }
                    // non-standard actions
                    else if (action_type == 'process') {
                        if (selected_ids.length == 1) {
                            a += sprintf('%s/', selected_ids[0]+'');
                            $(form(a, target)).appendTo('body').submit().remove();
                        }
                        else if (selected_ids.length > 1) {
                            // multiselect
                            var a0 = a;
                            for(var i=0, l=selected_ids.length; i<l; i++) {
                                $(form(a0 + selected_ids[i], '_blank')).appendTo('body').submit().remove();
                            }
                        }
                        else {
                            // no selection at all
                            $(form(a, target)).appendTo('body').submit().remove();
                        }
                    }
                }
            }
            else {
                _func();
            }
        });
        
        // export button 
        $('#grid-export_' + self.name).live('change', function() {
            var fmt = $('#grid-export_' + self.name + ' option:selected').val();
            
            if (fmt == '') {
                // nothing selected 
                return;
            }
            
            var formats = self.exportable_formats;             
            
            var extra_params = '';
            if (typeof(self.exportable) == 'object') {
                
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
            for (var i=0, l=formats.length; i<l; i++) {
                if (formats[i].id == fmt) {
                    url = formats[i].url;
                    break;
                }
            }
            
            var form_export =
                '<form action="' + url + '" method="get" >' +
                    '<input type="hidden" name="cls" value="' + self.cls + '">' +
                    '<input type="hidden" name="q" value="' + self.q + '">' +
                    '<input type="hidden" name="ch_attr" value="' + self.ch_attr + '">' +
                    '<input type="hidden" name="parent_id" value="' + self.parent_id + '">' +
                    extra_params +
                '</form>';
            
            $(form_export).appendTo('body').submit().remove();
            
            // reset the select 
            $(this).find('option:first').attr('selected', true);
        });        
    }
    
    // std_new
    /*
    SapnsGrid.prototype.std_new = function() {
        //console.log('std_new');
        var self = this;
        return;
    }
    */
    
    // std_edit
    /*
    SapnsGrid.prototype.std_edit = function(id) {
        //console.log('std_edit');
        var self = this;
        
        console.log(id);
        
        return;
    }
    */
    
    // std_delete
    SapnsGrid.prototype.std_delete = function(ids, url) {
        
        var self = this;
        var cls = self.cls;
        
        var id = JSON.stringify(ids);
        
        var delete_html = 
            "<p id='delete-question'>{{_('Do you really want to delete this record?')}}</p>" +
            "<p id='object-title'></p>";
            
        var error_html =
            "<p id='delete-error-title'>{{_('Oops, something went wrong...')}}</p>" +
            "<div id='delete-error-message'></div>";
        
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
                    if (typeof(res.title) == 'string') {
                        title = res.title;
                    }
                    else {
                        title = res.title.join(' | ');
                    }
                    
                    $('#grid-dialog_' + self.name + ' #object-title').html(title);
                }
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
                                    
                                    for (var i=0; i<res.rel_tables.length; i++) {
                                        var title = res.rel_tables[i].class_title;
                                        var attr_title = res.rel_tables[i].attr_title;
                                        message += '<li><span style="font-weight: bold;">' + title + '</span>' + 
                                          ' (<span style="color: gray;">' + attr_title + '</span>)</li>';
                                    }
                                    
                                    message += "</ul>";
                                }
                                
                                // load message 
                                $('#grid-dialog_' + self.name).html(error_html).find('#delete-error-message').html(message);
                                
                                // show error dialog 
                                $('#grid-dialog_' + self.name).dialog({
                                    width: 700,
                                    height: 250,
                                    buttons: {"{{_('Close')}}": function() {
                                        $('#grid-dialog_' + self.name).dialog('close');
                                    }}
                                });
                            }
                        },
                        error: function() {
                            $('#grid-dialog_' + self.name).dialog('close');
                            $('#grid-dialog_' + self.name).html(error_html).dialog({
                                buttons: {
                                    "{{_('Close')}}": function() {
                                        $('#grid-dialog_' + self.name).dialog('close');
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

    $.fn.sapnsGrid = function(arg1, arg2, arg3) {
        
        if (typeof(arg1) == "object") {
            
            var g = new SapnsGrid(arg1);
            this.data('sapnsGrid', g);
            
            this.append('<div id="grid-dialog_' + g.name + '" style="display: none;"></div>');
            
            var g_content = '';            
            g_content += '<div class="sp-grid-container" id="' + g.name + '" cls="' + g.cls + '">';
            
            if (g.caption) {
                g_content += '<div class="sp-grid-caption">' + g.caption + '</div>';
            }
            
            if (g.with_search) {
                
                g_content += 
                    '<div><div id="search_box" style="float: left;">' +
                        '<input class="sp-search-txt" style="float: left;" name="q" type="text" value="">' +
                        '<button class="sp-button sp-search-btn" style="float: left;">{{_("Search...")}}</button></div>';                     
                        
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
            
            var g_table = 
                '<div class="sp-grid-parent" style="overflow: auto; clear: left; ' + 
                    'height: ' + (g.height+5) + 'px; background-color: transparent;"></div>';
            
            // pager
            var g_pager = '';
            if (g.with_pager) {
                g_pager += '<div class="sp-grid-pager">';
                g_pager += '<div class="sp-grid-pager-desc"></div>';
                
                var sel_10 = '', sel_50 = '', sel_100 = '', sel_all = '';
                var sel = ' selected';
                var another_value = '';
                if (g.rp == 10) {
                    sel_10 = sel;
                }
                else if (g.rp == 50) {
                    sel_50 = sel;
                }
                else if (g.rp == 100) {
                    sel_100 = sel;
                }
                else if (g.rp == 0) {
                    sel_all = sel;
                }
                else {
                    another_value = '<option value="' + g.rp + '" selected>' + g.rp + '</option>';
                }
                
                g_pager += 
                    '<select class="sp-button sp-grid-rp">' +
                    another_value +
                    '<option value="10"' + sel_10 + '>10</option>' +
                    '<option value="50"' + sel_50 + '>50</option>' +
                    '<option value="100"' + sel_100 + '>100</option>' +
                    '<option value="0"' + sel_all + '>{{_("All")}}</option>' +
                    '</select>' +
                    '<button class="sp-button sp-grid-first-page" style="float: left;">|&lt;&lt;</button>' +
                    '<button class="sp-button sp-grid-page-back" style="float: left;">&lt;&lt;</button>' +
                    '<div>' +
                    '<input class="sp-grid-current-page" type="text" style="text-align: center;" readonly>' +
                    '</div>' +
                    '<button class="sp-button sp-grid-page-forth" style="float: left;">&gt;&gt</button>' +
                    '<button class="sp-button sp-grid-last-page" style="float: left;">&gt;&gt|</button>';
                
                g_pager += '</div>';
                
                $('#' + g.name + ' .sp-grid-select-all').live('click', function() {
                    var chk = $(this).attr('checked');
                    $('#' + g.name + ' .sp-grid-rowid').attr('checked', chk);
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
            
            this.append(g_content+'<div class="actions" style="clear: left; position: relative; min-height: 20px;"></div>'+g_table+g_pager+'</div>');
            
            g.loadActions();
            $('#'+g.name + ' .sp-search-txt').val(g.q);
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
                }
                else if (arg2) {
                    q = arg2;
                }
                
                if (self.with_search) {
                    $('#'+self.name + ' .sp-search-txt').val(q);
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
            // TODO: other sapnsGrid methods
        }
        
        return this;
    };
}) (jQuery);