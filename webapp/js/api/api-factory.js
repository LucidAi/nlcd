/*
 * Author: Vova Zaytsev <zaytsev@usc.edu>
 */
"use strict";

app.factory("NcldApiFactory", ["$http", "$location",
    function($http, $location) {

        return {

            getTestGraph: function() {
                return $http({
                    url:    "/api/v1/get_test_graph/",
                    method: "GET"
                });
            }

        };


}]);