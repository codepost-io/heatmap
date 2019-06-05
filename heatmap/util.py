
# Python dependencies
#
from __future__ import print_function # Python 2
#
import copy as copy
import functools as functools
import json as json
import logging as logging
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

def getLogger():
    return _logger

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
