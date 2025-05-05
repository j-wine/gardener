import requests
import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException

from .logging import logger
from .models import Plant


# Helper function for calculating temperature suitability scores

def calculate_temperature_suitability(temperature_min, temperature_max, temperature_mean, plant):
    """
    Calculate daily temperature suitability based on min, max, and mean temperatures relative to the plant's tolerance ranges.
    This function uses a linear scoring mechanism, combining the contributions from the three temperature values.
    """

    # Temperature suitability score calculation (mean)
    if plant.TOPMN <= temperature_mean <= plant.TOPMX:
        temp_mean_score = 100  # Perfect score within the optimal range
    elif plant.TMIN <= temperature_mean < plant.TOPMN:
        temp_mean_score = 50 + 50 * (temperature_mean - plant.TMIN) / (
                    plant.TOPMN - plant.TMIN)  # Linear between TMIN and TOPMN
    elif plant.TOPMX < temperature_mean <= plant.TMAX:
        temp_mean_score = 50 + 50 * (plant.TMAX - temperature_mean) / (
                    plant.TMAX - plant.TOPMX)  # Linear between TOPMX and TMAX
    else:
        deviation = abs(temperature_mean - (plant.TMAX if temperature_mean > plant.TMAX else plant.TMIN))
        temp_mean_score = max(0, 100 - deviation * 10)  # Aggressively reduce score for extreme deviations

    # Temperature suitability score calculation (min)
    if plant.TOPMN <= temperature_min <= plant.TOPMX:
        temp_min_score = 100  # Perfect score within the optimal range
    elif plant.TMIN <= temperature_min < plant.TOPMN:
        temp_min_score = 50 + 50 * (temperature_min - plant.TMIN) / (plant.TOPMN - plant.TMIN)
    elif plant.TOPMX < temperature_min <= plant.TMAX:
        temp_min_score = 50 + 50 * (plant.TMAX - temperature_min) / (plant.TMAX - plant.TOPMX)
    else:
        deviation = abs(temperature_min - (plant.TMAX if temperature_min > plant.TMAX else plant.TMIN))
        temp_min_score = max(0, 100 - deviation * 10)

    # Temperature suitability score calculation (max)
    if plant.TOPMN <= temperature_max <= plant.TOPMX:
        temp_max_score = 100  # Perfect score within the optimal range
    elif plant.TMIN <= temperature_max < plant.TOPMN:
        temp_max_score = 50 + 50 * (temperature_max - plant.TMIN) / (plant.TOPMN - plant.TMIN)
    elif plant.TOPMX < temperature_max <= plant.TMAX:
        temp_max_score = 50 + 50 * (plant.TMAX - temperature_max) / (plant.TMAX - plant.TOPMX)
    else:
        deviation = abs(temperature_max - (plant.TMAX if temperature_max > plant.TMAX else plant.TMIN))
        temp_max_score = max(0, 100 - deviation * 10)

    # Average the temperature scores
    temp_score = (temp_mean_score + temp_min_score + temp_max_score) / 3
    return temp_score


def calculate_suitability_score(weather_data, plant) -> int:
    """
    Calculate the overall suitability score [0,100] for a 30-day period based on historical daily weather data.
    This approach averages daily temperature suitability scores and uses a fixed precipitation score.
    """

    # Sum up the precipitation over 30 days and annualize it
    total_precipitation_30_days = sum(weather_data['precipitation_sum'])
    annualized_precipitation = total_precipitation_30_days * (365 / 30)  # Scale the 30-day total to an annual value

    # Calculate the precipitation suitability score once
    if plant.ROPMN <= annualized_precipitation <= plant.ROPMX:
        precip_score = 100  # Perfect score within the optimal range
    elif plant.RMIN <= annualized_precipitation < plant.ROPMN:
        precip_score = 50 + 50 * (annualized_precipitation - plant.RMIN) / (plant.ROPMN - plant.RMIN)
    elif plant.ROPMX < annualized_precipitation <= plant.RMAX:
        precip_score = 50 + 50 * (plant.RMAX - annualized_precipitation) / (plant.RMAX - plant.ROPMX)
    else:
        deviation = abs(
            annualized_precipitation - (plant.RMAX if annualized_precipitation > plant.RMAX else plant.RMIN))
        precip_score = max(0, 100 - deviation * 10)

    logger.info(f"Annualized Precipitation: {annualized_precipitation}, Precipitation Score: {precip_score}")

    suitability_scores = []

    # Calculate temperature suitability for each day's weather data
    for temp_min, temp_max, temp_mean in zip(
            weather_data['temperature_2m_min'],
            weather_data['temperature_2m_max'],
            weather_data['temperature_2m_mean']):
        temp_score = calculate_temperature_suitability(temp_min, temp_max, temp_mean, plant)
        daily_score = (temp_score + precip_score) / 2  # Combine temperature and precipitation scores
        suitability_scores.append(daily_score)

    # Log the overall suitability score
    logger.info(f"Suitability scores for the 30 days: {suitability_scores}")

    # Return the average suitability score over the 30-day period
    final_suitability_score = sum(suitability_scores) / len(suitability_scores)

    return int(final_suitability_score)


