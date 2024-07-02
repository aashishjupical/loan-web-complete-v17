//-*- coding: utf-8 -*-
odoo.define('jt_loan_project.button_click',[], function() {
    'use strict';

    var ajax = require('web.ajax');
    var BasicRenderer = require('web.BasicRenderer');
    var config = require('web.config');
    var core = require('web.core');
    var Dialog = require('web.Dialog');
    var dom = require('web.dom');
    var field_utils = require('web.field_utils');
    var Pager = require('web.Pager');
    var utils = require('web.utils');
    var ListRenderer = require('web.ListRenderer');
    var FormController = require('web.FormController');
    var BasicController = require('web.BasicController');
    var BasicView = require('web.BasicView');
    var core = require('web.core');
    var ListController = require('web.ListController');
    var qweb = core.qweb;
    var _t = core._t;
    var rpc = require('web.rpc');
    var get_url = "https://jsonip.com/?format=json"

    BasicController.include({
        _getActionMenuItems: function (state) {
        if (this.model.loadParams.modelName == 'project.task' && this.model.loadParams.res_id){
            var get_task_id = this.model.loadParams.res_id;
            var data
            data = $.getJSON(get_url, function(e) {
                var def2 = rpc.query({
                    'model': 'project.task',
                    'method': 'write',
                    'args': [[get_task_id], {
                        'loan_disbused_ip': e.ip,
                    }],
                });
            });
        }
        var res = this._super.apply(this, arguments);
        return res;
       },
    })

    FormController.include({

        _onButtonClicked: function (ev) {
            ev.stopPropagation();
                       
            if (ev.data.record.model == 'project.task'){
                var get_task_id = ev.data.record.res_id;

                var data

                data = $.getJSON(get_url, function(e) {
                    ev.data.record.current_ip = e.ip
                    var def2 = rpc.query({
                        'model': 'project.task',
                        'method': 'write',
                        'args': [[get_task_id], {
                            'current_ip': e.ip,
                        }],
                    });
                    return e.ip
                });    
            }

            if(ev.data.attrs.name=="action_done" || ev.data.attrs.name=="action_done_schedule_next")
            {
                if (ev.data.record.model == 'mail.activity' &&  ev.data.record.data.res_model == 'project.task')
                {
                    var get_task_id = ev.data.record.data.res_id;
                    var data

                    const params = {
                            model: 'ir.model.data',
                            method:'check_object_reference',
                            args: ['jt_loan_project','project_loan_stage_6'],
                        };
                    const def = rpc.query(params).then(function (result) {return Promise.resolve(result);});

                    var b = def.then((a) => {
                        if(ev.data.record.data.stage_id && ev.data.record.data.stage_id.data.id==a[1])
                        {
                            data = $.getJSON(get_url, function(e) {
                            var def2 = rpc.query({
                                'model': 'project.task',
                                'method': 'write',
                                'args': [[get_task_id], {
                                    'current_ip': e.ip,
                                    //'disbursment_ip':e.ip,
                                }],
                            });

                            
                            return e.ip
                            });
                        }         
                        });
                        
                }
            }
            var res = this._super.apply(this, arguments);
            return res;
        },
        
    });
});
