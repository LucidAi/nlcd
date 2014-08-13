/**
 * Author: Vova Zaytsev <zaytsev@usc.edu>
 */

app.controller("NlcdClientController", ["$scope", "$location", "$sce", "NcldApiFactory",
    function ($scope, $location, $sce, NcldApiFactory) {
        /**
        **/

        $scope.central              = null;
        $scope.related              = [];
        $scope.meta                 = null;
        $scope.selection            = [];
        $scope.textSelection        = null;
        $scope.display = {

            // Tab 'ALL'
            relatedTabAllReversed:        false,
            relatedTabAllPredicate:       "inSelection",

            // Tab 'SELECTION'
            relatedTabSelectionReversed:  false,
            relatedTabSelectionPredicate: "pubDate",

            // Tab 'SOURCES'
            relatedTabSourcesReversed:    false,
            relatedTabSourcesPredicate:   "referenceCount",

            // Tab 'AUTHORS'
            relatedTabAuthorsReversed:    false,
            relatedTabAuthorsPredicate:   "referenceCount"

        };


        // Init bootstrap javascript
        $("#relatedTabs a").click(function (e) {
            e.preventDefault();
            $(this).tab("show");
        });
        $("#relatedTabs a:first").tab("show");


        NcldApiFactory.getTestGraph().success(function(data){
            $scope.sg = new StoryGraph(data.data);
            $scope.central = $scope.sg.getCentralNode();
            $scope.related = $scope.sg.getNodes();
            $scope.meta = data.data.meta;


            var distrPlaceId = "storyDistribution";
            var nwPlaceId = "storyNetwork";

            var distrWidth = document.getElementById(distrPlaceId).offsetWidth;
            var nwWidth = document.getElementById(nwPlaceId).offsetWidth;

            console.log(nwWidth);

            var height = 300;

            $scope.sg.drawDistribution(distrPlaceId, distrWidth, height);
            $scope.sg.drawNetwork(nwPlaceId, nwWidth, height);
        });


        //
        $scope.RelatedAllTabOrderBy = function(predicate) {
            if ($scope.display.relatedTabAllPredicate == predicate) {
                $scope.display.relatedTabAllReversed = !$scope.display.relatedTabAllReversed;
            }
            $scope.display.relatedTabAllPredicate = predicate;
        }


        //
        $scope.RelatedSelectionTabOrderBy = function(predicate) {
            if ($scope.display.relatedTabSelectionPredicate == predicate) {
                $scope.display.relatedTabSelectionReversed = !$scope.display.relatedTabSelectionReversed;
            }
            $scope.display.relatedTabSelectionPredicate = predicate;
        }


        //
        $scope.SetSelection = function(referencesList) {
            for (var i in $scope.selection) {
                $scope.selection[i].inSelection = null;
            };
            $scope.selection = [];
            for (var i in referencesList) {
                var refId = referencesList[i];
                var item = $scope.sg.getNode(refId);
                item.inSelection = true;
                $scope.selection.push(item);
            };
            $scope.sg.gfx.SetDistributionSelection(referencesList);
            $scope.sg.gfx.SetNetworkSelection(referencesList);
        };


        //
        $scope.TextSelection = function(chunk, referencesList) {
            if ($scope.textSelection) {
                $scope.textSelection.isSelected = false;
                if ($scope.textSelection.tagId == chunk.tagId) {
                    $scope.textSelection = null;
                    $scope.SetSelection([]);
                    return;
                }
            }
            $scope.textSelection = chunk;
            $scope.textSelection.isSelected = true;
            $scope.SetSelection(referencesList);
        };



}]);