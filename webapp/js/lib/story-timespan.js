/*
 *
 * Author: Vova Zaytsev <zaytsev@usc.edu>
 *
 */


function StoryTimespan(data, api, index, $scope) {
    this.data       = data;
    this.index      = index;
    this.api        = api;

    var distr       = this.api.dateAPI.allDatesDistrList;
    var values      = [];
    var dateFormat  = d3.time.format("%x");

    for (var i in distr) {
        values.push({
            "x": distr[i].pubDate,
            "y": distr[i].freq
        });
    }

    this.timespanData   = [{
        "key"       : "News Distribution",
        "values"    : values
    }];
    this.timespanOptions = {
        chart: {
            type: "lineWithFocusChart",
            height: 256,
            margin: {
                top: 24,
                right: 24,
                bottom: 30,
                left: 24
            },
            transitionDuration: 0,
            xAxis: {
                axisLabel: "Date",
                tickFormat: function (d) {
                    return dateFormat(new Date(d));
                }
            },
            x2Axis: {
                tickFormat: function (d) {
                    return dateFormat(new Date(d));
                }
            },
            yAxis: {
                axisLabel: "Articles",
                tickFormat: function (d) {
                    return d;
                },
                rotateYLabel: false
            },
            y2Axis: {
                tickFormat: function (d) {
                    return d;
                }
            }

        }
    };


    // $("#preset-range").on("click", function() {
    //     // Get the min and max
    //     // min = $(this).data("min")
    //     // max = $(this).data("max")

    //     // Change the focus chart range programatically
    //     // chart.brushExtent([min, max]).update();
    // });

    $scope.timespanData = this.timespanData;
    $scope.timespanOptions = this.timespanOptions;

}


//
StoryTimespan.prototype.Resize = function(placeId, place, width, height, radius, ticks) {
    // TODO: correctly remove the old component view
    this.RenderDistribution(placeId, place, width, height, radius, ticks);
};


//
StoryTimespan.prototype.RenderDistribution = function(placeId, place, width, height, radius, ticks) {

    console.log(height);

    this.timespanOptions.chart.height = height;

};
