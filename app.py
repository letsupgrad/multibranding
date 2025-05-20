
import streamlit as st
import pandas as pd
import altair as alt
import io # Import io for handling uploaded files
import folium
from streamlit_folium import st_folium
import plotly.graph_objects as go

st.set_page_config(page_title="Combined Data Dashboards", layout="wide")
st.title("📊 Combined Data Dashboards")

# --- Common Functions (Used by one or both sections) ---

@st.cache_data # Cache preprocessing for performance
def preprocess(df):
    """Cleans DataFrame columns to be lowercase, snake_case, and alpha-numeric."""
    if df is None or df.empty: # Add check for None input
         return pd.DataFrame() # Return empty DataFrame for consistency

    # Convert column names to string type to handle potential non-string headers
    df.columns = df.columns.astype(str)
    df.columns = df.columns.str.strip().str.lower().str.replace(r'[^a-z0-9_]', '_', regex=True)
    return df

def pie_chart(data, label_col, value_col, title):
    """Generates and displays an Altair pie chart."""
    st.subheader(title)
    # Ensure data is not empty and required columns exist
    if not data.empty and label_col in data.columns and value_col in data.columns:
        # Ensure value column is numeric for theta encoding
        data[value_col] = pd.to_numeric(data[value_col], errors='coerce').fillna(0)
        # Filter out rows where the value column is effectively zero after coercion
        data_to_plot = data[data[value_col] > 0].copy()

        if not data_to_plot.empty:
            chart = alt.Chart(data_to_plot).mark_arc(innerRadius=50).encode(
                theta=alt.Theta(field=value_col, type="quantitative"),
                color=alt.Color(field=label_col, type="nominal", title=label_col.replace('_', ' ').title()),
                tooltip=[label_col, value_col]
            ).properties(title=title)
            st.altair_chart(chart, use_container_width=True)
        else:
             st.info(f"No valid data points (count > 0) to plot pie chart for '{title}'.")
    else:
        st.info(f"Not enough valid data columns ({label_col}, {value_col}) or data to plot pie chart for '{title}'.")


def bar_chart(data, label_col, value_col, title, sort_order='-y'):
    """Generates and displays an Altair bar chart."""
    st.subheader(title)
    # Ensure data is not empty and required columns exist
    if not data.empty and label_col in data.columns and value_col in data.columns:
         # Ensure value column is numeric for y encoding
        data[value_col] = pd.to_numeric(data[value_col], errors='coerce').fillna(0)
         # Filter out rows where the value column is effectively zero after coercion
        data_to_plot = data[data[value_col] > 0].copy()

        if not data_to_plot.empty:
            # Use readable title for axis labels
            x_title = label_col.replace('_', ' ').title()
            y_title = value_col.replace('_', ' ').title() if value_col != 'Count' else 'Count'


            chart = alt.Chart(data_to_plot).mark_bar().encode(
                x=alt.X(label_col, sort=sort_order, title=x_title),
                y=alt.Y(value_col, title=y_title),
                tooltip=[label_col, value_col]
            ).properties(title=title).interactive() # Add interactivity for zooming/panning
            st.altair_chart(chart, use_container_width=True)
        else:
             st.info(f"No valid data points (count > 0) to plot bar chart for '{title}'.")
    else:
        st.info(f"Not enough valid data columns ({label_col}, {value_col}) or data to plot bar chart for '{title}'.")

# Define a helper function to safely format strings for display
def safe_display_string(value, default_display="N/A"):
    """Converts a value to a display string, handling None/NaN."""
    if pd.isna(value) or value is None or str(value).strip() == '':
        return default_display
    # Convert to string and then apply string methods
    return str(value).strip().replace('_', ' ').title()


# --- Sidebar (Empty or for other controls if needed) ---
st.sidebar.header("Sidebar")
st.sidebar.write("Use the main content area to upload files and interact with the dashboards.")


# --- Main Content Columns ---
# Adjust the width ratio [left_column_width, right_column_width] as needed
col_insights, col_billboard = st.columns([1, 1]) # Equal width columns

