/**
 * Author: Vova Zaytsev <zaytsev@usc.edu>
 */


app.controller("MdClientController", ["$scope", "$rootScope", "$location", "MdApi",
    function ($scope, $rootScope, $location, MdApi) {

        // Get node ID from URL parameters.
        var graphId = $location.search().g;
        if (!graphId) graphId = "1_0"; // Default

        $scope.meta         = null;       // TODO: remove this
        $scope.central      = null;       // Central Node
        $scope.filterQuery  = "";

        //
        var storyIndex;
        var storyApi;
        var storyTimespan;
        var storyHeatmap;
        var layout;

        MdApi.getTestGraph(graphId).success(function(response) {

            var data        = response.data;                                    // unpack data
            storyApi        = new StoryApi(data);                               // create API to story data
            storyIndex      = new StoryIndex(data, storyApi);                   // index story entities
            var centralNode = storyApi.GetCentralNode();                        // main article
            
            /*
             * Index Entity Graph.
             * Entities: authors, sources, articles, body fragments and dates
             * Each entity is a vertex indexed by group ("author", "source", etc..) and local ID (unique inside group).
             *  + Author ID = auhor name
             *  + 
             *  +
             *  +
             */
            
            //
            // Index Authors
            //
            storyIndex.IndexItems(storyApi.GetNodes(), "author", function(node) {
                var entities = [];
                var dateRef = node.pubDate ? ["date_" + node.pubDate] : [];
                for (var i in node.authors) {
                    var entityName = node.authors[i];
                    var entity = new Entity({
                        "unique"    : entityName,
                        "name"      : entityName,
                        "extra"     : {},
                        "central"   : node.refId == centralNode.refId,
                        "ref"       : {
                            "article"   : ["article_" + String(node.refId)],
                            "source"    : [].concat(node.sources),
                            "date"      : dateRef
                        }
                    });
                    entities.push(entity);
                }
                return entities;
            });


            //
            // Index Sources
            //
            storyIndex.IndexItems(storyApi.GetNodes(), "source", function(node) {
                var entities = [];
                var dateRef = node.pubDate ? ["date_" + node.pubDate] : [];
                for (var i in node.sources) {
                    var entityName = node.sources[i];
                    var entity = new Entity({
                        "unique"    : entityName,
                        "name"      : entityName,
                        "extra"     : {},
                        "central"   : node.refId == centralNode.refId,
                        "ref"       : {
                            "article"   : ["article_" + String(node.refId)],
                            "source"    : [],
                            "date"      : dateRef,
                        }
                    });
                    entities.push(entity);
                }
                return entities;
            });
            
            
            //
            // Index articles
            //
            storyIndex.IndexItems(storyApi.GetNodes(), "article", function(node) {
                var dateRef = node.pubDate ? ["date_" + node.pubDate] : [];
                return [new Entity({
                    "unique"    : "article_" + String(node.refId),
                    "name"      : node.title,
                    "extra"     : node,
                    "central"   : node.refId == centralNode.refId,
                    "ref"       : {
                        "article"   : [],
                        "source"    : [],
                        "date"      : dateRef
                    }
                })];
            });


            //
            // Index Dates
            //
            var dates = storyApi.dateAPI.dates;
            storyIndex.IndexItems(dates, "date", function(date) {
                var entities = [new Entity({
                    "unique"    : "date_" + date,
                    "name"      : date,
                    "central"   : false,
                    "extra"     : {
                        "freq"      : storyApi.dateAPI.datesDistr[date],
                        "pubDate"   : date
                    },
                    "ref"       : {
                        "article"   : [],
                        "source"    : [],
                        "date"      : []
                    }
                })];
                return entities;
            });


            //
            // Index Body Fragments
            //
            var fragmentCounter = 0;
            storyIndex.IndexItems(data.meta.markup.body, "bodyFragment", function(markupItem) {

                var entities = [];

                for(var i in markupItem.taggedText) {

                    var fragment          = markupItem.taggedText[i];
                    var articleReferences = [];
                    var authorReferences  = [].concat(centralNode.authors);
                    var sourceReferences  = [];
                    var dateReferences    = [];

                    for (var j in fragment.references) {
                        var refId   = fragment.references[j];
                        var article = storyApi.GetNode(refId);
                        for (var k in article.authors) authorReferences.push(article.authors[k]);
                        for (var k in article.sources) sourceReferences.push(article.sources[k]);
                        if (article.pubDate) dateReferences.push("date_" + article.pubDate)
                        articleReferences.push("article_" + String(refId));
                    }

                    entities.push(new Entity({
                        "unique"    : "fragment_" + String(++fragmentCounter),
                        "name"      : fragment.text,
                        "central"   : true,
                        "extra"     : {
                            "tagged"        : fragment.tagged,
                            "paragraphEnd"  : false
                        },
                        "ref"       : {
                            "article"       : articleReferences,
                            "author"        : authorReferences,
                            "source"        : sourceReferences,
                            "date"          : dateReferences
                        }
                    }));
                }
                entities.push(new Entity({
                    "unique"        : "fragment_" + String(++fragmentCounter),
                    "name"          : "",
                    "central"       : true,
                    "extra"         : {
                        "tagged"            : false,
                        "paragraphEnd"      : true
                    }
                }));
                return entities;
            });

            
            ///
            storyIndex.IndexReferences();
            
            //
            // Group Markup Entities by paragraphs
            //
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
                storyHeatmap    = new StoryHeatmap(data, storyApi, storyIndex, $scope);

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
            
            
            setTimeout(function(){

                $rootScope.$chartScope.api.getScope().chart.dispatch.on("brush", function(e) {
                    var extent = e.extent;
                    console.log(extent);
                });

            });

        });

}]);
