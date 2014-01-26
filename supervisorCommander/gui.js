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
    
    $scope.sendCommand = function (svc, cmd) {
        var process = svc.name + "/processCommand";
        if (cmd == 'restart') {
            $http.post(process, {cmd: 'stopProcess'})
            .then(function () {
                $scope.refreshState();
                $http.post(process, {cmd: 'startProcess'})
                .then($scope.refreshState, $scope.refreshState);
            }, $scope.refreshState);
        } else {
            $http.post(process, {cmd: cmd})
            .then($scope.refreshState, $scope.refreshState);
        }
    };

    $scope.currentlySwiping = {};
    var firstDragButton = null;
    $scope.mouseDown = function (event) {
        firstDragButton = event.target.textContent;
    };
    $scope.mouseUp = function () {
        firstDragButton = null;
        $scope.currentlySwiping = {}
    };
    $scope.swipe = function (rowIndex, svc, event) {
        var buttonLabel = event.target.textContent
        if (event.which == 1 && buttonLabel == firstDragButton) {
            if ($scope.currentlySwiping[buttonLabel] === undefined) {
                $scope.currentlySwiping[buttonLabel] = {};
            }
            if (!$scope.currentlySwiping[buttonLabel][rowIndex]) {
                setTimeout(function () { event.target.click(); }, 1);
                $scope.currentlySwiping[buttonLabel][rowIndex] = true;
            }
        }
    };
}
