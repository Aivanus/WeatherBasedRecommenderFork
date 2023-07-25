import copy
from fmiopendata.wfs import download_stored_query
from .poi import PointOfInterest

class Current:
    def __init__(self):
        self.weather = None
        self.aqi = None
        self.get_current_weather()
        self.get_current_airquality()

    def get_current_weather(self):
        '''
        Retrieves the current weather data for various stations.

        Returns:
            dict: A dictionary containing the current weather data for each station.
        '''

        obs = download_stored_query('fmi::observations::weather::multipointcoverage',
                                    args=['bbox=24.5,60,25.5,60.5', 'timeseries=True'])
        data = {}
        for station, metadata in obs.location_metadata.items():
            weatherdata = {
                'Air temperature': str(obs.data[station]['t2m']['values'][-1]) + ' °C',
                'Wind speed': str(obs.data[station]['ws_10min']['values'][-1]) + ' m/s',
                'Humidity': str(obs.data[station]['rh']['values'][-1]) + ' %',
                'Precipitation': str(obs.data[station]['ri_10min']['values'][-1]) + ' mm',
                'Cloud amount': str(obs.data[station]['n_man']['values'][-1]) + ' %',
            }
            for value in list(weatherdata):
                if 'nan' in str(weatherdata[value]):
                    weatherdata.pop(value)
            if weatherdata:
                weatherdata['Latitude'] = metadata['latitude']
                weatherdata['Longitude'] = metadata['longitude']
                data[station] = weatherdata
        self.weather = data

    def get_current_airquality(self):
        '''
        Retrieves the current AQI data for various stations.

        Returns:
            dict: A dictionary containing the current weather data for each station.
        '''
        obs = download_stored_query('urban::observations::airquality::hourly::multipointcoverage',
                                    args=['bbox=24.5,60,25.5,60.5', 'timeseries=True'])
        data = {}
        for station, metadata in obs.location_metadata.items():
            aqidata = {
                'Air quality': str(obs.data[station]['AQINDEX_PT1H_avg']['values'][-1]) + ' AQI'
            }
            for value in list(aqidata):
                if 'nan' in str(aqidata[value]):
                    aqidata.pop(value)
            if aqidata:
                aqidata['Latitude'] = metadata['latitude']
                aqidata['Longitude'] = metadata['longitude']
                data[station] = aqidata
        self.aqi = data

    def find_nearest_stations_weather_data(self, poi: PointOfInterest):
        '''
        Finds the nearest weather station to a given point of interest (POI) and adds its weather data to the POI,
        also adds the Air Quality Index data.

        Args:
            poi (PointOfInterest): The POI for which weather data needs to be added.

        Returns:
            PointOfInterest: The modified POI with weather information.

        '''
        lat = poi.latitude
        lon = poi.longitude
        weather = copy.deepcopy(self.weather)
        aqi = copy.deepcopy(self.aqi)
        missing_fields = ['Air temperature', 'Wind speed', 'Precipitation', 'Cloud amount', 'Humidity']
        returned = {}
        while True:
            smallest, nearest = float('inf'), ''
            for station in weather:
                dist = abs(weather[station]['Latitude'] - lat)\
                                        + abs(weather[station]['Longitude'] - lon)
                if dist < smallest:
                    smallest, nearest = dist, station
            for key, value in weather[nearest].items():
                if key not in ['Latitude', 'Longitude']:
                    returned.setdefault(key, value)
                    if key in missing_fields:
                        missing_fields.remove(key)
            if not missing_fields or not weather:
                smallest, nearest = float('inf'), ''
                for station in aqi:
                    dist = abs(aqi[station]['Latitude'] - lat)\
                                            + abs(aqi[station]['Longitude'] - lon)
                    if dist < smallest:
                        smallest, nearest = dist, station
                returned.setdefault('Air quality', aqi[nearest]['Air quality'])
                break
            del weather[nearest]
        poi.weather['Current'] = returned
        return poi
