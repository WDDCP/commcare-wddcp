var url = hqImport('hqwebapp/js/urllib.js').reverse;


function UnderweightChildrenReportController($routeParams, maternalChildService) {
    var vm = this;
    vm.step = $routeParams.step;
    vm.steps = [
        {route: '/underweight_children/1', label: 'MapView'},
        {route: '/underweight_children/2', label: 'ChartView'},
    ];

    vm.mapData = {};
    vm.fills = {
        '0-25%': '#eef2ff',
        '26%-50%': '#bcd6e7',
        '51%-75%': '#6baed6',
        '76%-100%': '#2171b5',
        'defaultFill': '#eef2ff',
    };

    maternalChildService.getUnderweightChildrenData().then(function(response) {
        vm.mapData = response.data;
    });
}

UnderweightChildrenReportController.$inject = ['$routeParams', 'maternalChildService'];

window.angular.module('icdsApp').directive('underweightChildrenReport', function() {
    return {
        restrict: 'E',
        templateUrl: url('icds-ng-template', 'underweight-children-report.directive'),
        bindToController: true,
        controller: UnderweightChildrenReportController,
        controllerAs: '$ctrl',
    };
});
