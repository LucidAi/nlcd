/**
 *
 *
 */

app.controller("NlcdSegmentizerController", ["$scope", "$location", "$http", "NcldApiFactory",
    function ($scope, $location, $http, NcldApiFactory) {
        /**
        **/


        $scope.Segmentize = function() {


            if ($scope.query.storyOriginText.length == 0) {
                //TODO(zaytsev@usc.edu): Show Error Message
                alert("//TODO(zaytsev@usc.edu): Show Error Message");
                return;
            }

            NcldApiFactory.getSegments($scope.query.storyOriginText)
            .success(function(response) {

                var segments = response.data;

                $scope.query.storyOriginSentences = segments.sentences;
                $scope.query.storyOriginQuoted = segments.quoted;
                $scope.query.storyOriginSegments = segments.filtered;

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