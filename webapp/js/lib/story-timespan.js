/*
 *
 * Author: Vova Zaytsev <zaytsev@usc.edu>
 *
 */


function StoryTimespan(data, api, index) {
    this.data       = data;
    this.index      = index;
    this.api        = api;
}


//
StoryTimespan.prototype.ComputeDistribution = function() {

};


//
StoryTimespan.prototype.Resize = function(placeId, place, width, height, radius, ticks) {
    // TODO: correctly remove the old component view
    this.RenderDistribution(placeId, place, width, height, radius, ticks);
};

var KZ = undefined;
//
StoryTimespan.prototype.RenderDistribution = function(placeId, place, width, height, radius, ticks) {

    if (!$("#" + placeId).html()) return;

    var data = this.api.dateAPI.allDatesDistrList;
    var small = {};
    small.width = width;
    small.height = height;
    small.left = 20;
    small.right = 20;
    small.top = 20;
    small.xax_count = 5;

    KZ = function () {

        data_graphic({
            title: "Small Text Inferred By Size",
            description: "Description",
            data: data,
            width: small.width,
            height: small.height,
            right: small.right,
            top: small.top,
            xax_count: 4,
            target: "#" + placeId,
            x_accessor: "pubDate",
            y_accessor: "freq",
            animate_on_load: true
            //markers: [{
            //    "year": this.api.dateAPI.Str2Date(this.api.dateAPI.first),
            //    "label": "Article published"
            //}]
        });

    };




    /*
    if (!radius) radius = 10;
    if (!ticks)  ticks = 20;

    var margin  = {
        top: 20,
        right: 20,
        bottom: 64,
        left: 60
    };
    width       =  width - margin.left - margin.right;
    height      = height - margin.top - margin.bottom;

    var f = this.api.dateAPI.Str2Date(this.api.dateAPI.first);
    var l = this.api.dateAPI.Str2Date(this.api.dateAPI.last);

    this.xScale = d3.time.scale().domain([f, l]).range([0, width]);
    this.yScale = d3.scale.linear().range([height, 0]);


    var xScale = this.xScale;
    var yScale = this.yScale;

    yScale.domain([0, d3.max(this.api.dateAPI.allDatesDistrList, function(d) { return d.freq; })]);

    // Interpolate counts
    var line = d3.svg.line()
        .interpolate("basis")
        .x(function(d) { return xScale(d.pubDate); })
        .y(function(d) { return yScale(d.freq); });

    // Generate axises
    var xAxis = d3.svg.axis()
        .scale(xScale)
        .orient("bottom")
        .ticks(ticks)
        .tickFormat(d3.time.format("%Y.%m.%d"));
    var yAxis = d3.svg.axis().scale(yScale).orient("left");


    var svg = d3.select("#" + placeId).append("svg")
        .attr("width", width + margin.left + margin.right)
        .attr("height", height + margin.top + margin.bottom)
        .append("g")
        .attr("transform", "translate(" + margin.left + "," + margin.top + ")");


    svg.selectAll("line.verticalGrid").data(xScale.ticks(ticks)).enter()
        .append("line")
        .attr({
            "class":"verticalGrid",
            "y1": 0,
            "y2": height,
            "x1": function(d){ return xScale(d);},
            "x2": function(d){ return xScale(d);},
            "fill": "none",
            "shape-rendering": "crispEdges",
            "stroke" : "#EEE",
            "stroke-width": "1px"
        });

    svg.append("g")
        .attr("class", "x axis")
        .attr("transform", "translate(0," + height + ")")
        .call(xAxis)
        .selectAll("text")
        .attr("dy", ".25em")
        .attr("dx", "-2em")
        .attr("transform", "rotate(-45)");

    svg.append("g")
        .attr("class", "y axis")
        .call(yAxis)
        .append("text")
        .attr("class", "label")
        .attr("transform", "rotate(-90)")
        .attr("y", 6)
        .attr("dy", ".71em")
        .style("text-anchor", "end")
        .text("Daily News Volume");

    svg.append("path")
        .datum(this.api.dateAPI.allDatesDistrList)
        .attr("class", "line")
        .attr("d", line)
        .attr("id", "VolumeDistribution");

    svg.append("g")
        .datum(this.api.dateAPI.allDatesDistrList)
        .attr("class", "line")
        .attr("d", line);

    //svg.selectAll("rect.DistrSelectionBar").remove();

    console.log("RENDER");
    svg.selectAll("rect.DistrSelectionBar")
        .data(this.api.dateAPI.allDates).enter()
        .insert("rect", "#VolumeDistribution")
        .attr("class", "DistrSelectionBar")
        .attr("x", function (dRange) {
            return xScale(dRange);
        })
        .attr("y", 0)
        .attr("height", height)
        .attr("width", function (dRange) {
            return 12;
        });
    */
};
