from .preprocess import HeatmapData as HeatmapData

def build_heatmap(hmp: HeatmapData):
    heatmap = {}
    
    comments = hmp.get_comments()

    for (_comment_id, comment_obj) in comments.items():
        
        rubricComment_obj = comment_obj["rubricComment"]
        
        key = (rubricComment_obj["text"], rubricComment_obj["id"])
        value = comment_obj["author"]
        
        # Insert in heatmap
        heatmap[key] = heatmap.get(key, dict())
        heatmap[key][value] = heatmap[key].get(value, 1)
    
    return heatmap
