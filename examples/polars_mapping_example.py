# noqa: E402

"""
Example: Large dataset processing with Polars and geographic visualization with Folium

This example demonstrates:
1. Loading a large CSV dataset from the internet using Polars
2. Data filtering and cleaning operations
3. Geographic visualization using Folium maps
4. Integration with Microlog for performance profiling
"""

from functools import cache
from io import StringIO
import os
import webbrowser

import folium
import polars as pl
import requests


@cache
def download_earthquake_data():
    """Download earthquake data from USGS (last 30 days, magnitude 4.5+)"""
    print("Downloading earthquake data from USGS")
    url = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/4.5_month.csv"

    # Download with requests (bypassing SSL verification)
    response = requests.get(url, verify=False, timeout=10)
    response.raise_for_status()

    # Read into Polars DataFrame from string
    schema_overrides = {
        "mag": pl.Float64,
        "latitude": pl.Float64,
        "longitude": pl.Float64,
        "depth": pl.Float64,
        "gap": pl.Float64,
        "dmin": pl.Float64,
        "rms": pl.Float64,
        "horizontalError": pl.Float64,
        "depthError": pl.Float64,
        "magError": pl.Float64,
        "nst": pl.Int64,
        "magNst": pl.Int64,
    }

    df = pl.read_csv(
        StringIO(response.text),
        infer_schema_length=0,
        schema_overrides=schema_overrides
    )

    # Make dataset 30x larger by concatenating with itself
    df = pl.concat([df] * 30)
    print(f"Downloaded dataset shape (30x larger): {df.shape}")

    return df


def load_and_clean_data(df):
    """Clean earthquake data with Polars operations"""
    print("Cleaning earthquake data")

    print(f"Original dataset shape: {df.shape}")

    # Clean and filter the data
    cleaned_df = (
        df.filter(pl.col("mag").is_not_null())  # Remove null magnitudes
        .filter(
            pl.col("latitude").is_not_null() & pl.col("longitude").is_not_null()
        )  # Valid coordinates
        .filter(pl.col("mag") >= 5.0)  # Focus on significant earthquakes (5.0+)
        .with_columns(
            [
                pl.col("time")
                .str.to_datetime("%Y-%m-%dT%H:%M:%S%.fZ")
                .alias("datetime"),
                pl.col("mag").round(1).alias("magnitude"),
                pl.col("place").str.strip_chars().alias("location"),
            ]
        )
        .select(
            [
                "datetime",
                "latitude",
                "longitude",
                "magnitude",
                "depth",
                "location",
                "type",
            ]
        )
        .sort("magnitude", descending=True)
    )

    print(f"Cleaned dataset shape: {cleaned_df.shape}")
    print(
        f"Magnitude range: {cleaned_df['magnitude'].min()} - {cleaned_df['magnitude'].max()}"
    )

    return cleaned_df


def create_earthquake_map(df):
    """Create an interactive Folium map of earthquake locations"""
    print("Creating interactive earthquake map")

    # Convert to pandas for Folium compatibility
    df_pandas = df.to_pandas()

    # Create base map centered on global view
    m = folium.Map(
        location=[20, 0],  # Center of world
        zoom_start=2,
        tiles="OpenStreetMap",
    )

    # Add earthquake markers
    for _, row in df_pandas.iterrows():
        # Color code by magnitude
        if row["magnitude"] >= 7.0:
            color = "red"
            radius = 15
        elif row["magnitude"] >= 6.0:
            color = "orange"
            radius = 12
        else:
            color = "yellow"
            radius = 8

        # Create popup text
        popup_text = f"""
        <b>Magnitude:</b> {row["magnitude"]}<br>
        <b>Location:</b> {row["location"]}<br>
        <b>Depth:</b> {row["depth"]} km<br>
        <b>Time:</b> {row["datetime"]}<br>
        <b>Type:</b> {row["type"]}
        """

        folium.CircleMarker(
            location=[row["latitude"], row["longitude"]],
            radius=radius,
            popup=folium.Popup(popup_text, max_width=300),
            color="black",
            weight=1,
            fillColor=color,
            fillOpacity=0.7,
        ).add_to(m)

    # Add legend
    legend_html = """
    <div style="position: fixed;
                bottom: 50px; left: 50px; width: 150px; height: 90px;
                background-color: white; border:2px solid grey; z-index:9999;
                font-size:14px; padding: 10px">
    <p><b>Earthquake Magnitude</b></p>
    <p><i class="fa fa-circle" style="color:red"></i> 7.0+ Major</p>
    <p><i class="fa fa-circle" style="color:orange"></i> 6.0-6.9 Strong</p>
    <p><i class="fa fa-circle" style="color:yellow"></i> 5.0-5.9 Moderate</p>
    </div>
    """
    m.get_root().add_child(folium.Element(legend_html))

    return m


def generate_statistics(df):
    """Generate summary statistics about the earthquake data"""
    print("Generating earthquake statistics")

    stats = {
        "total_earthquakes": df.height,
        "avg_magnitude": df["magnitude"].mean(),
        "max_magnitude": df["magnitude"].max(),
        "avg_depth": df["depth"].mean(),
        "countries_affected": df["location"].str.count_matches(r",\s*\w+$").sum(),
    }

    # Top 5 locations by earthquake count
    top_locations = (
        df.group_by("location")
        .agg(pl.len().alias("count"))
        .sort("count", descending=True)
        .head(5)
    )

    print(f"Statistics: {stats}")
    print(f"Top locations:\n{top_locations}")

    return stats, top_locations


def main():
    """Main function to run the earthquake data analysis and mapping example."""

    print("Starting earthquake data analysis and mapping")

    # Step 1: Download data directly to DataFrame
    raw_df = download_earthquake_data()

    # Step 2: Clean data with Polars
    earthquake_df = load_and_clean_data(raw_df)

    # Step 3: Generate statistics
    stats, top_locations = generate_statistics(earthquake_df)

    # Step 4: Create interactive map
    earthquake_map = create_earthquake_map(earthquake_df)

    # Step 5: Save map to HTML file
    earthquake_map.save("examples/earthquake_map.html")

    # Step 6: Done
    print(f"Interactive map created with {earthquake_df.height} earthquakes:")

    print("\n🌍 Earthquake Analysis Complete!")
    print(f"📊 Processed {stats['total_earthquakes']} earthquakes")
    print(f"📈 Average magnitude: {stats['avg_magnitude']:.1f}")
    print(f"📍 Top affected location: {top_locations.row(0)[0]}")


if __name__ == "__main__":
    main()
    path = os.path.join(os.getcwd(), "examples", "earthquake_map.html")
    webbrowser.open(f"file://{path}")
