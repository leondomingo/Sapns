$("{{selector}}").each(function() {
    
    // date format settings 
    var first_day = "{{tg.config.get('js.first_day', '1')}}";
    
    // "datepicker" setting 
    var date_fmt0 = "{{tg.config.get('js.date_format', 'mm/dd/yyyy')}}";
    
    // "format date library" setting 
    var date_fmt1 = "{{tg.config.get('js.date_format2', 'mm/dd/yyyy')}}";
    
    if (!$(this).attr('disabled')) {
        $(this).datepicker({
            firstDay: first_day,
            changeMonth: true,
            changeYear: true,
            showOn: 'button',
            autoSize: true,
            nextText: "{{_('Next')}}",
            prevText: "{{_('Prev')}}",
            dateFormat: date_fmt0,
            dayNames: ["{{_('Sunday')}}", "{{_('Monday')}}", "{{_('Tuesday')}}",
                       "{{_('Wednesday')}}", "{{_('Thursday')}}", "{{_('Friday')}}",
                       "{{_('Saturday')}}"],
            dayNamesMin: ["{{_('Su')}}", "{{_('Mo')}}", "{{_('Tu')}}", "{{_('We')}}",
                          "{{_('Th')}}", "{{_('Fr')}}", "{{_('Sa')}}"],
            monthNames: ["{{_('January')}}", "{{_('February')}}", "{{_('March')}}",
                         "{{_('April')}}", "{{_('May')}}", "{{_('June')}}",
                         "{{_('July')}}", "{{_('August')}}", "{{_('September')}}", 
                         "{{_('October')}}", "{{_('November')}}", "{{_('December')}}"],
            monthNamesShort: ["{{_('Jan')}}", "{{_('Feb')}}", "{{_('Mar')}}",
                              "{{_('Apr')}}", "{{_('May_')}}", "{{_('Jun')}}",
                              "{{_('Jul')}}", "{{_('Aug')}}", "{{_('Sep')}}",
                              "{{_('Oct')}}", "{{_('Nov')}}", "{{_('Dec')}}"],
       });
    }
    else {
        /*
        var d = $(this).val();
        var date_value = '';
        if (d) {
            date_value = new Date(d).format(date_fmt1);
        }
        */
        
        $(this).css('width', '85px'); //.val(date_value);
    }
});