
# Python dependencies
#
from __future__ import print_function # Python 2
#
import copy
import functools
import json
import logging
import os
import time

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

from yaml import load as _load_yaml
try:
    from yaml import CLoader as _YamlLoader
except ImportError:
    from yaml import Loader as _YamlLoader

#########################################################################


API_KEY = None         # Temporary Api token provided to CourseAdmin user

BASE_URL = "http://api.codepost.io/"
DEFAULT_API_KEY_VARNAME = "CP_API_KEY"
DEFAULT_CONFIG_PATHS = [
    "codepost-config.yaml",
    ".codepost-config.yaml",
    "~/codepost-config.yaml",
    "~/.codepost-config.yaml",
    "../codepost-config.yaml",
    "../.codepost-config.yaml",
]

#########################################################################


class _Color:
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    DARKCYAN = '\033[36m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

class SimpleColorFormatter(logging.Formatter):
    _title = {
        "DEBUG": "{END}[{BOLD}DBUG{END}]{END}".format(**_Color.__dict__),
        "INFO": "{END}[{BOLD}{GREEN}INFO{END}]{END}".format(**_Color.__dict__),
        "ERROR": "{END}[{BOLD}{RED}ERR {END}]{END}".format(**_Color.__dict__),
        "WARNING": "{END}[{BOLD}{BLUE}WARN{END}]{END}".format(**_Color.__dict__)
    }

    def normalizePath(self, path):
        abs_path = os.path.abspath(path)
        pwd_path = os.getcwd()
        return abs_path.replace(pwd_path, ".", 1)

    def formatMessage(self, msg: logging.LogRecord):
        header = self._title.get(msg.levelname, self._title.get("INFO"))
        return("{} {} (\"{}\", line {}): {}".format(
            header,
            msg.module,
            self.normalizePath(msg.filename),
            msg.lineno,
            msg.message
        ))

def _setupLogging(level="INFO"):

    # Add the color handler to the terminal output
    handler = logging.StreamHandler()
    formatter = SimpleColorFormatter()
    handler.setFormatter(formatter)

    # Set logging level
    root = logging.getLogger()
    root.setLevel(os.environ.get("LOGLEVEL", level))

    # Add the color handler to the logger
    root.addHandler(handler)

    return root

_logger = _setupLogging()

#########################################################################


def configure_apikey():
    global API_KEY
    
    # Hard-coded API_KEY

    if API_KEY != None and API_KEY != "":
        _logger.debug(
            "API_KEY detected in source code. Not overriding it.")
        return API_KEY
    
    # Environment variable API_KEY

    if os.environ.get(DEFAULT_API_KEY_VARNAME, None) != None:
        API_KEY = os.environ.get(DEFAULT_API_KEY_VARNAME)
        _logger.debug(
            ("API_KEY detected in environment " +
            "variable ({}): '{:.5}...'").format(
                DEFAULT_API_KEY_VARNAME,
                API_KEY
            ))
        return API_KEY

    # YAML configuration API_KEY

    location = None

    for config_path in DEFAULT_CONFIG_PATHS:
        config_path = os.path.abspath(os.path.expanduser(config_path))
        if os.path.exists(config_path) and os.path.isfile(config_path):
            location = config_path
            break
        else:
            _logger.debug(
                "No config file here: {}".format(
                    config_path))
    
    if location != None:
        _logger.debug("Configuration file detected: {}".format(location))

        config = None
        try:
            config = _load_yaml(open(location), Loader=_YamlLoader)
        except:
            config = None

        if config == None:
            _logger.debug(
                "Configuration file detected: "
                "Loading failed, no valid API_KEY.")
            return None
        
        if config.get("api_key", "") == "":
            _logger.debug(
                "Configuration file detected: "
                "Loading successful, but no valid API_KEY.")
            return None
        
        API_KEY = config.get("api_key")
        _logger.debug(
            ("API_KEY detected in configuration file ({}): " +
            "'{:.5}...'").format(
                DEFAULT_API_KEY_VARNAME,
                API_KEY
            ))
        return API_KEY
    
    _logger.warn(
        "API_KEY could not be detected. "
        "codePost API calls are expected to fail.")
    return None
    
#########################################################################


class HeatmapData(object):
    
    def __init__(self, assignment_id, cache=True, refresh_cache=False, cache_filename=None, api_key=None):
        self._assignment_id = assignment_id

        if api_key == None:
            api_key = configure_apikey()

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
                url=urljoin(BASE_URL, endpoint),
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
                
    def build_heatmap(self):
        heatmap = {}
        
        for (comment_id, comment_obj) in self._map_comments_id_to_cache.items():
            
            rubricComment_obj = comment_obj["rubricComment"]
            
            key = (rubricComment_obj["text"], rubricComment_obj["id"])
            value = comment_obj["author"]
            
            # Insert in heatmap
            heatmap[key] = heatmap.get(key, dict())
            heatmap[key][value] = heatmap[key].get(value, 1)
        
        return heatmap
