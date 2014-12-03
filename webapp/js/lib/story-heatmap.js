/*
 *
 * Author: Vova Zaytsev <zaytsev@usc.edu>
 *
 */

function StoryHeatmap(data, api, index, $scope) {

    this.data       = data;
    this.index      = index;
    this.api        = api;
    this.cal        = new CalHeatMap();
    this.startDate  = this.api.dateAPI.Str2Date(api.GetCentralNode().pubDate);

    var data = {};
    var cal = this.cal;
    var startDate = this.startDate;
    startDate = this.api.dateAPI.AddDays(startDate, -30);
    var sourceData = this.api.dateAPI.datesDistrList;

    for (var i in sourceData) {
        var date = String(this.api.dateAPI.Str2Date(sourceData[i].pubDate).getTime() / 1000);
        data[date] = sourceData[i].freq;
    };

    this.cal.init({
        itemSelector        : "#HeatmapCanvas",
        start               : startDate,
        data                : data,
        domain              : "month",
        subDomain           : "day",
        range               : 3,
        cellSize            : 12,
        cellPadding         : 2,
        domainMargin        : 0,
        highlight           : [startDate, "now"],
        legend              : [1, 5, 10, 15],
        legendCellSize      : 12,
        tooltip             : true,
        itemName            : ["article", "articles"],
        domainLabelFormat   : "%m-%Y",
        previousSelector    : "#HeatmapCanvas_Prev",
        nextSelector        : "#HeatmapCanvas_Next",
        subDomainTextFormat : function(date ,value) {
            date = api.dateAPI.Date2Str(date);
            return api.dateAPI.datesDistr[date];
        },
        onClick             : function(date, value) {
            var dateUnique = "date_" + api.dateAPI.Date2Str(date);
            if (dateUnique in index.groups["date"]) {
                $scope.SelectEntity(index.groups["date"][dateUnique].gid);
                var selectedDates = [startDate];
                for (var i in index.selected) {
                    var entity = index.selected[i];
                    if (entity.groupId == "date")
                        selectedDates.push(api.dateAPI.Str2Date(entity.extra.pubDate));
                }
                cal.highlight(selectedDates);
            } else {
                $scope.SelectEntity(null);
            }
            $scope.$apply();
        }
    });

}
