"use strict";

app.factory("NcldApiFactory", ["$http", "$location",
    function($http, $location) {

        return {


            getArticle: function(url) {
                return $http({
                    url:    "/api/get_article/",
                    method: "GET",
                    params: {url: url}
                });
            },


            getSegments: function(text) {
                return $http({
                    url:    "/api/get_segments/",
                    method: "GET",
                    params: {text: text}
                });
            },

            findRelated: function(filteredSegments) {
                return $http({
                    url:    "/api/find_related/",
                    method: "GET",
                    params: {segments: JSON.stringify(filteredSegments) }
                });
            }

        };


}]);