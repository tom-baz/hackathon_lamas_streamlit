import streamlit as st
import pandas as pd
import plotly.express as px
from shapely.wkt import loads
from shapely.geometry import mapping, Polygon, MultiPolygon
import geopandas as gpd
import numpy as np

# also openpyxl is needed


def load_data(excel_path):
    # Read Excel file
    df = pd.read_excel(excel_path)
    
    # Define a safe loading function for WKT geometries
    def safe_loads(wkt):
        try:
            if pd.isna(wkt) or wkt == '':
                return None
            geom = loads(wkt)
            if geom.is_empty:
                return None
            return geom
        except Exception as e:
            return None
    
    # Convert geometries and filter out None values
    geometries = df['geometry'].apply(safe_loads)
    valid_mask = geometries.notna()
    
    # Create GeoDataFrame with only valid geometries
    gdf = gpd.GeoDataFrame(
        df[valid_mask], 
        geometry=geometries[valid_mask],
        crs="EPSG:2039"  # Israeli TM Grid
    )
    
    # Convert to WGS84 (lat/lon) coordinates
    gdf = gdf.to_crs('EPSG:4326')
    
    return gdf

def create_choropleth(gdf, column_name):
    # Create GeoJSON
    geojson = gdf.__geo_interface__
    
    # Calculate the center of the data
    bounds = gdf.total_bounds  # returns (minx, miny, maxx, maxy)
    center_lat = (bounds[1] + bounds[3]) / 2
    center_lon = (bounds[0] + bounds[2]) / 2
    
    # Create choropleth map
    fig = px.choropleth_mapbox(
        gdf,
        geojson=geojson,
        locations=gdf.index,
        color=column_name,
        color_continuous_scale='Viridis',
        mapbox_style="carto-positron",
        zoom=7,
        center={"lat": center_lat, "lon": center_lon},
        opacity=0.7,
        labels={column_name: column_name},
        hover_data=['SHEM_YISHUV_ENG', 'SHEM_YISHUV_HEB', column_name]
    )
    
    # Update layout
    fig.update_layout(
        margin={"r":0,"t":0,"l":0,"b":0},
        mapbox=dict(
            bearing=0,
            pitch=0
        )
    )
    
    return fig

def main():
    st.title("Israel Census 2022 Data Visualization")
    
    # Load data
    gdf = load_data("census_2022_gdf.xlsx")
    
    # Create sidebar
    st.sidebar.title("Visualization Controls")
    
    # Get numeric columns for the dropdown
    numeric_columns = gdf.select_dtypes(include=[np.number]).columns.tolist()
    # Remove geometry-related columns and index-like columns
    columns_to_exclude = ['geometry', 'SEMEL_YISHUV', 'Shape_Length', 'Shape_Area']
    numeric_columns = [col for col in numeric_columns if col not in columns_to_exclude]
    
    # Create dropdown for column selection
    selected_column = st.sidebar.selectbox(
        "Select data to visualize",
        options=numeric_columns,
        index=numeric_columns.index('pop_approx') if 'pop_approx' in numeric_columns else 0
    )
    
    # Display some information about the selected column
    st.sidebar.write(f"Statistics for {selected_column}:")
    st.sidebar.write(gdf[selected_column].describe())
    
    # Create and display the map
    st.write(f"### Choropleth Map of {selected_column}")
    fig = create_choropleth(gdf, selected_column)
    st.plotly_chart(fig, use_container_width=True)
    
    # Add some context about the data
    st.write(f"Number of localities shown: {len(gdf)}")
    
if __name__ == "__main__":
    main()