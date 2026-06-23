import streamlit as st
import pandas as pd
import streamlit.components.v1 as components
import geopandas as gpd
from shapely import wkt
import folium
from streamlit_folium import st_folium

st.set_page_config('IO', layout="wide")

CLARITY_ID = "xbciepc0n0"
components.html(
    f"""
    <script type="text/javascript">
        (function(c,l,a,r,i,t,y){{
            c[a]=c[a]||function(){{(c[a].q=c[a].q||[]).push(arguments)}};
            t=l.createElement(r);t.async=1;t.src="https://www.clarity.ms/tag/"+i;
            y=l.getElementsByTagName(r)[0];y.parentNode.insertBefore(t,y);
        }})(window, document, "clarity", "script", "{CLARITY_ID}");
    </script>
    """,
    height=0,
)

st.title("InvestOttawa Real Estate V1.5")
st.header('This tool serves as a decision-making aid and does not replace on-site analysis or advice from a real estate expert.')

df = pd.read_csv('data.csv')

if 'map_data' not in st.session_state:
    st.session_state.map_data = None

def style_function(feature):
    score = feature["properties"]["Cash_Flow"]
    color = "green" if score >= 0 else "red"
    return {
        "fillColor": color,
        "color": "black",
        "weight": 1,
        "fillOpacity": 0.7
    }

bar = st.sidebar.selectbox('Options', ['Cash_flow', 'HELP'])

if bar == 'Cash_flow':
    with st.columns(2)[0]:
        st.markdown("**Funding**")
        budget = st.number_input("Enter your Budget")
        apport = st.number_input("Enter your personal contribution")
        interest_rate = st.number_input("Enter the annual interest rate of your loan") / 100
        year = st.number_input("What is the duration of the loan (must be in years)")

    with st.columns(2)[1]:
        st.markdown("**Incomes & Charges**")
        rent = st.number_input("Monthly rent expected")
        Monthly_charges = st.number_input("Monthly charges (insurance, Maintenance)")

    if st.button('find the best wards 🚀'):

        df['vacancy'] = df['Vacancy_Rate'] / 100
        loan = budget - apport
        Monthly_rate = interest_rate / 12
        nb_month = year * 12

        if Monthly_rate > 0:
            Monthly_payment = loan * (Monthly_rate * (1 + Monthly_rate) ** nb_month) / ((1 + Monthly_rate) ** nb_month - 1)
        else:
            Monthly_payment = loan / nb_month if nb_month > 0 else 0

        df['Cash_Flow'] = (rent * (1 - df['vacancy'])) - (Monthly_payment + Monthly_charges)

        df['Geometry'] = df['Geometry'].apply(wkt.loads)
        gdf = gpd.GeoDataFrame(df, geometry='Geometry')
        gdf = gdf.set_crs(epsg=4326)

        st.session_state.map_data = gdf

    if st.session_state.map_data is not None:
        m = folium.Map(location=[45.42, -75.69], zoom_start=9)

        folium.GeoJson(
            st.session_state.map_data,
            tooltip=folium.GeoJsonTooltip(fields=['Name', 'Vacancy_Rate', 'Cash_Flow']),
            style_function=style_function
        ).add_to(m)

        st_folium(m, width=800, height=500)

elif bar == 'HELP':
    with st.container():
        st.markdown('* **Cash Flow = Net Rental Income - Total Expenses***')
        st.markdown('*The Net Rental Income is obtained through the formula: Monthly_rent × (1 - Vacancy_rate)*')
        st.markdown('*By accounting for the vacancy rate, we ensure your projections remain realistic rather than optimistic. Your monthly outflow consists of two primary components:*')
        st.markdown('- *Monthly Mortgage Payment: Calculated using your loan amount, interest rate, and term length.*')
        st.markdown('- *Operating Charges: These include recurring costs such as property insurance, maintenance fees, and other fixed charges.*')
        st.markdown('*I used both 2025 and 2026 data from open Ottawa and CMHC*')
    with st.container():
        st.markdown('***Tip:** If your cash flow is negative, you should increase your personal contribution or the rent, or consider decreasing your expenses.*')