# --- Column 1: Brand Insights Dashboard ---
with col_insights:
    st.header("📈 Multi-Brand Insights Dashboard")
    st.write("Upload individual brand CSV files below and use the checkboxes to select which ones to include in the 'Overall Insights' tab.")

    # --- File Uploaders (Moved to Main Page Column) ---
    st.subheader("📂 Upload Brand CSV Files")
    # This list must match the brands you have uploaders/tabs for
    all_potential_brands = [
       "AirAsia", "Cheetos", "Mucilion", "RTD Drinks", "Fried Chicken",
       "Chocolate", "Phones", "Coca-Cola", "Mudah", "KFC", "Panasonic"
    ]

    # Use distinct keys for uploaders now that they are not in sidebar
    airasia_file = st.file_uploader("AirAsia Data", type="csv", key="main_airasia_uploader")
    cheetos_file = st.file_uploader("Cheetos Data", type="csv", key="main_cheetos_uploader")
    mucilion_file = st.file_uploader("Mucilion Data", type="csv", key="main_mucilion_uploader")
    rtd_file = st.file_uploader("RTD Data", type="csv", key="main_rtd_uploader")
    fried_file = st.file_uploader("Fried Chicken Data", type="csv", key="main_fried_uploader")
    choco_file = st.file_uploader("Chocolate Data (March)", type="csv", key="main_choco_uploader")
    phone_file = st.file_uploader("Samsung Phone Data", type="csv", key="main_phone_uploader")
    cola_file = st.file_uploader("Coca-Cola Data", type = "csv", key="main_cola_uploader")
    mudah_file = st.file_uploader("Mudah Data", type="csv", key="main_mudah_uploader")
    kfc_file = st.file_uploader("KFC Data", type="csv", key="main_kfc_uploader")
    panasonic_file = st.file_uploader("Panasonic Data", type="csv", key="main_panasonic_uploader")

    # Map file variables to brand names for the Overall tab loader
    brand_file_map = {
        "AirAsia": airasia_file,
        "Cheetos": cheetos_file,
        "Mucilion": mucilion_file,
        "RTD Drinks": rtd_file,
        "Fried Chicken": fried_file,
        "Chocolate": choco_file,
        "Phones": phone_file,
        "Coca-Cola": cola_file,
        "Mudah": mudah_file,
        "KFC": kfc_file,
        "Panasonic": panasonic_file,
    }

    # --- Overall Dashboard Selection (Moved to Main Page Column) ---
    st.subheader("📋 Overall Dashboard Selection")
    include_brands_overall = {}
    for brand_name in all_potential_brands:
         # Use slightly different label for Chocolate for clarity
         display_name = "Chocolate (March)" if brand_name == "Chocolate" else brand_name
         display_name = "Samsung Phone" if brand_name == "Phones" else display_name
         display_name = "Mudah Data" if brand_name == "Mudah" else display_name
         display_name = "KFC Data" if brand_name == "KFC" else display_name
         display_name = "Panasonic Data" if brand_name == "Panasonic" else display_name

         # Only show checkbox if a file uploader variable exists for it
         # We can check if the file variable exists in the map, and optionally if it's uploaded
         if brand_name in brand_file_map:
            # Default to True if file is uploaded, False otherwise
            default_value = brand_file_map[brand_name] is not None
            include_brands_overall[brand_name] = st.checkbox(
                f"Include {display_name}",
                value=default_value,
                key=f"overall_checkbox_{brand_name}" # Keep key unique
            )
         else:
             include_brands_overall[brand_name] = False # Fallback

    # --- Data Loading for Multi-Brand Overall Tab (Now depends on main page uploaders) ---
    @st.cache_data # Cache this function for performance
    def load_selected_data_for_overall_cached_main(file_map, include_selection):
        """Loads and preprocesses only the selected AND uploaded files."""
        loaded_dataframes = {}
        for brand_name, file_obj in file_map.items():
            # Check if the brand is selected for overall AND the file is uploaded
            if include_selection.get(brand_name, False) and file_obj is not None:
                 try:
                     df = pd.read_csv(file_obj)
                     df = preprocess(df) # Apply preprocessing
                     # Ensure basic demo columns exist for overall tab before storing
                     # Relax this check slightly, maybe just check if df is not empty after preprocess
                     if not df.empty:
                          loaded_dataframes[brand_name] = df
                     else:
                          st.warning(f"Skipping '{brand_name}' for Overall tab: Data is empty after processing.")

                 except Exception as e:
                     st.error(f"Error loading or preprocessing {brand_name} data for Overall tab: {e}")
                     # Don't add the dataframe if loading failed or preprocessing failed significantly
        return loaded_dataframes

    # Call the loading function with the map and selection state (now defined within the column)
    loaded_dataframes_overall = load_selected_data_for_overall_cached_main(
        brand_file_map, include_brands_overall
    )


    # --- Create ALL possible tabs (Overall + Originals) (Nested within col_insights) ---
    brand_insight_tab_names = [
       "💡 Overall Insights", # New tab
       "AirAsia", "Cheetos", "Mucilion", "RTD Drinks", "Fried Chicken",
       "Chocolate", "Phones", "Coca-Cola", "Mudah", "KFC", "Panasonic" # Original names
    ]

    # Create nested Brand Insights tabs
    brand_insight_tabs = st.tabs(brand_insight_tab_names)

    # Map brand insight tab names to tab objects for easy access
    brand_insight_tab_map = {name: obj for name, obj in zip(brand_insight_tab_names, brand_insight_tabs)}

    # --- Overall Insights Tab Content (Nested within col_insights) ---
    with brand_insight_tab_map["💡 Overall Insights"]:
        st.header("💡 Cross-Brand Insights")
        st.write("This tab provides a high-level overview and comparison across the **selected and uploaded** brand datasets.")

        if not loaded_dataframes_overall:
            st.warning("Please select brands for the Overall dashboard using the checkboxes above and upload their CSV files to see overall insights.")
        else:
            st.subheader("Combined Respondent Demographics")

            combined_demographics = pd.DataFrame()
            # Identify common demographic columns based on likely preprocessed names
            # Use a broad list to catch columns present in different datasets
            demo_cols_to_combine = ['age_group', 'gender', 'monthly_income',
                               'household_income', 'location', 'city', 'region',
                               'marital_status', 'children_under_5',
                               'please_select_the_age_group_based_on_your_age', # Panasonic age col
                               'please_select_your_gender'] # Panasonic gender col

            found_common_demo_cols = []
            # First pass: find which of the common demo cols actually exist in *any* loaded dataframe
            # Check existence *after* preprocessing
            for col in demo_cols_to_combine:
                if any(col in df.columns for df in loaded_dataframes_overall.values()):
                     found_common_demo_cols.append(col)

            if found_common_demo_cols:
                for brand_name, df in loaded_dataframes_overall.items():
                    temp_df = pd.DataFrame()
                    has_demo_data = False
                    for col in found_common_demo_cols:
                        # Check if the column exists in the current dataframe *after* loading
                        if col in df.columns:
                             # Use .copy() and convert to string to handle potential mixed types
                            temp_df[col] = df[col].astype(str).str.strip().copy()
                            has_demo_data = True

                    if has_demo_data:
                        # Add source brand column only if we added some demographic data
                        temp_df['Source Brand'] = brand_name
                        combined_demographics = pd.concat([combined_demographics, temp_df], ignore_index=True)


            if not combined_demographics.empty:
                st.write("Distribution of combined respondents across all selected datasets:")

                # Now, iterate through the demographic columns that were actually found and combined
                for col in found_common_demo_cols:
                    if col in combined_demographics.columns: # Double check it was successfully combined
                         st.markdown(f"**{col.replace('_', ' ').title()} Distribution**")
                         # Exclude empty strings and 'nan' strings from value counts for charts
                         # Convert NaNs from concat to string 'nan' first
                         valid_data = combined_demographics[col].fillna('nan').astype(str).loc[~combined_demographics[col].isin(['', 'nan', 'nan ', ' none', 'None'])] # Added more clean
                         if not valid_data.empty:
                             chart_data = valid_data.value_counts().reset_index()
                             chart_data.columns = ['Category', 'Count']
                             # Limit categories if too many for a readable bar chart
                             if len(chart_data) > 20: # Arbitrary limit
                                 st.info(f"(Showing top 20 categories for {col.replace('_', ' ').title()})")
                                 chart_data = chart_data.head(20)


                             st.altair_chart(
                                 alt.Chart(chart_data).mark_bar().encode(
                                     x=alt.X('Category', sort='-y', title=col.replace('_', ' ').title()),
                                     y=alt.Y('Count', title='Count'),
                                     tooltip=['Category', 'Count']
                                 ).properties(title=f"Combined {col.replace('_', ' ').title()}"),
                                 use_container_width=True
                             )
                         else:
                              st.info(f"No valid data for '{col.replace('_', ' ').title()}' across loaded datasets.")


                # Distribution by Source Brand (to see how many respondents each dataset contributed)
                st.markdown("**Respondent Count by Source Brand**")
                source_counts = combined_demographics['Source Brand'].value_counts().reset_index()
                source_counts.columns = ['Source Brand', 'Count']
                st.altair_chart(
                     alt.Chart(source_counts).mark_bar().encode(
                         x='Source Brand', y='Count', tooltip=['Source Brand', 'Count']
                     ).properties(title="Respondents per Source Dataset"),
                     use_container_width=True
                )

            else:
                 st.info("No common demographic data (Age Group, Gender, Income, Location, Region, Marital Status, Children under 5) found across the selected and uploaded datasets.")


            st.subheader("Key Insights by Brand")
            st.write("Below are value counts for a representative key metric identified for each uploaded dataset.")

            # Define a mapping of brand names to ONE representative key column for display
            # Use the preprocessed column names (lowercase, snake_case)
            brand_representative_metrics = {
                'AirAsia': 'brand', # Example: Airline Brand Selected
                'Cheetos': 'preferred_snack_brand', # Example: Preferred Snack Brand
                'Mucilion': 'purchased_brand', # Example: Purchased Brand
                'RTD Drinks': 'brand_aware_coca_cola', # Example: Awareness of Coke (Adjust if Coke is not the focus)
                'Fried Chicken': 'brand_you_visit_the_most', # Example: Most Visited Brand (Check if this column exists after preprocess)
                'Chocolate': 'prefer_kitkat', # Example: Preference for Kitkat (Adjust if Kitkat is not the focus)
                'Phones': 'current_phone_samsung', # Example: Own Samsung Phone
                'Coca-Cola': 'best_choice_softdrink', # Example: Favorite Soft Drink Brand (Check if this column exists after preprocess)
                'Mudah': 'likelihood_to_purchase_via_mudah_next_6_months', # Example: Purchase Intent (Check if this column exists after preprocess)
                'KFC': 'brand_you_visit_the_most', # Example: Most Visited Fast Food Brand (Check if this column exists after preprocess)
                'Panasonic': 'panasonic', # Example: Own Panasonic Hairdryer (Check if this column exists after preprocess)
            }

            # Filter out metrics for brands that weren't loaded
            available_metrics = {brand: col_key for brand, col_key in brand_representative_metrics.items() if brand in loaded_dataframes_overall}

            if available_metrics:
                 # Display metrics using columns
                 cols_per_row = 3 # Display up to 3 metrics per row
                 current_cols = None
                 col_index = 0

                 # Sort metrics by brand name for consistent display order
                 sorted_available_metrics = sorted(available_metrics.items())

                 for brand_name, col_key in sorted_available_metrics:
                    df = loaded_dataframes_overall[brand_name]

                    # Get the current column layout or create a new one
                    if current_cols is None or col_index % cols_per_row == 0:
                        # Use st.columns within the main column context
                        current_cols = st.columns(cols_per_row)
                        col_index = 0 # Reset index for the new row

                    # Check if the column exists in the current dataframe *after* loading
                    if col_key in df.columns:
                        with current_cols[col_index]:
                             st.markdown(f"#### {brand_name}: {col_key.replace('_', ' ').title()}")
                              # Get value counts, including NaN for completeness unless explicitly dropped
                              # Convert column to string first to handle mixed types and NaNs gracefully
                             data_counts = df[col_key].astype(str).value_counts(dropna=False).reset_index()
                             data_counts.columns = ['Response', 'Count']
                              # Replace 'nan' string with something more readable
                             data_counts['Response'] = data_counts['Response'].replace('nan', 'No Response / N/A')

                              # Limit responses shown if too many categories
                             if len(data_counts) > 15: # Arbitrary limit for summary table
                                   st.write("(Showing top 15 responses)")
                                   data_counts = data_counts.head(15)

                             if not data_counts.empty:
                                   st.dataframe(data_counts, use_container_width=True, height=300) # Fixed height for consistency
                             else:
                                   st.info("No data for this metric.")
                    else:
                         # This case is already handled by filtering available_metrics initially, but double-check
                         pass # Or add a specific message if needed

                    col_index += 1 # Move to the next column slot

                 # Add empty columns to complete the last row if needed
                 while col_index % cols_per_row != 0:
                     # Check if current_cols was actually created (i.e., available_metrics wasn't empty)
                     if current_cols is not None:
                        with current_cols[col_index]:
                            st.empty() # Add an empty element to fill the column
                     col_index += 1


            else:
                 st.info("Could not identify or find representative key metrics for the selected and uploaded datasets.")

    # --- Individual Brand Tabs Content (Original Code Structure - Nested within col_insights) ---
    # Need to map original tab variables to the new nested tab objects
    # Overall tab is index 0, so original tabs start from index 1
    if len(brand_insight_tabs) > 1:
        airasia_tab = brand_insight_tabs[1]
        cheetos_tab = brand_insight_tabs[2]
        mucilion_tab = brand_insight_tabs[3]
        rtd_tab = brand_insight_tabs[4]
        fried_tab = brand_insight_tabs[5]
        choco_tab = brand_insight_tabs[6]
        phone_tab = brand_insight_tabs[7]
        cola_tab = brand_insight_tabs[8]
        mudah_tab = brand_insight_tabs[9]
        kfc_tab = brand_insight_tabs[10]
        panasonic_tab = brand_insight_tabs[11]
    else:
         airasia_tab = cheetos_tab = mucilion_tab = rtd_tab = fried_tab = \
         choco_tab = phone_tab = cola_tab = mudah_tab = kfc_tab = panasonic_tab = None
         st.warning("Please upload at least one Brand Insights CSV file to see individual brand tabs.")


    # AIRASIA TAB
    if airasia_tab:
        with airasia_tab:
            st.header("📋 AirAsia ")
            if airasia_file:
                df = preprocess(pd.read_csv(airasia_file))

                if not df.empty:
                    # --- Key Fields (auto-detected/defined) ---
                    # Use preprocessed column names
                    demographic_cols = ['age_group', 'gender', 'monthly_income']
                    seen_ads_col = 'seen_airline_ads_billboards' # Example, verify actual column name
                    brand_col = 'brand' # Example, verify actual column name

                    if seen_ads_col in df.columns:
                        bar_chart(df.astype(str).value_counts([seen_ads_col]).reset_index(),
                                  seen_ads_col, 0, # Use index 0 for the count column name
                                  "🪧 Seen Airline Billboard Ads") # Added title and icon
                    else:
                         st.info(f"Column '{seen_ads_col}' not found in AirAsia data.")


                    st.subheader("👤 Demographics")
                    for col in demographic_cols:
                        if col in df.columns:
                             chart_data = df[col].astype(str).str.strip().value_counts(dropna=False).reset_index()
                             chart_data.columns = [col, 'count']
                             bar_chart(chart_data, col, 'count', col.replace('_', ' ').title())
                        else:
                             st.info(f"Demographic column '{col.replace('_', ' ').title()}' not found in AirAsia data.")


                    # --- Brand Preference ---
                    if brand_col in df.columns:
                        pie_chart(df.astype(str).value_counts([brand_col]).reset_index(),
                                  brand_col, 0, # Use index 0 for the count column name
                                  "✈️ Airline Brand Selected") # Added title and icon
                    else:
                        st.info(f"Brand column '{brand_col}' not found in AirAsia data.")

                else:
                     st.info("AirAsia data is empty after processing.")
            else:
                st.info("Please upload the AirAsia CSV file above.")


    # CHEETOS TAB
    if cheetos_tab:
        with cheetos_tab:
            st.header("🧀 Cheetos")
            if cheetos_file:
                df = preprocess(pd.read_csv(cheetos_file))

                if not df.empty:
                    # Section 1: Demographics
                    st.header("👥 Demographics")
                    for col in ['age_group', 'gender', 'city']:
                        if col in df.columns:
                            data = df[col].astype(str).str.strip().value_counts(dropna=False).reset_index()
                            data.columns = [col.title().replace('_', ' '), 'Count']
                            bar_chart(data, data.columns[0], 'Count', data.columns[0])
                        else:
                             st.info(f"Demographic column '{col.replace('_', ' ').title()}' not found in Cheetos data.")


                    # Section 2: Ad Exposure & Recall
                    st.header("📢 Ad Exposure & Recall")
                    for col in ['seen_snack_ads', 'recall_snack_ads']:
                        if col in df.columns:
                            data = df[col].astype(str).str.strip().value_counts(dropna=False).reset_index()
                            data.columns = [col.title().replace('_', ' '), 'Count']
                            pie_chart(data, data.columns[0], 'Count', data.columns[0])
                        else:
                             st.info(f"Ad Exposure/Recall column '{col.replace('_', ' ').title()}' not found in Cheetos data.")


                    # Section 3: Ad Brand & Slogan
                    st.header("🏷️ Ad Brand and Slogan")
                    for col in ['ad_brand_snack', 'ad_slogan_snack']:
                         if col in df.columns:
                            data = df[col].astype(str).str.strip().value_counts(dropna=False).reset_index()
                            data.columns = [col.title().replace('_', ' '), 'Count']
                            bar_chart(data, data.columns[0], 'Count', data.columns[0])
                         else:
                             st.info(f"Ad Brand/Slogan column '{col.replace('_', ' ').title()}' not found in Cheetos data.")


                    # Section 4: Brand Familiarity
                    st.header("🔍 Familiarity with Snack Brands")
                    fam_cols = [col for col in df.columns if col.startswith('familiar_')]
                    # Filter to columns that actually exist in the dataframe
                    existing_fam_cols = [col for col in fam_cols if col in df.columns]

                    if existing_fam_cols:
                        fam_data = df[existing_fam_cols].astype(str).melt(var_name='Brand_Col', value_name='Response')
                        fam_data = fam_data[fam_data['Response'].str.strip().str.lower() != 'nan'] # Filter out NaNs turned to string

                        if not fam_data.empty:
                            # Use Response directly for counting as multiple brands might have "Cheetos" etc.
                            brand_counts = fam_data['Response'].str.strip().value_counts().reset_index()
                            brand_counts.columns = ['Brand', 'Count']
                            bar_chart(brand_counts, 'Brand', 'Count', "Familiarity Mentions by Brand")
                        else:
                             st.info("No valid brand familiarity data found after filtering for Cheetos.")
                    else:
                         st.info("No brand familiarity columns found (e.g., 'familiar_cheetos').")


                    # Section 5: Preferred Brand
                    st.header("⭐ Preferred Snack Brand")
                    if 'preferred_snack_brand' in df.columns:
                        pref = df['preferred_snack_brand'].astype(str).str.strip().value_counts(dropna=False).reset_index()
                        pref.columns = ['Brand', 'Count']
                        bar_chart(pref, 'Brand', 'Count', "Preferred Snack Brand")
                    else:
                         st.info("Preferred snack brand column not found ('preferred_snack_brand').")


                    # Section 6: Likelihood to Buy Cheetos
                    st.header("🛒 Likelihood to Buy Cheetos")
                    if 'likelihood_buy_cheetos' in df.columns:
                        like = df['likelihood_buy_cheetos'].astype(str).str.strip().value_counts(dropna=False).reset_index()
                        like.columns = ['Likelihood', 'Count']
                        pie_chart(like, 'Likelihood', 'Count', "Likelihood to Buy Cheetos")
                    else:
                         st.info("Likelihood to buy Cheetos column not found ('likelihood_buy_cheetos').")


                    # Section 7: Feelings about Cheetos
                    st.header("💬 Feelings about Cheetos")
                    if 'feelings_cheetos' in df.columns:
                        feeling = df['feelings_cheetos'].astype(str).str.strip().value_counts(dropna=False).reset_index()
                        feeling.columns = ['Feeling', 'Count']
                        bar_chart(feeling, 'Feeling', 'Count', "Feelings about Cheetos")
                    else:
                         st.info("Feelings about Cheetos column not found ('feelings_cheetos').")

                else:
                     st.info("Cheetos data is empty after processing.")
            else:
                st.info("Please upload the Cheetos CSV file above.")

    # MUCILION TAB
    if mucilion_tab:
        with mucilion_tab:
            st.header("🟡 Mucilion")
            if mucilion_file:
                df = preprocess(pd.read_csv(mucilion_file))

                if not df.empty:
                    # Section 1: Demographics
                    st.header("👤 Demographics")
                    demo_cols = ['age_group', 'gender', 'marital_status', 'region', 'children_under_5']
                    for col in demo_cols:
                        if col in df.columns:
                            data = df[col].astype(str).str.strip().value_counts(dropna=False).reset_index()
                            data.columns = [col.title().replace('_', ' '), 'Count']
                            bar_chart(data, data.columns[0], 'Count', data.columns[0])
                        else:
                             st.info(f"Demographic column '{col.replace('_', ' ').title()}' not found in Mucilion data.")


                    # Section 2: Ad Exposure & Recall
                    st.header("📢 Ad Exposure & Recall")
                    for col in ['seen_ad', 'recall_ad']:
                        if col in df.columns:
                            data = df[col].astype(str).str.strip().value_counts(dropna=False).reset_index()
                            data.columns = [col.title().replace('_', ' '), 'Count']
                            pie_chart(data, data.columns[0], 'Count', data.columns[0])
                        else:
                             st.info(f"Ad Exposure/Recall column '{col.replace('_', ' ').title()}' not found in Mucilion data.")


                    # Section 3: Ad Brand & Message
                    st.header("🏷️ Ad Brand and Message Breakdown")
                    for col in ['ad_brand', 'ad_message']:
                         if col in df.columns:
                            data = df[col].astype(str).str.strip().value_counts(dropna=False).reset_index()
                            data.columns = [col.title().replace('_', ' '), 'Count']
                            bar_chart(data, data.columns[0], 'Count', data.columns[0])
                         else:
                             st.info(f"Ad Brand/Message column '{col.replace('_', ' ').title()}' not found in Mucilion data.")


                    # Section 4: Brand Awareness
                    st.header("📌 Brand Awareness")
                    awareness_cols = [col for col in df.columns if col.startswith('aware_brand')]
                    existing_awareness_cols = [col for col in awareness_cols if col in df.columns]
                    if existing_awareness_cols:
                        awareness_data = df[existing_awareness_cols].astype(str).melt(var_name='Brand_Slot', value_name='Brand')
                        awareness_data = awareness_data[awareness_data['Brand'].str.strip().str.lower() != 'nan'] # Filter out NaNs

                        if not awareness_data.empty:
                            brand_counts = awareness_data['Brand'].str.strip().value_counts().reset_index()
                            brand_counts.columns = ['Brand', 'Count']
                            bar_chart(brand_counts, 'Brand', 'Count', "Brand Awareness Mentions")
                        else:
                            st.info("No valid brand awareness data found after filtering for Mucilion.")
                    else:
                         st.info("No brand awareness columns found (e.g., 'aware_brand_mucilion').")

                    # Section 5: Purchased Brand
                    st.header("🛒 Purchased Brand")
                    if 'purchased_brand' in df.columns:
                        purchased = df['purchased_brand'].astype(str).str.strip().value_counts(dropna=False).reset_index()
                        purchased.columns = ['Brand', 'Count']
                        pie_chart(purchased, 'Brand', 'Count', "Purchased Brand")
                    else:
                        st.info("Purchased brand column not found ('purchased_brand').")


                    # Section 6: Future Purchase Intent
                    st.header("🔮 Likely Future Brand Purchase")
                    likely_cols = [col for col in df.columns if col.startswith('likely_buy_')]
                    existing_likely_cols = [col for col in likely_cols if col in df.columns]
                    if existing_likely_cols:
                        future_data = df[existing_likely_cols].astype(str).melt(var_name='Intent_Slot', value_name='Brand')
                        future_data = future_data[future_data['Brand'].str.strip().str.lower() != 'nan'] # Filter out NaNs

                        if not future_data.empty:
                            future_counts = future_data['Brand'].str.strip().value_counts().reset_index()
                            future_counts.columns = ['Brand', 'Count']
                            bar_chart(future_counts, 'Brand', 'Count', "Likely Future Brand Purchase Mentions")
                        else:
                             st.info("No valid future purchase intent data found after filtering for Mucilion.")
                    else:
                         st.info("No future purchase intent columns found (e.g., 'likely_buy_mucilion').")
                else:
                     st.info("Mucilion data is empty after processing.")
            else:
                st.info("Please upload the Mucilion CSV file above.")

    # RTD DRINKS TAB
    if rtd_tab:
        with rtd_tab:
            st.header("🥤 RTD Drinks")
            if rtd_file:
                df = preprocess(pd.read_csv(rtd_file))

                if not df.empty:
                    # ---- DEMOGRAPHICS ----
                    st.subheader("👥 Demographics")
                    # Use preprocessed column names
                    demo_cols = ['gender', 'age', 'household_income', 'location']
                    for col in demo_cols:
                        if col in df.columns:
                            chart_data = df[col].astype(str).value_counts(dropna=False).reset_index()
                            chart_data.columns = ['Category', 'Count']
                            bar_chart(chart_data, 'Category', 'Count', col.replace('_', ' ').title())
                        else:
                             st.info(f"Demographic column '{col.replace('_', ' ').title()}' not found in RTD Drinks data.")

                    # ---- BRAND AWARENESS ----
                    st.subheader("🔎 Brand Awareness (Pie Chart)")
                    # Use preprocessed column names
                    brand_aware_cols = [col for col in df.columns if col.startswith('brand_aware_') and 'none' not in col]
                    existing_brand_aware_cols = [col for col in brand_aware_cols if col in df.columns]
                    if existing_brand_aware_cols:
                        for col in existing_brand_aware_cols:
                            # Extract brand name from preprocessed column
                            brand = col.replace('brand_aware_', '', regex=False).replace('_', ' ').title()
                            data = df[col].astype(str).value_counts(dropna=False).reset_index()
                            data.columns = ['Response', 'Count']
                            st.markdown(f"**{brand}**") # Use markdown for smaller title within subheader
                            pie_chart(data, 'Response', 'Count', f"{brand} Awareness")
                    else:
                         st.info("No brand awareness columns found (e.g., 'brand_aware_coca_cola').")

                    # ---- OVERALL AD RECALL PERFORMANCE ----
                    st.subheader("📢 Overall Brand Ad Recall Performance (Yes Responses)")
                    # Use preprocessed column names
                    recall_cols = [col for col in df.columns if col.startswith('brand_ad_aware_')]
                    existing_recall_cols = [col for col in recall_cols if col in df.columns]

                    if existing_recall_cols:
                        recall_melted = df[existing_recall_cols].astype(str).melt(var_name='Brand_Col', value_name='Response')
                        # Filter out non-response entries (like 'nan', 'None', etc.) and keep only 'Yes'
                        recall_melted = recall_melted[recall_melted['Response'].str.strip().str.lower() == 'yes'] # Assuming responses are 'Yes'/'No'

                        if not recall_melted.empty:
                             # Extract Brand Name from the column name like 'brand_ad_aware_coca_cola_c1'
                             # Need a more robust way to get brand name
                             # Let's just use the full column name for grouping initially if structure is complex
                             # Or assume brand is between brand_ad_aware_ and _c1/c2
                            recall_melted['Brand'] = recall_melted['Brand_Col'].str.replace('brand_ad_aware_', '', regex=False).str.replace('_c[0-9]+', '', regex=True).str.replace('_', ' ').str.title()

                            # Count 'Yes' responses per brand
                            yes_recall_counts = recall_melted.groupby('Brand').size().reset_index(name='Yes Count')

                            bar_chart(yes_recall_counts, 'Brand', 'Yes Count', "Brand Ad Recall (Yes Responses)")
                        else:
                            st.info("No 'Yes' responses found for ad recall across brands.")
                    else:
                        st.info("No ad recall columns found (e.g., 'brand_ad_aware_coca_cola_c1').")


                    # ---- HOT WEATHER BRAND PREFERENCE ----
                    st.subheader("🌞 Brand Preference in Hot Weather")
                    # Use preprocessed column names
                    hot_weather_cols = [col for col in df.columns if col.startswith('hot_weather_purchase')]
                    existing_hot_weather_cols = [col for col in hot_weather_cols if col in df.columns]

                    if existing_hot_weather_cols:
                        for col in existing_hot_weather_cols:
                            # Extract brand name from preprocessed column
                            brand = col.replace('hot_weather_purchase_', '').replace('_', ' ').title()
                            data = df[col].astype(str).value_counts(dropna=False).reset_index()
                            data.columns = ['Response', 'Count']

                            # Skip if no data points exist after value_counts (can happen if column is all NaN)
                            if not data.empty:
                                col1, col2 = st.columns(2)

                                with col1:
                                    st.markdown(f"**{brand} – Pie Chart**")
                                    pie_chart(data, 'Response', 'Count', f"{brand} Hot Weather Preference")

                                with col2:
                                    st.markdown(f"**{brand} – Bar Chart**")
                                    bar_chart(data, 'Response', 'Count', f"{brand} Hot Weather Preference")
                            else:
                                st.info(f"No data for '{brand}' Hot Weather Preference column.")
                    else:
                         st.info("No hot weather purchase preference columns found (e.g., 'hot_weather_purchase_coca_cola').")
                else:
                    st.info("RTD Drinks data is empty after processing.")
            else:
                st.info("Please upload the RTD Drinks CSV file above.")

    # FRIED CHICKEN TAB
    if fried_tab:
        with fried_tab:
            st.header("🍗 Fried Chicken")
            if fried_file:
                df = preprocess(pd.read_csv(fried_file))

                if not df.empty:
                    # ---- DEMOGRAPHICS ----
                    st.subheader("👥 Demographics")
                    # Use preprocessed column names
                    demo_cols = ['gender', 'age_group', 'household_income', 'location']
                    for col in demo_cols:
                        if col in df.columns:
                            chart_data = df[col].astype(str).value_counts(dropna=False).reset_index()
                            chart_data.columns = ['Category', 'Count']
                            bar_chart(chart_data, 'Category', 'Count', col.replace('_', ' ').title())
                        else:
                             st.info(f"Demographic column '{col.replace('_', ' ').title()}' not found in Fried Chicken data.")

                    # ---- TOP OF MIND ----
                    st.subheader("💭 Top of Mind Awareness")
                    # Use preprocessed column names
                    mind_cols = [col for col in df.columns if col.startswith('mind_')]
                    existing_mind_cols = [col for col in mind_cols if col in df.columns]
                    if existing_mind_cols:
                        mind_melted = df[existing_mind_cols].astype(str).melt(var_name='Mind_Col', value_name='Response')
                        mind_melted = mind_melted[mind_melted['Response'].str.strip().str.lower() != 'nan']

                        if not mind_melted.empty:
                            # Count occurrences of each unique response across all 'mind_' columns
                            mind_counts = mind_melted['Response'].str.strip().value_counts().reset_index()
                            mind_counts.columns = ['Brand / Response', 'Count']
                            bar_chart(mind_counts, 'Brand / Response', 'Count', "Top of Mind Mentions")
                        else:
                            st.info("No valid top of mind data found after filtering for Fried Chicken.")
                    else:
                        st.info("No top of mind columns found (e.g., 'mind_kfc', 'mind_mcd').")


                    # ---- AD RECALL ----
                    st.subheader("📢 Ad Recall")
                    # Use preprocessed column names
                    if 'recall_fried_chicken_ad' in df.columns:
                        st.markdown("**Recall Seeing a Fried Chicken Ad**")
                        recall_data = df['recall_fried_chicken_ad'].astype(str).value_counts(dropna=False).reset_index()
                        recall_data.columns = ['Response', 'Count']
                        pie_chart(recall_data, 'Response', 'Count', "Recall Seeing Fried Chicken Ad")
                    else:
                         st.info("No 'recall_fried_chicken_ad' column found.")

                    if 'ad_fried_chicken_brand' in df.columns:
                        st.markdown("**Ad Brand Recalled**")
                        ad_brand_data = df['ad_fried_chicken_brand'].astype(str).value_counts(dropna=False).reset_index()
                        ad_brand_data.columns = ['Brand', 'Count']
                        bar_chart(ad_brand_data, 'Brand', 'Count', "Ad Brand Recalled", sort_order='-y')
                    else:
                         st.info("No 'ad_fried_chicken_brand' column found.")


                    # ---- BIGGEST BRAND PERCEPTION ----
                    st.subheader("🏆 Biggest Fried Chicken Brand Perception")
                    # Use preprocessed column names
                    biggest_cols = [col for col in df.columns if col.startswith('biggest_')]
                    existing_biggest_cols = [col for col in biggest_cols if col in df.columns]
                    if existing_biggest_cols:
                        biggest_melted = df[existing_biggest_cols].astype(str).melt(var_name='Biggest_Col', value_name='Response')
                        biggest_melted = biggest_melted[biggest_melted['Response'].str.strip().str.lower() != 'nan']

                        if not biggest_melted.empty:
                            biggest_counts = biggest_melted['Response'].str.strip().value_counts().reset_index()
                            biggest_counts.columns = ['Brand / Response', 'Count']
                            bar_chart(biggest_counts, 'Brand / Response', 'Count', "Perception: Biggest Fried Chicken Brand")
                        else:
                            st.info("No valid 'biggest' brand perception data found after filtering for Fried Chicken.")
                    else:
                        st.info("No 'biggest' brand perception columns found (e.g., 'biggest_kfc', 'biggest_mcd').")


                    # ---- TASTE PERCEPTION ----
                    st.subheader("😋 Tastiest Fried Chicken Perception")
                    # Use preprocessed column names
                    tastiest_cols = [col for col in df.columns if col.startswith('tastiest_')]
                    existing_tastiest_cols = [col for col in tastiest_cols if col in df.columns]
                    if existing_tastiest_cols:
                        tastiest_melted = df[existing_tastiest_cols].astype(str).melt(var_name='Tastiest_Col', value_name='Response')
                        tastiest_melted = tastiest_melted[tastiest_melted['Response'].str.strip().str.lower() != 'nan']

                        if not tastiest_melted.empty:
                            tastiest_counts = tastiest_melted['Response'].str.strip().value_counts().reset_index()
                            tastiest_counts.columns = ['Brand / Response', 'Count']
                            bar_chart(tastiest_counts, 'Brand / Response', 'Count', "Perception: Tastiest Fried Chicken Brand")
                        else:
                            st.info("No valid 'tastiest' brand perception data found after filtering for Fried Chicken.")
                    else:
                         st.info("No 'tastiest' brand perception columns found (e.g., 'tastiest_kfc', 'tastiest_mcd').")


                    # ---- NEXT PURCHASE ----
                    st.subheader("🛒 Next Purchase Intent")
                    # Use preprocessed column names
                    buy_cols = [col for col in df.columns if col.startswith('next_buy_')]
                    existing_buy_cols = [col for col in buy_cols if col in df.columns]
                    if existing_buy_cols:
                        for col in existing_buy_cols:
                            # Extract brand name from preprocessed column
                            brand = col.replace('next_buy_', '').replace('_', ' ').title()
                            data = df[col].astype(str).value_counts(dropna=False).reset_index()
                            data.columns = ['Response', 'Count']

                             # Skip if no data points exist after value_counts
                            if not data.empty:
                                col1, col2 = st.columns(2)

                                with col1:
                                    st.markdown(f"**{brand} – Pie Chart**")
                                    pie_chart(data, 'Response', 'Count', f"{brand} Next Purchase Intent")

                                with col2:
                                    st.markdown(f"**{brand} – Bar Chart**")
                                    bar_chart(data, 'Response', 'Count', f"{brand} Next Purchase Intent")
                            else:
                                 st.info(f"No data for '{brand}' Next Purchase Intent column.")
                    else:
                         st.info("No next purchase intent columns found (e.g., 'next_buy_kfc').")
                else:
                     st.info("Fried Chicken data is empty after processing.")
            else:
                st.info("Please upload the Fried Chicken CSV file above.")

    # CHOCOLATE TAB
    if choco_tab:
        with choco_tab:
            st.header("🍫 Chocolate")
            if choco_file:
                df = preprocess(pd.read_csv(choco_file))

                if not df.empty:
                    # --- DEMOGRAPHICS ---
                    st.subheader("👤 Demographic Overview")
                    # Use preprocessed column names
                    demo_cols = ['gender', 'age', 'household_income', 'location']
                    # Filter to columns that actually exist
                    existing_demo_cols = [col for col in demo_cols if col in df.columns]
                    if existing_demo_cols:
                        cols = st.columns(len(existing_demo_cols))
                        for i, col in enumerate(existing_demo_cols):
                             chart_data = df[col].astype(str).value_counts(dropna=False).reset_index()
                             chart_data.columns = ['Category', 'Count']
                             with cols[i]:
                                bar_chart(chart_data, 'Category', 'Count', col.replace('_', ' ').title())
                    else:
                         st.info("No common demographic columns found in Chocolate data.")

                    # --- SEEN CHOCOLATE ADS ---
                    # Use preprocessed column names
                    if 'seen_chocolate_ad' in df.columns:
                        st.subheader("📺 Seen Chocolate Ads")
                        seen_ads = df['seen_chocolate_ad'].astype(str).value_counts(dropna=False).reset_index()
                        seen_ads.columns = ['Seen', 'Count']
                        pie_chart(seen_ads, 'Seen', 'Count', "Seen Chocolate Ads")
                    else:
                         st.info("No 'seen_chocolate_ad' column found.")


                    # --- AD RECALL ---
                    st.subheader("🔁 Ad Recall per Brand (Yes Responses)")
                    # Use preprocessed column names
                    ad_cols = [col for col in df.columns if col.startswith('ad_') and col not in ['ad_others_1', 'ad_others_2']]
                    existing_ad_cols = [col for col in ad_cols if col in df.columns]
                    if existing_ad_cols:
                        ad_melted = df[existing_ad_cols].astype(str).melt(var_name='Ad_Col', value_name='Response')
                        # Filter out non-response entries and keep only 'Yes'
                        ad_melted = ad_melted[ad_melted['Response'].str.strip().str.lower() == 'yes']

                        if not ad_melted.empty:
                             # Extract Brand Name from column names like 'ad_kitkat', 'ad_cadbury'
                            ad_melted['Brand'] = ad_melted['Ad_Col'].str.replace('ad_', '', regex=False).str.replace('_', ' ').str.title()
                            # Count 'Yes' responses per brand
                            yes_recall_counts = ad_melted.groupby('Brand').size().reset_index(name='Yes Count')

                            bar_chart(yes_recall_counts, 'Brand', 'Yes Count', "Ad Recall (Yes Responses) by Brand")
                        else:
                             st.info("No 'Yes' responses found for ad recall across brands.")
                    else:
                         st.info("No specific ad recall columns found (e.g., 'ad_kitkat', 'ad_cadbury').")

                    # --- PREFERENCE ---
                    st.subheader("💖 Brand Preference (Yes Responses)")
                    # Use preprocessed column names
                    prefer_cols = [col for col in df.columns if col.startswith('prefer_')]
                    existing_prefer_cols = [col for col in prefer_cols if col in df.columns]
                    if existing_prefer_cols:
                        prefer_melted = df[existing_prefer_cols].astype(str).melt(var_name='Prefer_Col', value_name='Response')
                        # Filter out non-response entries and keep only 'Yes'
                        prefer_melted = prefer_melted[prefer_melted['Response'].str.strip().str.lower() == 'yes']

                        if not prefer_melted.empty:
                             # Extract Brand Name from column names like 'prefer_kitkat', 'prefer_cadbury'
                            prefer_melted['Brand'] = prefer_melted['Prefer_Col'].str.replace('prefer_', '', regex=False).str.replace('_', ' ').str.title()
                            # Count 'Yes' responses per brand
                            yes_prefer_counts = prefer_melted.groupby('Brand').size().reset_index(name='Yes Count')

                            bar_chart(yes_prefer_counts, 'Brand', 'Yes Count', "Brand Preference (Yes Responses)")
                        else:
                            st.info("No 'Yes' responses found for brand preference across brands.")
                    else:
                         st.info("No brand preference columns found (e.g., 'prefer_kitkat', 'prefer_cadbury').")


                    # --- LIKELY TO BUY ---
                    st.subheader("🛒 Likely to Buy")
                    # Use preprocessed column names
                    likely_cols = [col for col in df.columns if col.startswith('likely_buy_')]
                    existing_likely_cols = [col for col in likely_cols if col in df.columns]
                    if existing_likely_cols:
                        for col in existing_likely_cols:
                            # Extract brand name from preprocessed column
                            brand = col.replace('_likely_to_buy', '').replace('_', ' ').title()
                            data = df[col].astype(str).value_counts(dropna=False).reset_index()
                            data.columns = ['Response', 'Count']

                            # Skip if no data points exist
                            if not data.empty:
                                col1, col2 = st.columns(2)

                                with col1:
                                    st.markdown(f"**{brand} – Pie Chart**")
                                    pie_chart(data, 'Response', 'Count', f"{brand} Likely to Buy")

                                with col2:
                                    st.markdown(f"**{brand} – Bar Chart**")
                                    bar_chart(data, 'Response', 'Count', f"{brand} Likely to Buy")
                            else:
                                 st.info(f"No data for '{brand}' Likely to Buy column.")
                    else:
                         st.info("No 'likely to buy' columns found (e.g., 'likely_buy_kitkat').")
                else:
                     st.info("Chocolate data is empty after processing.")
            else:
                st.info("Please upload the Chocolate CSV file above.")

    # PHONES TAB
    if phone_tab:
        with phone_tab:
            st.header("📱 Phone Brands")
            if phone_file:
                df = preprocess(pd.read_csv(phone_file))

                if not df.empty:
                    # Preview
                    st.subheader("📄 Data Preview")
                    st.dataframe(df.head(), use_container_width=True)

                    # Demographics
                    st.subheader("👥 Demographics")
                    for col in ['age_group', 'gender']:
                        if col in df.columns:
                             chart_data = df[col].astype(str).str.strip().value_counts(dropna=False).reset_index()
                             chart_data.columns = ['Category', 'Count']
                             bar_chart(chart_data, 'Category', 'Count', col.replace('_', ' ').title())
                        else:
                             st.info(f"Demographic column '{col.replace('_', ' ').title()}' not found in Phone data.")


                    # Current Phone Ownership
                    st.subheader("📱 Current Phone Ownership")
                    # Use preprocessed column names
                    current_phone_cols = [col for col in df.columns if 'current_phone_' in col]
                    existing_current_phone_cols = [col for col in current_phone_cols if col in df.columns]
                    if existing_current_phone_cols:
                        # Melt the columns for a combined view if needed, or loop individually
                        # Let's loop individually as in the original code
                        for col in existing_current_phone_cols:
                            brand = col.replace('current_phone_', '').replace('_', ' ').title()
                            data = df[col].astype(str).value_counts(dropna=False).reset_index()
                            data.columns = ['Response', 'Count']
                            st.markdown(f"**{brand}**") # Use markdown for smaller title within subheader
                            pie_chart(data, 'Response', 'Count', f"{brand} Ownership")
                    else:
                         st.info("No current phone ownership columns found (e.g., 'current_phone_samsung').")


                    # Next Phone Purchase Intent
                    st.subheader("🛒 Next Phone Purchase Intent")
                    # Use preprocessed column names
                    purchase_cols = [col for col in df.columns if 'next_purchase_' in col]
                    existing_purchase_cols = [col for col in purchase_cols if col in df.columns]
                    if existing_purchase_cols:
                        for col in existing_purchase_cols:
                            brand = col.replace('next_purchase_', '').replace('_', ' ').title()
                            data = df[col].astype(str).value_counts(dropna=False).reset_index()
                            data.columns = ['Response', 'Count']
                            st.markdown(f"**{brand}**") # Use markdown for smaller title within subheader
                            pie_chart(data, 'Response', 'Count', f"{brand} Next Purchase Intent")
                    else:
                         st.info("No next phone purchase intent columns found (e.g., 'next_purchase_samsung').")


                    # Ad Recall
                    st.subheader("📢 Ad Recall")
                    # Use preprocessed column names
                    recall_cols = [col for col in df.columns if 'recall_ads' in col]
                    existing_recall_cols = [col for col in recall_cols if col in df.columns]
                    if existing_recall_cols:
                        for col in existing_recall_cols:
                            data = df[col].astype(str).value_counts(dropna=False).reset_index()
                            data.columns = ['Response', 'Count']
                            st.markdown(f"**{col.replace('_', ' ').title()}**") # Use markdown for smaller title within subheader
                            pie_chart(data, 'Response', 'Count', f"{col.replace('_', ' ').title()} Ad Recall")
                    else:
                         st.info("No ad recall columns found (e.g., 'recall_ads_samsung').")
                else:
                     st.info("Phone data is empty after processing.")
            else:
                st.info("Please upload the Samsung Phone CSV file above.")


    # COCA-COLA TAB
    if cola_tab:
        with cola_tab:
            st.header("🥤 Coca-Cola ")
            if cola_file:
                df=preprocess(pd.read_csv(cola_file))

                if not df.empty:
                    # Demographics
                    st.subheader("👥 Demographics")
                    for col in ['age_group', 'gender']:
                        if col in df.columns:
                             chart_data = df[col].astype(str).str.strip().value_counts(dropna=False).reset_index()
                             chart_data.columns = ['Category', 'Count']
                             bar_chart(chart_data, 'Category', 'Count', col.replace('_', ' ').title())
                        else:
                             st.info(f"Demographic column '{col.replace('_', ' ').title()}' not found in Coca-Cola data.")

                    # Location Visit Frequency
                    st.subheader("📍 Visited Locations")
                    # Use preprocessed column names
                    visit_cols = [col for col in df.columns if col.startswith('visit_')]
                    existing_visit_cols = [col for col in visit_cols if col in df.columns]
                    if existing_visit_cols:
                        for col in existing_visit_cols:
                            data = df[col].astype(str).value_counts(dropna=False).reset_index()
                            data.columns = ['Visited', 'Count']
                            st.markdown(f"**{col.replace('visit_', '').replace('_', ' ').title()}**")
                            bar_chart(data, 'Visited', 'Count', f"{col.replace('visit_', '').replace('_', ' ').title()} Visit Frequency")
                    else:
                         st.info("No visit frequency columns found (e.g., 'visit_supermarket').")

                    # Ad Recall
                    st.subheader("📢 Ad Recall")
                    # Use preprocessed column names
                    recall_cols = [col for col in df.columns if 'recall' in col or 'advertisement' in col]
                    existing_recall_cols = [col for col in recall_cols if col in df.columns]
                    if existing_recall_cols:
                        for col in existing_recall_cols:
                             data = df[col].astype(str).value_counts(dropna=False).reset_index()
                             data.columns = ['Response', 'Count']
                             st.markdown(f"**{col.replace('_', ' ').title()}**")
                             bar_chart(data, 'Response', 'Count', f"{col.replace('_', ' ').title()} Ad Recall")
                    else:
                         st.info("No ad recall columns found (e.g., 'recall_coca_cola_ad').")

                    # Brand Preference
                    st.subheader("🏆 Favorite Soft Drink Brand")
                    # Use preprocessed column names
                    brand_cols = [col for col in df.columns if col.startswith('best_choice_')]
                    existing_brand_cols = [col for col in brand_cols if col in df.columns]
                    if existing_brand_cols:
                        for col in existing_brand_cols:
                            if df[col].dropna().nunique() > 0: # Ensure column has non-NaN data
                                chart_data = df[col].astype(str).value_counts(dropna=False).reset_index()
                                chart_data.columns = ['Brand', 'Count']
                                st.markdown(f"**{col.replace('best_choice_', '').replace('_', ' ').title()}**")
                                bar_chart(chart_data, 'Brand', 'Count', f"{col.replace('best_choice_', '').replace('_', ' ').title()} Preference")
                            else:
                                st.info(f"No data for '{col.replace('best_choice_', '').replace('_', ' ').title()}' preference column.")
                    else:
                        st.info("No brand preference columns found (e.g., 'best_choice_softdrink').")

                    # Enjoyment
                    st.subheader("😋 Soft Drink Enjoyment")
                    # Use preprocessed column names
                    enjoy_cols = [col for col in df.columns if col.startswith('enjoy_')]
                    existing_enjoy_cols = [col for col in enjoy_cols if col in df.columns]
                    if existing_enjoy_cols:
                        for col in existing_enjoy_cols:
                             data = df[col].astype(str).value_counts(dropna=False).reset_index()
                             data.columns = ['Response', 'Count']
                             st.markdown(f"**{col.replace('enjoy_', '').replace('_', ' ').title()}**")
                             bar_chart(data, 'Response', 'Count', f"{col.replace('enjoy_', '').replace('_', ' ').title()} Enjoyment")
                    else:
                         st.info("No enjoyment columns found (e.g., 'enjoy_coca_cola').")

                    # Next Purchase Intent
                    st.subheader("🛒 Next Soft Drink Purchase")
                    # Use preprocessed column names
                    next_cols = [col for col in df.columns if col.startswith('next_purchase')]
                    existing_next_cols = [col for col in next_cols if col in df.columns]
                    if existing_next_cols:
                        for col in existing_next_cols:
                             data = df[col].astype(str).value_counts(dropna=False).reset_index()
                             data.columns = ['Response', 'Count']
                             st.markdown(f"**{col.replace('_', ' ').title()}**")
                             bar_chart(data, 'Response', 'Count', f"{col.replace('_', ' ').title()} Next Purchase")
                    else:
                         st.info("No next purchase columns found (e.g., 'next_purchase_coca_cola').")

                    # Media Usage
                    st.subheader("📺 Media Usage Frequency")
                    # Use preprocessed column names that start with the specific pattern
                    media_cols = [col for col in df.columns if col.startswith('how_often_do_you_use_the_following_media')]
                    existing_media_cols = [col for col in media_cols if col in df.columns]
                    if existing_media_cols:
                        media_melted = df[existing_media_cols].astype(str).melt(var_name='Media_Col', value_name='Frequency')
                        media_melted = media_melted[~media_melted['Frequency'].str.strip().str.lower().isin(['nan', 'none', ''])]

                        if not media_melted.empty:
                            # Extract media type - assuming format like '...__media_type' or '..._media_type'
                            media_melted['Media Type'] = media_melted['Media_Col'].apply(lambda x: x.split('__')[-1].replace('_', ' ').title()) # Use split __ first
                            # Fallback if no __
                            # This fallback logic might be complex, ensure it works or simplify pattern match
                            # Let's stick to the startswith pattern 'how_often_do_you_use_the_following_media'
                            # and assume the rest is the media type name separated by underscores
                            media_melted['Media Type'] = media_melted['Media_Col'].str.replace('how_often_do_you_use_the_following_media', '', regex=False).str.replace('__', '', regex=False).str.replace('_', ' ').str.strip().title()
                            # Handle cases where the full string is the media type itself if no other pattern works
                            if '' in media_melted['Media Type'].unique(): # If we ended up with empty strings after replacing prefix
                                media_melted['Media Type'] = media_melted.apply(
                                     lambda row: row['Media_Col'].replace('_', ' ').title() if row['Media Type'] == '' else row['Media Type'], axis=1
                                )


                            # Count frequencies per media type
                            media_counts = media_melted.groupby(['Media Type', 'Frequency']).size().reset_index(name='Count')

                            # Define order for frequency if known (optional)
                            frequency_order = ['Daily', 'Weekly', 'Monthly', 'Less often', 'Never', 'Prefer not to say'] # Example order
                            # Ensure the order only contains frequencies actually present in the data
                            frequency_order = [f for f in frequency_order if f in media_counts['Frequency'].unique()]

                            # Filter out empty frequency strings before plotting
                            media_counts = media_counts[media_counts['Frequency'].str.strip() != ''].copy()

                            if not media_counts.empty:
                                st.altair_chart(
                                    alt.Chart(media_counts).mark_bar().encode(
                                        x=alt.X('Frequency:N', sort=frequency_order, title='Frequency'), # Sort by defined order
                                        y=alt.Y('Count:Q', title='Count'),
                                        color=alt.Color('Media Type:N', title='Media Type'),
                                        tooltip=['Media Type', 'Frequency', 'Count']
                                    ).properties(title="Media Usage Frequency by Type"),
                                    use_container_width=True
                                )
                            else:
                                 st.info("No valid media usage frequency data found after processing.")
                        else:
                            st.info("No valid media usage frequency data found after melting and filtering.")
                    else:
                        st.info("No media usage frequency columns found.")

                else:
                     st.info("Coca-Cola data is empty after processing.")
            else:
                st.info("Please upload the Coca-Cola CSV file above.")


    # MUDAH TAB
    if mudah_tab:
        with mudah_tab:
            st.header("🛒 Mudah")
            if mudah_file:
                df = preprocess(pd.read_csv(mudah_file))

                if not df.empty:
                    # --- Standard Column Groupings ---
                    # Use preprocessed column names
                    # monthly_household_incom seems like a typo from original code? Assume that's the intended name after cleaning.
                    demographic_cols = ['age_group', 'gender', 'monthly_household_incom']
                    browsing_freq_col = 'property_automotive_browsing_frequency_past_month' # Assuming this cleaned name
                    mudah_platform_cols = [col for col in df.columns if 'used_platform' in col] # Assuming pattern matches preprocessed
                    ad_rounds = ['r1', 'r2', 'r3', 'r4']
                    # Media use pattern similar to Coca-Cola/Mudah
                    # Assuming pattern like 'how_often_do_you_use__media_type'
                    media_use_cols = [col for col in df.columns if col.startswith('how_often_do_you_use__')]
                    purchase_intent_col = 'likelihood_to_purchase_via_mudah_next_6_months' # Assuming this cleaned name

                    # --- Summary ---
                    st.subheader("📊 Summary")
                    col1, col2 = st.columns(2)
                    col1.metric("Total Responses", f"{len(df):,}")
                    # Recalculate platforms tracked based on found columns
                    col2.metric("Platforms Tracked (in survey)", len([c for c in mudah_platform_cols if c in df.columns])) # Only count if found after preprocess

                    # --- Demographics ---
                    st.subheader("👥 Demographics Distribution")
                    for col in demographic_cols:
                        if col in df.columns:
                            chart_data = df[col].astype(str).str.strip().value_counts(dropna=False).reset_index()
                            chart_data.columns = [col.replace('_', ' ').title(), 'Count'] # Use user-friendly title
                            bar_chart(chart_data, chart_data.columns[0], 'Count', chart_data.columns[0])
                        else:
                            st.info(f"Demographic column '{col.replace('_', ' ').title()}' not found in Mudah data.")


                    # --- Browsing Frequency ---
                    if browsing_freq_col in df.columns:
                        st.subheader("🚗 Property/Automotive Browsing Frequency")
                        freq_counts = df[browsing_freq_col].astype(str).str.strip().value_counts(dropna=False).reset_index()
                        freq_counts.columns = ['Frequency', 'Count']
                        bar_chart(freq_counts, 'Frequency', 'Count', "Property/Automotive Browsing Frequency")
                    else:
                         st.info(f"Browsing frequency column '{browsing_freq_col.replace('_', ' ').title()}' not found.")

                    # --- Used Platform Analysis ---
                    if mudah_platform_cols and any(c in df.columns for c in mudah_platform_cols):
                        st.subheader("📱 Platforms Used for Property/Auto Browsing")
                        # Select only the columns that actually exist in the dataframe
                        existing_platform_cols = [c for c in mudah_platform_cols if c in df.columns]
                        if existing_platform_cols:
                            used_platforms = df[existing_platform_cols].astype(str).apply(lambda col: col.str.strip()).stack().reset_index(drop=True)
                            used_platforms = used_platforms[~used_platforms.str.lower().isin(['', 'nan', 'none'])]

                            if not used_platforms.empty:
                                platform_counts = used_platforms.value_counts().reset_index()
                                platform_counts.columns = ['Platform', 'Mentions']
                                bar_chart(platform_counts, 'Platform', 'Mentions', "Platforms Used for Property/Auto Browsing")
                            else:
                                st.info("No valid data found for platforms used.")
                        else:
                            st.info("No platform usage columns found matching the expected pattern.")
                    else:
                         st.info("No platform usage columns found.")


                    # --- Ad Recall & Effectiveness ---
                    st.subheader("📺 Ad Recall & Effectiveness (by Round)")
                    found_ad_data = False
                    for round_ in ad_rounds:
                        recall_col = f'ad_recall_{round_}'
                        # Adjust finding impact columns based on preprocessed names
                        impact_cols = [col for col in df.columns if col.endswith(f'_{round_}') and col != recall_col] # Assume other metrics end with _rX
                        impact_cols = [col for col in impact_cols if 'info' in col or 'unique' in col or 'relevance' in col or 'engaging' in col] # Refine search

                        existing_impact_cols_round = [c for c in impact_cols if c in df.columns]

                        if recall_col in df.columns or existing_impact_cols_round:
                            st.markdown(f"### 🎯 Round {round_.upper()}")
                            found_ad_data = True # Mark that we found data for at least one round

                            # Ad Recall
                            if recall_col in df.columns:
                                st.markdown(f"**{recall_col.replace('_', ' ').title()}**")
                                recall_counts = df[recall_col].astype(str).str.strip().value_counts(dropna=False).reset_index()
                                recall_counts.columns = ['Recall', 'Count']
                                bar_chart(recall_counts, 'Recall', 'Count', f"Ad Recall Round {round_.upper()}")
                            else:
                                st.info(f"Ad Recall column '{recall_col.replace('_', ' ').title()}' not found for Round {round_.upper()}.")


                            # Other Metrics (Info, Uniqueness, Relevance, etc.)
                            if existing_impact_cols_round:
                                for col in existing_impact_cols_round:
                                    label = col.replace('_', ' ').replace(f' {round_}', '').title() # Remove round suffix for label
                                    chart_data = df[col].astype(str).str.strip().value_counts(dropna=False).reset_index()
                                    chart_data.columns = [label, 'Count']
                                    st.markdown(f"**{label}**")
                                    bar_chart(chart_data, label, 'Count', f"{label} Round {round_.upper()}")
                            elif recall_col not in df.columns: # Only show this message if no recall *or* impact columns were found for the round
                                 st.info(f"No ad effectiveness columns found for Round {round_.upper()}.")

                    if not found_ad_data:
                         st.info("No ad recall or effectiveness columns found for any round (e.g., 'ad_recall_r1', 'info_r1').")


                    # --- Purchase Intent ---
                    if purchase_intent_col in df.columns:
                        st.subheader("🛍️ Likelihood to Purchase via Mudah (Next 6 Months)")
                        purchase_counts = df[purchase_intent_col].astype(str).str.strip().value_counts(dropna=False).reset_index()
                        purchase_counts.columns = ['Intent', 'Count']
                        bar_chart(purchase_counts, 'Intent', 'Count', "Likelihood to Purchase via Mudah (Next 6 Months)")
                    else:
                         st.info(f"Purchase intent column '{purchase_intent_col.replace('_', ' ').title()}' not found.")


                    # --- Media Usage ---
                    if media_use_cols and any(c in df.columns for c in media_use_cols):
                        st.subheader("📡 Media Usage Frequency")
                        # Select only columns that actually exist
                        existing_media_cols = [c for c in media_use_cols if c in df.columns]
                        if existing_media_cols:
                            media_melted = df[existing_media_cols].astype(str).melt(var_name='Media_Col', value_name='Frequency')
                            media_melted = media_melted[~media_melted['Frequency'].str.strip().str.lower().isin(['nan', 'none', ''])]

                            if not media_melted.empty:
                                # Extract media type - assuming format like 'how_often_do_you_use__media_type'
                                media_melted['Media Type'] = media_melted['Media_Col'].apply(lambda x: x.split('__')[-1].replace('_', ' ').title())

                                # Count frequencies per media type
                                media_counts = media_melted.groupby(['Media Type', 'Frequency']).size().reset_index(name='Count')

                                # Define order for frequency if known (optional)
                                frequency_order = ['Daily', 'Weekly', 'Monthly', 'Less often', 'Never', 'Prefer not to say'] # Example order
                                frequency_order = [f for f in frequency_order if f in media_counts['Frequency'].unique()] # Filter to existing values

                                st.altair_chart(
                                    alt.Chart(media_counts).mark_bar().encode(
                                        x=alt.X('Frequency:N', sort=frequency_order, title='Frequency'), # Sort by defined order
                                        y=alt.Y('Count:Q', title='Count'),
                                        color=alt.Color('Media Type:N', title='Media Type'),
                                        tooltip=['Media Type', 'Frequency', 'Count']
                                    ).properties(title="Media Usage Frequency by Type"),
                                    use_container_width=True
                                )
                            else:
                                st.info("No valid media usage data found after processing.")
                        else:
                            st.info("No media usage columns found matching the expected pattern.")
                    else:
                         st.info("No media usage columns found.")

                else:
                     st.info("Mudah data is empty after processing.")
            else:
                st.info("Please upload the Mudah CSV file above.")

    # KFC TAB
    if kfc_tab:
        with kfc_tab:
            st.header("🍗 KFC Brand Study Dashboard")
            if kfc_file:
                df=preprocess(pd.read_csv(kfc_file))

                if not df.empty:
                    # Identify sections - Use preprocessed names
                    demographics = [col for col in df.columns if 'age' in col or 'gender' in col or 'income' in col]
                    fast_food_freq_cols = [col for col in df.columns if 'eat_out' in col] # Plural for safety
                    brand_visit_cols = [col for col in df.columns if 'brand_you_visit_the_most' in col and 'other' not in col]
                    decision_factors_cols = [col for col in df.columns if 'important_to_you_when_choosing' in col] # Plural for safety
                    # This psychographics column name is very long, need to verify after preprocess
                    psychographics_prefix = 'how_agree_or_disagree_are_you_with_these_following_statements'
                    psychographics_cols = [col for col in df.columns if col.startswith(psychographics_prefix)] # Look for columns starting with this
                    ad_recall_cols = [col for col in df.columns if 'recall_seeing_these_ads' in col or 'advertisement_for' in col] # Plural for safety
                    # Media use pattern similar to Coca-Cola/Mudah
                    media_use_cols = [col for col in df.columns if col.startswith('how_often_do_you_use_the_following_media')] # Adjusted pattern

                    # Preview
                    st.subheader("📄 Data Preview")
                    st.dataframe(df.head(), use_container_width=True)

                    # Demographics
                    st.subheader("👥 Demographics")
                    for col in demographics:
                         if col in df.columns:
                            col_name = col.replace('_', ' ').title()
                            chart_data = df[col].astype(str).str.strip().value_counts(dropna=False).reset_index()
                            chart_data.columns = [col_name, 'Count']
                            bar_chart(chart_data, col_name, 'Count', col_name)
                         else:
                              st.info(f"Demographic column '{col.replace('_', ' ').title()}' not found in KFC data.")


                    # Fast Food Habits
                    st.subheader("🍔 Fast Food Dining Frequency")
                    if fast_food_freq_cols and any(c in df.columns for c in fast_food_freq_cols):
                        # Assuming there's one main frequency column or we combine them
                        # Let's assume there's one key one like 'how_often_do_you_eat_out'
                        main_freq_col = [c for c in fast_food_freq_cols if 'how_often' in c or 'frequency' in c]
                        if main_freq_col:
                            col = main_freq_col[0] # Take the first one found that exists
                            if col in df.columns:
                                chart_data = df[col].astype(str).str.strip().value_counts(dropna=False).reset_index()
                                chart_data.columns = ['Frequency', 'Count']
                                bar_chart(chart_data, 'Frequency', 'Count', col.replace('_', ' ').title())
                            else:
                                st.info(f"Main frequency column '{col.replace('_', ' ').title()}' not found.")
                        else:
                            st.info("No specific 'how_often' or 'frequency' dining column found.")
                    else:
                         st.info("No fast food dining frequency columns found.")


                    # Most Visited Brand
                    st.subheader("🏪 Most Visited Fast Food Brand")
                    if brand_visit_cols and any(c in df.columns for c in brand_visit_cols):
                        # Assume there's one main 'most visited' column
                        existing_visit_cols = [c for c in brand_visit_cols if c in df.columns]
                        if existing_visit_cols:
                            col = existing_visit_cols[0] # Take the first existing one
                            chart_data = df[col].astype(str).str.strip().value_counts(dropna=False).reset_index()
                            chart_data.columns = ['Brand', 'Count']
                            bar_chart(chart_data, 'Brand', 'Count', col.replace('_', ' ').title())
                        else:
                            st.info("The specific 'brand_you_visit_the_most' column was not found after processing.")
                    else:
                         st.info("No 'most visited brand' column found.")


                    # Decision Factors (Ranking)
                    st.subheader("📌 Top Factors When Choosing Fast Food")
                    # Decision factors might be like "rank_1", "rank_2" or specific factor columns
                    # The original code assumes columns *end with* 'important_to_you_when_choosing'
                    # Let's re-evaluate based on expected preprocessed names. Maybe they start with the factor name?
                    # E.g., 'price_important_to_you_when_choosing', 'taste_important_to_you_when_choosing'
                    factor_cols_pattern = '_important_to_you_when_choosing'
                    decision_factors_cols = [col for col in df.columns if factor_cols_pattern in col]

                    if decision_factors_cols and any(c in df.columns for c in decision_factors_cols):
                        # Filter to existing columns
                        existing_factor_cols = [c for c in decision_factors_cols if c in df.columns]
                        # Melt to combine data
                        factor_melted = df[existing_factor_cols].astype(str).melt(var_name='Factor_Col', value_name='Response')
                        factor_melted = factor_melted[~factor_melted['Response'].str.strip().str.lower().isin(['nan', 'none', ''])]

                        if not factor_melted.empty:
                            # Extract Factor Name from column name (e.g., 'price' from 'price_important_...')
                            factor_melted['Factor'] = factor_melted['Factor_Col'].str.replace(factor_cols_pattern, '', regex=False).str.replace('_', ' ').str.title()

                            # Count responses for each factor/response combination
                            factor_counts = factor_melted.groupby(['Factor', 'Response']).size().reset_index(name='Count')

                            # Attempt to infer if it's a ranking question (1st, 2nd, etc.) or agreement (Agree, Disagree)
                            # If Responses look like ranks (1, 2, 3 or '1st', '2nd'), treat as ranking
                            possible_ranks = ['1', '2', '3', '4', '5', '1st', '2nd', '3rd', '4th', '5th']
                            # Check if *any* response in the melted data looks like a rank
                            is_ranking = factor_counts['Response'].astype(str).str.contains('|'.join(possible_ranks), na=False).any()

                            if is_ranking:
                                # Ranking chart - stacked bar by rank
                                # Define order for ranks if possible
                                rank_order = ['1st', '2nd', '3rd', '4th', '5th'] # Example order
                                # Ensure the order only contains frequencies actually present in the data
                                rank_order = [f for f in rank_order if f in factor_counts['Response'].unique()]

                                st.altair_chart(
                                    alt.Chart(factor_counts).mark_bar().encode(
                                        x=alt.X('Factor:N', title='Factor', sort='-y'),
                                        y=alt.Y('Count:Q', title='Count'),
                                        color=alt.Color('Response:N', sort=rank_order, title='Rank'), # Sort by rank order
                                        tooltip=['Factor', 'Response', 'Count']
                                    ).properties(title="Decision Factor Ranking"),
                                    use_container_width=True
                                )
                            else:
                                # Assume it's an agreement scale or similar
                                # Define order for agreement scale if known (optional)
                                agreement_order = ['Strongly Disagree', 'Disagree', 'Neutral', 'Agree', 'Strongly Agree'] # Example order
                                # Ensure the order only contains frequencies actually present in the data
                                agreement_order = [f for f in agreement_order if f in factor_counts['Response'].unique()]

                                st.altair_chart(
                                    alt.Chart(factor_counts).mark_bar().encode(
                                        x=alt.X('Factor:N', title='Factor', sort='-y'),
                                        y=alt.Y('Count:Q', title='Count'),
                                        color=alt.Color('Response:N', title='Response'),
                                        tooltip=['Factor', 'Response', 'Count']
                                    ).properties(title="Decision Factor Response"),
                                    use_container_width=True
                                )

                        else:
                             st.info("No valid decision factor data found after filtering for KFC.")
                    else:
                         st.info("No decision factor columns found (e.g., 'price_important_to_you_when_choosing').")


                    # Psychographic Agreement
                    st.subheader("🧠 Psychographic Agreement")
                    if psychographics_cols and any(c in df.columns for c in psychographics_cols):
                        # Filter to existing columns
                        existing_psycho_cols = [c for c in psychographics_cols if c in df.columns]
                        # Melt to combine data
                        agreement_melted = df[existing_psycho_cols].astype(str).melt(var_name='Statement_Col', value_name='Response')
                        agreement_melted = agreement_melted[~agreement_melted['Response'].str.strip().str.lower().isin(['nan', 'none', ''])]

                        if not agreement_melted.empty:
                             # Extract Statement from column name (e.g., 'i_like_to_try_new_things' from 'how_agree_..._i_like_to_try_new_things')
                            agreement_melted['Statement'] = agreement_melted['Statement_Col'].str.replace(f'{psychographics_prefix}__', '', regex=False).str.replace('_', ' ').str.title() # Assuming __ separator after prefix

                            # Count responses per statement
                            agreement_counts = agreement_melted.groupby(['Statement', 'Response']).size().reset_index(name='Count')

                            # Define order for agreement scale if known (optional)
                            agreement_order = ['Strongly Disagree', 'Disagree', 'Neutral', 'Agree', 'Strongly Agree'] # Example order
                            agreement_order = [a for a in agreement_order if a in agreement_counts['Response'].unique()] # Filter to existing values

                            st.altair_chart(
                                alt.Chart(agreement_counts).mark_bar().encode(
                                    x=alt.X('Response:N', sort=agreement_order, title='Agreement Level'), # Sort by order
                                    y=alt.Y('Count:Q', title='Count'),
                                    color=alt.Color('Statement:N', title='Statement'),
                                    tooltip=['Statement', 'Response', 'Count']
                                ).properties(title="Psychographic Agreement by Statement"),
                                use_container_width=True
                            )
                        else:
                             st.info("No valid psychographic data found after filtering for KFC.")
                    else:
                        st.info(f"No psychographic columns found starting with '{psychographics_prefix.replace('_', ' ').title()}'.")


                    # Ad Recall
                    st.subheader("📢 Ad Recall & Brand Mention")
                    if ad_recall_cols and any(c in df.columns for c in ad_recall_cols):
                        for col in ad_recall_cols:
                             if col in df.columns:
                                st.markdown(f"**{col.replace('_', ' ').title()}**")
                                ad_data = df[col].astype(str).str.strip().value_counts(dropna=False).reset_index()
                                ad_data.columns = ['Response', 'Count']
                                bar_chart(ad_data, 'Response', 'Count', col.replace('_', ' ').title())
                             else:
                                 st.info(f"Ad Recall column '{col.replace('_', ' ').title()}' not found.")
                    else:
                         st.info("No ad recall columns found.")


                    # Media Use
                    st.subheader("📺 Media Consumption")
                    if media_use_cols and any(c in df.columns for c in media_use_cols):
                        # Filter to existing columns
                        existing_media_cols = [c for c in media_use_cols if c in df.columns]
                        if existing_media_cols:
                            media_melted = df[existing_media_cols].astype(str).melt(var_name='Media_Col', value_name='Frequency')
                            media_melted = media_melted[~media_melted['Frequency'].str.strip().str.lower().isin(['nan', 'none', ''])]

                            if not media_melted.empty:
                                # Extract media type - assuming format like 'how_often_do_you_use_the_following_media__media_type'
                                media_melted['Media Type'] = media_melted['Media_Col'].str.replace('how_often_do_you_use_the_following_media__', '', regex=False).str.replace('_', ' ').str.title()

                                # Count frequencies per media type
                                media_counts = media_melted.groupby(['Media Type', 'Frequency']).size().reset_index(name='Count')

                                # Define order for frequency if known (optional)
                                frequency_order = ['Daily', 'Weekly', 'Monthly', 'Less often', 'Never', 'Prefer not to say'] # Example order
                                frequency_order = [f for f in frequency_order if f in media_counts['Frequency'].unique()] # Filter to existing values

                                st.altair_chart(
                                    alt.Chart(media_counts).mark_bar().encode(
                                        x=alt.X('Frequency:N', sort=frequency_order, title='Frequency'), # Sort by defined order
                                        y=alt.Y('Count:Q', title='Count'),
                                        color=alt.Color('Media Type:N', title='Media Type'),
                                        tooltip=['Media Type', 'Frequency', 'Count']
                                    ).properties(title="Media Usage Frequency by Type"),
                                    use_container_width=True
                                )
                            else:
                                st.info("No valid media usage data found after processing.")
                        else:
                            st.info("No media usage columns found matching the expected pattern.")
                    else:
                         st.info("No media usage columns found.")


                else:
                     st.info("KFC data is empty after processing.")
            else:
                st.info("Please upload the KFC CSV file above.")

    # PANASONIC TAB
    if panasonic_tab:
        with panasonic_tab:
            st.header("💨 Panasonic Hairdryer Consumer")
            if panasonic_file:
                df=preprocess(pd.read_csv(panasonic_file))

                if not df.empty:
                    # Preview
                    st.subheader("📄 Data Preview")
                    st.dataframe(df.head(), use_container_width=True)

                    # Demographics: Bar Chart for Age and Gender
                    st.subheader("👥 Demographics")
                    col1, col2 = st.columns(2)

                    # Use preprocessed column names
                    age_col = 'please_select_the_age_group_based_on_your_age'
                    gender_col = 'please_select_your_gender'

                    with col1:
                        if age_col in df.columns:
                            chart_data = df[age_col].astype(str).str.strip().value_counts(dropna=False).reset_index()
                            chart_data.columns = ['Category', 'Count']
                            bar_chart(chart_data, 'Category', 'Count', age_col.replace('_', ' ').title())
                        else:
                            st.info(f"Demographic column '{age_col.replace('_', ' ').title()}' not found in Panasonic data.")

                    with col2:
                        if gender_col in df.columns:
                            chart_data = df[gender_col].astype(str).str.strip().value_counts(dropna=False).reset_index()
                            chart_data.columns = ['Category', 'Count']
                            bar_chart(chart_data, 'Category', 'Count', gender_col.replace('_', ' ').title())
                        else:
                             st.info(f"Demographic column '{gender_col.replace('_', ' ').title()}' not found in Panasonic data.")


                    # Brand Ownership - Pie Chart + Bar Chart (for Current Hairdryer Brand)
                    st.subheader("💨 Current Hairdryer Brand Ownership")
                    # Use preprocessed column names
                    brand_cols = ['dyson', 'philips', 'laifen', 'khind', 'panasonic', 'dreame', 'xiaomi', 'revlon', 'vidal_sassoon']
                    existing_brand_cols = [col for col in brand_cols if col in df.columns]

                    if existing_brand_cols:
                        cols1, cols2 = st.columns(2) # Two columns for side-by-side charts

                        for brand in existing_brand_cols:
                             data = df[brand].astype(str).value_counts(dropna=False).reset_index()
                             data.columns = ['Response', 'Count']

                             # Skip if no data points exist
                             if not data.empty:
                                # Pie Chart
                                with cols1:
                                    st.markdown(f"**{brand.replace('_', ' ').title()}**")
                                    pie_chart(data, 'Response', 'Count', f"{brand.replace('_', ' ').title()} Ownership")

                                # Bar Chart
                                with cols2:
                                    st.markdown(f"**{brand.replace('_', ' ').title()}**")
                                    bar_chart(data, 'Response', 'Count', f"{brand.replace('_', ' ').title()} Ownership")
                             else:
                                 st.info(f"No data for '{brand.replace('_', ' ').title()}' Ownership column.")
                    else:
                         st.info("No brand ownership columns found matching expected patterns.")


                    # Likely to Buy - Pie Chart + Bar Chart
                    st.subheader("🛒 Likely to Buy Hairdryer")
                    # Use preprocessed column names
                    purchase_cols = ['dyson_likely_to_buy', 'philips_likely_to_buy', 'laifen_likely_to_buy', 'khind_likely_to_buy',
                                     'panasonic_likely_to_buy', 'dreame_likely_to_buy', 'xiaomi_likely_to_buy', 'revlon_likely_to_buy',
                                     'vidal_sassoon_likely_to_buy']
                    existing_purchase_cols = [col for col in purchase_cols if col in df.columns]

                    if existing_purchase_cols:
                        cols1, cols2 = st.columns(2) # Two columns for side-by-side charts

                        for col in existing_purchase_cols:
                            brand = col.replace('_likely_to_buy', '').replace('_', ' ').title()
                            data = df[col].astype(str).value_counts(dropna=False).reset_index()
                            data.columns = ['Response', 'Count']

                            # Skip if no data points exist
                            if not data.empty:
                                # Pie Chart
                                with cols1:
                                    st.markdown(f"**{brand}**")
                                    pie_chart(data, 'Response', 'Count', f"{brand} Likely to Buy")

                                with cols2:
                                    st.markdown(f"**{brand}**")
                                    bar_chart(data, 'Response', 'Count', f"{brand} Likely to Buy")
                            else:
                                 st.info(f"No data for '{brand}' Likely to Buy column.")
                    else:
                         st.info("No 'likely to buy' columns found matching expected patterns.")

                else:
                     st.info("Panasonic data is empty after processing.")
            else:
                st.info("Please upload the Panasonic CSV file above.")


