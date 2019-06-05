
# Python dependencies
#
from __future__ import print_function # Python 2
#
import os as os

try:
    # Python 3
    from urllib.parse import urljoin
except ImportError:
    # Python 2
    from urlparse import urljoin

# External dependencies
#     
import requests as _requests
import pandas as _pd               # Package to manipulate tables of data
import seaborn as _sns             # Package to create visual heatmap
import matplotlib.pyplot as _plt   # Package to plot heatmap
import numpy as _np                # array() to tweak the palette

# Local dependencies
#
from . import util as _util
from .preprocess import HeatmapData as HeatmapData

#########################################################################


_logger = _util.getLogger()

#########################################################################


class HeatmapXAxis(_util.DocEnum):
    """
    Describes all possible selectable data points for the heatmap's x-axis.
    """

    GRADERS = "graders", """Individual graders."""
    SECTIONS = "sections", """Course sections."""
    TEACHERS = "sectionsLeaders", """Section leaders."""

class HeatmapYAxis(_util.DocEnum):
    """
    Describes all possible selectable data points for the heatmap's y-axis.
    """

    COMMENTS = "rubricComments", """Individual rubric comments (caption, ID)."""
    CATEGORIES = "rubricCategories", """Rubric categories (caption)."""

#########################################################################


def axis_to_string(mode):
    if mode == HeatmapXAxis.GRADERS:
        return "Graders"
    if mode == HeatmapXAxis.SECTIONS:
        return "Sections"
    if mode == HeatmapXAxis.TEACHERS:
        return "Section Leaders"
    if mode == HeatmapYAxis.COMMENTS:
        return "Rubric Comment Text --- ID"
    if mode == HeatmapYAxis.CATEGORIES:
        return "Rubric Category"
    return ""

def build_heatmap(hmapdata: HeatmapData,
                  x: HeatmapXAxis =HeatmapXAxis.GRADERS,
                  y: HeatmapYAxis =HeatmapYAxis.COMMENTS,
                  section_to_teacher=None):
    """
    """
    heatmap = {}

    for (comment_id, comment_obj) in hmapdata.get_comments().items():

        rubricComment_obj = comment_obj["rubricComment"]
        
        # COMPUTE X-AXIS
        # Keys must be plural to support sections (multiple per assignment
        # since students from different sections could partner)
        keys = []
        if x == HeatmapXAxis.GRADERS:
            keys = [ comment_obj["author"] ]
        
        elif x == HeatmapXAxis.SECTIONS:
            keys = comment_obj["sections"]
        
        elif x == HeatmapXAxis.TEACHERS:
            
            if section_to_teacher == None:
                raise ValueError(
                    "'section_to_teacher' needs to be defined for TEACHERS")
            
            # Resolve the teachers from the sections
            keys = list(set(
                map(lambda s: section_to_teacher.get(s, ""),
                    comment_obj["sections"])))
            
        # COMPUTE Y-AXIS
        if y == HeatmapYAxis.COMMENTS:
            value = (rubricComment_obj["text"], rubricComment_obj["id"])
            
        elif y == HeatmapYAxis.CATEGORIES:
            value = comment_obj["category"]

        # INSERT
        # Insert in heatmap assuming multiple keys (typically only one)
        for key in keys:
            heatmap[key] = heatmap.get(key, dict())
            heatmap[key][value] = heatmap[key].get(value, 0) + 1
    
    return heatmap

def render_heatmap_data(data,
                  x: HeatmapXAxis =HeatmapXAxis.GRADERS,
                  y: HeatmapYAxis =HeatmapYAxis.COMMENTS,
                  x_caption=None,
                  y_caption=None):

    # Convert adequately formatted heatmap data into a dataframe
    dataframe = _pd.DataFrame(data)

    # Destructively fill in zeroes for missing fields (where there are no comments)
    dataframe.fillna(0, inplace=True)

    dataframe.rename(columns=lambda x: x.split("@")[0],inplace=True) # strip out netID for plot simplicity
    dataframe = dataframe.reindex(sorted(dataframe.columns), axis=1) # sort columns

    # Set a larger figure size for visibiliy
    _sns.set(rc={'figure.figsize':(20.7,15.27)})
    
    # Set palette as greens, but with a white for zero
    palette = [ _np.array([1.0, 1. , 1.0, 1. ]) ] + _sns.light_palette("green")

    # Make plot
    _sns.heatmap(dataframe, cmap=palette, cbar_kws={"label": "# of Comments"}, annot=True)

    # Label axes with standard caption if necessary
    x_caption = x_caption or axis_to_string(x)
    y_caption = y_caption or axis_to_string(y)
    _plt.xlabel(x_caption)
    _plt.ylabel(y_caption or "Rubric Comment Text --- ID")

    #plt.tight_layout()
    _plt.show()
