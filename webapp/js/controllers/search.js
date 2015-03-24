/**
 * Author: Vova Zaytsev <zaytsev@usc.edu>
 */


app.controller("LucidSearchC", ["$scope", "$rootScope", "$location", "LucidAPIProvider",
    function ($scope, $rootScope, $location, LucidAPIProvider) {

        $scope.compareAgainstEngine  = "";
        $scope.textQuery             = "Vova Zaytsev";

        LucidAPIProvider.tpasEngineList().success(function(response) {
            $scope.engines = response.data.engines;
            $scope.SetEngine("husky.tpas.GoogleAPI");
        });

        $scope.SetEngine = function(eId) {
            for (var i in $scope.engines) {
                $scope.engines[i].selected = eId != $scope.engines[i].eId;
            }
            $scope.compareAgainstEngine = eId;
        }

        $scope.RunEngines = function() {
            var selected = [];
            for (var i in $scope.engines)
                if ($scope.engines[i].selected)
                    selected.push($scope.engines[i].eId);

            console.log({
                "selected": selected,
                "compareAgainstEngine": $scope.compareAgainstEngine
            });

            LucidAPIProvider.tpasEngineCall($scope.textQuery, $scope.compareAgainstEngine, selected);

        }

}]);
