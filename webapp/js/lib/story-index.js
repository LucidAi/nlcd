/*
 *
 * Author: Vova Zaytsev <zaytsev@usc.edu>
 *
 */


function StoryIndex(data, api) {

    this.data           = data;
    this.api            = api;
    this.items          = [];
    this.activated      = [];
    this.groups         = {};
    this.globalIndex    = {};

}


StoryIndex.prototype.GetItem = function(globalId) {

};


StoryIndex.prototype.FindItem = function(textQuery, extraAttrib) {

};


StoryIndex.prototype.IndexItems = function(items, groupId, mapper) {
    if (!this.groups[groupId])
        this.groups[groupId] = {};
    for (var i in items) {
        var item = items[i];
        var entities = mapper(item);
        for (var j in entities) {
            var entity = entities[j];
            var isSeen = Boolean(this.groups[groupId][entity.unique]);

            if (!isSeen) {
                var globalId = Object.keys(this.globalIndex).length;
                entity.gid = globalId;
                entity.groupId = groupId;
                this.globalIndex[globalId] = entity
                this.groups[groupId][entity.unique] = entity;
            }
            else {
                for (var key in entity.ref) {
                    console.log("TODO: merge references");
                    // If object with the same `unique` occurred twice
                    // add its references to the existing index entry's
                    // references list
                }
            }
        }
    }
};




function Entity(options) {

    this.gid            = null;
    this.central        = options.central;
    this.name           = options.name;
    this.extra          = options.extra;
    this.unique         = options.unique;

    this.isSelected     = false;
    this.isRelated      = false;
    this.ref            = options.ref

}
