import os

import pandas as pd
import streamlit as st
import requests
import datetime
import matplotlib.pyplot as plt
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv
from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage

os.environ["OPENAI_API_KEY"] = "dummy"
def _clean_llm_output(generated_text):
    # # First, cut off the text at "P.S." if it exists
    # if "P.S." in generated_text:
    #     generated_text = generated_text.split("P.S.")[0]
    #
    # # Then, remove any Python code-like content starting with common keywords
    # stop_keywords = ["python", "import", "def", "class"]
    # for keyword in stop_keywords:
    #     if keyword in generated_text:
    #         generated_text = generated_text.split(keyword)[0]  # Stop at the first occurrence of any keyword
    #
    # # Final clean-up to remove any extraneous symbols or unwanted tokens
    # clean_text = generated_text.replace("</s>", "").strip()

    # return clean_text
    return generated_text
# Load environment variables from .env file if it exists
load_dotenv()

# Set up base URL and port for backend API
base_url = os.getenv("BACKEND_URL", "http://localhost")
port = int(os.getenv("BACKEND_PORT", 8000))

api_url = f"{base_url}:{port}"

client = ChatOpenAI(
    base_url="https://models.mylab.th-luebeck.dev/v1",
    model="llama-3.3-70b",
    temperature=0.25,
    streaming=True
)
#  BASE_URL = https://models.mylab.th-luebeck.dev/v1/chat/completions
# Define the refined prompt template with a fun, personalized touch
prompt_template = PromptTemplate.from_template("""
system
You are a friendly and quirky gardening gnome with a deep knowledge of botany. Your task is to analyze the growing conditions for a given plant at a specific location based on the provided weather data, plant requirements, and a calculated suitability score. Please provide your analysis in a fun and engaging way, adding a bit of personality to your responses.

user
Location: {location} (Latitude: {latitude}, Longitude: {longitude})
Date: {current_date}

Plant: {plant_name}
- Optimal Temperature Range: {topmn}-{topmx} °C
- Absolute Temperature Range: {tmin}-{tmax} °C
- Optimal Precipitation Range: {ropmn}-{ropmx} mm
- Absolute Precipitation Range: {rmin}-{rmax} mm

Weather Data for the Past 30 Days:
- Average Temperatures: {temperature_data}
- Precipitation: {precipitation_data}

Suitability Score: {suitability_score}
Suitability Score Legend: 
- 0-20: 🌧️ Very Poor - Conditions are not suitable for this plant.
- 21-40: 😟 Poor - The plant might struggle to grow.
- 41-60: 🤔 Moderate - Conditions are marginally acceptable.
- 61-80: 🙂 Good - Conditions are favorable for this plant.
- 81-100: 🌞 Excellent - Ideal growing conditions.

Warnings: {warnings}

### Response Instructions:
1. Greet the user in a fun way.
2. Provide an overview of the location and plant.
3. Analyze the temperature and precipitation data in a creative, storytelling manner.
4. Discuss the implications of the location’s latitude and longitude with some quirky comments.
5. Provide practical gardening advice in a friendly tone.
6. Conclude with a motivational message, encouraging the user to enjoy gardening.

Make sure to keep the response light-hearted and enjoyable!
""")

# Custom CSS for a better table display
st.markdown(
    """
    <style>
    /* Styling table for compact layout */
    .custom-table {
        width: 100%;
        max-height: 500px;
        overflow-y: scroll;
        margin: 0 auto;
        border-collapse: collapse;
        font-size: 12px;
    }

    .custom-table th, .custom-table td {
        padding: 8px 12px;
        text-align: left;
        border: 1px solid #ddd;
    }

    .custom-table th {
        background-color: #f4f4f4;
    }

    .custom-table tr:nth-child(even) {
        background-color: #f9f9f9;
    }

    </style>
    """, unsafe_allow_html=True
)

st.title("🌱 Gardening Helper 🧑‍🌾")

# Fetch all plant names from the backend API
plants_url = f"{api_url}/plants/"
print(plants_url)
plants_response = requests.get(plants_url)

if plants_response.status_code == 200:
    plants_data = plants_response.json()
    plant_names = [plant['ScientificName'] for plant in plants_data]
else:
    st.error("🚨 Failed to fetch plant names from the backend. Please try again later.")
    plant_names = []

# Location input with an example
location = st.text_input("🏡 Enter your location (city or address):", placeholder="e.g., Hamburg, Germany")

# Use a searchable dropdown for plant names
plant_name = st.selectbox("🌿 Select a plant (optional):", options=plant_names)

# Fetch and display plant details before proceeding

