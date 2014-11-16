/*
 *
 * Author: Vova Zaytsev <zaytsev@usc.edu>
 *
 */


function StoryApi(data) {
    /*
     * API abstracts cleints from actual data representation (JSON returned by server)
     * and also provides some useful function.
     * Requires D3.js
     */

    this.data = data;
    this.dateAPI = new DateAPI(data, this);

}


//
StoryApi.prototype.GetNode = function(nodeId) {
    /*
     *
     *
     */
    return this.data.nodes[nodeId];
};


//
StoryApi.prototype.GetNodes = function() {
    /*
     *
     *
     */

    return d3.values(this.data.nodes);

};


//
StoryApi.prototype.GetCentralNode = function() {
    /*
     *
     *
     */

     var centralNodeId = this.data.meta.centralNode;

     return this.GetNode(centralNodeId);

};


//
StoryApi.prototype.GetDates = function () {

};







// //
// StoryGraph.prototype.computeDistribution = function() {

//     this.distr = new DateAPI(this);


// }


// //
// StoryGraph.prototype.drawDistribution = function(placeId, width, height) {

//     if (!this.distr)
//         this.computeDistribution();

//     var sg = this;
//     var radius = 10;
//     var ticks = 7;
//     var data = [];
//     var dates = this.distr.getDateRange();
//     var l = this.distr.Str2Date(this.distr.lD);
//     var f = this.distr.Str2Date(this.distr.fD);

//     for (var i in dates)
//         data.push({
//             "key": this.distr.Str2Date(dates[i]),
//             "value": this.distr.getDistrValue(dates[i])
//         });


//     var margin = {top: 20, right: 20, bottom: 64, left: 60},
//         width =  width - margin.left - margin.right,
//         height = height - margin.top - margin.bottom;


//     this.gfx.xScale = d3.time.scale().domain([f, l]).range([0, width]);
//     this.gfx.yScale = d3.scale.linear().range([height, 0]);
//     var xScale = this.gfx.xScale, yScale = this.gfx.yScale;
//     yScale.domain([0, d3.max(data, function(d) { return d.value; })]);


//     // Interpolate counts
//     var line = d3.svg.line()
//         .interpolate("basis")
//         .x(function(d) { return xScale(d.key); })
//         .y(function(d) { return yScale(d.value); });


//     // Generate axises
//     var xAxis = d3.svg.axis()
//         .scale(xScale)
//         .orient("bottom")
//         .ticks(ticks)
//         .tickFormat(d3.time.format("%Y.%m.%d"));
//     var yAxis = d3.svg.axis().scale(yScale).orient("left");


//     var svg = d3.select("#" + placeId).append("svg")
//         .attr("width", width + margin.left + margin.right)
//         .attr("height", height + margin.top + margin.bottom)
//         .append("g")
//         .attr("transform", "translate(" + margin.left + "," + margin.top + ")");


//     svg.selectAll("line.verticalGrid").data(xScale.ticks(ticks)).enter()
//         .append("line")
//         .attr({
//             "class":"verticalGrid",
//             "y1": 0,
//             "y2": height,
//             "x1": function(d){ return xScale(d);},
//             "x2": function(d){ return xScale(d);},
//             "fill": "none",
//             "shape-rendering": "crispEdges",
//             "stroke" : "#EEE",
//             "stroke-width": "1px"
//         });

//     svg.append("g")
//         .attr("class", "x axis")
//         .attr("transform", "translate(0," + height + ")")
//         .call(xAxis)
//         .selectAll("text")
//         .attr("dy", ".25em")
//         .attr("dx", "-2em")
//         .attr("transform", "rotate(-45)");


//     svg.append("g")
//         .attr("class", "y axis")
//         .call(yAxis)
//         .append("text")
//         .attr("class", "label")
//         .attr("transform", "rotate(-90)")
//         .attr("y", 6)
//         .attr("dy", ".71em")
//         .style("text-anchor", "end")
//         .text("Daily News Volume");


//     svg.append("path")
//         .datum(data)
//         .attr("class", "line")
//         .attr("d", line)
//         .attr("id", "VolumeDistribution")


//     svg.append("g")
//         .datum(data)
//         .attr("class", "line")
//         .attr("d", line);


//     this.gfx.SetDistributionSelection = function(referencesList) {

