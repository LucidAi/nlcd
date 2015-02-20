/**
 * Author: Vova Zaytsev <zaytsev@usc.edu>
 */


app.controller("LucidAISearchC", ["$scope", "$rootScope", "$location", "LucidAIApi",
    function ($scope, $rootScope, $location, LucidAIApi) {

        // Get node ID from URL parameters.
        var queryText = $location.search().qT;

        LucidAIApi.tpas(queryText).success(function(response) {

        });

}]);