# --- Column 2: Billboard Merger & Map ---
with col_billboard:
    st.header("🗺️ Billboard Merger + Map + Charts")
    st.write("Upload billboard CSV files below. Data will be merged and visualized here.")

    # --- File Uploaders (Moved to Main Page Column) ---
    st.subheader("📂 Upload Billboard CSV Files")
    # This is the multi-file uploader, moved from the sidebar to the main column
    uploaded_billboard_files = st.file_uploader(
        "Upload Billboard CSV files (max 20)",
        type="csv",
        accept_multiple_files=True,
        key="main_billboard_uploader" # Changed key since it's no longer in sidebar
    )

    # --- Billboard Data Loading and Preprocessing (Now depends on main page column uploader) ---
    merged_billboard_df = None # Re-initialize within the column scope
    if uploaded_billboard_files:
        if len(uploaded_billboard_files) > 20:
            st.warning(f"You uploaded {len(uploaded_billboard_files)} billboard files. Only the first 20 will be used.")
            billboard_files_to_process = uploaded_billboard_files[:20]
        else:
            billboard_files_to_process = uploaded_billboard_files
            st.success(f"✅ {len(billboard_files_to_process)} billboard file(s) uploaded.") # Changed to st.success

        all_billboard_dataframes = []
        for file in billboard_files_to_process:
            try:
                # Use preprocess function here too for consistency
                # Read directly from the file-like object
                df = preprocess(pd.read_csv(file)) # Use preprocess on read
                # Store original file name BEFORE column preprocessing modifies it
                df['source_file'] = file.name.replace('.', '_').lower() # Clean source file name
                all_billboard_dataframes.append(df)
            except Exception as e:
                st.error(f"❌ Error reading or processing `{file.name}`: {e}") # Changed to st.error

        if all_billboard_dataframes:
            # Concatenate all billboard dataframes
            merged_billboard_df = pd.concat(all_billboard_dataframes, ignore_index=True, sort=False)

            # --- Billboard Data Cleaning (after concat) ---
            # Use preprocessed column names (lowercase, snake_case)
            lat_col = 'latitude'
            lon_col = 'longitude'
            views_col = 'potential_views'
            reach_col = 'reach'

            if lat_col in merged_billboard_df.columns and lon_col in merged_billboard_df.columns:
                merged_billboard_df[lat_col] = pd.to_numeric(merged_billboard_df[lat_col], errors='coerce')
                merged_billboard_df[lon_col] = pd.to_numeric(merged_billboard_df[lon_col], errors='coerce')
                # Filter rows with invalid lat/lon early
                merged_billboard_df = merged_billboard_df.dropna(subset=[lat_col, lon_col]).reset_index(drop=True)

                if views_col in merged_billboard_df.columns and reach_col in merged_billboard_df.columns:
                    # Custom cleaning function for potential thousands separators
                    def clean_numeric_string_billboard(val):
                        if pd.isna(val):
                            return pd.NA
                        # Handle numbers stored as strings like "1,234"
                        return str(val).replace(',', '').replace(' ', '').strip() or pd.NA

                    # Apply cleaning to the relevant columns *after* preprocessing
                    merged_billboard_df[views_col] = pd.to_numeric(merged_billboard_df[views_col].apply(clean_numeric_string_billboard), errors='coerce')
                    merged_billboard_df[reach_col] = pd.to_numeric(merged_billboard_df[reach_col].apply(clean_numeric_string_billboard), errors='coerce')

                    merged_billboard_df['reach_pct'] = pd.NA # New column for percentage
                    valid_mask = merged_billboard_df[views_col].notna() & (merged_billboard_df[views_col] != 0) & merged_billboard_df[reach_col].notna()
                    merged_billboard_df.loc[valid_mask, 'reach_pct'] = (merged_billboard_df.loc[valid_mask, reach_col] / merged_billboard_df.loc[valid_mask, views_col]) * 100
                    merged_billboard_df['reach_pct'] = merged_billboard_df['reach_pct'].clip(upper=100) # Cap percentage at 100%
            else:
                 st.warning("Latitude or Longitude columns not found or invalid in billboard data. Cannot plot map.")


    # Create nested Billboard tabs (Nested within col_billboard)
    billboard_tabs = st.tabs(["📍 Data & Map", "📊 Charts"])

    # --- Billboard Data & Map Tab (Nested within col_billboard) ---
    with billboard_tabs[0]:
        st.subheader("📋 Merged Data Preview")
        if merged_billboard_df is not None and not merged_billboard_df.empty:
            st.dataframe(merged_billboard_df.head(10), use_container_width=True)

            # --- Summary Metrics ---
            with st.expander("📈 Key Metrics Summary", expanded=True):
                total = len(merged_billboard_df)
                # Use preprocessed column names for calculations
                avg_views = merged_billboard_df.get('potential_views', pd.Series(dtype=float)).mean(skipna=True)
                avg_reach = merged_billboard_df.get('reach', pd.Series(dtype=float)).mean(skipna=True)
                avg_pct = merged_billboard_df.get('reach_pct', pd.Series(dtype=float)).mean(skipna=True)

                col1, col2 = st.columns(2) # Use columns within the main column for metrics
                col1.metric("Total Billboards", f"{total:,}")
                col2.metric("Avg. Potential Views", f"{avg_views:,.0f}" if pd.notna(avg_views) else "N/A")
                # Use different columns or rows for the other metrics if space is tight
                col3, col4 = st.columns(2)
                col3.metric("Avg. Reach", f"{avg_reach:,.0f}" if pd.notna(avg_reach) else "N/A")
                col4.metric("Avg. Reach (%)", f"{avg_pct:.2f}%" if pd.notna(avg_pct) else "N/A")


            st.subheader("📍 Billboard Locations Map")

            # Use preprocessed column names for map
            lat_col = 'latitude'
            lon_col = 'longitude'
            reach_pct_col = 'reach_pct' # New column created during Billboard data loading

            # Ensure we have Lat/Lon and at least one valid row before proceeding with map
            if lat_col in merged_billboard_df.columns and lon_col in merged_billboard_df.columns and not merged_billboard_df.dropna(subset=[lat_col, lon_col]).empty:
                try:
                    # Filter out rows with invalid Lat/Lon before calculating center and iterating
                    map_df = merged_billboard_df.dropna(subset=[lat_col, lon_col]).copy()

                    center_lat = map_df[lat_col].mean()
                    center_lon = map_df[lon_col].mean()
                    # Adjust zoom start if needed for a wider view
                    m = folium.Map(location=[center_lat, center_lon], zoom_start=5)

                    def get_marker_color(reach_pct_val):
                        if pd.isna(reach_pct_val):
                            return "gray"
                        elif reach_pct_val >= 75:
                            return "green"
                        elif reach_pct_val >= 40:
                            return "orange"
                        else:
                            return "red"

                    # Iterate only over rows with valid Lat/Lon from map_df
                    for _, row in map_df.iterrows():

                        # Use the safe_display_string function for potentially missing/non-string data
                        location_raw = row.get('location', row.get('country'))
                        location_display = safe_display_string(location_raw)

                        district_raw = row.get('district')
                        district_display = safe_display_string(district_raw)

                        reference_id_raw = row.get('reference_id')
                        reference_id_display = safe_display_string(reference_id_raw)

                        source_file_raw = row.get('source_file') # Get the preprocessed source file name
                        source_file_display = safe_display_string(source_file_raw, default_display='Unknown File')

                        potential_views_display = f"{row.get('potential_views', pd.NA):,.0f}" if pd.notna(row.get('potential_views')) else "N/A"
                        reach_display = f"{row.get('reach', pd.NA):,.0f}" if pd.notna(row.get('reach')) else "N/A"
                        reach_percent_val = row.get(reach_pct_col, pd.NA)
                        reach_percent_display = f"{reach_percent_val:.2f}%" if pd.notna(reach_percent_val) else "N/A"

                        tooltip = f"""
                            <strong>File:</strong> {source_file_display}<br>
                            <strong>Location:</strong> {location_display}<br>
                            <strong>District:</strong> {district_display}<br>
                            <strong>Reference ID:</strong> {reference_id_display}<br>
                            <strong>Lat:</strong> {row[lat_col]}<br>
                            <strong>Lon:</strong> {row[lon_col]}<br>
                            <strong>Potential Views:</strong> {potential_views_display}<br>
                            <strong>Reach:</strong> {reach_display}<br>
                            <strong>Reach %:</strong> {reach_percent_display}
                        """

                        folium.Marker(
                            location=[row[lat_col], row[lon_col]],
                            popup=folium.Popup(tooltip, max_width=300),
                            icon=folium.Icon(color=get_marker_color(reach_percent_val), icon="info-sign")
                        ).add_to(m)

                    # Use st_folium with use_container_width=True to fit the column
                    st_folium(m, width=None, height=600, use_container_width=True)

                except Exception as map_e:
                    st.error(f"❌ Could not plot map: {map_e}")
            else:
                st.info("No valid Latitude and Longitude data found in the uploaded billboard files to plot the map.")


            # --- Download ---
            if merged_billboard_df is not None and not merged_billboard_df.empty:
                 # Include the calculated 'reach_pct' column in the download
                csv = merged_billboard_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="⬇️ Download Merged Billboard CSV",
                    data=csv,
                    file_name="merged_billboard_data.csv",
                    mime="text/csv"
                )

        else:
            st.info("Upload Billboard CSV files using the file uploader below to see the merged data and map.")

    # --- Billboard Charts Tab (Nested within col_billboard) ---
    with billboard_tabs[1]:
        st.header("📊 Billboard Data Charts")
        if merged_billboard_df is not None and not merged_billboard_df.empty:
            st.write("Analyze distributions and key metrics from the merged billboard data.")

            # --- Select Chart Type ---
            chart_type = st.selectbox(
                "Select chart type:",
                ["-- Select a chart type --", "Bar Chart (Counts)", "Pie Chart (Counts)", "Distribution (Views/Reach)", "Gauge (Avg. Reach %)"],
                key='billboard_chart_selector' # Add a unique key
            )

            # Use preprocessed column names for chart options
            potential_category_cols = ['location', 'country', 'district', 'category', 'media_owner', 'format', 'venue_type', 'schedule', 'source_file']
            chartable_categorical_cols = [col for col in potential_category_cols if col in merged_billboard_df.columns]

            if chart_type == "Bar Chart (Counts)":
                if chartable_categorical_cols:
                    selected_category_col = st.selectbox(
                        "Select a column for category count:",
                        ["-- Select a column --"] + chartable_categorical_cols,
                        key='billboard_bar_col'
                    )

                    if selected_category_col != "-- Select a column --":
                         st.subheader(f"Count of Billboards by '{selected_category_col.replace('_', ' ').title()}'")

                         count_data = merged_billboard_df[selected_category_col].astype(str).value_counts(dropna=False).reset_index()
                         count_data.columns = [selected_category_col, 'Count']
                         # Filter out 'nan' if it exists
                         count_data = count_data[count_data[selected_category_col].str.lower() != 'nan']


                         if not count_data.empty:
                             if len(count_data) > 20:
                                 st.info(f"Showing top 20 {selected_category_col.replace('_', ' ').title()} values.")
                                 count_data = count_data.head(20)

                             chart = alt.Chart(count_data).mark_bar().encode(
                                 x=alt.X(selected_category_col, sort='-y', axis=alt.Axis(labelAngle=-45), title=selected_category_col.replace('_', ' ').title()),
                                 y=alt.Y('Count', title='Count'),
                                 tooltip=[selected_category_col, 'Count']
                             ).properties(title=f"Count by {selected_category_col.replace('_', ' ').title()}").interactive()

                             st.altair_chart(chart, use_container_width=True)
                         else:
                            st.info(f"No valid data found for column '{selected_category_col.replace('_', ' ').title()}'.")
                else:
                     st.info("No suitable categorical columns found for a bar chart.")


            elif chart_type == "Pie Chart (Counts)":
                if chartable_categorical_cols:
                    selected_category_col = st.selectbox(
                        "Select a column for pie chart:",
                        ["-- Select a column --"] + chartable_categorical_cols,
                        key='billboard_pie_col'
                    )

                    if selected_category_col != "-- Select a column --":
                        st.subheader(f"Pie Chart of Billboards by '{selected_category_col.replace('_', ' ').title()}'")

                        count_data = merged_billboard_df[selected_category_col].astype(str).value_counts(dropna=False).reset_index()
                        count_data.columns = [selected_category_col, 'Count']
                        # Filter out 'nan'
                        count_data = count_data[count_data[selected_category_col].str.lower() != 'nan']


                        if not count_data.empty:
                            # Limit categories if too many for a readable pie chart
                            if len(count_data) > 15:
                                st.info(f"Showing top 15 {selected_category_col.replace('_', ' ').title()} values.")
                                count_data = count_data.head(15)


                            pie_chart = alt.Chart(count_data).mark_arc(outerRadius=120, innerRadius=40).encode( # Added inner/outer radius
                                theta=alt.Theta('Count:Q'),
                                color=alt.Color(selected_category_col, title=selected_category_col.replace('_', ' ').title()),
                                tooltip=[selected_category_col, 'Count']
                            ).properties(title=f"Distribution by {selected_category_col.replace('_', ' ').title()}").interactive()

                            st.altair_chart(pie_chart, use_container_width=True)
                        else:
                             st.info(f"No valid data found for column '{selected_category_col.replace('_', ' ').title()}'.")
                else:
                     st.info("No suitable categorical columns found for a pie chart.")


            elif chart_type == "Distribution (Views/Reach)":
                 # Use preprocessed column names
                 numeric_cols = ['potential_views', 'reach', 'reach_pct']
                 chartable_numeric_cols = [col for col in numeric_cols if col in merged_billboard_df.columns and pd.api.types.is_numeric_dtype(merged_billboard_df[col])]

                 if chartable_numeric_cols:
                     selected_numeric_col = st.selectbox(
                         "Select a numeric column for distribution:",
                         ["-- Select a column --"] + chartable_numeric_cols,
                         key='billboard_numeric_col'
                     )

                     if selected_numeric_col != "-- Select a column --":
                         st.subheader(f"Distribution of '{selected_numeric_col.replace('_', ' ').title()}'")

                         # Create a histogram
                         # Filter out NaNs before plotting histogram
                         distribution_data = merged_billboard_df[selected_numeric_col].dropna()

                         if not distribution_data.empty:
                             # Create a temporary DataFrame for Altair if using a Series directly is problematic
                             distribution_df = pd.DataFrame({selected_numeric_col: distribution_data})
                             chart = alt.Chart(distribution_df).mark_bar().encode(
                                 x=alt.X(selected_numeric_col, bin=True, title=selected_numeric_col.replace('_', ' ').title()),
                                 y=alt.Y('count()', title='Frequency'),
                                 tooltip=[alt.Tooltip(selected_numeric_col, bin=True, title=selected_numeric_col.replace('_', ' ').title()), 'count()']
                             ).properties(title=f"Histogram of {selected_numeric_col.replace('_', ' ').title()}").interactive()
                             st.altair_chart(chart, use_container_width=True)
                         else:
                             st.info(f"No valid numeric data found for column '{selected_numeric_col.replace('_', ' ').title()}' for distribution chart.")
                 else:
                      st.info("No suitable numeric columns found for a distribution chart (requires 'potential_views', 'reach', or 'reach_pct').")


            elif chart_type == "Gauge (Avg. Reach %)":
                # Gauge chart for Reach % (average for all locations)
                # Use preprocessed column name
                reach_pct_col = 'reach_pct'
                if reach_pct_col in merged_billboard_df.columns and pd.api.types.is_numeric_dtype(merged_billboard_df[reach_pct_col]):
                    # Calculate mean, skipping NaNs
                    avg_reach_pct = merged_billboard_df[reach_pct_col].mean(skipna=True)

                    if pd.notna(avg_reach_pct):
                        # Ensure value is within gauge range [0, 100]
                        gauge_value = max(0, min(100, avg_reach_pct))

                        gauge_fig = go.Figure(go.Indicator(
                            mode="gauge+number",
                            value=gauge_value,
                            title={'text': f"Average Reach %"},
                            gauge={'axis': {'range': [0, 100]},
                                   'bar': {'color': "lightgreen"},
                                   'steps': [
                                       {'range': [0, 40], 'color': 'red'},
                                       {'range': [40, 75], 'color': 'orange'},
                                       {'range': [75, 100], 'color': 'green'}
                                   ],
                                   'threshold': {'line': {'color': "red", 'width': 4}, 'thickness': 0.75, 'value': gauge_value}} # Show current value line
                            ),
                            number={'suffix': "%", 'font': {'size': 24}},
                        )
                        # Add a layout to ensure full range is visible and fits column
                        gauge_fig.update_layout(height=300, margin=dict(t=0, b=0, l=0, r=0))


                        st.plotly_chart(gauge_fig, use_container_width=True)
                    else:
                         st.info("Average Reach % could not be calculated from the data.")
                else:
                    st.info("Reach (%) column not found or is not numeric in the merged data.")


        else:
            st.info("Upload and process Billboard CSV files using the file uploader above to see charts.")


# --- Footer ---
st.markdown("---")
st.write("Dashboard created with Streamlit | Data analysis powered by Pandas and Altair/Plotly")
