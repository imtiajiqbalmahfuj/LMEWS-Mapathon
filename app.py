import streamlit as st
import geemap.foliumap as geemap
import ee
import google.generativeai as genai
import datetime

# --- Configuration & Authentication ---
st.set_page_config(page_title="LMEWS Dashboard", layout="wide")

# Initialize Earth Engine (Requires Streamlit Secrets for deployment)
try:
    ee.Initialize()
except Exception as e:
    ee.Authenticate() # Fallback for local testing
    ee.Initialize()

# Configure Gemini API
# Store your API key in Streamlit Community Cloud Secrets: st.secrets["GEMINI_API_KEY"]
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", "YOUR_LOCAL_TEST_KEY") 
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-3.1-pro') # Using the advanced model for accurate translation

# --- UI & Sidebar ---
st.title("Last-Mile Early Warning System (LMEWS)")
st.markdown("Automated multi-hazard risk mapping and localized Bengali alerts.")

st.sidebar.header("Hazard Analysis Parameters")
hazard_type = st.sidebar.selectbox(
    "Select Vulnerability Type",
    ["Flood Vulnerability", "Deforestation", "Heatwaves / UHI", "Drought", "Groundwater Depletion"]
)

# --- Map Setup ---
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Interactive Risk Map")
    st.markdown("Draw a rectangle or place a marker to select a region for analysis.")
    
    # Initialize Map centered on Bangladesh
    m = geemap.Map(center=[23.6850, 90.3563], zoom=7)
    
    # --- Hazard Logic (GEE) ---
    # Note: These are simplified GEE visualizations for the prototype. 
    # You can plug in your specific complex algorithms here.
    
    if hazard_type == "Flood Vulnerability":
        # Example: JRC Global Surface Water 
        dataset = ee.Image('JRC/GSW1_4/GlobalSurfaceWater')
        water_occurrence = dataset.select('occurrence')
        vis_params = {'min': 0, 'max': 100, 'palette': ['lightblue', 'blue', 'darkblue']}
        m.addLayer(water_occurrence, vis_params, 'Water Occurrence (Flood Risk)')
        
    elif hazard_type == "Deforestation":
        # Example: Hansen Global Forest Change
        dataset = ee.Image('UMD/hansen/global_forest_change_2022_v1_10')
        loss = dataset.select('loss')
        m.addLayer(loss.updateMask(loss), {'palette': ['red']}, 'Deforestation (Tree Cover Loss)')
        
    elif hazard_type == "Heatwaves / UHI":
        # Example: MODIS Land Surface Temperature
        dataset = ee.ImageCollection("MODIS/061/MOD11A2").filterDate('2023-01-01', '2023-12-31').mean()
        lst = dataset.select('LST_Day_1km').multiply(0.02).subtract(273.15) # Convert to Celsius
        m.addLayer(lst, {'min': 20, 'max': 45, 'palette': ['blue', 'yellow', 'red']}, 'Land Surface Temp')
        
    elif hazard_type == "Drought":
        # Example: MODIS NDVI
        dataset = ee.ImageCollection('MODIS/061/MOD13A2').filterDate('2023-01-01', '2023-12-31').mean()
        ndvi = dataset.select('NDVI')
        m.addLayer(ndvi, {'min': -2000, 'max': 10000, 'palette': ['red', 'yellow', 'green']}, 'NDVI (Drought Indicator)')
        
    elif hazard_type == "Groundwater Depletion":
        # Example: GRACE Tellus Monthly Mass Grids
        dataset = ee.ImageCollection("NASA/GRACE/MASS_GRIDS/LAND").filterDate('2021-01-01', '2021-12-31').mean()
        lwe = dataset.select('lwe_thickness')
        m.addLayer(lwe, {'min': -10, 'max': 10, 'palette': ['red', 'white', 'blue']}, 'Liquid Water Equivalent')

    m.to_streamlit(height=600)

# --- Analysis & AI Integration ---
with col2:
    st.subheader("AI Insight & Alerts")
    
    if st.button(f"Analyze {hazard_type} for Selected Area"):
        with st.spinner("Processing satellite imagery and generating AI alerts..."):
            # In a full build, you extract exact geometry from the map drawing tools.
            # For the prototype, we simulate the spatial statistics extraction.
            
            prompt = f"""
            You are a disaster management AI for Bangladesh. 
            The system has just analyzed an area for {hazard_type}. 
            Based on standard geospatial thresholds for {hazard_type}, assume the risk level is currently HIGH.
            
            Provide the following in exactly three sections:
            1. Danger Status: State clearly if the user is in a danger zone (in English and Bengali).
            2. Explanation: Explain what the {hazard_type} map shows and why it's dangerous, localized for a rural Bangladeshi context (in Bengali).
            3. SMS Alert: Draft a strict, 160-character maximum, highly actionable SMS alert for local residents (in Bengali).
            """
            
            try:
                response = model.generate_content(prompt)
                
                st.markdown("### 🚨 Threat Assessment")
                st.write(response.text)
                
            except Exception as e:
                st.error(f"Error connecting to AI: {e}")
