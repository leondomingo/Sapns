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
        this.uploaded = false;
        set(this, 'url', "{{tg.url('/dashboard/docs/upload_file')}}");
        set(this, 'repo', '');
        set(this, 'show_button', true);
        set(this, 'onUpload', null);
        
        set(this, 'qtip', {});
        set(this.qtip, 'style', 'ui-tooltip-red ui-tooltip-rounded', this.qtip);
        set(this.qtip, 'position', {my: 'left center', at: 'right center'}, this.qtip);
    }

    // getFilename
    SapnsUploader.prototype.getFilename = function() {
        return this.file_name;
    }
    
    // setFilename
    SapnsUploader.prototype.setFilename = function(value) {
        this.file_name = value;
    }
    
    // getUploadedfile
    SapnsUploader.prototype.getUploadedfile = function() {
        return this.uploaded_file;
    }
    
    // setUploadedfile
    SapnsUploader.prototype.setUploadedfile = function(value) {
        this.uploaded_file = value;
    }

    // upload
    SapnsUploader.prototype.upload = function() {
        
        if ($('#upload_file_form_' + this.name + ' input[name=f]').val() == '') {
            return;
        }
        
        if (this.getRepo() == '') {
            this.showWarning($('#btn_upload_' + this.name), 
                    "{{_('There is no repo selected')}}");
            return;
        }
        
        $('#upload_file_form_' + this.name + ' input[name=id_repo]').val(this.repo);
        $('#upload_file_form_' + this.name).submit();
    }
    
    // getUploaded
    SapnsUploader.prototype.isUploaded = function() {
        return this.uploaded;
    }
    
    // setUploaded
    SapnsUploader.prototype.setUploaded = function(value) {
        this.uploaded = value;
    }
    
    // setRepo
    SapnsUploader.prototype.setRepo = function(repo) {
        this.repo = repo;
    }
    
    // getRepo
    SapnsUploader.prototype.getRepo = function() {
        return this.repo;
    }
    
    // showWarning
    SapnsUploader.prototype.showWarning = function(target, message) {
        try {
            target.qtip({
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
    
    // deleteFile
    SapnsUploader.prototype.deleteFile = function(remove_from_disk) {
        var self = this;
        var f = self.getFilename();
        if (f != '') {
            var sufix = self.name;
            
            var show_form = function() {
                $('#file_name_' + sufix).hide();
                $('#upload_file_form_' + sufix).show();
                self.setFilename('');
                self.setUploadedfile('');
            }
            
            if (remove_from_disk) {
                $.ajax({
                    url: "{{tg.url('/dashboard/docs/remove_file')}}",
                    data: {
                        file_name: f,
                        id_repo: self.getRepo(),
                    },
                    success: function(data) {
                        if (data.status) {
                            show_form();
                        }
                    }
                });
            }
            else {
                show_form();
            }
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
                '<div id="file_name_' + sufix + '" class="file_name">' +
                    '<div style="width: 80%; float: left;' + 
                        ' border: 1px solid lightgray;' + 
                        ' margin-top: 3px;">...</div>' +
                    '<button id="btn_delete_file_' + sufix + '">{{_("Delete")}}</button>' +                
                '</div>';
            
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
            
            if (sapnsUploader.getFilename() == '') {
                $('#file_name_' + sufix).css('display', 'none');
            }
            else {
                //console.log(sapnsUploader.getFilename());
                $('#upload_file_form_' + sufix).hide();
                $('#file_name_' + sufix).find('div').html(sapnsUploader.getUploadedfile()).show();                
            }
            
            $('#btn_delete_file_' + sufix).click(function() {
                // hides filename but does not remove the file from disk
                sapnsUploader.deleteFile();
            });
            
            // event handlers 
            var container = this;
            this.find('#upload_target_' + sufix).load(function() {
                var result = document.getElementById('upload_target_' + sufix).contentWindow.document.body.innerHTML;
                if (result != '') {
                    result = JSON.parse(result);
                    if (result.status) {
                        $('#upload_file_form_' + sufix).hide();
                        $('#file_' + sufix).val('');                        
                        $('#file_name_' + sufix).find('div').html(result.uploaded_file);
                        $('#file_name_' + sufix).show();
                        
                        sapnsUploader.uploaded_file = result.uploaded_file;
                        sapnsUploader.file_name = result.file_name;
                        
                        if (sapnsUploader.onUpload) {
                            sapnsUploader.onUpload();
                        }
                        
                        sapnsUploader.setUploaded(true);
                    }
                    else {
                        // result.status = false
                        sapnsUploader.showWarning($('#btn_upload_' + sufix), result.message);
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
            else if (arg1 == "deleteFile") {
                sapnsUploader.deleteFile(arg2);
            }
            else if (arg1 == "isUploaded") {
                return sapnsUploader.isUploaded();
            }
            // TODO: other sapnsUploader methods
        }
        
        return this;
    };
}) (jQuery);