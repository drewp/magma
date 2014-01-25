angular
    .module('app', ['ngRoute'])
    .config(function($routeProvider, $locationProvider) {
        $routeProvider.when('/:serviceName/', {
            templateUrl: 'service.html',
            controller: ServiceCntl,
        });
        $routeProvider.when('/', {
            templateUrl: 'allservices.html',
            controller: AllServicesCntl,
        });
        $locationProvider.html5Mode(true);
    });
 
function ServiceCntl($scope, $route, $routeParams, $location, $http) {

    $scope.name = $routeParams.serviceName;
    document.title = "sup > " + $scope.name;
    
    $http.get("config")
        .success(function(data, status, headers, config) {
            $scope.config = data;
        }).
        error(function(data, status, headers, config) {

        });
    
    $scope.sendCommand = function (cmd) {
        $scope.lastResult = "...";
        $http.post("processCommand", {cmd: cmd})
            .success(function(data, status, headers, config) {
                $scope.lastResult = data;
                refreshStatus();
            }).
            error(function(data, status, headers, config) {
                $scope.lastResult = data;
                refreshStatus();
            });
    }
    function refreshStatus() {
        window.requestAnimationFrame(function () {
            $http.get("status")
                .success(function(data, status, headers, config) {
                    $scope.host = data.host;
                    $scope.processInfo = data.processInfo;
                    $scope.log = data.log;
                    $scope.dataTime = new Date();
                }).
                error(function(data, status, headers, config) {
                    $scope.error = data;
                });
        });
    }
    var refreshLoop = setInterval(refreshStatus, 2000);
    $scope.$on('$routeChangeStart', function (next, current) {
        clearInterval(refreshLoop);
    });
}

function AllServicesCntl($scope, $route, $routeParams, $location, $http) {
    $scope.name = $routeParams.serviceName;
    $scope.refreshState = function () {
        $http.get("services")
            .success(function(data, status, headers, config) {
                $scope.host = data.host;
                $scope.services = data.services;
            });
    };
    $scope.refreshState();

}
