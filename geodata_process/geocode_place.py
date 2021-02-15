import geocoder
import nltk 
import logging
import numpy as np

from nltk.corpus import brown


logger = logging.getLogger("infapi.plugins")


def is_string_address(input_str):
    """
    Checking whether the input string is address or not
    Parameters:
        - input_str as (str): input string to be checked
    Returns:
        - boolean depending on the checking (True if address and False if not)
    """
    
    for chunk in nltk.ne_chunk(nltk.pos_tag(nltk.word_tokenize(input_str))):
        if hasattr(chunk, "label"):
            if chunk.label() == "GPE" or chunk.label() == "GSP":
                return True
    
    return False


def get_coords_by_address(addr_str):
    """
    Returns coordinates (lat/lon) of the point with a given address (OSM geocoder is used)
    Parameters:
        - addr_str as (str): address of the point 
    Returns:
        - coords as (tuple): the point's coordinates (lat/lon)
        - None if the address wasn't recognized
    """
    
    gcd = geocoder.osm(addr_str)
    location = gcd.latlng
    
    if location is None:
        logger.error('Address was not recognized...')
        return None
    else:
        coords = tuple(location)
    
    return coords


def simple_dist(point1, point2):
    """
    Returns distance between given points in meters calculated by simplified formula
    Parameters:
        - point1, point2: lists of lat/lon coordinates of the points
    Returns:
        - dist as (float): distance in kilometers between the points    
    """
    
    dx = (40074.275 * (np.abs(point2[1] - point1[1]) / 360) 
          * np.cos(np.deg2rad(np.mean([point1[0], point2[0]]))))
    dy = 20004.146 * (np.abs(point1[0] - point2[0])) / 180
    dist = np.sqrt(np.square(dx) + np.square(dy))
    
    return dist

