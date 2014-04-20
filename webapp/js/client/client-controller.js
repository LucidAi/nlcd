/**
 *
 *
 */

app.controller("NlcdClientController", ["$scope", "$location", "$http",
    function ($scope, $location, $http) {
        /**
        **/

        $scope.query = {
            storyOriginUrl:             "http://www.bbc.com/news/world-middle-east-25810934",
            storyOriginText:            "Some 174 passengers have been rescued, with another 266 still missing. Recovery operations may take two months, officials say, as the divers battle strong currents and poor visibility to reach the sunken vessel. \"Divers broke through the window of a passenger cabin... and pulled out three bodies,\" a coastguard official told the AFP news agency on Saturday. All three were wearing lifejackets, he added.",
            storyOriginSentences:       [],
            storyOriginQuoted:          [],
            storyOriginSegments:        []
        };

        $scope.related                = [];

        /**
        **/
}]);