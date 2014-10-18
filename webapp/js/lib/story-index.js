/*
 *
 * Author: Vova Zaytsev <zaytsev@usc.edu>
 *
 */


function StoryIndex(data, api) {

    this.data           = data;
    this.api            = api;
    this.items          = [];
    this.selected       = [];
    this.related        = [];
    this.groups         = {};
    this.globalIndex    = {};

}


StoryIndex.prototype.GetItem = function(globalId) {
    return this.globalIndex[globalId];
};


StoryIndex.prototype.Group = function(groupId) {
    var group = [];
    for (var i in this.groups[groupId])
        group.push(this.groups[groupId][i]);
    return group;
};


StoryIndex.prototype.SelectItem = function(globalId) {
    var entity = this.GetItem(globalId);
    var deselect = this.selected.length > 0 && (entity.gid == this.selected[0].gid);
    if (entity) {
        for (var i in this.selected)
            this.selected[i].isSelected = false;
        for (var i in this.related)
            this.related[i].isRelated = false;
        this.selected = deselect ? [] : [entity];
        entity.isSelected = !deselect;
        this.related = [];
        if (!deselect)
            for (var groupId in entity.ref) {
                var groupReferences = entity.ref[groupId];
                for (var i in groupReferences) {
                    var related = groupReferences[i];
                    related.isRelated = true;
                    this.related.push(related);
                }
            }
    }
    console.log(this.related);
    return entity;
}



StoryIndex.prototype.FindItem = function(textQuery, extraAttrib) {

};


StoryIndex.prototype.IndexReferences = function() {
    for (var i in this.globalIndex) {
        var item = this.globalIndex[i];
        for (var groupId in item.ref) {
            var groupReferences = item.ref[groupId];
            for (var k in groupReferences) {
                var groupUnique = groupReferences[k];
                var refItem = this.groups[groupId][groupUnique];
                if (!refItem.ref[item.groupId])
                    refItem.ref[item.groupId] = [];
                refItem.ref[item.groupId].push(item.unique)
            }
        }
    }
    for (var i in this.globalIndex) {
        var item = this.globalIndex[i];
        for (var groupId in item.ref) {
            var groupReferences = item.ref[groupId];
            var indexReferences = [];
            // TODO: filter duplicates
            for (var k in groupReferences) {
                var groupUnique = groupReferences[k];
                var refItem = this.groups[groupId][groupUnique];
                indexReferences.push(refItem);
            }
            item.ref[groupId] = indexReferences;
        }
    }
}



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
                var newRef = entity.ref;
                entity = this.groups[groupId][entity.unique];
                for (var key in newRef) {
                    if (entity.ref[key])
                        entity.ref[key] = d3.set(entity.ref[key].concat(newRef[key])).values();
                    else
                        entity.ref[key] = newRef[key];
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
