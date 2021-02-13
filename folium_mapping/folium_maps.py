import numpy as np
import folium

def get_map_with_markers(markers_coords_list, zoom_start=15):
    """
    Returns folium map object with points with coordinates from 'markers_coords_list'.
    Example of the list: [(lat1, lon1), (lat2, lon2), ...]
    Parameters:
        - markers_coords_list as (list of tuple pairs): markers' list
        - zoom_start as (int): map zoom initial level
    Returns:
        - m as (map object): map with markers
    """
    
    center_point = np.mean(np.array(markers_coords_list), axis=0)
    m = folium.Map(location=center_point, zoom_start=zoom_start)
    
    for i in range(len(markers_coords_list)):
        cur_coords = markers_coords_list[i]
        folium.Marker(cur_coords).add_to(m)
    
    return m
	
	
def get_map_with_events(events_list, zoom_start=15):
    """
    Returns folium map object with points with coordinates from 'markers_coords_list'.
    Example of the list: [(lat1, lon1), (lat2, lon2), ...]
    Parameters:
        - events_list as (list of dicts): events' list
        - zoom_start as (int): map zoom initial level
    Returns:
        - m as (map object): map with markers
    """
    
    markers_coords_list = get_places_coords_list(events_list)
    
    center_point = np.mean(np.array(markers_coords_list), axis=0)
    m = folium.Map(location=center_point, zoom_start=zoom_start)
    
    for event in events_list:
        cur_coords = (float(event['attributes']['lat']), 
                      float(event['attributes']['lon'])
                     )
        cur_idx = event['attributes']['place_id']
        folium.Marker(
            cur_coords,
            popup=cur_idx
        ).add_to(m)
    
    return m


def get_places_coords_list(events_list):
    """
    Returns list of events' coordinates
    Parameters:
        - events_list as (list of dicts): events' list
    Returns:
        - places_coords_list as (list of tuples): list of places' coordinates
    """
    
    places_coords_list = []
    for event in events_list:
        cur_lat = float(event['attributes']['lat'])
        cur_lon = float(event['attributes']['lon'])
        
        places_coords_list.append((cur_lat, cur_lon))
        
    return places_coords_list
