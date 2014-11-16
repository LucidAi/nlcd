/*
 * Author: Vova Zaytsev <zaytsev@usc.edu>
 */

"use strict";

app.factory("MdApi", ["$http", "$location",
    function($http, $location) {
                
        return {

            getTestGraph: function(graphId) {
                return $http({
                    url:    "/api/v1/get_test_graph",
                    method: "GET",
                    params: {
                        "graphId": graphId
                    }
                });
            }

        };


}]);
