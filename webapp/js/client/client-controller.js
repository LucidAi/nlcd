/**
 * Author: Vova Zaytsev <zaytsev@usc.edu>
 */

app.controller("NlcdClientController", ["$scope", "$location", "NcldApiFactory",
    function ($scope, $location, NcldApiFactory) {
        /**
        **/

        $scope.query = {
            storyOriginUrl:         undefined,
            storyOriginText:        undefined,
            storyOriginSentences:   undefined,
            storyOriginQuoted:      undefined,
            storyOriginSegments:    undefined,
        };

        $scope.related              = [];
        $scope.graph                = null;


        NcldApiFactory.getTestGraph().success(function(data){

            var width = document.getElementById("StoryGraphHeader").offsetWidth;

            $scope.graph = new StoryGraph(data.data);
            $scope.graph.renderDistribution("#StoryLifespanGraph", width, 300);


        });


}]);