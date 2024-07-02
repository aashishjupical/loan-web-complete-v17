odoo.define('appointment_calendar.CalendarViewJt', function (require) {
"use strict";
    var CalendarView = require('web.CalendarView');
    var viewRegistry = require('web.view_registry');
    var CalendarViewJt  = CalendarView.extend({
        get_color: function(key) {
                if (this.name = 'Exception Calendar')
                    if (this.color_map[key]) {
                        return this.color_map[key];
                    }
                var index = (((_.keys(this.color_map).length + 1) *
                    5) % 24) + 1;
                if (key == 'appointment') {
                    index = 'green';
                } else if (key == 'exception') {
                    index = 'red';
                }
                this.color_map[key] = index
                return index;
            },
    });
    viewRegistry.add('calendar', CalendarViewJt);
    return CalendarViewJt
});
