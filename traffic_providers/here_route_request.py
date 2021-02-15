import requests
import datetime 
import pytz 
import logging

logger = logging.getLogger("infapi.plugins")

from ..exceptions import HereResponseError, TsTypeValueError


def get_here_route_for_event(start_coords, end_coords, ts_sec, tz_str, 
                             here_addr, app_id, app_code, ts_type="departure"):
    """
    Returns table with data of the HERE route for the given trip
    Parameters:
        - start_coords as (tuple of float): lat/lon of the start point
        - end_coords as (tuple of float): lat/lon of the end point
        - ts_sec as (float): arrival or departure time in seconds (UTC-time)
        - timezone as (str): timezone name 
        - here_addr as (str): url for the HERE request
        - ts_type as (str): type of time used in the route request
    Returns:
        - here_resp as (dict): data of the HERE route(/s) for the given trip
    """
    
    # Generate initial parameters for the HERE request
    params = getInitialParametersForRequestToHERE()

    # Add credentials
    params["app_id"] = app_id
    params["app_code"] = app_code
    
    # Add waypoints parameters to the request from the start/end coordinates data
    params["waypoint0"] = str(start_coords)[1:-1].replace(" ", "")
    params["waypoint1"] = str(end_coords)[1:-1].replace(" ", "")

    # Add time parameter to the HERE request
    if ts_type == "arrival":
        params["arrival"] = get_local_iso_time(ts_sec, tz_str)
    else:
        params["departure"] = get_local_iso_time(ts_sec, tz_str)

    # request to HERE
    response = requests.get(here_addr, params=params)
    
    return response


def get_local_iso_time(utc_ts_seconds, tz_str):
    """
    Converts UTC-timestamp in seconds to local datetime in ISO format
    Parameters:
        - utc_ts_seconds as (float): UTC-timestamp in seconds
        - tz_str as (str): timezone name
    Returns:
        - date_time_iso as (str): local datetime in ISO format
    """

    timezone = pytz.timezone(tz_str)
    tz_hours = get_tz_hours_from_str(tz_str)
    
    loc_datetime = datetime.datetime.utcfromtimestamp(utc_ts_seconds + tz_hours * 3600)  
    date_zone_aware = timezone.localize(loc_datetime)
    date_time_iso = date_zone_aware.isoformat()
    
    return date_time_iso


def get_tz_hours_from_str(tz_str):
    
    loc_now = datetime.datetime.now(pytz.timezone(tz_str))
    tz_hours = loc_now.utcoffset().total_seconds()/3600
    
    return tz_hours


def getInitialParametersForRequestToHERE(mode="fastest;car;traffic:enabled;",
                                         alternatives="0",
                                         routeAttributes="sh,-wp",
                                         legAttributes="links,-maneuvers",
                                         linkAttributes="sh,le,sl,ds,ro,ma,fc",
                                         returnElevation="true"
                                        ):
    '''
    Purpose:
        setting initial parameters for the request to HERE
    Input:
        - HERE request parameters values
    Output:
        params - a dictionary of parameters for the request    
    '''
    # setting initial parameters
    params = {
        "mode":mode,
        "alternatives":alternatives,
        "routeAttributes":routeAttributes,
        "legAttributes":legAttributes,
        "linkAttributes":linkAttributes,
        "returnElevation":returnElevation
    }
    
    return params


def get_trip_data(prev_event, next_event, tz_str, here_addr, app_id, app_code,ts_type="arrival"):
    """
    Returns trip to go from origin place to the destination. Depending on the "ts_type" parameter,
    uses time of departure from the previous event end (ts_type="departure") or time of arrival
    at the beginning of the next event (ts_type="arrival")
    Parameters:
        - prev_event as (dict): data about the given event
        - next_event as (dict): data about the next_event 
        - tz_str as (str): timezone as string
        - here_addr as (str): url for the HERE request
        - app_id as (str): application id
        - app_code as (str): application code
        - ts_type as (str):type of time used in the route request 
    Returns:
        - trip_data as (dict): data about trip to go from the given prev_event 
                               to the next event
    """
    
    # Validation of the 'ts_type' value
    check_ts_type(ts_type)
    
    # Make request for the HERE route to the given destination
    dep_lat = prev_event["attributes"]["lat"]
    dep_lon = prev_event["attributes"]["lon"]
    arriv_lat = next_event["attributes"]["lat"]
    arriv_lon = next_event["attributes"]["lon"]
    
    if ts_type == "arrival":
        time_param_ms = next_event["attributes"]["start_time"]
    else:
        event_durat_min = prev_event["attributes"]["duration_minutes"]
        event_durat_ms = 60000 * event_durat_min
        time_param_ms = prev_event["attributes"]["start_time"] + event_durat_ms
                            
    start_coords = (dep_lat, dep_lon)
    end_coords = (arriv_lat, arriv_lon)
    ts = time_param_ms / 1000
    
    resp = get_here_route_for_event(start_coords, end_coords, ts, tz_str, 
                                    here_addr, app_id, app_code, ts_type=ts_type)

    try:  
        here_resp = resp.json()
    except HereResponseError:
        logger.warning('The returned response is not a JSON!')
    
    # Validate the HERE response
    if resp.status_code == 200:

        here_resp_summary = here_resp["response"]["route"][0]["summary"]

        here_route_len_m = here_resp_summary["distance"]
        here_route_time_sec = here_resp_summary["travelTime"]
        
        if ts_type == "arrival":
            dep_time_ts_ms = time_param_ms - 1000 * here_route_time_sec
            arriv_time_ts_ms = time_param_ms
        else:
            dep_time_ts_ms = time_param_ms
            arriv_time_ts_ms = time_param_ms + 1000 * here_route_time_sec        
        
        # Fill the outcome data (trip from previous to next)
        trip_data = {}

        trip_data["type"] = "trip"
        trip_data["id"] = dep_time_ts_ms
        trip_data["mobility_type"] = "vehicle"
        trip_data["distance"] = here_route_len_m
        trip_data["trip_start_time"] = dep_time_ts_ms
        trip_data["trip_finish_time"] = arriv_time_ts_ms
        trip_data["start_timezone"] = prev_event["attributes"]["timezone"]
        trip_data["finish_timezone"] = next_event["attributes"]["timezone"]
        
        return trip_data

    else:
        err_message = here_resp['details']
        raise HereResponseError(err_message)  


def check_ts_type(ts_type):
    if not ts_type in ["arrival", "departure"]:
        raise TsTypeValueError("The events data type must be 'arrival' or 'departure'!") 
