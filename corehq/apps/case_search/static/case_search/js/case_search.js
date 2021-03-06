/* globals hqDefine, ko, $ */

hqDefine('case_search/js/case_search.js', function(){
    'use strict';
    return function(case_data_url){
        var self = this;
        self.type = ko.observable();
        self.owner_id = ko.observable();
        self.customQueryAddition = ko.observable();
        self.results = ko.observableArray();
        self.case_data_url = case_data_url;
        self.parameters = ko.observableArray([{
            key: "",
            value: "",
            clause: "must",
            fuzzy: false,
            regex: '',
        }]);

        self.addParameter = function(){
            self.parameters.push({
                key: "",
                value: "",
                clause: "must",
                fuzzy: false,
                regex: '',
            });
        };
        self.removeParameter = function(){
            self.parameters.remove(this);
        };

        self.submit = function(){
            self.results([]);
            $.post({
                url: window.location.href,
                data: {q: JSON.stringify({
                    type: self.type(),
                    owner_id: self.owner_id(),
                    parameters: self.parameters(),
                    customQueryAddition: self.customQueryAddition()}
                )},
                success: function(data){
                    self.results(data.values);
                },
            });
        };
    };
});