//         var dates = [];
//         for (var i in referencesList) {
//             var refId = referencesList[i];
//             var node = sg.getNode(refId);
//             if (node.pubDate) {
//                 var start = sg.distr.Str2Date(node.pubDate);
//                 var end = sg.distr.addDays(start, 2);
//                 start = sg.distr.addDays(start, -2);
//                 dates.push({
//                     "start": start,
//                     "end": end
//                 });
//             }
//         }

//         svg.selectAll("rect.DistrSelectionBar").remove();
//         svg.selectAll("rect.DistrSelectionBar")
//             .data(dates).enter()
//             .insert("rect", "#VolumeDistribution")
//             .attr("class", "DistrSelectionBar")
//             .attr("x", function(dRange) {
//                 return xScale(dRange.start)-4;
//             })
//             .attr("y", 0)
//             .attr("height", height)
//             .attr("width", function(dRange) {
//                 return 12;
//             });

//     };

// }


// //
// StoryGraph.prototype.drawNetwork = function(placeId, width, height, config) {

//     if (!config) {
//         config = {
//             "gravity": 0.08,
//             "linkDistance": 40,
//             "charge": -200,
//             "radius": 6
//         }
//     }

//     if (!this.distr)
//         this.computeDistribution();

//     var sg = this;

//     var svg = d3.select("#"+placeId).append("svg")
//         .attr("width", width)
//         .attr("height", height);

//     this.gfx.SetNetworkSelection = function(referencesList) {

//         svg.selectAll("*").remove();

//         var force = d3.layout.force()
//             .gravity(config.gravity)
//             .linkDistance(config.linkDistance)
//             .charge(config.charge)
//             .size([width, height])
//             .nodes([])
//             .links([]);

//         var nwNodes = force.nodes();
//         var nwLinks = force.links();

//         var linkSelector = svg.selectAll(".link");
//         var nodeSelector = svg.selectAll(".node");
//         var textSelector = svg.selectAll("text.nodecircle");
//         var circleSelector = svg.selectAll("circle.nodetext");

//         force.on("tick", function() {

//             nodeSelector.each(function(d) {

//               if (d.isFixed) {
//                   d.x = d.px = Math.min(d.boxX + 50, Math.max(d.boxX - 50, d.px));
//                   d.y = d.py = Math.min(d.boxY + 75, Math.max(d.boxY - 75, d.py));
//               }

//             });


//             linkSelector.attr("x1", function(d) { return d.source.x; })
//                 .attr("y1", function(d) { return d.source.y; })
//                 .attr("x2", function(d) { return d.target.x; })
//                 .attr("y2", function(d) { return d.target.y; });

//             nodeSelector.attr("transform", function(d) {
//                 var x = Math.max(config.radius, Math.min(width - config.radius, d.x));
//                 var y = Math.max(config.radius, Math.min(height - config.radius, d.y));
//                 return "translate(" + x + "," + y + ")";
//             });

//         });

//         nwNodes.splice(0, nwNodes.length);
//         nwLinks.splice(0, nwLinks.length);

//         var nwNodesI = {};

//         if (!referencesList || referencesList.length == 0) {

//             for (var i in sg.data.nodes) {
//                 var node = new StoryNode(sg.data.nodes[i], sg, config, height, width);
//                 nwNodes.push(node);
//                 nwNodesI[node.data.refId] = node;
//             }

//             for (var i in sg.data.edges) {
//                 var edge = sg.data.edges[i];
//                 var sourceRefId = edge[0];
//                 var targetRefId = edge[1];
//                 var sourceNode = nwNodesI[sourceRefId];
//                 var targetNode = nwNodesI[targetRefId];
//                 var newLink = {"source": sourceNode, "target": targetNode};
//                 nwLinks.push(newLink);
//             }

//         } else {

//             for (var i in referencesList) {
//                 var k = referencesList[i];
//                 var node = new StoryNode(sg.data.nodes[k], sg, config, height, width);
//                 nwNodes.push(node);
//                 nwNodesI[node.data.refId] = node;
//             }

//             for (var i in sg.data.edges) {
//                 var edge = sg.data.edges[i];
//                 var sourceRefId = edge[0];
//                 var targetRefId = edge[1];
//                 if (nwNodesI[sourceRefId] && nwNodesI[targetRefId]) {
//                     var sourceNode = nwNodesI[sourceRefId];
//                     var targetNode = nwNodesI[targetRefId];
//                     var newLink = {"source": sourceNode, "target": targetNode};
//                     nwLinks.push(newLink);
//                 }
//             }
//         }

//         var nwLinksC = []
//         var nwNodesC = []

