/**
**/

"use strict";

var app = angular.module("NlcdClient", ["ngRoute"])
    .config(["$routeProvider", "$locationProvider",
    function($routeProvider, $locationProvider) {
        $routeProvider.when("/", {
             templateUrl: "/webapp/partials/nlcd-client/client.html",
             controller: "NlcdClientController"
        });
        $routeProvider.otherwise({redirectTo: "/"});
}]);