async def get_plant_data_by_scientific_name(scientific_name: str, session: AsyncSession) -> Plant:
    """
    Retrieve plant data from the database using the scientific name.
    Raises a 404 HTTPException if the plant is not found in the database.
    """
    query = select(Plant).where(Plant.ScientificName.ilike(scientific_name))
    result = await session.execute(query)
    plant = result.scalars().first()
    if not plant:
        raise HTTPException(status_code=404, detail="Plant not found")
    return plant


async def get_weather_and_suitability(location, scientific_name, session: AsyncSession):
    """
    Fetch weather data for a given location and calculate the suitability of the location for growing the specified plant
    The process involves:
    1. Geocoding the location to obtain latitude and longitude.
    2. Retrieving plant data based on the scientific name.
    3. Fetching historical weather data for the last 30 days.
    4. Calculating the plant suitability score
    """

    # Geocode the location to get latitude and longitude
    if isinstance(location, tuple):
        latitude, longitude = location
    else:
        geocode_url = f"https://geocode.xyz/{location}?json=1"
        geocode_response = requests.get(geocode_url)
        geocode_data = geocode_response.json()
        latitude = float(geocode_data['latt'])
        longitude = float(geocode_data['longt'])

    # Step 2: Fetch plant data from the database
    plant = await get_plant_data_by_scientific_name(scientific_name, session)

    # Step 3: Fetch forecast  weather data for next 14 days (+today)
    start_date = datetime.date.today()
    end_date = start_date + datetime.timedelta(days=15)

    # weather_url = f"https://archive-api.open-meteo.com/v1/archive?latitude={latitude}&longitude={longitude}&start_date={start_date}&end_date={end_date}&daily=temperature_2m_max,temperature_2m_min,temperature_2m_mean,precipitation_sum"
    weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&start_date={start_date}&end_date={end_date}&daily=temperature_2m_max,temperature_2m_min,temperature_2m_mean,precipitation_sum"

    logger.debug(f"Weather API URL: {weather_url}")

    weather_response = requests.get(weather_url)
    if weather_response.status_code != 200:
        logger.error(f"Failed to retrieve weather data: {weather_response.text}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve weather data: {weather_response.text}")

    weather_data = weather_response.json()
    if 'daily' not in weather_data:
        logger.error("No daily weather data found in the API response.")
        raise HTTPException(status_code=500, detail="No daily weather data found in the API response.")

    daily_weather = weather_data.get("daily", {})
    temperature_2m_max = [t for t in daily_weather.get('temperature_2m_max', []) if t is not None]
    temperature_2m_min = [t for t in daily_weather.get('temperature_2m_min', []) if t is not None]
    temperature_2m_mean = [t for t in daily_weather.get('temperature_2m_mean', []) if t is not None]
    precipitation_sum = [p for p in daily_weather.get('precipitation_sum', []) if p is not None]

    if not temperature_2m_max or not temperature_2m_min or not temperature_2m_mean or not precipitation_sum:
        logger.error(f"Temperature or precipitation data missing or invalid: {daily_weather}")
        raise HTTPException(status_code=500, detail="Temperature or precipitation data missing or invalid.")

    # Log weather data for debugging
    logger.debug(f"Temperature Max Data: {temperature_2m_max}")
    logger.debug(f"Temperature Min Data: {temperature_2m_min}")
    logger.debug(f"Temperature Mean Data: {temperature_2m_mean}")
    logger.debug(f"Precipitation Data: {precipitation_sum}")

    # Calculate the final suitability score using the daily max/min/mean temperatures and annualized precipitation
    final_suitability_score = calculate_suitability_score(
        {"temperature_2m_max": temperature_2m_max, "temperature_2m_min": temperature_2m_min,
         "temperature_2m_mean": temperature_2m_mean, "precipitation_sum": precipitation_sum},
        plant
    )

    response_data = {
        "location": location,
        "latitude": latitude,
        "longitude": longitude,
        "plant_name": plant.ScientificName,
        "suitability_details": {
            "suitability_score": final_suitability_score,
            "interval_used": 30  # Indicates the 30-day interval used for the calculation
        },
        "weather_data": {
            "temperature_2m_mean": temperature_2m_mean,
            "precipitation_sum": precipitation_sum
        }
    }

    return response_data
