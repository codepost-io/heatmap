
# Python dependencies
#
from __future__ import print_function # Python 2
#
import copy as copy
import functools as functools
import json as json
import os as os
import time as time

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

#########################################################################


_logger = _util.getLogger()

#########################################################################


class HeatmapData(object):
    
    def __init__(self, assignment_id, cache=True, refresh_cache=False, cache_filename=None, api_key=None):
        self._assignment_id = assignment_id

        if api_key == None:
            api_key = _util.configure_apikey()

        self._headers = {"Authorization": "Token " + api_key}
        
        self._map_comments_id_to_cache = {}
        if cache and not refresh_cache:
            self._load_cache(filename=cache_filename)
        
        if len(self._map_comments_id_to_cache) == 0:
            self.init()
        
            if cache:
                self._store_cache(filename=cache_filename)
    
    def _default_cache_filename(self):
        return "codePost_heatmap_cache_assignment_{}.json".format(
            self._assignment_id)
    
    def _load_cache(self, filename=None):
        if not filename:
            filename = self._default_cache_filename()
        try:
            with open(filename) as f:
                self._map_comments_id_to_cache = json.loads(f.read())
        except:
            self._map_comments_id_to_cache = {}
    
    def _store_cache(self, filename=None):
        if not filename:
            filename = self._default_cache_filename()
        with open(filename, "w") as f:
            f.write(json.dumps(self._map_comments_id_to_cache, indent=2))
    
    def init(self):
        # Data
        self._map_comments_id_to_cache = {}
        self._map_student_to_section = {}
        self._map_rubricComments_id_to_obj = {}
        self._map_rubricComments_id_to_category = {}
        
        # Statistics
        self._c_get_total = 0
        self._c_get_err = 0
        self._c_get_exc = 0
        self._t_init_start = None
        self._t_init_start
        
        # Initialization
        self._t_init_start = time.time()
        
        self.process_sections()
        self.process_rubric()
        
        self._t_init_end = time.time()
        self._t_init_duration = (self._t_init_end - self._t_init_start)
    
    def _get(self, endpoint, **kwargs):
        r = None
        try:
            self._c_get_total += 1
            r = _requests.get(
                url=urljoin(_util.BASE_URL, endpoint),
                headers=self._headers,
                **kwargs
            )
        except:
            self._c_get_exc += 1
            return None
        
        if r.status_code == 401:
            raise Exception("Auth failed: API key missing or invalid,"
                            " or does not have access to this ressource?")
            
        if r.status_code != 200:
            self._c_get_err += 1
            return None
        else:
            try:
                r.json()
            except:
                self._c_get_err += 1
                return None
            
        return r
    
    def _getjson(self, endpoint, **kwargs):
        r = self._get(endpoint=endpoint, **kwargs)
        return r.json()
    
    def _get_comments_submission(self, comment_id=None, comment_obj=None):
        if comment_obj == None:
            comment_obj = self._getjson("/comments/{}/".format(comment_id))
        
        file_id = comment_obj["file"]
        file_obj = self._getjson("/files/{}/".format(file_id))
        
        submission_id = file_obj["submission"]
        submission_obj = self._getjson("/submissions/{}/".format(submission_id))
        
        return submission_obj
    
    def process_sections(self):
        self._map_student_to_section = {}
        
        assignment_obj = self._getjson("/assignments/{}/".format(self._assignment_id))
        if assignment_obj == None:
            raise Exception("API Error: Cannot access assignment.")
        
        course_id = assignment_obj["course"]
        course_obj = self._getjson("/courses/{}/".format(course_id))
        
        for section_id in course_obj["sections"]:
            section_obj = self._getjson("/sections/{}/".format(section_id))
            for student in section_obj["students"]:
                self._map_student_to_section[student] = section_obj["name"]
    
    def process_rubric(self):
        a_id = self._assignment_id
        
        rubric_obj = self._getjson("/assignments/{}/rubric/".format(a_id))
        if rubric_obj == None:
            raise Exception("API Error: Cannot access rubric.")
        
        # Process rubric categories
        self._map_comments_id_to_category = {}
        for rubricCategory_obj in rubric_obj["rubricCategories"]:
            for rubricComments_id in rubricCategory_obj["rubricComments"]:
                self._map_rubricComments_id_to_category[rubricComments_id] = rubricCategory_obj
        
        # Process rubric comments
        #  {'id': 2335,
        #   'text': 'inverse performance: takes nlogn time to use a comparison based sort',
        #   'pointDelta': 2.0,
        #   'category': 350,
        #   'comments': [71068, 71516, 72471, 73285, 73440, 73508, 73685, 74565],
        #   'sortKey': 0}
        
        self._map_rubricComments_id_to_obj = {}
        self._map_comments_id_to_cache = {}
        for rubricComment_obj in rubric_obj["rubricComments"]:
            self._map_rubricComments_id_to_obj[rubricComment_obj["id"]] = rubricComment_obj
            
            # Get all the submission comments that are linked to the rubricComment
            linked_comment_ids = rubricComment_obj["comments"]
            
            for comment_id in linked_comment_ids:
                comment_obj = self._getjson("/comments/{}/".format(comment_id))
                
                # Enrich object
                comment_obj["rubricComment"] = rubricComment_obj
                category_obj = self._map_rubricComments_id_to_category.get(rubricComment_obj["id"], dict())
                comment_obj["category"] = category_obj.get("name", "")
                
                submission_obj = self._get_comments_submission(comment_obj=comment_obj)
                comment_obj["student"] = submission_obj["students"]
                comment_obj["sections"] = list(
                    filter(lambda x: x != None,
                           map(lambda s: self._map_student_to_section.get(s, None),
                              comment_obj["student"])))
                
                self._map_comments_id_to_cache[comment_id] = comment_obj
    
    def get_comments(self):
        return copy.deepcopy(self._map_comments_id_to_cache)
    
