/**
 * Author: Vova Zaytsev <zaytsev@usc.edu>
 */


app.controller("MdClientController", ["$scope", "$location", "MdApi",
    function ($scope, $location, MdApi) {

        // Get node ID from URL parameters
        var graphId = $location.search().g;
        if (!graphId) graphId = "1_1"; // Default

        $scope.meta         = null;       // TODO: remove this
        $scope.central      = null;       // Central Node
        $scope.filterQuery  = "";

        //
        var storyIndex;
        var storyApi;
        var layout = new StoryLayout();

        MdApi.getTestGraph(graphId).success(function(response) {

            var data        = response.data;                    // Unpack data
            storyApi    = new StoryApi(data);               // Create API to story data
            storyIndex  = new StoryIndex(data, storyApi);   // Index story entities
            var centralNode = storyApi.GetCentralNode();        // main article
            console.log(["data", data]);

            // Index authors
            storyIndex.IndexItems(storyApi.GetNodes(), "author", function(node) {
                var entities = [];
                for (var i in node.authors) {
                    var entityName = node.authors[i];
                    var entity = new Entity({
                        "unique":   entityName,
                        "name":     entityName,
                        "extra":    {},
                        "central":  node.refId == centralNode.refId,
                        "ref": {
                            "article": ["article_" + String(node.refId)],
                            "source":  [].concat(node.sources),
                            "date":    []
                        }
                    });
                    entities.push(entity);
                }
                return entities;
            });


            // Index sources
            storyIndex.IndexItems(storyApi.GetNodes(), "source", function(node) {
                var entities = [];
                for (var i in node.sources) {
                    var entityName = node.sources[i];
                    var entity = new Entity({
                        "unique":   entityName,
                        "name":     entityName,
                        "extra":    {},
                        "central":  node.refId == centralNode.refId,
                        "ref": {
                            "article": [],
                            "source":  [],
                            "date":    []
                        }
                    });
                    entities.push(entity);
                }
                return entities;
            });

            // Index articles
            storyIndex.IndexItems(storyApi.GetNodes(), "article", function(node) {
                return [new Entity({
                    "unique":   "article_" + String(node.refId),
                    "name":     node.title,
                    "extra":    node,
                    "central":  node.refId == centralNode.refId,
                    "ref": {
                        "article": [],
                        "source":  [],
                        "date":    []
                    }
                })];
            });

            // Index article body fragments
            var fragmentCounter = 0;
            storyIndex.IndexItems(data.meta.markup.body, "bodyFragment", function(markupItem) {
                var entities = [];
                for(var i in markupItem.taggedText) {
                    var fragment = markupItem.taggedText[i];
                    var articleReferences = [];
                    var authorReferences = [].concat(centralNode.authors);
                    for (var j in fragment.references) {
                        var refId = fragment.references[j];
                        var article = storyApi.GetNode(refId);
                        for (var k in article.authors) {
                            authorReferences.push(article.authors[k]);
                        }
                        articleReferences.push("article_" + String(refId));
                    }
                    entities.push(new Entity({
                        "unique":   "fragment_" + String(++fragmentCounter),
                        "name":     fragment.text,
                        "extra":    {
                            "tagged": fragment.tagged,
                            "paragraphEnd": false,
                        },
                        "central":  true,
                        "ref": {
                            "article": articleReferences,
                            "author": authorReferences,
                            "source":  [],
                            "date":    []
                        }
                    }));
                };
                entities.push(new Entity({
                    "unique":   "fragment_" + String(++fragmentCounter),
                    "name":     "",
                    "extra":    {
                        "tagged": false,
                        "paragraphEnd": true
                    },
                    "central":  true
                }));
                return entities;
            });

            // Group markup by paragraphs
            storyIndex.IndexReferences();
            var bodyFragments = [[]];
            var j = 0;
            for(var i in storyIndex.groups.bodyFragment) {
                var fragment = storyIndex.groups.bodyFragment[i];
                if (fragment.extra.paragraphEnd) {
                    bodyFragments.push([]);
                    j++;
                } else {
                    bodyFragments[j].push(fragment);
                }
            }

            $scope.meta = data.meta;
            $scope.bodyFragments = bodyFragments;
            $scope.authors = storyIndex.Group("author");
            $scope.central = centralNode;

            console.log($scope.authors);

            /**

            var distrPlaceId = "storyDistribution";
            var nwPlaceId = "storyNetwork";
            var distrWidth = document.getElementById(distrPlaceId).offsetWidth;
            var nwWidth = document.getElementById(nwPlaceId).offsetWidth;
            var height = 300;

            $scope.sg.drawDistribution(distrPlaceId, distrWidth, height);
            $scope.sg.drawNetwork(nwPlaceId, nwWidth, height);
            $scope.dateDistr = $scope.sg.distr.dateDistr;

            **/

        });


        //

        $scope.SelectEntity = function(entityId) {
            var selected = storyIndex.SelectItem(entityId);
        }


        $scope.tableAPI = layout.tableAPI;


        return;


        // //
        // $scope.RelatedAllTabOrderBy = function(predicate) {
        //     if ($scope.display.relatedTabAllPredicate == predicate) {
        //         $scope.display.relatedTabAllReversed = !$scope.display.relatedTabAllReversed;
        //     }
        //     $scope.display.relatedTabAllPredicate = predicate;
        // }


        // //
        // $scope.RelatedDatesTabOrderBy = function(predicate) {
        //     if ($scope.display.relatedTabDatesPredicate == predicate) {
        //         $scope.display.relatedTabDatesReversed = !$scope.display.relatedTabDatesReversed;
        //     }
        //     $scope.display.relatedTabDatesPredicate = predicate;
        // }


        // //
        // $scope.SetSelection = function(referencesList) {

        //     for (var i in $scope.selection) {
        //         $scope.selection[i].inSelection = null;
        //     };
        //     $scope.selection = [];
        //     for (var i in referencesList) {
        //         var refId = referencesList[i];
        //         var item = $scope.sg.getNode(refId);
        //         item.inSelection = true;
        //         $scope.selection.push(item);
        //     };

        //     if (referencesList !== 0) {
        //         $scope.sg.gfx.SetDistributionSelection(referencesList);
        //         $scope.sg.gfx.SetNetworkSelection(referencesList);
        //     }

        // };


        // //
        // $scope.TextSelection = function(chunk, referencesList) {

        //     $scope.SetSelection(0);

        //     if ($scope.selectedDateEntry) {
        //         $scope.SelectDate($scope.selectedDateEntry);
        //     }

        //     if ($scope.textSelection) {
        //         $scope.textSelection.isSelected = false;
        //         if ($scope.textSelection.tagId == chunk.tagId) {
        //             $scope.textSelection = null;
        //             return;
        //         }
        //     }
        //     $scope.textSelection = chunk;
        //     $scope.textSelection.isSelected = true;
        //     $scope.SetSelection(referencesList);

        // };


        // //
        // $scope.SelectDate = function(dateEntry) {

        //     if ($scope.textSelection) {
        //         $scope.TextSelection($scope.textSelection, []);
        //     }

        //     $scope.SetSelection(0);

        //     if ($scope.selectedDateEntry == dateEntry) {

        //         $scope.selectedDateEntry.selected = false;
        //         $scope.selectedDateEntry = null;

        //     } else {

        //         $scope.SetSelection(dateEntry.selection);

        //         if ($scope.selectedDateEntry)
        //             $scope.selectedDateEntry.selected = false;

        //         $scope.selectedDateEntry = dateEntry;
        //         $scope.selectedDateEntry.selected = true;

        //     }


        // };


        // //
        // $scope.toolPopoverContent = function(node) {

        //     var authors = node.authors.join(", ").toTitleCase();
        //     var source = "";
        //     var len = 10000;
        //     for (var i in node.sources) {
        //         if (node.sources[i].length < len) {
        //             source = node.sources[i];
        //             len = node.sources[i].length;
        //         }
        //     }

        //     return "<ul><li>authror: "
        //            + authors
        //            + "</li><li>source: "
        //            + source
        //            + "</li></ul><p><small>"
        //            + String.prototype.CutStr(node.body, true, 256, "...")
        //            + "</small><p>";
        // }

}]);
