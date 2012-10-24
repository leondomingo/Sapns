var SidebarMessages = function(args) {
    
    var self = this;
    
    var args_ = $.extend(true, {
        width: 200,
        after_show_message: null,
        after_hide_message: null
    }, args);
    
    $.extend(true, self, args_);
    self.messages = {};
    
    // create sidebar
    if ($('.sidebar-messages').length === 0) {
        var sb = '<div class="sidebar-messages" style="width:' + self.width + 'px;"></div>';
        $(sb).appendTo('body');
    }
    
    // show
    self.show = function(args) {
        var args_ = $.extend(true, {
            id: 'sbm-message_' + Math.floor(Math.random()*99999),
            hide_after: 5000,
            styles: 'sbm-message-std'
        }, args);
        
        self.messages[args_.id] = true;
        
        var message = '<div id="' + args_.id + '" class="sbm-message ' + args_.styles + '">' + args_.message + '</div>';
        $('.sidebar-messages').append(message);
        if (self.after_show_message) {
            self.after_show_message(args_.id);
        }
        
        if (typeof(args_.hide_after) === 'number' && args_.hide_after > 0) {
            setTimeout(function() {
                self.hide({id: args_.id});
            }, args_.hide_after);
        }
        
        return args_.id;
    }
    
    // hide
    self.hide = function(args) {
        var args_ = $.extend(true, {}, args);
        
        var resultado = $('#' + args_.id).length > 0;
        
        for (id in self.messages) {
            if (id === args_.id) {
                delete self.messages[id];
            }
        }
        
        $('#' + args_.id).fadeOut('slow', function() {
            $('#' + args_.id).remove();
            
            delete self.messages[args_.id];
            
            if (self.after_hide_message) {
                self.after_hide_message(args_.id);
            }
        });
        
        return resultado;
    }
    
    // hide_all
    self.hide_all = function() {
        for (id in self.messages) {
            self.hide({id: id});
        }
    }
}
