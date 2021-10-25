import numpy as np
import pickle
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport
from datetime import datetime, timedelta
from math import floor
from pyowm.owm import OWM

#There are now more stations than there were during 2018-2019.
#We can only make predictions for the latter.
stations_in_dataset = [76.0, 64.0, 30.0, 69.0,  6.0, 11.0, 118.0, 130.0, 44.0, 46.0, 86.0, 89.0,  8.0, 31.0, 122.0, 29.0, 123.0, 38.0, 114.0, 24.0, 33.0,  7.0, 23.0, 60.0, 120.0, 17.0, 21.0, 22.0, 70.0, 18.0, 27.0, 28.0, 63.0, 25.0, 26.0,  5.0,  1.0, 78.0, 117.0, 12.0, 19.0, 137.0, 39.0, 75.0, 53.0, 43.0, 121.0, 10.0, 127.0, 133.0,  3.0, 129.0, 48.0, 14.0, 83.0, 20.0, 58.0, 125.0, 116.0, 113.0, 62.0, 42.0, 68.0, 115.0, 128.0, 40.0, 134.0, 110.0, 61.0, 105.0, 149.0, 36.0, 73.0, 109.0, 34.0, 45.0, 32.0, 81.0, 54.0, 57.0, 95.0, 101.0, 74.0, 15.0,  4.0, 50.0, 52.0, 144.0, 150.0, 13.0, 108.0, 16.0, 96.0, 141.0, 147.0,  2.0, 136.0, 65.0, 135.0, 146.0, 142.0, 56.0, 71.0, 82.0, 94.0, 119.0, 79.0, 111.0, 131.0, 140.0, 138.0, 106.0, 103.0, 112.0, 139.0, 148.0, 107.0, 104.0, 99.0, 93.0, 51.0, 91.0, 41.0, 997.0, 66.0, 145.0, 47.0, 157.0, 162.0, 59.0, 77.0, 88.0, 90.0, 84.0, 132.0, 100.0, 92.0, 49.0, 67.0, 80.0, 72.0, 155.0, 161.0, 163.0, 124.0, 156.0, 35.0, 87.0, 999.0, 159.0, 55.0, 143.0, 126.0, 547.0, 531.0, 545.0, 543.0, 507.0, 527.0, 529.0, 597.0, 563.0, 555.0, 537.0, 533.0, 631.0, 619.0, 617.0, 607.0, 601.0, 603.0, 609.0, 615.0, 541.0, 587.0, 539.0, 621.0, 611.0, 613.0, 623.0, 589.0, 585.0, 583.0, 653.0, 523.0, 581.0, 651.0, 575.0, 517.0, 573.0, 521.0, 557.0, 637.0, 647.0, 577.0, 509.0, 511.0, 645.0, 519.0, 595.0, 633.0, 591.0, 571.0, 565.0, 639.0, 561.0, 635.0, 525.0, 643.0, 641.0, 513.0, 627.0, 559.0, 629.0, 515.0, 505.0, 593.0, 625.0, 579.0, 553.0, 503.0, 551.0, 85.0, 37.0, 98.0, 596.0, 715.0, 713.0, 717.0, 707.0, 735.0, 723.0, 649.0, 701.0, 711.0, 721.0, 705.0, 727.0, 719.0, 729.0, 725.0, 733.0, 737.0, 769.0, 741.0, 749.0, 761.0, 763.0, 751.0, 739.0, 745.0, 753.0, 755.0, 757.0, 767.0, 765.0, 747.0, 709.0, 549.0, 501.0, 731.0, 901.0, 998.0, 235.0, 202.0, 240.0, 233.0, 230.0, 206.0, 239.0, 703.0, 231.0, 532.0, 242.0, 241.0, 518.0, 203.0, 228.0, 224.0, 221.0, 207.0, 236.0, 208.0, 234.0, 227.0, 210.0, 244.0, 246.0, 226.0, 229.0, 220.0, 259.0, 213.0, 237.0, 225.0, 217.0, 232.0, 268.0, 218.0, 258.0, 219.0, 222.0, 256.0, 262.0, 260.0, 211.0, 245.0, 255.0, 254.0, 238.0, 223.0, 257.0, 261.0, 263.0, 273.0, 270.0, 275.0, 265.0, 284.0, 276.0, 274.0, 272.0, 209.0, 214.0, 215.0, 271.0, 249.0, 538.0, 264.0, 248.0, 247.0, 253.0, 279.0, 252.0, 280.0, 285.0, 243.0, 286.0, 278.0, 212.0, 269.0, 281.0, 250.0, 200.0, 201.0, 283.0, 277.0, 216.0, 205.0, 282.0, 267.0, 266.0, 900.0, 251.0, 204.0, 290.0, 292.0, 291.0, 151.0]
key = "b4a8cf502c2afc3ecbfed7b30c2b831c"

