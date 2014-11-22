/**
 * Author: Vova Zaytsev <zaytsev@usc.edu>
 */


app.controller("MdClientController", ["$scope", "$location", "MdApi",
    function ($scope, $location, MdApi) {

        // Get node ID from URL parameters.
        var graphId = $location.search().g;
        if (!graphId) graphId = "3"; // Default

        $scope.meta         = null;       // TODO: remove this
        $scope.central      = null;       // Central Node
        $scope.filterQuery  = "";

        //
        var storyIndex;
        var storyApi;
        var storyTimespan;
        var layout;

        MdApi.getTestGraph(graphId).success(function(response) {

            var data        = response.data;                                    // unpack data
            storyApi        = new StoryApi(data);                               // create API to story data
            storyIndex      = new StoryIndex(data, storyApi);                   // index story entities
            var centralNode = storyApi.GetCentralNode();                        // main article

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
                            "article": ["article_" + String(node.refId)],
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
                        "article": ["article_" + String(node.refId)],
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
                    var sourceReferences = [];
                    for (var j in fragment.references) {
                        var refId = fragment.references[j];
                        var article = storyApi.GetNode(refId);
                        for (var k in article.authors) {
                            authorReferences.push(article.authors[k]);
                        }
                        for (var k in article.sources) {
                            sourceReferences.push(article.sources[k]);
                        }
                        articleReferences.push("article_" + String(refId));
                    }
                    entities.push(new Entity({
                        "unique":   "fragment_" + String(++fragmentCounter),
                        "name":     fragment.text,
                        "extra":    {
                            "tagged": fragment.tagged,
                            "paragraphEnd": false
                        },
                        "central":  true,
                        "ref": {
                            "article":  articleReferences,
                            "author":   authorReferences,
                            "source":   sourceReferences,
                            "date":     []
                        }
                    }));
                }
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

            $scope.meta             = data.meta;
            $scope.bodyFragments    = bodyFragments;
            $scope.authors          = storyIndex.Group("author");
            $scope.articles         = storyIndex.Group("article");
            $scope.sources          = storyIndex.Group("source");
            $scope.central          = centralNode;


            $scope.$evalAsync(function() {

                storyTimespan   = new StoryTimespan(data, storyApi, storyIndex, $scope);

                layout = new StoryLayout();
                layout.AddComponent(storyTimespan, "TimespanComponent",
                    function (wW, pW) {
                        return pW;
                    },
                    function (wH, pH) {
                        return pH;
                    });
                layout.ResizeContainers();
                layout.RenderComponents();
                $scope.tableAPI = layout.tableAPI;
            });


            $scope.SelectEntity = function(entityId) {
                storyIndex.SelectItem(entityId);
            };

        });


}]);
