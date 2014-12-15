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

    for (var i in this.data.nodes)
        if (this.data.nodes[i].sources.length > 0)
            this.data.nodes[i].sources = [this.data.nodes[i].sources[0]];


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
