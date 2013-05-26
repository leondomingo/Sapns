var sapnsLoader = (function(global_settings) {
    var self = this;

    if (global_settings === undefined) {
        global_settings = {};
    }

    var PREFIX = 'sapns-loader-';

    function remove_version(url) {
        return url.replace(/\?v=[\d\.]+$/, '', 'g');
    }

    function save_to_storage(settings, text) {
        settings.text = text;

        localStorage.setItem(PREFIX + settings.url, JSON.stringify(settings));

        var url_ = remove_version(settings.url), items = [];
        for (var i=0, l=localStorage.length; i<l; i++) {
            var k = localStorage.key(i).replace(PREFIX, '');
            if (remove_version(k) === url_ && k !== settings.url) {
                items.push(k);
            }
        }

        for (var i=0, l=items.length; i<l; i++) {
            localStorage.removeItem(PREFIX + items[i]);
        }
    }

    function injectScript(id, text) {
        var script = document.getElementById(id);
        if (!script) {
            var head = document.head || document.getElementsByTagName('head')[0],
                script = document.createElement('script');

            script.async = true;
            script.id = id;
            script.text = text;
            head.appendChild(script);
        }
        else {
            if (global_settings.log) {
                console.log(id + ' already exists in the document');
            }
        }
    }

    self.load = function() {
        function _load(settings, callback) {
            var item = null;
            if (window.localStorage) {
                item = localStorage.getItem(PREFIX + settings.url);
            }

            if (item === null) {
                if (global_settings.log) {
                    console.log('Loading from ' + settings.url);
                }

                if (settings.json === true) {
                    $.ajax({
                        url: settings.url,
                        cache: false,
                        async: false,
                        success: function(res) {
                            if (res.status) {
                                save_to_storage(settings, res.content);

                                if (!global_settings.no_injection) {
                                    injectScript(settings.url, res.content);
                                }

                                if (callback) {
                                    callback();
                                }
                            }
                        }
                    });
                }
                else {
                    $.ajax({
                        url: settings.url,
                        cache: false,
                        async: false,
                        success: function(content) {
                            save_to_storage(settings, content);

                            if (!global_settings.no_injection) {
                                injectScript(settings.url, content);
                            }

                            if (callback) {
                                callback();
                            }
                        }
                    });
                }
            }
            else {
                if (global_settings.log) {
                    console.log('Reading from localStorage ' + settings.url)
                }

                item = JSON.parse(item);

                if (!global_settings.no_injection) {
                    injectScript(settings.url, item.text);
                }

                if (callback) {
                    callback();
                }
            }
        }

        var n = arguments.length;
        for (var i=0, l=arguments.length; i<l; i++) {
            _load(arguments[i], function() {
                n--;
                if (n === 0 && global_settings.then) {
                    global_settings.then();
                }
            });
        }
    }

    self.clear = function() {
        var r = new RegExp('^'+PREFIX);
        for (var i=localStorage.length-1; i>=0; i--) {
            var k = localStorage.key(i);
            if (r.test(k)) {
                localStorage.removeItem(k);
            }

        }
    }

    self.refresh = function() {
        var r = new RegExp('^'+PREFIX);
        for (var i=localStorage.length-1; i>=0; i--) {
            var k = localStorage.key(i);
            if (r.test(k)) {
                var settings = JSON.parse(localStorage.getItem(k));
                if (settings.json === true) {
                    $.ajax({
                        url: settings.url,
                        cache: false,
                        success: function(res) {
                            if (res.status) {
                                save_to_storage(settings, res.content);
                            }
                        }
                    });
                }
                else {
                    $.ajax({
                        url: settings.url,
                        cache: false,
                        success: function(content) {
                            save_to_storage(settings, content);
                        }
                    });
                }
            }

        }
    }
});
