/**
 * Author: Vova Zaytsev <zaytsev@usc.edu>
 */


app.controller("LucidTrackC", ["$scope", "$rootScope", "$location", "LucidAPIProvider",
    function ($scope, $rootScope, $location, LucidAPIProvider) {

        // Get node ID from URL parameters.
        var graphId = $location.search().g;  //
        if (!graphId) graphId = "1";         // Default

        $scope.meta         = null;          // TODO: remove this
        $scope.central      = null;          // Central Node
        $scope.filterQuery  = "";            //

        //
        var storyIndex;
        var storyApi;
        var storyTimespan;
        var storyHeatmap;
        var layout;

        LucidAPIProvider.getTestGraph(graphId).success(function(response) {

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
                            "author"    : []
                        }
                    });
                    entities.push(entity);
                }
                return entities;
            });


            //
            // Index Articles
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
            var taggedCounter   = 0;
            storyIndex.IndexItems(data.meta.markup.body, "bodyFragment", function(markupItem) {

                var entities = [];

                for(var i in markupItem.taggedText) {

                    var fragment          = markupItem.taggedText[i];
                    var articleReferences = [];
                    var authorReferences  = [].concat(centralNode.authors);
                    var sourceReferences  = [];
                    var dateReferences    = [];
                    if (fragment.tagged)  ++taggedCounter;

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
                            "taggedCounter" : taggedCounter,
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


            //
            // Set pop-overs
            //
            storyIndex.SetPopOver("article", function(entity) {

                var pubDate = entity.extra.pubDate;
                var authors = entity.extra.authors;
                var sources = entity.extra.sources;
                var text    = "";
                text += "<br/>";
                text += "<blockquote class='MdSerif'>" + entity.extra.text.CutStr(true, 150, " ...");
                text += "<br/><br/>" + "Click to <a><strong class='glyphicon glyphicon-link'></strong></a> to open full text." + "</blockquote>"
                text += "<ul>";
                if (pubDate) {
                    pubDate = storyApi.dateAPI.Str2Date(pubDate);
                    text += "<li> Published on " + layout.Date2Str(pubDate) + "</li>";
                }
                if (authors.length > 0) {
                    authors = authors.map(function(a){return a.ToTitleCase();});
                    text += "<li> Authors: " + authors.join(", ") + "</li>";
                }
                if (sources.length > 0) {
                    text += "<li> Source: " + sources[0] + "</li>";
                }
                text += "</ul>";

                return text;

            });


            storyIndex.SetPopOver("bodyFragment", function(entity) {

                var dates       = entity.ref.date;
                var articles    = entity.ref.article;
                var authors     = entity.ref.author;
                var sources     = entity.ref.source;
                var text        = "";

                text += "<div class='MdSerif'>";
                text += "<strong>Fragment details:</strong>";
                // text += "<blockquote class='MdSerif'>";
                text += "<ul>";

                if (articles.length > 0) {
                    text += "<li>Appeares in " + String(articles.length)
                         + ((articles.length > 1) ? " articles</li>" : " article</li>");
                }

                if (sources.length > 0) {
                    text += "<li>In " + String(sources.length)
                         + ((sources.length > 1) ? " sources</li>" : " source</li>");
                }

                if (authors.length > 0) {
                    text += "<li>By " + String(authors.length)
                         + ((authors.length > 1) ? " authors</li>" : " author</li>");
                }


                if (dates.length > 0) {
                    var firstDate = dates[0];
                    for (var i in dates)
                        if (dates[i].name < firstDate)
                            firstDate = dates[i].name;
                    firstDate = storyApi.dateAPI.Str2Date(firstDate);
                    text += "<li>First time appeared on " + layout.Date2Str(firstDate)
                         + " in <strong>TODO</strong></li>";
                }

                text += "</ul>";
                text += "Click on fragment to highlight related entities."
                text += "</div>";
                return text;

            });

            //
            //
            //
            storyIndex.IndexReferences();

            //
            // Group Markup Entities by paragraphs
            //
            var bodyFragments = [[]];
            var j             = 0;
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
                layout          = new StoryLayout();

                if ($scope.central.pubDate) {
                    $scope.central.pubDatePretty = layout.Date2Str(storyApi.dateAPI.Str2Date($scope.central.pubDate));
                }

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
                var related         = storyIndex.SelectItem(entityId);
                var firstAppeared   = -1;
                var dateEntities    = [];

                for (var i in related) {
                    var entity = related[i];
                    if (entity.groupId == "bodyFragment") {
                        if (firstAppeared == -1 || entity.extra.taggedCounter < firstAppeared)
                            firstAppeared = entity.extra.taggedCounter;
                    }
                    if (entity.groupId == "date") {
                        dateEntities.push(entity);
                    }
                }

                if (firstAppeared != -1) {
                    if (firstAppeared == 0) firstAppeared = 1; // TODO: fix this
                    firstAppeared = "#fragment_" + String(firstAppeared);
                    $("#ClientBarCenter").scrollTop($("#ClientBarCenter").scrollTop()+$(firstAppeared).position().top-200);
                }

                storyHeatmap.Highlight(dateEntities);

            };


            setTimeout(function(){

                $rootScope.$chartScope.api.getScope().chart.dispatch.on("brush", function(e) {
                    var extent = e.extent;
                });

            });

        });

}]);
