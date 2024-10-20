from flask import Flask,render_template,request
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport
import pandas as pd
from pyowm.owm import OWM
from datetime import datetime, timedelta, date
import pickle
from bikePrediction import predict_balancing
import requests
import json
import numpy as np
import re
from api_keys import weather_key, hsl_key

model_arrivals = pickle.load(open('/home/happierbikeridershelsinki/mysite/model_arrivals.pkl','rb'))
model_departures = pickle.load(open('/home/happierbikeridershelsinki/mysite/model_departures.pkl','rb'))

app = Flask(__name__)
predictions_g = None


#Home page
#We print the current weather, current status of the bike system and our predictions for the next 6 hours
@app.route("/")
def index():
#    if date.today().strftime("%m") not in ["04","05","06","07","08","09","10"]:
#        return render_template("sorry.html")
    low, high = predict_balancing()
    weather = get_current_weather()
    return render_template("index.html", low = low, high = high, weather = weather, stations_coord = json.load(open('/home/happierbikeridershelsinki/mysite/stations_coord.json')),bikes = get_bike_data())

def get_current_weather():
    #Returns the current weather information

    owm = OWM(weather_key)
    mgr = owm.weather_manager()

    one_call = mgr.one_call(lat=60.1733244, lon=24.9410248, exclude='minutely,daily,alerts', units='metric')
    cweather = {}
    cweather['icon'] = requests.get("https://api.openweathermap.org/data/3.0/onecall?lat=60.1733244&lon=24.9410248&exclude=minutely,daily,alerts,hourly&appid="+weather_key+"&units=metric").json()["current"]['weather'][0]['icon']
    cweather['temp'] = one_call.current.temp['temp']
    cweather['humidity'] = one_call.current.humidity
    cweather['clouds'] = one_call.current.clouds
    cweather['wind'] = one_call.current.wind()['speed']
    if one_call.current.rain == {}:
        cweather['rain'] = 0
    else:
        cweather['rain'] = one_call.current.rain['1h']
    return cweather


#See times in details page
#We print the map with our predictions for a chosen time
@app.route("/mapsbytime")
def maps():
#    if date.today().strftime("%m") not in ["04","05","06","07","08","09","10"]:
#        return render_template("sorry.html")
    time = request.args.get('time')
    times = get_time()
    stations = json.load(open('/home/happierbikeridershelsinki/mysite/stations_coord.json'))
    if time == None:
        bikes = get_bike_data()
        bike_list = bikes['stationId'].values
        return render_template("maps.html", stations_coord = stations,bikes = bikes, bike_list = bike_list,times = times,selected = datetime.now().strftime('%d/%m/%Y %H:%M'))
    else:
        for i,val in stations.items():
            if re.match('(.)*[a-z]+(.)*',val['stationId']) == None:
                val['stationId'] = int(val['stationId'])
        bikes = get_bikes_for_map()
        bikes = bikes.loc[bikes['datetime']==times.loc[int(time)][0]]
        bike_list = bikes['stationId'].values
        return render_template("maps.html", stations_coord = stations,bikes = bikes, bike_list = bike_list,times = times,selected = times.loc[int(time)][0].strftime('%d/%m/%Y %H:%M'))

def get_time():
    #Returns a list of time. We have every 30min in the next 6hours
    now = datetime.now()
    prediction_time = pd.date_range(now,(now+timedelta(hours=6)),freq='5T')
    prediction_time = prediction_time.round("30min")
    if prediction_time[0] <= pd.to_datetime(now.strftime('%Y-%m-%d %H:%M:00')):
        prediction_time = prediction_time+timedelta(minutes=5)
    prediction_time = pd.DataFrame(prediction_time.unique())
    if prediction_time.loc[prediction_time.index[-1]][0] > pd.to_datetime(now.strftime('%Y-%m-%d %H:%M:00'))+timedelta(hours=6):
        prediction_time.drop(index=prediction_time.index[-1],axis=0,inplace=True)
    return prediction_time

def get_bikes_for_map():
    #Returns a dataframe with our predictions and capacity for each station
    run_model()
    bikes, station_name = predictions_g
    bike_api = get_bike_data()
    bike_api.stationId = bike_api.stationId.astype(int)
    return bikes.merge(bike_api[['stationId','capacity']],left_on="id",right_on="stationId").drop(columns="id").rename(columns={'bikes_evolution':"bikesAvailable","spaces_evolution":"spacesAvailable"})


