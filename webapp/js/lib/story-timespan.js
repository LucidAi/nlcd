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


//
StoryTimespan.prototype.RenderDistribution = function(placeId, place, width, height, radius, ticks) {

    place.html("");

    var data = this.api.dateAPI.allDatesDistrList;
    var small = {};
    small.width = width;
    small.height = height;
    small.left = 20;
    small.right = 20;
    small.top = 20;
    small.xax_count = 5;

    data_graphic({
        title: "Timespan",
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
    });


};