def get_current_station_status():
    transport = RequestsHTTPTransport(
    url="https://api.digitransit.fi/routing/v1/routers/hsl/index/graphql",
    verify=True, retries=3,)

    client = Client(transport=transport, fetch_schema_from_transport=True)

    query = gql(
        """
        query {
            bikeRentalStations {
                bikesAvailable
                spacesAvailable
                stationId
                name
                capacity
                }
            }
        """
    )
    return client.execute(query)

def get_time_codes():
    #returns array of arrays of the time numbers for the next 6 hours
    now = datetime.now().replace(microsecond=0)
    times = []
    for i in range(72):
        time = floor((now - now.replace(hour=0, minute=0, second=0, microsecond=0)).total_seconds()/300)
        times.append([time, now.weekday(), now.timetuple().tm_yday, now.strftime("%Y-%m-%d, %H:%M")])
        now += timedelta(minutes=5)
    return times

def get_weather():
    owm = OWM(key)
    mgr = owm.weather_manager()
    one_call = mgr.one_call(lat=60.1733244, lon=24.9410248, exclude='minutely,daily,alerts', units='metric')
    n = 0
    weather = []
    for i in one_call.forecast_hourly:
        rain = (i.rain.get('1h'), 0)[i.rain.get('1h') == None]
        weather.append([i.clouds*8/100, i.humidity, rain, i.temperature()['temp'], i.wind()['speed']])
        n +=1
        if n == 7:
            break
    return weather


def predict_balancing():
    arrival_model = pickle.load(open('/home/happierbikeridershelsinki/mysite/model_arrivals.pkl','rb'))
    departure_model = pickle.load(open('/home/happierbikeridershelsinki/mysite/model_departures.pkl','rb'))
    station_status = get_current_station_status()
    times = get_time_codes()
    weather = get_weather()

    need_more_bikes = []
    overflow_of_bikes = []
    for i in station_status['bikeRentalStations']:
        station = float(i['stationId'])
        capacity = float(i['capacity'])
        if station not in stations_in_dataset:
            continue
        bikes = i['bikesAvailable']
        spaces = i['spacesAvailable']
        for j in range(len(times)):
            time, day_of_week, day_of_year, human_readable = times[j]
            cloud, humidity, precipitation, temperature, wind = weather[floor(j/12)]
            data = np.array([station,time, day_of_week, day_of_year, cloud, humidity, precipitation, temperature, wind]).reshape(-1, 9)
            bikes = bikes + arrival_model.predict(data) - departure_model.predict(data)
            if(bikes <= 1):
                need_more_bikes.append((human_readable, i['name']))
                break
            if(capacity == 0):
                capacity = bikes + spaces
                if(bikes >= capacity + 10):
                    overflow = bikes-capacity
                    overflow_of_bikes.append((human_readable, i['name'], round(overflow[0])))
                    break
            else:
                if(bikes >= capacity + 10):
                    overflow = bikes-capacity
                    overflow_of_bikes.append((human_readable, i['name'], round(overflow[0])))
                    break

    return sorted(need_more_bikes), sorted(overflow_of_bikes)