#See stations in details page
#We show the predictions for the next 6 hours for a chosen station
@app.route("/project")
def project():
#    if date.today().strftime("%m") not in ["04","05","06","07","08","09","10"]:
#        return render_template("sorry.html")
    global predictions_g
    station_id = request.args.get('station')
    run_model()
    prediction, station_name = predictions_g
    if station_id == None:
        return render_template("project.html",predictions = prediction.loc[prediction['id']==204], stations = station_name)
    else:
        return render_template("project.html",predictions = prediction.loc[prediction['id']==int(station_id)], stations = station_name)


def run_model():
    #Get all the needed data and compute the predictons

    #Get current information for each station
    current_bikes = get_bike_data()

    #Creation of a dataframe with the current time
    date = pd.DataFrame(columns=['datetime'])
    date.loc[0]=datetime.now().strftime('%Y-%m-%d %H:%M:00')

    #Adding the current time to the current status of the stations
    current_bikes = current_bikes.assign(key=1).merge(date.assign(key=1), on="key").drop("key", axis=1)
    current_bikes.rename(columns={'bikesAvailable':'bikes_evolution','spacesAvailable':'spaces_evolution','stationId':'id'},inplace=True)

    #Dataframe with the stations used for predictions (we can only use the stations from 2019 and before because our model trained only on these data)
    station_id = pd.DataFrame(pd.read_json("/home/happierbikeridershelsinki/mysite/id.json",typ="series"))
    station_id.rename(columns ={0:'id'},inplace=True)
    station_id.drop_duplicates("id",inplace=True)

    current_bikes['id'] = current_bikes['id'].astype(int)
    station_id['id'] = station_id['id'].astype(int)

    #Dataframe of the names of the stations
    current_bikes2 = current_bikes[['id','name']]
    station_name = station_id.merge(current_bikes2,on='id',how='left')
    station_name = station_name.set_index('id').sort_values(by='name')
    station_name = station_name.dropna()

    #Creation of a dataframe with all the times (every 5min in the next 6hours)
    now = datetime.now()
    prediction_time = pd.date_range(now,(now+timedelta(hours=6)),freq='5T')
    prediction_time = prediction_time.round("5min")
    if prediction_time[0] <= pd.to_datetime(now.strftime('%Y-%m-%d %H:%M:00')):
        prediction_time = prediction_time+timedelta(minutes=5)

    #Weather data dataframe
    weather = get_weather_data()
    weather_data = pd.DataFrame(index=prediction_time,columns=['Cloud amount (1/8)','Relative humidity (%)','Precipitation intensity (mm/h)','Air temperature (degC)','Wind speed (m/s)'])
    for i in weather_data.iterrows():
        weather_row = weather.loc[weather['datetime'] == i[0].strftime('%Y-%m-%d %H:00:00')]
        if weather_row.empty :
            weather_data.drop(index = i[0],inplace=True)
            continue
        i[1]['Cloud amount (1/8)'] = weather_row['Cloud amount (1/8)'].iloc[0]
        i[1]['Relative humidity (%)'] = weather_row['Relative humidity (%)'].iloc[0]
        i[1]['Precipitation intensity (mm/h)'] = weather_row['Precipitation intensity (mm/h)'].iloc[0]
        i[1]['Air temperature (degC)'] = weather_row['Air temperature (degC)'].iloc[0]
        i[1]['Wind speed (m/s)'] = weather_row['Wind speed (m/s)'].iloc[0]
    weather_data['time'] = weather_data.index.strftime('%H:%M:00')

    #Dataframe to convert the time to an int
    time_convert = pd.DataFrame(pd.date_range(start="00:00:00",end="23:55:00",freq ='5T').strftime('%H:%M:%S'))
    time_convert.rename(columns = {0:'time'}, inplace = True)
    time_convert['to_int'] = pd.RangeIndex(start=1,stop=time_convert.shape[0]+1)
    time_convert = time_convert.set_index('time')

    #Adding the time as an int
    weather_data = weather_data.join(time_convert,on="time")
    weather_data.drop(columns="time",inplace=True)
    weather_data.rename(columns = {'to_int':'time'}, inplace = True)

    #Adding the other needed columns
    weather_data.index = pd.to_datetime(weather_data.index)
    weather_data['datetime'] = weather_data.index
    weather_data['day_of_week'] = weather_data.index.dayofweek
    weather_data['day_of_year'] = weather_data.index.dayofyear

    #Creating the final dataframe to be used in the model for predictions
    data = weather_data.assign(key=1).merge(station_id.assign(key=1), on="key").drop("key", axis=1)

    #Predicted departures dataframe
    predictions = [ elem for elem in model_departures.predict(data[['id','time','day_of_week','day_of_year','Cloud amount (1/8)','Relative humidity (%)','Precipitation intensity (mm/h)','Air temperature (degC)','Wind speed (m/s)']].values.reshape(-1, 9))]
    departures_prediction = pd.concat([pd.DataFrame(predictions),pd.DataFrame(data[['id','datetime']])],axis=1).rename(columns={0:'bike_departures'})

    #Predicted arrivals dataframe
    predictions = [ elem for elem in model_arrivals.predict(data[['id','time','day_of_week','day_of_year','Cloud amount (1/8)','Relative humidity (%)','Precipitation intensity (mm/h)','Air temperature (degC)','Wind speed (m/s)']].values.reshape(-1, 9))]
    arrivals_prediction = pd.concat([pd.DataFrame(predictions),pd.DataFrame(data[['id','datetime']])],axis=1).rename(columns={0:'bike_arrivals'})

    #Computing the evolution of the number of bikes and spaces in each station every 5 min
    predict_df = arrivals_prediction.merge(departures_prediction, how='outer', on=['id','datetime'])
    predict_df = predict_df.fillna(0)

    predict_df['bikes_evolution'] = predict_df['bike_arrivals'] - predict_df['bike_departures']
    predict_df['spaces_evolution'] = -1 * predict_df['bikes_evolution']

    predict_df.drop(columns=['bike_arrivals','bike_departures'],inplace=True)
    predict_df = pd.concat([predict_df[['datetime','id','bikes_evolution','spaces_evolution']],current_bikes[['datetime','id','bikes_evolution','spaces_evolution']]])
    predict_df['datetime'] = pd.to_datetime(predict_df['datetime'] )

    predict_df = predict_df.sort_values(by='datetime')

    predict_df2 = predict_df.groupby(['id']).cumsum()
    predict_df2 = predict_df2.assign(id=predict_df['id'])
    predict_df2 = predict_df2.assign(datetime = predict_df['datetime'])

    predict_df2 = predict_df2.merge(current_bikes[['id','name']],on='id',how='left')

    predict_df2['bikes_evolution'] = predict_df2['bikes_evolution'].round().astype(int)
    predict_df2['spaces_evolution'] = predict_df2['spaces_evolution'].round().astype(int)

    global predictions_g
    predictions_g = predict_df2.sort_values(by=['id','datetime']), station_name


