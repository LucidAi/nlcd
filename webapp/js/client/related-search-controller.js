/**
 *
 *
 */

app.controller("NlcdRelatedSearchController", ["$scope", "$location", "$http", "NcldApiFactory",
    function ($scope, $location, $http, NcldApiFactory) {
        /**
        **/


        $scope.FindRelated = function() {


            if ($scope.query.storyOriginSegments.length == 0) {
                //TODO(zaytsev@usc.edu): Show Error Message
                alert("//TODO(zaytsev@usc.edu): Show Error Message");
                return;
            }

            NcldApiFactory.findRelated($scope.query.storyOriginSegments)
            .success(function(response) {

                console.log(response);

            }).
            error(function(data, status, headers, config) {

                //TODO(zaytsev@usc.edu): Show Error Message
                console.log(data);
                alert("//TODO(zaytsev@usc.edu): Show Error Message");

            });

        };






        /**
        **/
}]);