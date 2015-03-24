/*
 * Author: Vova Zaytsev <zaytsev@usc.edu>
 */

"use strict";

app.factory("LucidAPIProvider", ["$http", "$location",
    function($http, $location) {

        return {

            //
            getTestGraph: function(graphId) {
                return $http({
                    url:    "/api/v1/get_test_graph",
                    method: "GET",
                    params: {
                        "graphId": graphId
                    }
                });
            },

            //
            tpasEngineList: function() {
                return $http({
                    url:    "/api/v1/tpas_engine_list",
                    method: "GET",
                    params: {

                    }
                });
            },

            //
            tpasEngineCall: function(queryText, controlEngine, treatmentEngines) {
                return $http({
                    url:    "/api/v1/tpas_engine_call",
                    method: "GET",
                    params: {
                        "queryText"         : queryText,
                        "controlEngine"     : controlEngine,
                        "treatmentEngines"  : treatmentEngines.join(",")
                    }
                });
            }

        };


}]);