if plant_name:
    plant_details_url = f"{api_url}/plants/scientific_name/{plant_name}"
    plant_details_response = requests.get(plant_details_url)

    if plant_details_response.status_code == 200:
        plant_details = plant_details_response.json()[0]  # We expect one plant per scientific name

        st.subheader(f"🌿 Plant Details: {plant_name}")
        st.write(
            "Here are the details for the selected plant. Optionally review and download them as .csv before proceeding to calculate suitabiltiy score.")

        field_descriptions = {
            'EcoPortCode': 'A unique identifier for each crop entry in the database.',
            'ScientificName': 'The scientific (Latin) name of the plant species.',
            'AUTH': 'The author who described the species scientifically.',
            'FAMNAME': 'The botanical family.',
            'SYNO': 'Synonyms or alternative names.',
            'COMNAME': 'Common names in various languages.',
            'LIFO': 'Life form (herb, shrub, tree, etc.).',
            'HABI': 'Habitat where the plant is found.',
            'LISPA': 'Life span (annual, biennial, perennial, etc.).',
            'PHYS': 'Physical structure (single stem, multi-stem).',
            'CAT': 'Category or use (vegetables, fruits, etc.).',
            'PLAT': 'Plant attributes (deciduous, evergreen, etc.).',
            'TOPMN': 'Optimal minimum temperature (°C).',
            'TOPMX': 'Optimal maximum temperature (°C).',
            'TMIN': 'Absolute minimum temperature (°C).',
            'TMAX': 'Absolute maximum temperature (°C).',
            'ROPMN': 'Optimal minimum rainfall (mm/year).',
            'ROPMX': 'Optimal maximum rainfall (mm/year).',
            'RMIN': 'Absolute minimum rainfall (mm/year).',
            'RMAX': 'Absolute maximum rainfall (mm/year).',
            'PHOPMN': 'Optimal minimum soil pH.',
            'PHOPMX': 'Optimal maximum soil pH.',
            'PHMIN': 'Absolute minimum soil pH level.',
            'PHMAX': 'Absolute maximum soil pH level.',
            'LATOPMN': 'Optimal minimum latitude where the plant can grow.',
            'LATOPMX': 'Optimal maximum latitude where the plant can grow.',
            'LATMN': 'Absolute minimum latitude where the plant can survive.',
            'LATMX': 'Absolute maximum latitude where the plant can survive.',
            'ALTMX': 'Maximum altitude (in meters above sea level) where the plant can grow.',
            'LIOPMN': 'Optimal minimum light intensity required for growth.',
            'LIOPMX': 'Optimal maximum light intensity suitable for growth.',
            'LIMN': 'Absolute minimum light intensity the plant can tolerate.',
            'LIMX': 'Absolute maximum light intensity the plant can tolerate.',
            'DEP': 'Optimal soil depth (in cm) required for the plant’s root system.',
            'DEPR': 'Range of soil depth suitable for the plant.',
            'TEXT': 'Soil texture preference (heavy, medium, light, or organic).',
            'TEXTR': 'Range of soil textures the plant can tolerate.',
            'FER': 'Fertility requirement for the plant to grow optimally.',
            'FERR': 'Fertility range that the plant can tolerate.',
            'TOX': 'Toxicity levels that the plant can tolerate.',
            'TOXR': 'Range of toxicity levels tolerable by the plant.',
            'SAL': 'Salinity levels suitable for the plant’s growth.',
            'SALR': 'Range of salinity levels the plant can tolerate.',
            'DRA': 'Drainage preference for the soil where the plant grows.',
            'DRAR': 'Range of drainage conditions tolerable by the plant.',
            'KTMPR': 'Range of killing temperature for the plant.',
            'KTMP': 'Absolute killing temperature where the plant dies.',
            'PHOTO': 'Photoperiod requirement (short day, neutral day, long day).',
            'CLIZ': 'Climatic zone where the plant grows optimally.',
            'ABITOL': 'Additional biotic tolerance levels (e.g., pest resistance).',
            'ABISUS': 'Additional biotic susceptibility (specific pests or diseases).',
            'INTRI': 'Intraspecific relationships (e.g., self-compatible, dioecious).',
            'PROSY': 'Propagation system or method (how the plant is propagated).',
            'GMIN': 'Minimum growing cycle length (in days).',
            'GMAX': 'Maximum growing cycle length (in days).'

        }

        # Prepare data for download
        plant_df = pd.DataFrame({
            "Field": list(plant_details.keys()),
            "Description": [field_descriptions.get(key, "No description available.") for key in plant_details.keys()],
            "Value": [str(v) for v in plant_details.values()]  # Explicit string conversion
        })
        # Convert the DataFrame as strings and to CSV for download
        plant_csv = plant_df.astype(str).to_csv(index=False).encode('utf-8')

        # Provide a download button for the plant data
        st.download_button(
            label="📥 Download Plant Data as CSV",
            data=plant_csv,
            file_name=f"{plant_name}_details.csv",
            mime='text/csv',
        )
        if st.button("🌟 Calculate Suitability 🌟", disabled=not location):
            plant_details_url = f"{api_url}/plants/scientific_name/{plant_name}"
            plant_details_response = requests.get(plant_details_url)

            if plant_details_response.status_code == 200:
                plant_details = plant_details_response.json()[0]

                # Fetch plant suitability data from backend API
                suitability_url = f"{api_url}/plants/suitability/{plant_name}?location={location}"
                suitability_response = requests.get(suitability_url)

                if suitability_response.status_code == 200:
                    suitability_data = suitability_response.json()

                    latitude = suitability_data['latitude']
                    longitude = suitability_data['longitude']
                    suitability_score = suitability_data['suitability_details']['suitability_score']
                    st.subheader("📈 Suitability Score Legend")
                    st.write("""
                            - **0-20:** 🌧️ Very Poor - Conditions are not suitable for this plant.
                            - **21-40:** 😟 Poor - The plant might struggle to grow.
                            - **41-60:** 🤔 Moderate - Conditions are marginally acceptable.
                            - **61-80:** 🙂 Good - Conditions are favorable for this plant.
                            - **81-100:** 🌞 Excellent - Ideal growing conditions.
                        """)
                    st.subheader(f"🌟 Suitability Score for {plant_name} at {location}: {suitability_score} 🌟")

                    weather_data = suitability_data['weather_data']
                    st.subheader("📊 Weather Data (Next 14 Days):")

                    fig, ax1 = plt.subplots()
                    ax1.plot(weather_data['temperature_2m_mean'], label='Temperature (°C)', color='orange', marker='o')
                    ax1.set_xlabel('Days')
                    ax1.set_ylabel('Temperature (°C)', color='orange')
                    ax1.tick_params(axis='y', labelcolor='orange')

                    ax2 = ax1.twinx()
                    ax2.bar(range(len(weather_data['precipitation_sum'])), weather_data['precipitation_sum'], alpha=0.5,
                            label='Precipitation (mm)', color='blue')
                    ax2.set_ylabel('Precipitation (mm)', color='blue')
                    ax2.tick_params(axis='y', labelcolor='blue')

                    fig.legend(loc="upper right", bbox_to_anchor=(1, 1), bbox_transform=ax1.transAxes)
                    st.pyplot(fig)

                    st.info(
                        "The weather data is collected over the past 30 days to provide an accurate analysis of current growing conditions.")

                    current_date = datetime.datetime.now().strftime("%Y-%m-%d")
                    prompt = prompt_template.format(
                        location=location,
                        latitude=latitude,
                        longitude=longitude,
                        plant_name=plant_name,
                        topmn=plant_details['TOPMN'],
                        topmx=plant_details['TOPMX'],
                        tmin=plant_details['TMIN'],
                        tmax=plant_details['TMAX'],
                        ropmn=plant_details['ROPMN'],
                        ropmx=plant_details['ROPMX'],
                        rmin=plant_details['RMIN'],
                        rmax=plant_details['RMAX'],
                        temperature_data=weather_data['temperature_2m_mean'],
                        precipitation_data=weather_data['precipitation_sum'],
                        suitability_score=suitability_score,
                        warnings="; ".join([]),
                        current_date=current_date
                    )


                    response = client.invoke([
                        HumanMessage(content=prompt)
                    ])
                    clean_text = _clean_llm_output(response.content.strip())

                    st.write("📜 Analysis Report:")
                    st.write(clean_text)

                else:
                    st.error(
                        "🚨 Failed to fetch suitability data. This can happen due to external API restrictions. Please wait a few seconds and try again.")
            else:
                st.error("🚨 Failed to fetch plant details. Please try again.")

        # Combine plant details and descriptions in a table (casted to string to avoid Arrow error)
        plant_table_df = pd.DataFrame({
            "Field": list(plant_details.keys()),
            "Description": [field_descriptions.get(key, "No description available.") for key in plant_details.keys()],
            "Value": [str(v) for v in plant_details.values()]  # 💡 Cast to string here too
        })

        st.table(plant_table_df)


    else:
        st.error("🚨 Failed to fetch plant details. Please try again.")
