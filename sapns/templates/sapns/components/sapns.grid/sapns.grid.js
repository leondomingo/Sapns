/* Sapns grid */

var __DEFAULT_FILTER = 'default';
(function($) {
    
    function Filter(params) {
        this.field = $.trim(params.field);
        this.operator = params.operator;
        this.value = $.trim(params.value);
        this.active = params.active !== undefined ? !!params.active : true;
    }
    
    function normalize(s) {
        s = $.trim(s.toLowerCase());
        s = s.replace(/[áäà]/g, 'a');
        s = s.replace(/[éëè]/g, 'e');
        s = s.replace(/[íïì]/g, 'i');
        s = s.replace(/[óöò]/g, 'o');
        s = s.replace(/[úüù]/g, 'u');
        s = s.replace(/[^a-z]/g, '');
            
        return s;
    }
    
    Filter.prototype = {
            tip: function() {
                var self = this;
                return sprintf('&lt;%s&gt; %s "%s"', self.field, self.operator_title().toLowerCase(), self.value);
            },
            operator_title: function() {
                var titles = {
                        co: "{{_('Contains')}}",
                        eq: "{{_('Equals to')}}",
                        lt: "{{_('Less than')}}",
                        gt: "{{_('Greater than')}}",
                        let: "{{_('Less than or equals to')}}",
                        get: "{{_('Greater than or equals to')}}",
                        nco: "{{_('Does not contain')}}",
                        neq: "{{_('Not equals to')}}"
                };
                
                return titles[this.operator];
            },
            toggle: function() {
                if (this.active) {
                    this.active = false;
                }
                else {
                    this.active = true;
                }
            },
            
            toString: function() {
                var self = this;
                
                var fld = normalize(self.field);
                
                var _operators = {
                        // co (contain)
                        co: '=',
                        // eq (equal to)
                        eq: '=',
                        // lt (less than)
                        lt: '<',
                        // gt (greater than)
                        gt: '>',
                        // let (less or equal)
                        let: '<=',
                        // get (greater or equal)
                        get: '>=',
                        // nco (not contain)
                        nco: '<>',
                        // neq (not equal)
                        neq: '<>'
                };
                
                var op = _operators[self.operator];
                var v = self.value;
                
                if (self.operator == 'eq' || self.operator == 'neq') {
                    
                    if (v) {
                        v = sprintf('"%s"', v);
                    }
                    else {
                        if (self.operator == 'eq') {
                            return sprintf('!%s', fld);
                        }
                        else if (self.operator == 'neq') {
                            return sprintf('#%s', fld);
                        }
                    }
                }
                else if ((self.operator == 'co' || self.operator == 'nco') && !v) {
                    if (self.operator == 'co') {
                        return sprintf('!%s', fld);
                    }
                    else if (self.operator == 'nco') {
                        return sprintf('#%s', fld);
                    }
                }
                
                return sprintf('%s%s%s', fld, op, v);
            },
            stringify: function() {
                return sprintf('%s"%s" %s "%s"', !this.active ? '_' : '', this.field, this.operator, this.value);
            }
    };
    
    function parseFilters(s) {
        var terms = s.split(',');
        var filters = [];
        for (var i=0, l=terms.length; i<l; i++) {
            var m = $.trim(terms[i]).match('^(_)?"([^"]+)"\\s([a-z]{2,3})\\s"([^"]*)"$');
            if (m) {
                filters.push(new Filter({
                    field: m[2],
                    operator: m[3],
                    value: m[4],
                    active: !m[1]
                }));
            }
        }
        
        return filters;
    };

    function OrderFilter(params) {
        this.field = params.field;
        
        if (params.type == '+') {
            this.type = 'asc';
        }
        else if (params.type == '-') {
            this.type = 'desc';
        }
        else {
            this.type = params.type;
        }
    }
    
    OrderFilter.prototype = {
            toString: function() {
                var self = this;
                var type;
                if (self.type == 'asc') {
                    type = '+';
                }
                else if (self.type == 'desc') {
                    type = '-'; 
                }
                
                var fld = normalize(self.field);
                
                return sprintf('%s%s', type, fld);
            },
            stringify: function() {
                var self = this;
                
                var type;
                if (self.type == 'asc') {
                    type = '+';
                }
                else if (self.type == 'desc') {
                    type = '-'; 
                }
                
                return sprintf('%s"%s"', type, self.field);
            }
    }
    
    function parseOrder(s) {
        var terms = s.split(',');
        var order = [];
        for (var i=0, l=terms.length; i<l; i++) {
            // (+|-)...........
            var m = $.trim(terms[i]).match('^(\\+|\\-)"([^"]+)"$');
            if (m) {
                order.push(new OrderFilter({
                    field: m[2],
                    type: m[1]
                }));
            }
        }
        
        return order
    }
    
    // SapnsGrid (constructor)
    function SapnsGrid(settings) {
        
        var self = this;

        if (typeof(settings.caption) === 'function') {
            settings.caption = settings.caption();
        }
        
        if (typeof (settings.actions) === 'function') {
            settings.actions = settings.actions();
        }

        var exportable_formats = [{
            id: 'csv',
            title: 'CSV',
            url: "{{tg.url('/dashboard/tocsv/')}}"
        },
        {
            id: 'excel',
            title: 'Excel',
            url: "{{tg.url('/dashboard/toxls/')}}"
        }];
        
        // default "pager_options"
        var pager_options = settings.pager_options;
        if (!pager_options) {
            pager_options = [{
                val: 10,
                desc: '10',
                sel: false
            },
            {
                val: 50,
                desc: '50',
                sel: false
            },
            {
                val: 100,
                desc: '100',
                sel: false
            },
            {
                val: 0,
                desc: "{{_('All')}}",
                sel: false
            }];
        }
        
        if ($.inArray(settings.rp*1, [10, 50, 100, 0]) === -1) {
            pager_options.push({ val: settings.rp*1, desc: settings.rp, sel: true });
        }
        else {
            pager_options[0].sel = true;
        }
        
        pager_options.sort(function(x, y) {
            return x.val - y.val;
        });
        
        var _settings = $.extend(true, {
            caption: '',
            name: 'sapns_grid_' + Math.floor(Math.random() * 999999),
            cls: '',
            with_search: true,
            with_filters: true,
            search_params: {},
            show_ids: false,
            link: '',
            q: '',
            user_filters: [],
            ch_attr: '',
            parent_id: '',
            cols: [],
            data: {},
            height: 500,
            url_base: '',
            multiselect: false,
            allow_multiselect: true,
            actions: null,
            actions_inline: false,
            hide_check: false,
            hide_id: true,
            dblclick: null,
            select_first: false,
            shift_enabled: false,
            exportable: true,
            exportable_formats: exportable_formats,
            with_pager: true,
            pag_n: 1,
            rp: 10,
            onLoad: null,
            resize: {
                min_width: 90,
                after: null
            },
            default_: {
                col_width: 60,
                col_align: 'center',
                empty_value: ''
            }
        }, settings);
        
        $.extend(true, self, _settings);

        self.pager_options = pager_options;
        self.this_page = 0;
        self.total_count = 0;
        self.total_pag = 0;
        self.ajx_data = JSON.stringify({});
        self.styles = [];
        
        self.setQuery(self.q);
        
        self._new_default = {
            name: 'new',
            url: '{{tg.url("/dashboard/new/")}}',
            require_id: 'false',
            type: 'new'
        };
        
        self._edit_default = {
            name: 'edit',
            url: '{{tg.url("/dashboard/edit/")}}',
            require_id: 'true',
            type: 'edit'
        };
        
        self._delete_default = {
            name: 'delete',
            url: '{{tg.url("/dashboard/delete/")}}',
            require_id: 'true',
            type: 'delete'
        };
        
        self._docs_default = {
            name: 'docs',
            url: '{{tg.url("/docs/")}}',
            require_id: 'true',
            type: 'docs'
        };
    }
    
    SapnsGrid.prototype.setQuery = function(query) {
        var self = this;
        
        // split "query" in three parts
        // q$$filters$$order
        var q_parts = query.split('$$');
        
        // q
        self.q = q_parts[0];
        
        // filters
        self.filters = [];
        if (q_parts.length > 1) {
            self.filters = parseFilters(q_parts[1]);
        }
        
        // order
        self.order = [];
        if (q_parts.length > 2) {
            self.order = parseOrder(q_parts[2]);
        }
        
        // user filter
        if (q_parts.length > 3) {
            self.current_user_filter = q_parts[3];
        }
        else {
            self.current_user_filter = __DEFAULT_FILTER;
        }
    }

    // getSelectedIds
    SapnsGrid.prototype.getSelectedIds = function() {
        var self = this;
        var selected_ids = [];
        $('#' + self.name + ' .sp-grid-row').each(function() {
            var rowid = $(this).find('.sp-grid-rowid');
            if (rowid.prop('checked')) {
                selected_ids.push(rowid.attr('id_row') * 1);
            }
        });

        return selected_ids;
    }

    SapnsGrid.prototype.getAction = function(action_name) {
        var self = this;
        for (var i=0, l=self.actions.length; i < l; i++) {
            var act = self.actions[i];
            if (typeof(act.type) === 'object') {
                if (act.type.id === action_name) {
                    return act;
                }
            }
            else if (act.name === action_name) {
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
            if (rowid.attr('id_row') === id) {
                row = rowid.parent();
                return;
            }
        });

        return row;
    }

    // loadData
    SapnsGrid.prototype.loadData = function(callback) {

        var self = this;
        
        var cols = self.cols;
        if (typeof(cols) === 'function') {
            cols = cols();
        }
        
        var g_wd = 23; // min-width: 20px;
        if (self.hide_check) {
            g_wd = -6;
        }
        
        // row width
        var row_wd = cols.length * 42;
        
        if (cols[0].title != 'id') {
            self.hide_check = true;
            self.hide_id = true;
            self.actions_inline = false;
        }
        
        // hide_check
        if (!self.hide_check) {
            row_wd += 23;
        }
        
        // hide_id
        if (!self.hide_id) {
            row_wd += 60;
        }
        
        var MIN_ROW = 905;
        
        if (row_wd < MIN_ROW) {
            row_wd = MIN_ROW;
        }

        var select_fields = '';
        for (var i=0, l=cols.length; i<l; i++) {
            var col = cols[i];
            
            if (col.title != 'id') {
                select_fields += '<option value="' + col.title + '">' + col.title + '</option>';
            }
            
            if (self.hide_id && col.title === 'id') {
                continue;
            }
            
            g_wd += (col.width + 5);
        }
        
        $('#'+self.name + ' .sp-grid-filter-field').html(select_fields);
        
        var g_table = '<div class="sp-grid" style="width:' + (g_wd+200) + 'px">';
        
        var grid_header = '<div class="sp-grid-row" style="width:' + (g_wd+150) + 'px">';
        
        if (!self.hide_check) {
            
            var disabled = '';
            if (!self.allow_multiselect) {
                disabled = 'disabled';
            }
            
            grid_header += '<div class="sp-col-title" style="width:23px">\
                <input class="sp-grid-select-all" type="checkbox" ' + disabled + '></div>';
        }
        
        if (self.actions_inline) {
            grid_header += '<div class="sp-col-title" style="%(actions_wd)s">*</div>';
        }
        
        var ordered_cols = {};
        for (var i=0, l=self.order.length; i<l; i++) {
            var o = self.order[i];
            o['index'] = i+1;
            ordered_cols[self.order[i].field] = o; 
        }
        
        for (var i=0, l=cols.length; i<l; i++) {
            var col = cols[i];
            var wd = col.width;
            if (!wd) {
                wd = self.default_.col_width;
            }

            if (self.hide_id && col.title === 'id') {
                continue;
            }
            
            var is_ordered = '';
            var order_type = '';
            var order_index = '';
            if (ordered_cols[col.title]) {
                var o = ordered_cols[col.title];
                is_ordered = 'sp-grid-ordered-col';
                order_type = ' order_type="' + o.type + '"';
                
                var ot;
                if (o.type === 'asc') {
                    ot = '+';
                }
                else {
                    ot = '-';
                }
                
                order_index = ' (' +  o.index + ot + ')';
            }
            
            grid_header += '<div class="sp-col-title sp-col-title-sortable ' + is_ordered + '"' + order_type + 
                ' col_num="' + i + '" style="width:' + wd + 'px" col_title="' + col.title + '">' + col.title + order_index + '</div>';
        }

        grid_header += '</div>';
        
        var data = self.data;
        if (typeof (data) === 'function') {
            data = data();
        }
        
        var ld = data.length;
        if (ld > 0) {
            for (var i=0; i<ld; i++) {
                
                var row = data[i];
                
                var row_style = '';
                if (self.styles.length && self.styles.length > i) {
                    row_style = self.styles[i];
                }
                
                var grid_row = '<div class="sp-grid-row" style="width:'+(g_wd+150)+'px">';
                
                if (!self.hide_check) {
                    var border_radius = '';
                    if (i === ld-1) {
                        border_radius = 'border-radius:0 0 0 5px';
                    }
                    
                    grid_row += '<div class="sp-grid-cell" title="' + row[0] + '" style="width:23px;' + border_radius + '">' +
                        '<input class="sp-grid-rowid" type="checkbox" id_row="' + row[0] + '"></div>';
                }
                
                if (self.actions_inline) {
                    
                    var actions_wd = 'width:107px';
                    if (!self.nonstd) {
                        actions_wd = 'width:82px';
                    }
                    
                    var _actions = 
                        '<div class="sp-grid-cell" style="%(actions_wd)s">\
                        <img class="inline_action edit_inline" title="{{_("Edit")}}" \
                            src="{{tg.url("/images/sapns/icons/edit.png")}}">\
                        <img class="inline_action delete_inline" title="{{_("Delete")}}" \
                            src="{{tg.url("/images/sapns/icons/delete.png")}}">\
                        <img class="inline_action docs_inline" title="{{_("Docs")}}" \
                            src="{{tg.url("/images/sapns/icons/docs.png")}}">';
                    
                    grid_row += sprintf(_actions, {actions_wd: actions_wd}) + self.nonstd + '</div>';
                }
                
                // grid_header
                if (i === 0) {
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
                        width = ' width:' + wd + 'px;';
                    }
                    
                    var border_radius = '';
                    if ((self.hide_check && i == ld-1) && 
                            (!self.hide_id && j == 0 || self.hide_id && j == 1)) {
                        border_radius = 'border-radius:0 0 0 5px;';
                    }
                    
                    if (i == ld-1 && j == lr-1) {
                        border_radius = 'border-radius:0 0 5px 0;';
                    }
                    
                    grid_row += '<div class="sp-grid-cell sp-grid-cell-tip clickable ' + row_style + '" \
                        col_num="' + j + '" style="text-align:' + al + ';' + width + border_radius + '"';
                    
                    if (cell) {
                        grid_row += sprintf('title="%s"', cell.replace(/"/gi, "''"));
                    }
                    else {
                        grid_row += 'title="({{_("empty")}})"';
                    }
                    
                    grid_row += '>' + cell + '</div>';
                }
                
                grid_row += '</div>';
                
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
                '<div class="sp-grid-row"><div class="sp-grid-cell sp-grid-noresults" title="{{_("No results")}}" ' +
                    'style="width:' + wd_ + 'px" >{{_("No results")}}</div></div>';
        }
        
        g_table += '</div>';
        
        $('#' + self.name).find('.sp-grid-parent').html(g_table);
        $('.sp-col-title-sortable').disableSelection();
        if (self.select_first && self.with_search && self.q && ld < 5 && ld > 0) {
            $('#' + self.name + ' .sp-grid-rowid:first').prop('checked', true);
        }
        
        var grid_id = '#'+self.name;
        $('.sp-col-title-sortable').resizable({
            handles: 'e',
            minWidth: self.resize.min_width,
            resize: function(e, ui) {
                var width = ui.element.width(),
                    col_num = ui.element.attr('col_num'),
                    row_width = $('.sp-grid-row').width(),
                    current_width = $('.sp-grid-cell[col_num=' + col_num + ']').width();
                
                $(grid_id + ' .sp-grid-cell[col_num=' + col_num + ']').width(width);
                $(grid_id + ' .sp-grid-row').width(row_width + (width - current_width));
            },
            stop: function(e, ui) {
                
                var col_num = ui.element.attr('col_num');
                
                if (self.resize.after) {
                    self.resize.after(col_num*1);
                }
                else {
                    // TODO: guardar anchos para el "current_user_filter" del usuario correspondiente
                    var length = self.cols.length;
                    if (self.cols[0].title === 'id') {
                        length -= 1;
                    }
                    
                    $.ajax({
                        url: "{{tg.url('/dashboard/save_col_width/')}}",
                        data: {
                            cls: self.cls,
                            length: length,
                            col_num: col_num,
                            width: ui.element.width()
                        },
                        success: function(res) {
                            if (res.status) {
                            }
                        }
                    });
                }
            }
        });
        
        if (callback) {
            callback();
        }
    }
    
    SapnsGrid.prototype.query = function() {
        
        var self = this;
        
        var q = self.q;
        
        // filters
        var active_filters = $.map(self.filters, function(f) {
            if (f.active) {
                return f;
            }
        });
        
        if (active_filters.length) {
            if (q) {
                q = q + ', ' + active_filters.join(', ');
            }
            else {
                q = active_filters.join(', ');
            }
        }
        
        // order
        if (self.order.length) {
            if (q) {
                q = q + ', ' + self.order.join(', ');
            }
            else {
                q = self.order.join(', ');
            }
        }
        
        return q;
    }
    
    SapnsGrid.prototype.query_ = function() {
        var self = this,
            qry = self.q + '$$';
        
        // filters
        for (var i=0, l=self.filters.length; i<l; i++) {
            if (i > 0) {
                qry += ', ';
            }
            
            qry += self.filters[i].stringify();
        }
        
        // order
        qry += '$$';
        for (var i=0, l=self.order.length; i<l; i++) {
            if (i > 0) {
                qry += ', ';
            }
            
            qry += self.order[i].stringify();
        }
        
        // user_filter
        if (self.current_user_filter !== __DEFAULT_FILTER) {
            qry += '$$' + self.current_user_filter;
        }
        
        return qry;
    }

    // search
    SapnsGrid.prototype.search = function(q, force, on_load) {
        var self = this;
        
        if (force === undefined) {
            force = false;
        }

        if (q === undefined) {
            q = self.q;
        }

        if (self.q != q || force) {
            self.pag_n = 1;
        }

        self.q = q;
        
        self.filters_tip();
        
        var q = self.query();
        
        var loading = sprintf('<div class="sp-grid-loading" style="height:%(hg)dpx">{{_("Loading")}}...</div>', {hg: self.height-50});
        
        $('#' + self.name).find('.sp-grid-parent').html(loading);
        
        var ajx = $.extend(true, {
            url: "{{tg.url('/dashboard/grid/')}}",
            cache: false,
            data: {
                cls: self.cls,
                q: q,
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
                    
                    // styles
                    if (response.styles) {
                        self.styles = response.styles;
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
                        $('#' + self.name + ' .sp-grid-page-back').attr('title', prev_page).prop('disabled', false);
                    } 
                    else {
                        $('#' + self.name + ' .sp-grid-page-back').prop('disabled', true);
                    }
                    
                    // page-forth
                    if (params.curr_page < params.total_page) {
                        var next_page = sprintf("{{_('page %(p)d')}}", {p: params.curr_page + 1});
                        $('#' + self.name + ' .sp-grid-page-forth').attr('title', next_page).prop('disabled', false);
                    } 
                    else {
                        $('#' + self.name + ' .sp-grid-page-forth').prop('disabled', true);
                    }
                    
                    // set focus on the search box
                    $('#' + self.name + ' .sp-search-txt').focus();
                    
                    // last-page
                    var last_page = sprintf("{{_('page %(p)d')}}", {p: params.total_page});
                            
                    $('#' + self.name + ' .sp-grid-last-page').attr('title', last_page);
                    
                    //$('#' + self.name + ' .sp-grid-pager-desc').html(pag_desc);
                    $('#' + self.name + ' .sp-grid-current-page').val(self.pag_n);

                    self.data = response.data;
                    self.loadData(function() {
                        $('.sp-grid-cell-tip, .edit_inline, .delete_inline, .docs_inline, .new_inline, .sp-grid-save-filter').qtip({
                            content: {
                                text: true
                            },
                            position: {
                                my: 'top left',
                                at: 'bottom center'
                            },
                            style: 'ui-tooltip-rounded'
                        });
                    });
                    
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

        $('#grid-dialog_' + self.name).html("<p style='text-align:center;font-style:italic'>{{_('You must select a row before click on this action')}}</p>")
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
                    var new_btn = '<img class="inline_action new_inline" ' +
                        'title="{{_("New")}}" src="{{tg.url("/images/sapns/icons/new.png")}}">';
                    $('#'+self.name + ' .sp-grid-search-box').append(new_btn);
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
                self.nonstd = '<select class="nonstd_actions"><option value=""></option>' 
                    + self.nonstd 
                    + '</select>';
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

                var s_export = '<div class="export">\
                    <select class="sp-button sp-grid-action">\
                    <option value="">({{_("Export")}})</option>' + 
                    options + '</select></div>';
                
                $('#'+self.name + ' .sp-grid-search-box').append(s_export);
            }
        }

        return g_actions;
    }
    
    SapnsGrid.prototype.complete_actions = function() {
        
        var self = this;
        
        for (var i=0, l=self.actions.length; i<l; i++) {
            var act = self.actions[i];
            if (typeof(act.type) === 'string') {
                // new
                if (act.type === 'new') {
                    self.actions[i] = $.extend(self._new_default, act);
                }
                // edit
                else if (act.type === 'edit') {
                    self.actions[i] = $.extend(self._edit_default, act);
                }
                // delete
                else if (act.type === 'delete') {
                    self.actions[i] = $.extend(self._delete_default, act);
                }
                // docs
                else if (act.type === 'docs') {
                    self.actions[i] = $.extend(self._docs_default, act);
                }
            }
        }
    }

    SapnsGrid.prototype.loadActions = function(callback) {

        var self = this;
        var g_actions = '';
        var actions_selector = sprintf('#%s .actions', self.name);

        if (self.actions != null) {
            if (self.actions.length === undefined) {
                // it's an object
                var ajx = $.extend(true, {
                    url: "{{tg.url('/dashboard/grid_actions/')}}",
                    //type: "post",
                    cache: false,
                    data: { cls: self.cls },
                    success: function(response) {
                        if (response.status) {
                            self.actions = response.actions;
                        }
                        
                        //self.complete_actions();
                        $(actions_selector).html(self._loadActions(self.actions));
                        if (callback) {
                            callback();
                        }
                    }
                }, self.actions);

                $.ajax(ajx);
            } else {
                //self.complete_actions();
                $(actions_selector).html(self._loadActions(self.actions));
                if (callback) {
                    callback();
                }
            }
        }
        else {
            if (callback) {
                callback();
            }
        }
        
        // if the row is selected, then mark the checkbox
        var cell_selector = sprintf('#%s .sp-grid-cell.clickable', self.name),
            cb_selector_checked = sprintf('#%s .sp-grid-cell .sp-grid-rowid:checked', self.name);
        $(document).off('click', cell_selector).on('click', cell_selector, function(event) {
            
            var ctrl = (event.ctrlKey || event.metaKey) && self.allow_multiselect;
            
            var row_id = $(this).parent().find('.sp-grid-rowid');
            if (!row_id.prop('checked') || ctrl || (self.multiselect && self.allow_multiselect)) {
                
                $('#'+self.name + ' .sp-grid-select-all').prop('checked', false);
                
                $('#'+self.name + ' .sp-grid-rowid').each(function() {
                    if ($(this) != row_id && !self.multiselect && !ctrl) {
                        $(this).prop('checked', false);
                        $(this).parent().parent().removeClass('sp-grid-row-selected');
                    }
                });
                
                if (row_id.prop('checked')) {
                    row_id.prop('checked', false);
                    $(this).parent().removeClass('sp-grid-row-selected');
                }
                else {
                    row_id.prop('checked', true);
                    $(this).parent().addClass('sp-grid-row-selected');
                }
            }
            else {
                if (self.dblclick) {
                    // run 'dblclick' action
                    run_action(row_id.attr('id_row')*1, self.dblclick, event.ctrlKey || event.metaKey, event.shiftKey);
                }
            }
        });
        
        var cb_selector = sprintf('#%s .sp-grid-cell .sp-grid-rowid', self.name);
        $(document).off('click', cb_selector).on('click', cb_selector, function() {
            var chk = $(this).prop('checked');
            
            if (!self.allow_multiselect) {
                $(cb_selector).prop('checked', false);
                $(this).prop('checked', chk);
            }
        });

        function form(action, target) {
            
            var qry = self.query_();
            
            qry = encodeURI(qry).replace('-', '%2D', 'g').
                replace('"', '%22', 'g').replace('+', '%2B', 'g').
                replace('#', '%23', 'g');
            
            var came_from = '';
            if (target != '_blank') {
                var came_from = self.url_base + '?q=' + qry + 
                    '&rp=' + self.rp + '&pag_n=' + self.pag_n +
                    '&ch_attr=' + self.ch_attr + '&parent_id=' + self.parent_id;
            }

            var f = '<form type="post" action="' + action + '" target="' + target + '">' +
                '<input type="hidden" name="came_from" value="' + came_from + '">';

            if (self.ch_attr) {
                f += '<input type="hidden" name="_' + self.ch_attr + '" value="' + self.parent_id + '">';
            }

            f += '</form>';

            return f;
        }
        
        function _run_action(id, ids, act, ctrl, shift) {
            
            if (typeof(act.type) === 'string') {
                
                if (shift && self.shift_enabled) {
                    
                    // new
                    if (act.type === 'new') {
                        act = self._new_default;
                    }
                    // edit
                    else if (act.type === 'edit') {
                        act = self._edit_default;
                    }
                    // delete
                    else if (act.type === 'delete') {
                        act = self._delete_default;
                    }
                    // docs
                    else if (act.type === 'docs') {
                        act = self._docs_default;
                    }
                }
                
                var a = act.url;
                if (a[a.length - 1] != '/') {
                    a += '/';
                }
                
                if (!act.data) {
                    var target = '';
                    if (ctrl) {
                        target = '_blank';
                    }
                    
                    if (act.type === 'process') {
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
                    else if (act.type === 'new') {
                        a += sprintf('%s/', self.cls);
                    }
                    else if (act.type === 'delete') {
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
                    var data = JSON.parse(act.data), 
                        on_progress = false;
                    
                    var params = {};
                    params[data.param_name] = id;
                    
                    var button_title = "{{_('Ok')}}";
                    if (data.button_title) {
                        button_title = data.button_title;
                    }
                    
                    var refresh = true;
                    if (data.refresh !== undefined) {
                        refresh = data.refresh;
                    }
                    
                    // init dialog
                    var dialog_id = self.name + '_dialog';
                    $('#'+dialog_id).remove();
                    $('<div id="' + dialog_id + '" style="display:none"></div>').appendTo('body');
                    
                    // buttons
                    var buttons = [];
                    if (data.buttons === undefined) {
                        data.buttons = [{
                            button_title: button_title,
                            callback: data.callback,
                            refresh: refresh
                        }];
                    }

                    var F = function(b) {
                        
                        var self_ = this;
                        self_.b = b;
                        
                        self_.call = function () {
                            if (!on_progress) {
                                on_progress = true;
                                
                                window[self_.b.callback](function() {
                                    if (self_.b.refresh) {
                                        self.search(self.q, true);
                                    }
                                    
                                    $('#'+dialog_id).dialog('close');
                                },
                                function() {
                                    on_progress = false;
                                });
                            }
                        }
                    };
                    
                    for (var i=0, l=data.buttons.length; i<l; i++) {
                        var b = data.buttons[i],
                            f = new F(b);
                        
                        buttons.push({
                            text: b.button_title,
                            click: f.call
                        });
                    }
                    
                    // "Cancel" button
                    buttons.push({
                        text: "{{_('Cancel')}}",
                        click: function() {
                            if (!on_progress) {
                                $('#'+dialog_id).dialog('close');
                            }
                        
                        }
                    });
                    
                    // load dialog content
                    $.ajax({
                        url: a,
                        data: params,
                        success: function(content) {
                            $('#'+dialog_id).html(content).dialog({
                                title: act.title,
                                modal: true,
                                resizable: false,
                                width: data.width,
                                height: data.height,
                                closeOnEscape: false,
                                buttons: buttons,
                            });
                        }
                    });
                }
            }
            else {
                // typeof(act.type) === 'object'
                var selected_ids = ids;
                if (act.require_id) {
                    if (selected_ids.length > 0) {
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

        function run_action(item, action_name, ctrl, shift) {
            var act = self.getAction(action_name);
            
            if (typeof(item) !== 'number') {
                var id = item.parent().parent().find('.sp-grid-rowid').attr('id_row');
            }
            else {
                var id = item;
            }
            
            _run_action(id, [], act, ctrl, shift);
        }

        // new
        var new_selector = sprintf('#%s .new_inline', self.name)
        $(document).off('click', new_selector).on('click', new_selector, function(event) {
            run_action($(this), 'new', event.ctrlKey || event.metaKey, event.shiftKey);
        });

        if (self.actions_inline) {
            
            // edit
            var edit_selector = sprintf('#%s .edit_inline', self.name);
            $(document).off('click', edit_selector).on('click', edit_selector, function(event) {
                run_action($(this), 'edit', event.ctrlKey || event.metaKey, event.shiftKey);
            });
    
            // delete
            var delete_selector = sprintf('#%s .delete_inline', self.name);
            $(document).off('click', delete_selector).on('click', delete_selector, function(event) {
                var ids = self.getSelectedIds();
                if (ids.length == 0) {
                    var id = $(this).parent().parent().find('.sp-grid-rowid').attr('id_row');
                    ids = [id];
                }
                
                var act = self.getAction('delete');
                self.std_delete(ids, act.url);
            });
    
            // docs
            var docs_selector = sprintf('#%s .docs_inline', self.name);
            $(document).off('click', docs_selector).on('click', docs_selector, function(event) {
                run_action($(this), 'docs', false, event.shiftKey);
            });
    
            // non-standard actions
            var nonstd_selector = sprintf('#%s .nonstd_actions', self.name);
            $(document).off('change', nonstd_selector).on('change', nonstd_selector, function(event) {
                var action_id = $(this).val();
                if (action_id) {
                    run_action($(this), action_id);
                    // select first option again
                    $(nonstd_selector).val('');
                }
            });
        }
        // !actions_inline
        else {
            var action_sel = sprintf('#%s .sp-grid-button-action', self.name);
            $(document).off('click', action_sel).on('click', action_sel, function(event) {
                var act = self.getAction($(this).attr('id'));
                var selected_ids = self.getSelectedIds();
                _run_action(selected_ids[0], selected_ids, act, event.ctrlKey || event.metaKey, event.shiftKey);
            });
        }

        // export button
        var export_sel = sprintf('#%s .export select', self.name);
        $(document).on('change', export_sel, function() {
            var fmt = $(export_sel).val();
            
            if (fmt == '') {
                // nothing selected
                return;
            }
            
            var formats = self.exportable_formats;
            
            var extra_params = '';
            if (typeof (self.exportable) === 'object') {
                
                formats = self.exportable.formats;

                if (self.exportable.data) {
                    for (k in self.exportable.data) {
                        var v = self.exportable.data[k];
                        if (typeof(v) === 'function') {
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
            
            var form_export = '<form action="' + url + '" method="get">\
                <input type="hidden" name="cls" value="' + self.cls + '">\
                <input type="hidden" name="q" value="' + self.query() + '">\
                <input type="hidden" name="ch_attr" value="' + self.ch_attr + '">\
                <input type="hidden" name="parent_id" value="' + self.parent_id + '">' + 
                extra_params + '</form>';

            $(form_export).appendTo('body').submit().remove();

            // reset the select
            $(this).find('option:first').prop('selected', true);
        });
    }

    // std_delete
    SapnsGrid.prototype.std_delete = function(ids, url) {

        var self = this,
            cls = self.cls,
            in_progress = false;
        
        var id = JSON.stringify(ids);

        var delete_html = "<p id='delete-question'>{{_('Do you really want to delete this record?')}}</p>" +
                "<p id='object-title'></p><div class='wait-message' style='display:none'>{{_('Wait, please')}}...</div>";

        var error_html = "<p id='delete-error-title'>{{_('Oops, something went wrong...')}}</p>" +
                "<div id='delete-error-message'></div>";

        $('#grid-dialog_' + self.name).html(delete_html);

        // get object's title
        var title = '';
        $.ajax({
            url: "{{tg.url('/dashboard/title/')}}",
            data: { cls: cls, id: id },
            success: function(res) {
                if (res.status) {
                    var title;
                    if (typeof (res.title) === 'string') {
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
            title: "{{_('Delete')}}",
            modal: true,
            resizable: false,
            closeOnEscape: false,
            width: 650,
            height: 210,
            buttons: {
                "{{_('Ok')}}": function() {
                    if (!in_progress) {
                        
                        in_progress = true;
                        $('#grid-dialog_' + self.name + ' .wait-message').fadeIn();
                        
                        $.ajax({
                            url: url,
                            data: { cls: cls, id_: id },
                            dataType: 'json',
                            success: function(res) {
                                in_progress = false;
                                $('#grid-dialog_' + self.name + ' .wait-message').fadeOut();
                                
                                if (res.status) {
                                    self.search(self.q, true);
                                    $('#grid-dialog_' + self.name).dialog('close');
                                } 
                                else {
                                    $('#grid-dialog_' + self.name).dialog('close');
    
                                    var message = "<p style='color:#777'>" + res.message + "</p>";
    
                                    if (res.rel_tables != undefined && res.rel_tables.length > 0) {
                                        message += "<div>{{_('For your information this object is related with other objects in the following classes:')}}</div>";
                                        message += "<ul>";
    
                                        for (var i = 0; i < res.rel_tables.length; i++) {
                                            var title = res.rel_tables[i].class_title;
                                            var attr_title = res.rel_tables[i].attr_title;
                                            message += '<li><span style="font-weight:bold">'
                                                    + title
                                                    + '</span> (<span style="color:#777">'
                                                    + attr_title + '</span>)</li>';
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
                                in_progress = false;
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
                    }
                },
                "{{_('Cancel')}}": function() {
                    if (!in_progress) {
                        $('#grid-dialog_' + self.name).dialog('close');
                    }
                }
            }
        });
    }
    
    SapnsGrid.prototype.selectAll = function(chk) {
        var self = this;
        if (chk === undefined) {
            chk = true;
        }
        
        $('#'+self.name + ' .sp-grid-rowid').prop('checked', chk);
    }
    
    SapnsGrid.prototype.filters_tip = function() {
        var self = this;
        
        $('#' + self.name + ' .sp-search-btn').qtip({
            content: {
                text: function() {
                    var s = '';
                    if (self.filters.length) {
                        for (var i=0, l=self.filters.length; i<l; i++) {
                            
                            if (!self.filters[i].active) {
                                s += '<font style="text-decoration:line-through">' + self.filters[i].tip() + '</font><br>';
                            }
                            else {
                                s += self.filters[i].tip() + '<br>';
                            }
                        }
                    }
                    else {
                        s = 'No hay filtros';
                    }
                    
                    return s;
                }
            },
            position: {
                at: 'top right',
                my: 'bottom left'
            },
            style: 'ui-tooltip-rounded'
        });
        
        if (self.filters.length) {
            $('#' + self.name + ' .sp-search-btn').css('border-color', 'orange');
        }
        else {
            $('#' + self.name + ' .sp-search-btn').css('border-color', '');
        }
    }

    $.fn.sapnsGrid = function(arg1, arg2, arg3) {

        if (typeof(arg1) === "object") {
            
            var g = new SapnsGrid(arg1);
            this.data('sapnsGrid', g);
            var g_id = '#'+g.name;

            this.append(sprintf('<div id="grid-dialog_%(name)s" class="sp-grid-dialog" style="display:none"></div>', {name: g.name}));

            var g_content = '';
            g_content += sprintf('<div class="sp-grid-container" id="%(name)s" cls="%(cls)s">', {name: g.name, cls: g.cls});

            if (g.caption) {
                g_content += sprintf('<div class="sp-grid-caption">%(caption)s</div>', {caption: g.caption});
            }

            if (g.with_search) {

                g_content += '<div><div class="sp-grid-search-box">\
                    <input class="sp-search-txt" name="q" type="text" value="">\
                    <img class="inline_action sp-search-btn" \
                        src="{{tg.url("/images/sapns/icons/search.png")}}" title="{{_("Search...")}}">';
                
                if (g.with_filters) {
                    
                    var filters_ = '';
                    for (var i=0, l=g.user_filters.length; i<l; i++) {
                        var f = g.user_filters[i],
                            selected = '';
                        
                        if (g.current_user_filter == f.name) {
                            selected = ' selected';
                        }
                        
                        filters_ += '<option value="' + f.name + '"' + selected + '>' + f.name + '</option>';
                    }
                    
                    g_content += 
                        '<img class="inline_action sp-grid-save-filter" \
                            src="{{tg.url("/images/sapns/icons/filters.png")}}" title="{{_("Manage filter")}}">\
                        <select class="sp-grid-action sp-button sp-grid-select-filter">' + filters_ + '</select>';
                }
                
                g_content += '</div>';
                
                g_content += '<div class="sp-grid-filters" style="display:none"></div>';
                g_content += '<div class="sp-grid-edit-filter" style="display:none">\
                    <div style="float:left;height:40px;margin-right:5px">\
                        <div class="sp-grid-filter-label">{{_("Field")}}</div>\
                        <div><select class="sp-grid-filter-field"></select></div>\
                    </div>\
                    <div style="float:left;height:40px;margin-right:5px">\
                        \<div class="sp-grid-filter-label">{{_("Operator")}}</div>\
                        <div><select class="sp-grid-filter-operator">\
                            <option value="co">{{_("Contains")}}</option>\
                            <option value="eq">{{_("Equals to")}}</option>\
                            <option value="lt">{{_("Less than")}}</option>\
                            <option value="gt">{{_("Greater than")}}</option>\
                            <option value="let">{{_("Less than or equals to")}}</option>\
                            <option value="get">{{_("Greater than or equals to")}}</option>\
                            <option value="nco">{{_("Does not contain")}}</option>\
                            <option value="neq">{{_("Not equals to")}}</option>\
                        </select></div>\
                    </div>\
                    <div style="float:left;height:40px">\
                        <div class="sp-grid-filter-label">{{_("Value")}}</div>\
                        <input class="sp-grid-filter-value" type="text">\
                        <select class="sp-grid-filter-functions">\
                            <option value="">({{_("date functions")}})</option>\
                            <option value="{today}">{{_("Today")}}</option>\
                            <option value="{today - 1}">{{_("Yesterday")}}</option>\
                            <option value="{today + 1}">{{_("Tomorrow")}}</option>\
                            <option value="{start_week}">{{_("Start week")}}</option>\
                            <option value="{end_week}">{{_("End week")}}</option>\
                            <option value="{start_month}">{{_("Start month")}}</option>\
                            <option value="{end_month}">{{_("End month")}}</option>\
                            <option value="{start_year}">{{_("Start year")}}</option>\
                            <option value="{end_year}">{{_("End year")}}</option>\
                        </select>\
                    </div></div>';
                
                var ad_sel = '.sp-grid-activate-filter, .sp-grid-deactivate-filter';
                
                var s_ = '.sp-grid-filter-value';
                $(document).off('keypress', s_).on('keypress', s_, function(e) {
                    if (e.which === 13) {
                        // INTRO
                        $(this).parents('.ui-dialog').find('.ui-dialog-buttonset button:first').click();
                    }
                });
                
                var s_ = '.sp-grid-filter-functions';
                $(document).off('change', s_).on('change', s_, function() {
                    var date_function = $(this).val();
                    $(this).parent().find('.sp-grid-filter-value').val(date_function);
                });
                
                var s_ = '.sp-grid-row-filter button';
                $(document).off('click', s_).on('click', s_, function() {
                    var i = $(this).parent().attr('filter_order');
                    var f = g.filters[i];
                    
                    if (f.active) {
                        $(this).parent().removeClass('active').addClass('inactive');
                        $(this).text("{{_('Activate')}}");
                    }
                    else {
                        $(this).parent().removeClass('inactive').addClass('active');
                        $(this).text("{{_('Deactivate')}}");
                    }
                    
                    $(this).addClass('sp-grid-filter-changed');
                    
                    f.toggle();
                });
                
                var search_sel = g_id + ' .sp-search-btn';
                $(document).off('click', search_sel).on('click', search_sel, function() {
                    
                    function load_filters() {
                        var s = '',
                            l = g.filters.length;
                        
                        if (l) {
                            for (var i=0; i<l; i++) {
                                var f = g.filters[i];
                                
                                var activate_filter = '',
                                    activate_class = 'active';
                                if (f.active) {
                                    activate_filter = '<button>{{_("Deactivate")}}</button>';
                                }
                                else {
                                    activate_class = 'inactive';
                                    activate_filter = '<button>{{_("Activate")}}</button>';
                                }
                                
                                s += '<div class="sp-grid-row-filter ' + activate_class + '" style="clear:left" filter_order="' + i + '">\
                                    <div style="float:left;margin-right:10px"><input class="sp-grid-check-filter" type="checkbox"></div>\
                                    <div class="sp-grid-filter-description"><span class="col">&lt;' + f.field + '&gt;</span> \
                                    <span class="operator">' + f.operator_title().toLowerCase() + '</span>\
                                    <span class="value">"' + f.value + '"</span></div>' +
                                    activate_filter + '</div>';
                            }
                        }
                        else {
                            s = '<p class="sp-grid-no-filters">{{_("There are no filters")}}</p>';
                        }
                        
                        $(g_id + ' .sp-grid-filters').html(s);
                    }
                    
                    load_filters();
                    
                    function edit_filter(filter, callback) {
                        
                        $('<div/>').html($(g_id + ' .sp-grid-edit-filter').html()).dialog({
                            title: "{{_('Edit filter')}}",
                            modal: true,
                            resizable: false,
                            width: 700,
                            height: 150,
                            open: function() {
                                if (filter) {
                                    $(this).find('.sp-grid-filter-field').val(filter.field);
                                    $(this).find('.sp-grid-filter-operator').val(filter.operator);
                                    $(this).find('.sp-grid-filter-value').val(filter.value);
                                }
                            },
                            buttons: {
                                "{{_('Ok')}}": function() {
                                    var self = this;
                                    if (!filter) {
                                        filter = new Filter({
                                            field: $(this).find('.sp-grid-filter-field').val(),
                                            operator: $(this).find('.sp-grid-filter-operator').val(),
                                            value:  $(this).find('.sp-grid-filter-value').val()
                                        });
                                        
                                        g.filters.push(filter);
                                    }
                                    else {
                                        filter.field = $(this).find('.sp-grid-filter-field').val();
                                        filter.operator = $(this).find('.sp-grid-filter-operator').val();
                                        filter.value = $(this).find('.sp-grid-filter-value').val();
                                    }
                                    
                                    g.search($(g_id + ' .sp-search-txt').val(), true);
                                    $(this).dialog('destroy').remove();
                                    if (callback) {
                                        callback();
                                    }
                                },
                                "{{_('Cancel')}}": function() {
                                    $(this).dialog('destroy').remove();
                                }
                            }
                        });
                    }
                    
                    // filters management
                    $('<div/>').html($(g_id + ' .sp-grid-filters').html()).dialog({
                        title: "Filtros",
                        modal: true,
                        resizable: false,
                        width: 600,
                        height: 300,
                        closeOnEscape: false,
                        open: function() {
                            var dlg = $(this);
                            edit_filter(null, function() {
                                dlg.dialog('destroy').remove();
                            });
                        },
                        buttons: {
                            "{{_('Add')}}": function() {
                                var dlg = $(this);
                                edit_filter(null, function() {
                                    dlg.dialog('destroy').remove();
                                });
                            },
                            "{{_('Edit')}}": function() {
                                var i = $(this).find('.sp-grid-row-filter input[type=checkbox]:visible:checked:first').parent().parent().attr('filter_order');
                                var dlg = $(this);
                                edit_filter(g.filters[i], function() {
                                    dlg.dialog('destroy').remove();
                                });
                                
                                g.search($(g_id + ' .sp-search-txt').val(), true);
                            },
                            "{{_('Remove')}}": function() {
                                var filters = [];
                                $(this).find('.sp-grid-row-filter input[type=checkbox]:visible:checked').each(function() {
                                    filters.push($(this).parent().parent().attr('filter_order')*1);
                                });
                                
                                filters = filters.reverse()
                                for (var i=0, l=filters.length; i<l; i++) {
                                    g.filters.splice(filters[i], 1);
                                }
                                
                                g.search($(g_id + ' .sp-search-txt').val(), true);
                                $(this).dialog('destroy').remove();
                            },
                            "{{_('Remove all')}}": function() {
                                g.filters = [];
                                g.search($(g_id + ' .sp-search-txt').val(), true);
                                $(this).dialog('destroy').remove();
                            },
                            "{{_('Close')}}": function() {
                                if ($('.sp-grid-filter-changed').length) {
                                    $('.sp-grid-filter-changed').removeClass('sp-grid-filter-changed');
                                    g.search($(g_id + ' .sp-search-txt').val(), true);
                                }
                                
                                $(this).dialog('destroy').remove();
                            }
                        }
                    });
                });

                var search_txt = g_id + ' .sp-search-txt';
                $(document).off('keypress', search_txt).on('keypress', search_txt, function(event) {
                    // "Intro" key pressed
                    if (event.which === 13) {
                        g.search($(this).val());
                    }
                });
                
                /* select-filter */
                var select_filter = g_id + ' .sp-grid-select-filter';
                $(document).off('change', select_filter).on('change', select_filter, function() {
                    var filter_name = $(this).val(),
                        query_filter = '';
                    for (var i=0, l=g.user_filters.length; i<l; i++) {
                        var f = g.user_filters[i];
                        if (f.name === filter_name) {
                            g.setQuery(f.query);
                            g.current_user_filter = filter_name;
                            g.search(g.query_().split('$$')[0], true);
                            return;
                        }
                    }
                });
                
                /* save-filter */
                var save_filter = g_id + ' .sp-grid-save-filter';
                $(document).off('click', save_filter).on('click', save_filter, function() {
                    var current_query = g.query_(),
                        current_filter = $(select_filter).val(),
                        on_progress = false,
                        dialog = 
                        '<div id="sp-grid-save-filter-dialog" style="display:none">\
                            <div class="sp-field-row">\
                                <div class="sp-field">\
                                    <div class="label">{{_("Filter name")}}</div>\
                                    <input id="sp-grid-filter-name" type="text" value="' + current_filter + '">\
                                </div>\
                            </div>\
                        </div>';
                    
                    $('#sp-grid-save-filter-dialog').remove();
                    $(dialog).appendTo('body').dialog({
                        title: "{{_('Save filter')}}",
                        modal: true,
                        resizable: false,
                        width: 400,
                        height: 'auto',
                        buttons: {
                            "{{_('Create or Modify')}}": function() {
                                if (!on_progress) {
                                    on_progress = true;
                                    
                                    var filter_name = $('#sp-grid-filter-name').val().replace(/[^A-Za-z0-9_]/g, '_');
                                    
                                    // Web service to create/modify this filter
                                    $.ajax({
                                        url: "{{tg.url('/dashboard/save_user_filter/')}}",
                                        data: { cls: g.cls, filter_name: filter_name, query: current_query },
                                        success: function(res) {
                                            if (res.status) {
                                                /* looking for the filter */
                                                var exists = false;
                                                for (var i=0, l=g.user_filters.length; i<l; i++) {
                                                    var f = g.user_filters[i];
                                                    if (f.name === filter_name) {
                                                        f.query = current_query;
                                                        exists = true;
                                                    }
                                                }
                                                
                                                if (!exists) {
                                                    g.user_filters.push({ name: filter_name, query: current_query });
                                                    $(select_filter).append('<option value="' + filter_name + '">' + filter_name + '</option>');
                                                    $(select_filter).val(filter_name);
                                                }
                                                
                                                $('#sp-grid-save-filter-dialog').dialog('close');
                                            }
                                            else {
                                                if (res.msg) {
                                                    console.log(res.msg);
                                                }
                                                
                                                on_progress = false;
                                                alert('Error!');
                                            }
                                        },
                                        error: function() {
                                            on_progress = false;
                                            alert('Error!');
                                        }
                                    });
                                }
                            },
                            "{{_('Delete')}}": function() {
                                if (!on_progress) {
                                    var filter_name = $('#sp-grid-filter-name').val();
                                    //if (filter_name !== 'default') {
                                        on_progress = true;
                                        
                                        // Web service to delete this filter
                                        $.ajax({
                                            url: "{{tg.url('/dashboard/delete_user_filter/')}}",
                                            data: { cls: g.cls, filter_name: filter_name },
                                            success: function(res) {
                                                if (res.status) {
                                                    $(select_filter).val('default').change();
                                                    $(select_filter + ' option[value=' + filter_name + ']').remove();
                                                    
                                                    var user_filters = [];
                                                    for (var i=0, l=g.user_filters.length; i<l; i++) {
                                                        var uf = g.user_filters[i];
                                                        if (uf.name !== filter_name) {
                                                            user_filters.push(uf);
                                                        }
                                                    }
                                                    
                                                    g.user_filters = user_filters;
                                                    
                                                    $('#sp-grid-save-filter-dialog').dialog('close');
                                                }
                                                else {
                                                    on_progress = false;
                                                    alert('Error!');
                                                }
                                            },
                                            error: function() {
                                                on_progress = false;
                                                alert('Error!');
                                            }
                                        });
                                    /*}
                                    else {
                                        $('#sp-grid-save-filter-dialog').dialog('close');
                                    }*/
                                }
                            },
                            "{{_('Cancel')}}": function() {
                                if (!on_progress) {
                                    $('#sp-grid-save-filter-dialog').dialog('close');
                                }
                            }
                        }
                    });
                });
                
                g_content += '</div>';
            }
            
            var g_table = 
                '<div class="sp-grid-parent" style="overflow:auto;clear:left;height:' + 
                    (g.height+5) + 'px;background-color:transparent"></div>';
            
            // pager
            var g_pager = '';
            if (g.with_pager) {
                g_pager += '<div class="sp-grid-pager">\
                    <div class="sp-grid-pager-desc"></div>';
                
                // pager_options
                var pager_options = '';
                for (var i=0, l=g.pager_options.length; i<l; i++) {
                    var option = g.pager_options[i];
                    
                    var selected = '';
                    if (option.sel) {
                        selected = ' selected ';
                    }
                    
                    pager_options += '<option value="' + option.val + '"' + selected + '>' + option.desc + '</option>';
                }
                
                g_pager += '<div style="float:left;clear:right;height:25px;margin-top:2px">' +
                        '<select class="sp-button sp-grid-rp">' +
                        pager_options +
                        '</select>' +
                        '<button class="sp-button sp-grid-first-page" style="float:left">|&lt;&lt;</button>' +
                        '<button class="sp-button sp-grid-page-back" style="float:left">&lt;&lt;</button>' +
                        '<input class="sp-grid-current-page" type="text" style="text-align:center;font-size:11px;margin-top:3px" readonly>' +
                        '<button class="sp-button sp-grid-page-forth" style="float:left">&gt;&gt</button>';

                g_pager += '</div>';
                
                var select_all = g_id + ' .sp-grid-select-all',
                    rp = g_id + ' .sp-grid-rp',
                    first_page = g_id + ' .sp-grid-first-page',
                    page_back = g_id + ' .sp-grid-page-back',
                    page_forth = g_id + ' .sp-grid-page-forth',
                    last_page = g_id + ' .sp-grid-last-page';
                    
                $(document).off('click', select_all).on('click', select_all, function() {
                    var chk = $(this).prop('checked');
                    g.selectAll(chk);
                });

                $(document).off('change', rp).on('change', rp, function() {
                    g.rp = $(this).val();
                    g.pag_n = 1;
                    g.search(g.q);
                });

                $(document).off('click', first_page).on('click', first_page, function() {
                    g.pag_n = 1;
                    g.search(g.q);
                });

                $(document).off('click', page_back).on('click', page_back, function() {
                    if (g.pag_n > 1) {
                        g.pag_n -= 1;
                        g.search(g.q);
                    }
                });

                $(document).off('click', page_forth).on('click', page_forth, function() {
                    if (g.pag_n < g.total_pag) {
                        g.pag_n *= 1
                        g.pag_n += 1;
                        g.search(g.q);
                    }
                });

                $(document).off('click', last_page).on('click', last_page, function() {
                    g.pag_n = g.total_pag;
                    g.search(g.q);
                });
            }
            
            var col_sortable = g_id + ' .sp-col-title-sortable';
            
            $(document).off('click', col_sortable).on('click', col_sortable, function(event) {
                
                var field = $(this).attr('col_title');
                var shift = event.shiftKey;
                var ctrl = event.ctrlKey || event.metaKey;
                
                // order type (asc, desc)
                if ($(this).hasClass('sp-grid-ordered-col')) {
                    var type;
                    if ($(this).attr('order_type') == 'asc') {
                        type = 'desc';
                    }
                    else {
                        type = 'asc';
                    }
                    
                    if (shift) {
                        // modify an existing order
                        for (var i=0, l=g.order.length; i<l; i++) {
                            if (g.order[i].field === field) {
                                break;
                            }
                        }
                        
                        g.order[i].type = type
                    }
                    else {
                        if (!ctrl) {
                            // reseting multiple order
                            if (g.order.length > 1) {
                                type = 'asc';
                            }
                            
                            var o = new OrderFilter({ field: field, type: type});
                            g.order = [o];
                        }
                        else {
                            // delete order
                            for (var i=0, l=g.order.length; i<l; i++) {
                                if (g.order[i].field === field) {
                                    break;
                                }
                            }
                            
                            g.order.splice(i, 1);
                            $(this).removeClass('sp-grid-ordered-col');
                        }
                    }
                }
                else {
                    // add a new order
                    var o = new OrderFilter({field: field, type: 'asc'});
                    
                    if (shift) {
                        g.order.push(o);
                    }
                    else {
                        g.order = [o];
                    }
                }
                
                // refresh
                g.search(undefined, true);
            });
            
            var g_actions = '<div class="sp-grid-button-actions" style="display:none"></div>';

            this.append(g_content + g_actions + g_table + g_pager + '</div>');
            
            g.loadActions(function() {
                $(g_id + ' .sp-search-txt').val(g.q);
                g.search(g.q);
            });            
        } 
        else if (typeof(arg1) == "string") {

            var self = this.data('sapnsGrid');
            var g_id = '#' + self.name;

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
                    $(g_id + ' .sp-search-txt').val(q);
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
                $(g_id + ' .sp-grid-rp [value='+arg2+']').prop('selected', true);
            }
            // selectAll
            else if (arg1 == "selectAll") {
                self.selectAll();
            }
            // getQuery
            else if (arg1 === "getQuery") {
                return self.query_();
            }
            else if (arg1 === "setQuery") {
                self.setQuery(arg2);
            }
            // TODO: other sapnsGrid methods
        }

        return this;
    };
})(jQuery);