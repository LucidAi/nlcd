/**
Author: Vova Zaytsev <zaytsev@usc.edu>
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

angular.module("ng").filter("cut", function () {
    return function (value, wordwise, max, tail) {
        if (!value) return "";

        max = parseInt(max, 10);
        if (!max) return value;
        if (value.length <= max) return value;

        value = value.substr(0, max);
        if (wordwise) {
            var lastspace = value.lastIndexOf(' ');
            if (lastspace != -1) {
                value = value.substr(0, lastspace);
            }
        }

        return value + (tail || " ...");
    };
});

String.prototype.toTitleCase = function () {
    return this.replace(/\w\S*/g, function(txt){return txt.charAt(0).toUpperCase() + txt.substr(1).toLowerCase();});
};