/*
 * Author: Vova Zaytsev <zaytsev@usc.edu>
 */


function StoryGraph(graphData) {

    this.parseDate = d3.time.format("%Y.%m.%d").parse;
    this.graphData = graphData;
    this.edges = graphData.edges;

    this.nodes = [];
    this.dates = [];

    for (var i in graphData.nodes) {
        if (graphData.nodes[i].pubDate) {
            graphData.nodes[i].pubDate = this.parseDate(graphData.nodes[i].pubDate);
            this.dates.push(graphData.nodes[i].pubDate);
            this.nodes.push(graphData.nodes[i]);
        }
    }

    this.distrib = {};
    this.dateNodes = {};
    this.datesCount = 0;
    for (var i in this.nodes) {
        var node = this.nodes[i];
        if (node.pubDate) {
            if (this.dateNodes[node.pubDate]) {
                this.dateNodes[node.pubDate].push(node);
                this.distrib[node.pubDate] += 1;
            } else {
                this.dateNodes[node.pubDate] = [node];
                this.distrib[node.pubDate] = 1;
                this.datesCount += 1;
            }
        }
    }

    this.average = 0.0;
    for (var i in this.distrib) {
        this.average += this.distrib[i];
    }
    this.average /= this.datesCount;
    this.firstDate = d3.min(this.dates);
    this.lastDate = d3.max(this.dates);

    this.pikes = {};
    this.pikes[this.firstDate] = {
        count: this.distrib[this.firstDate],
        nodes: this.dateNodes[this.firstDate],
        date: this.firstDate
    };
    this.pikes[this.lastDate] = {
        count: this.distrib[this.lastDate],
        nodes: this.dateNodes[this.lastDate],
        date: this.lastDate
    };

    for (var i in this.distrib) {
        if (!this.pikes[this.distrib]) {
            if (this.distrib[i] >= this.average) {
                this.pikes[i] = {
                    count: this.distrib[i],
                    nodes: this.dateNodes[i],
                    date: i
                }
            }
        }
    }

    var dates = this.dateRange(this.firstDate, this.lastDate);
    for (var i in dates) {
        if (!this.distrib[dates[i]]) {
            this.distrib[dates[i]] = 0;
        }
    }

}


StoryGraph.prototype.dateRange = function(startDate, stopDate) {
    Date.prototype.addDays = function(days) {
        var dat = new Date(this.valueOf())
        dat.setDate(dat.getDate() + days);
        return dat;
    }
    var dateArray = new Array();
    var currentDate = startDate;
    while (currentDate <= stopDate) {
        dateArray.push( new Date (currentDate) )
        currentDate = currentDate.addDays(1);
    }
    return dateArray;
}


StoryGraph.prototype.renderDistribution = function(locationId, width, height) {

    var margin = {top: 20, right: 20, bottom: 120, left: 60},
        width =  width - margin.left - margin.right,
        height = height - margin.top - margin.bottom;

    var xScale = d3.time.scale().domain([this.firstDate, this.lastDate]).range([0, width]);
    var yScale = d3.scale.linear().range([height, 0]);
    var color = d3.scale.category10();
    var data = d3.entries(this.distrib);
    var pikes = d3.values(this.pikes);

    data.sort(function(a, b){ return d3.ascending(new Date(a.key), new Date(b.key)); });
    pikes.sort(function(a, b){ return d3.ascending(new Date(a.date), new Date(b.date)); });

    yScale.domain([0, d3.max(data, function(d) { return d.value; })]);

    var area = d3.svg.area()
        .interpolate("linear")
        .x(function(d) { return xScale(new Date(d.key)); })
        .y0(height)
        .y1(function(d) { return yScale(d.value); });

    var xAxis = d3.svg.axis()
        .scale(xScale)
        .orient("bottom")
        .ticks(12)
        .tickFormat(d3.time.format("%m.%d"));

    var yAxis = d3.svg.axis().scale(yScale).orient("left");

    var svg = d3.select(locationId).append("svg")
        .attr("width", width + margin.left + margin.right)
        .attr("height", height + margin.top + margin.bottom)
        .append("g")
        .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

    svg.selectAll("line.verticalGrid").data(xScale.ticks(12)).enter()
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
        .attr("dy", ".15em")
        .attr("dx", "-2em")
        .attr("transform", "rotate(-35)");

    svg.append("g")
        .attr("class", "y axis")
        .call(yAxis)
        .append("text")
        .attr("class", "label")
        .attr("transform", "rotate(-90)")
        .attr("y", 6)
        .attr("dy", ".71em")
        .style("text-anchor", "end")
        .text("Publications");

    svg.append("path")
        .datum(data)
        .attr("class", "area")
        .attr("d", area);

    svg.append("line")
        .attr("x1", xScale(this.firstDate))
        .attr("x2", xScale(this.lastDate))
        .attr("y1", yScale(this.average))
        .attr("y2", yScale(this.average))
        .attr("stroke-width", 1)
        .attr("stroke", "#EEE");

    data.sort(function(a, b){ return d3.ascending(new Date(a.key), new Date(b.key)); });
    yScale.domain([0, d3.max(data, function(d) { return d.value; })]);

     svg.append("g")
        .datum(data)
        .attr("class", "area")
        .attr("d", area);


    svg.selectAll(".dot").data(pikes)
        .enter()
        .append("rect")
        .attr("x", function(d) { return xScale(new Date(d.date)); })
        .attr("y", function(d) { return yScale(d.count); })
        .attr("width", 30)
        .attr("height", 20)
        .attr("stroke-width", 1)
        .attr("stroke", "#000")
        .attr("fill", "none");

};