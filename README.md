# Happier city bike riders in Helsinki 
This project has been made for the *Introduction to Data Science* course of 2021 at the University of Helsinki.  
**Group : Lea Krautheimer, Antti Kosonen, Katia Chardon**

City bikes are an excellent way to get around the city, but in order for the system to be useful, bike availability needs to be high: users should always find a bike at a station when they need it. Operators balance bikes between stations to achieve this, but these balancing operations can be made much more effective with machine learning!


## Conduct of the project
We will combine the bike journeys and available bikes - data to create a database of bike demand and “natural supply” (users ending their journeys) at each station during the year 2019. The demand calculation needs to also take into account the availability data - you can’t take a bike from a station that is empty, so just looking at journeys starting at stations is biased.

We will try to see if the demand and supply for each station are correlated to:

* The weather,
* The period of the year,
* The day of the week
* The time of day and
* maybe the number of tourists or other variables.  
   
We will then use the data that has correlation to build a predictor model for the optimal balancing operations between stations. That is, how bikes should be moved by truck:  

* From which station,
* To which station,
* How many bikes and
* When  
  
The optimal state is when there are as few “unavailable minutes” (stations with zero bikes) as possible in the system. The learning method is probably regression.

## Available Data

For this project, the main data are bike journeys and available bikes data. We can find these datasets on the HSL website and via API. We have also find a website where all the real-time data on availability of bikes at each station have been collected every five minutes since 2017. We can use this data according to Attribution 4.0 International (CC BY 4.0)-license.  
  
Bike journeys : https://www.hsl.fi/en/hsl/open-data  
Available bikes : https://data.markuskainu.fi/opendata/kaupunkipyorat/  
  
Open Weather Data are available on the Finnish Meteorogical Institute’s website. We have access to meteorogical data like the precipitation amount, the snow depth or the air temperature. Data were collected every 10 min over several years.  
  
Weather : https://en.ilmatieteenlaitos.fi/download-observations  
  
We have found some interesting data on tourism like the number of airport passengers in Finland by airport, the Statistical Yearbook of Helsinki and the number of tourists staying over night in Helsinki. However, we need to look more closely at whether it is possible to use this data in our project and whether it can be useful.  
  
Tourism : https://hri.fi/data/en_GB/dataset/helsingin-tilastollinen-vuosikirja  
https://www.statista.com/statistics/433752/finland-leading-airports-by-passenger-numbers/  
https://hri.fi/data/en_GB/dataset/helsingiss-y-pyvien-matkailijoiden-viipym-tilasto  

The data will be exported to json or csv for storage. The datasets need to be wrangled together - the other datasets need to be made to match the bike availability dataset. That is, for each interval we need to collate the data from all the sources at each station.  
  
We will not use the data for 2020 since it’s influenced by the coronavirus pandemic.  

## Results

The result is a model that operators can use to optimize bike balancing in the citybike system based on the current availability state, date, time and weather forecast (and maybe other variables too).  
  
We can visualize the difference between the current balancing operations and the results that could be achieved with our system. For example we can show how many more minutes per month the stations remain with zero bikes currently, versus when they are balanced according to our predictor model.  
  
The results are communicated in a blog post that shows the improvement in balancing operations that can be achieved by using our model.  
  
The added value of improved balancing operations is better user experience, which in turn leads to more cycling, with all the benefits that entails for society. When users learn that they can always find a bike at a station, the system becomes much more usable.
For citybike operators proven effective balancing operations are a good selling point, when they market their services to other cities that are in the process of selecting an operator for their citybike system.
