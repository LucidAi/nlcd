/*
 * Author: Vova Zaytsev <zaytsev@usc.edu>
 */


function StoryGraph(graphData, scope) {

    this.parseDate = d3.time.format("%Y.%m.%d").parse;
    this.graphData = graphData;
    this.edges = graphData.edges;
    this.scope = scope;

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

    this.f = new Date(this.firstDate);
    this.l = new Date(this.lastDate);
    this.f.setDate(this.f.getDate() - 7);
    this.l.setDate(this.l.getDate() + 7);
    var dates = this.dateRange(this.f, this.l);
    for (var i in dates) {
        if (!this.distrib[dates[i]]) {
            this.distrib[dates[i]] = 0;
        }
    }

}

StoryGraph.prototype.showDate = function(date, disrtItem) {
    console.log(disrtItem);
    this.scope.selectedDateData = disrtItem;
    this.scope.$apply();
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


StoryGraph.prototype.findYatX = function (x, line) {
    function getXY(len) {
        var point = line.getPointAtLength(len);
        return [point.x, point.y];
    }
    var curlen = 0;
    while (getXY(curlen)[0] < x) { curlen += 1; }
    return getXY(curlen);
}


StoryGraph.prototype.renderDistribution = function(locationId, width, height) {

    // Pre-process data
    var sg = this;
    var data = d3.entries(this.distrib);
    var chars = ["A", "B", "C", "D", "C", "E", "F"];
    data.sort(function(a, b){ return d3.ascending(new Date(a.key), new Date(b.key)); });


    // Set canvas margins
    var margin = {top: 20, right: 20, bottom: 48, left: 60},
        width =  width - margin.left - margin.right,
        height = height - margin.top - margin.bottom;
    var radius = 10;

    // Set scales
    var xScale = d3.time.scale().domain([this.f, this.l]).range([0, width]);
    var yScale = d3.scale.linear().range([height, 0]);
    var yMax = d3.max(data, function(d) { return d.value; });
    yScale.domain([0, yMax * 1.2]);

    // Interpolate counts
    var line = d3.svg.line()
        .interpolate("cardinal")
        .x(function(d) { return xScale(new Date(d.key)); })
        .y(function(d) { return yScale(d.value); });

    // Generate axises
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

    svg.append("line")
        .attr("x1", xScale(this.f))
        .attr("x2", xScale(this.l))
        .attr("y1", yScale(this.average))
        .attr("y2", yScale(this.average))
        .attr("stroke-width", 1)
        .attr("stroke", "#EEE");

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
        .text("News Volume");

    svg.append("path")
        .datum(data)
        .attr("class", "line")
        .attr("d", line)
        .attr("id", "VolumeDistribution")

    data.sort(function(a, b){ return d3.ascending(new Date(a.key), new Date(b.key)); });
    yScale.domain([0, d3.max(data, function(d) { return d.value; })]);

    svg.append("g")
        .datum(data)
        .attr("class", "line")
        .attr("d", line);


    // Draw pikes


    var pikes = {};

    pikes[this.firstDate] = {
        count: this.distrib[this.firstDate],
        nodes: this.dateNodes[this.firstDate],
        date: this.firstDate
    };
    pikes[this.lastDate] = {
        count: this.distrib[this.lastDate],
        nodes: this.dateNodes[this.lastDate],
        date: this.lastDate
    };

    var i_prev = this.firstDate;
    var was_incr = true; // is monotonically increasing
    var dates = this.dateRange(this.firstDate, this.lastDate);


    var lineElem = document.getElementById("VolumeDistribution");
    var getY = function(x) {return sg.findYatX(x, lineElem)[1];}

    for (var i in dates) {
        i = dates[i];

        var is_used = Boolean(pikes[i]); // already iterated
        var above_verage = this.distrib[i_prev] >= this.average;
        var is_decr = this.distrib[i] < this.distrib[i_prev];

        if (!is_used && is_decr && was_incr && above_verage) {
            pikes[i] = {
                count: this.distrib[i_prev],
                nodes: this.dateNodes[i_prev],
                date: i_prev
            }

        }

        was_incr = this.distrib[i] >= this.distrib[i_prev];
        i_prev = i;

    }

    pikes = d3.values(pikes);
    var k = 0;

    var elemEnter = svg.selectAll("node")
        .data(pikes)
        .enter().append("g")
        .attr("class", function(d) {
            d.nodeId = k++;
            d.pointLabel = chars[d.nodeId];
            if (d.nodeId == 0) {
                sg.showDate(d.date, d);
                return "pikeTip selected";
            }
            return "pikeTip"
        });

    elemEnter.append("svg:circle")
        .attr("cx", function(d) { return xScale(new Date(d.date)); })
        .attr("cy", function(d) {
            var x = xScale(d.date);
            d.x = x;
            d.y = getY(x);
            return d.y - 16;
        })
        .attr("r", "10px");

    elemEnter.append("text")
        .attr("x", function(d) { return d.x - 5; })
        .attr("y", function(d) { return d.y - 11; })
        .text( function (d) {
            return d.pointLabel;
        })
        .attr("font-size", "15px");

    elemEnter.on("click", function(d) {
        elemEnter.attr("class", "pikeTip");
        d3.select(this).attr("class", "pikeTip selected");
        sg.showDate(d.date, d);
    });



};