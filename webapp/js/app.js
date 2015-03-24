/**
Author: Vova Zaytsev <zaytsev@usc.edu>
**/

"use strict";


var app = angular.module("LucidApp", ["ngRoute", "ngSanitize", "nvd3"])
    .config(["$routeProvider", "$locationProvider",
    function($routeProvider, $locationPrvioder) {

        $routeProvider.when("/", {
             templateUrl:   "/webapp/partials/track.html",
             controller:    "LucidTrackC"

        });

        $routeProvider.when("/search", {
             templateUrl:   "/webapp/partials/search.html",
             controller:    "LucidSearchC"

        });

        $routeProvider.otherwise({redirectTo: "/"});

}]);


angular.module("LucidApp").filter("cut", function () {
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


angular.module("LucidApp").filter("titleCase", function() {
    return function(input) {
        input = input || "";
        return input.replace(/\w\S*/g, function(txt){return txt.charAt(0).toUpperCase() + txt.substr(1).toLowerCase();});
    };
})


// angular.module("ng")
//     .filter("to_trusted", ["$sce", function($sce){
//         return function(text) {
//             return $sce.trustAsHtml(text);
//         };
//     }]);


String.prototype.ToTitleCase = function () {
   return this.replace(/\w\S*/g, function(txt){return txt.charAt(0).toUpperCase() + txt.substr(1).toLowerCase();});
};


String.prototype.CutStr =  function (wordwise, max, tail) {

   max = parseInt(max, 10);
   if (!max) return this;
   if (this.length <= max) return this;

   var value = this.substr(0, max);
   if (wordwise) {
       var lastspace = value.lastIndexOf(' ');
       if (lastspace != -1) {
           value = value.substr(0, lastspace);
       }
   }

   return value + (tail || " ...");
};
