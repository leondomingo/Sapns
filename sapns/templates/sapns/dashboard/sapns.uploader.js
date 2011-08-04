/* Sapns uploader */

(function($) {

    // SapnsUploader (constructor)
    function SapnsUploader(settings) {
        
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
        
        set(this, 'name', Math.floor(Math.random()*999999));
        set(this, 'file_name', '');
        set(this, 'uploaded_file', '');
        set(this, 'url', "{{tg.url('/dashboard/docs/upload_file')}}");
        set(this, 'repo', '');
        set(this, 'show_button', true);
        set(this, 'onChange', null);
        
        set(this, 'qtip', {});
        set(this.qtip, 'style', 'ui-tooltip-red ui-tooltip-rounded', this.qtip);
        set(this.qtip, 'position', {my: 'left center', at: 'right center'}, this.qtip);
    }

    // getFilename
    SapnsUploader.prototype.getFilename = function() {
        return this.file_name;
    }
    
    // getUploadedfile
    SapnsUploader.prototype.getUploadedfile = function() {
        return this.uploaded_file;
    }

    // upload
    SapnsUploader.prototype.upload = function() {
        
        if ($('#upload_file_form_' + this.name + ' input[name=f]').val() == '') {
            return;
        }
        
        $('#upload_file_form_' + this.name + ' input[name=id_repo]').val(this.repo);
        $('#upload_file_form_' + this.name).submit();
    }
    
    // setRepo
    SapnsUploader.prototype.setRepo = function(repo) {
        this.repo = repo;
    }
    
    // getRepo
    SapnsUploader.prototype.getRepo = function() {
        return this.repo;
    }
    
    SapnsUploader.prototype.showWarning = function(container, message) {
        try {
            var sufix = this.name;
            //alert(JSON.stringify(sapnsUploader.qtip));
            container.find('#btn_upload_' + sufix).qtip({
                content: {text: message},
                show: {
                    target: false,
                    ready: true
                },
                position: this.qtip.position,
                hide: 'unfocus',
                style: this.qtip.style
            });
        }
        catch(e) {
            // qtip2 is not defined
            alert(e);
            alert(message);
        }
    }
    
    $.fn.sapnsUploader = function(arg1, arg2) {
        
        if (arg1 == undefined) {
            arg1 = {};
        }
        
        if (typeof(arg1) == "object") {
            
            var sapnsUploader = new SapnsUploader(arg1);
            
            var url = sapnsUploader.url;
            var sufix = sapnsUploader.name;
            
            var content = 
                '<div id="file_name_' + sufix + '" style="display: none;">&nbsp;</div>';
                
            content += 
                '<form id="upload_file_form_' + sufix + '" method="post" action="' + url + '"' + 
                ' target="upload_target_' + sufix + '" enctype="multipart/form-data">' +
                    ' <input type="hidden" name="id_repo" value="">' +
                    ' <input id="file_' + sufix + '" type="file" name="f">';
                    
            if (sapnsUploader.show_button) {
                content += ' <input id="btn_upload_' + sufix + '" type="button" value="Upload">';
            }
                    
            content += ' </form>';
            
            content += 
                '<iframe id="upload_target_' + sufix + 
                '" name="upload_target_' + sufix + '" style="display: none;"></iframe>';
            
            this.append(content);
            
            // event handlers 
            var container = this;
            this.find('#upload_target_' + sufix).load(function() {
                var result = document.getElementById('upload_target_' + sufix).contentWindow.document.body.innerHTML;
                if (result != '') {
                    result = JSON.parse(result);
                    if (result.status) {
                        $('#upload_file_form_' + sufix).hide();
                        $('#file_' + sufix).val('');                        
                        $('#file_name_' + sufix).addClass('file_name').html(result.uploaded_file).show();
                        
                        sapnsUploader.uploaded_file = result.uploaded_file;
                        sapnsUploader.file_name = result.file_name;
                    }
                    else {
                        // result.status = false
                        sapnsUploader.showWarning(container, result.message);
                    }
                }
            });
            
            this.find('#btn_upload_' + sufix).click(function() {
                sapnsUploader.upload();
            });
            
            this.data('sapnsUploader', sapnsUploader);
        }
        else if (typeof(arg1) == "string") {
            
            var sapnsUploader = this.data('sapnsUploader');
            
            // getFileName()
            // var file_name = $(element).sapnsUploader("getFilename");
            if (arg1 == "getFilename") {
                return sapnsUploader.getFilename();
            }
            // getUploadedfile()
            else if (arg1 == "getUploadedfile") {
                return sapnsUploader.getUploadedfile();
            }
            // setRepo(arg2)
            // $(element).sapnsUploader('setRepo', 1);
            else if (arg1 == "setRepo") {
                sapnsUploader.setRepo(arg2);
            }
            else if (arg1 == "getRepo") {
                return sapnsUploader.getRepo();
            }
            // TODO: other sapnsUploader methods
        }
        
        return this;
    };
}) (jQuery);