//         for(var i in nwLinks)
//             nwLinksC.push(nwLinks[i])
//         for(var i in nwNodes)
//             nwNodesC.push(nwNodes[i])

//         linkSelector = linkSelector.data(nwLinksC);
//         linkSelector.enter()
//             .append("line")
//             .attr("class", "link");

//         nodeSelector = nodeSelector.data(nwNodesC);

//         nodeGSelector = nodeSelector.enter()
//             .append("g")
//             .attr("class", "node");

//         nodeGSelector.append("circle")
//             .attr("cx", 0)
//             .attr("cy", 0)
//             .attr("class", "nodecircle")
//             .attr("r", function(d) { return d.radius; })
//             .call(force.drag);

//         nodeGSelector.append("text")
//             .attr("dx", 12)
//             .attr("dy", ".35em")
//             .attr("class", "nodetext")
//             .text(function(d) { return d.data.title; });

//         nodeGSelector.on("click", function(d) {

//             window.open(d.data.url, "_blank");

//         });

//         force.start();

//     };


//     this.gfx.SetNetworkSelection();

// };


// //
// function StoryNode(node, sg, config, height, width) {
//     this.boxX = node.pubDate? sg.gfx.xScale(sg.distr.Str2Date(node.pubDate)) : width / 2;
//     this.boxY = height / 2;
//     this.index = node.refId;
//     this.radius = config.radius;
//     this.data = node;
//     this.isFixed = false;//node.pubDate && sg.distr.referenceTop[node.pubDate].node.refId == node.refId;
//     this.fixed = false;

//     if (sg.distr.topKIndeces.indexOf(this.data.refId) > -1) {
//         this.isFixed = true;
//         this.y = this.boxY;
//         this.x = this.boxX;
//     }
// };


//
function DateAPI(data, api, dateMargin) {

    if (!dateMargin) dateMargin = 7;

    this.api                = api;
    this.data               = data;
    this.Str2Date           = d3.time.format("%Y.%m.%d").parse;
    this.Date2Str           = d3.time.format("%Y.%m.%d");
    this.dates              = [];
    this.datesDistr         = {};
    this.datesDistrList     = [];

    // Extract dates from data
    var nodes = this.api.GetNodes();
    for (var i in nodes) {
        var node = nodes[i];
        if (node.pubDate) {
            this.dates.push(node.pubDate);
            if (node.pubDate in this.datesDistr)
                this.datesDistr[node.pubDate] += 1;
            else
                this.datesDistr[node.pubDate] = 1;
        }
    }
    this.dates = d3.set(this.dates).values();
    this.dates = this.dates.sort(d3.ascending);
    for (var i in this.dates) {
        var pubDate = this.dates[i];
        this.datesDistrList.push({
            "pubDate":  pubDate,
            "freq":     this.datesDistr[pubDate]
        });
    }

    // Remember first and the last dates
    this.first              = d3.min(this.dates);
    this.last               = d3.max(this.dates);

    var first = this.Str2Date(this.first);
    var last = this.Str2Date(this.last);

    this.allDates           = this.DateRange(first, last);
    this.allDatesDistr      = {};
    this.allDatesDistrList  = [];

    for (var i in this.allDates) {
        var pubDate = this.allDates[i];
        if (pubDate in this.datesDistr) {
            this.allDatesDistr[pubDate] = this.datesDistr[pubDate];
            this.allDatesDistrList.push({
                "pubDateStr"    : pubDate,
                "pubDate"       : this.Str2Date(pubDate),
                "freq"          : this.datesDistr[pubDate]
            });
        } else {
            this.allDatesDistr[pubDate] = 0;
            this.allDatesDistrList.push({
                "pubDateStr"    : pubDate,
                "pubDate"       : this.Str2Date(pubDate),
                "freq"          : 0
            });
        }
    }
}


//
DateAPI.prototype.AddDays = function(date, deltaDays) {
     var dat = new Date(date.valueOf());
     dat.setDate(dat.getDate() + deltaDays);
     return dat;
};


//
DateAPI.prototype.DateRange = function(start, end) {
     var dateArray = [];
     var currentDate = start;
     while (currentDate <= end) {
         dateArray.push(this.Date2Str(new Date(currentDate)));
         currentDate = this.AddDays(currentDate, 1);
     }
     return dateArray;
};


//
DateAPI.prototype.GetDateRange = function() {
     return this.DateRange(this.Str2Date(this.first), this.Str2Date(this.last));
};


//
DateAPI.prototype.DaysDiff = function(first, second) {
     return (second-first) / (1000*60*60*24);
};