def get_bike_data():
    #Returns the current bike data
    transport = RequestsHTTPTransport(
    url="https://api.digitransit.fi/routing/v1/routers/hsl/index/graphql?digitransit-subscription-key="+hsl_key, verify=True, retries=3)

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

    result = client.execute(query)

    current_bikes = pd.DataFrame(result['bikeRentalStations'])

    #I drop the IDs containing letters
    id_drop = current_bikes[current_bikes.stationId.str.contains('[^0-9]')].index
    current_bikes.drop(id_drop,axis=0,inplace=True)

    return current_bikes


def get_weather_data():
    #Returns the predicted weather data in the next 6 hours
    now = datetime.now()
    df = pd.DataFrame(columns=["datetime",'Wind speed (m/s)','Relative humidity (%)','Air temperature (degC)','Precipitation intensity (mm/h)','Cloud amount (1/8)'])

    owm = OWM(weather_key)
    mgr = owm.weather_manager()

    one_call = mgr.one_call(lat=60.1733244, lon=24.9410248, exclude='minutely,daily,alerts', units='metric')
    n = 0
    for i in one_call.forecast_hourly:
        row = {"datetime":(now+timedelta(hours=n)).strftime("%Y-%m-%d %H:00:00"),'Wind speed (m/s)':i.wind()['speed'],'Relative humidity (%)':i.humidity,'Air temperature (degC)':i.temperature()['temp'],'Precipitation intensity (mm/h)':i.rain,'Cloud amount (1/8)':i.clouds}
        if row['Precipitation intensity (mm/h)'] == {}:
            row['Precipitation intensity (mm/h)'] = 0
        else:
            row['Precipitation intensity (mm/h)'] = row['Precipitation intensity (mm/h)']['1h']
        row['Cloud amount (1/8)'] = round((row['Cloud amount (1/8)']*8)/100)
        df = pd.concat([df,pd.DataFrame(row,index=[0])],ignore_index=True)
        n +=1
        if n == 7:
            break

    df['datetime'] = pd.to_datetime(df['datetime'])
    return df



#About page
@app.route("/about")
def presentation():
    return render_template("about.html")

