import streamlit as st
import pandas as pd
import plotly.express as px 
import plotly.graph_objects as go
import plotly.io as pio
pio.templates["jedha"] = go.layout.Template(layout_colorway=["#4B9AC7", "#4BE8E0", "#9DD4F3", "#97FBF6", "#2A7FAF", "#23B1AB", "#0E3449", "#015955"])
pio.templates.default = "jedha"
import numpy as np


### Config
st.set_page_config(
    page_title="Getaround",
    page_icon="🚘 ",
    layout="wide"
)

st.title("🚘 Getaround")

st.markdown("""
Welcome ! This is a dashboard that will help the Getaround's product Management team to take the best decisions 
about the minimum delay between two car rentals.
""")


@st.cache(allow_output_mutation=True)
def load_data(nrows):
    data = pd.read_csv('get_around_delay_analysis.csv')
    data.drop(['Unnamed: 7', 'Unnamed: 8'], axis=1, inplace=True)
    return data


data_load_state = st.text('Loading data...')
data = load_data(1000)
data_load_state.text("") # change text from "Loading data..." to "" once the the load_data function has run

## Run the below code if the check is checked ✅
if st.checkbox('Show raw data'):
    st.subheader('Raw data')
    st.write(data)  


st.header("Let's start with some stats about car rentals")

col1, col2 = st.columns(2)

with col1:
    st.markdown("**Percentage of late rentals per type of checkout**")
    data['late_checkout'] = data['delay_at_checkout_in_minutes'].apply(lambda x: 'late' if x > 0 else 'in time')
    checkout = st.selectbox("Select a type of checkout", ['all', 'mobile', 'connect'], key=1)
    late_df = data if checkout == 'all' else data[data["checkin_type"]==checkout]
    delay_percentage = round(len(late_df[late_df['late_checkout']=='late']) / late_df['late_checkout'].count() * 100)
    st.markdown(f'{delay_percentage}% of the rentals are late with {checkout} type of checkout.')
    fig = go.Figure(data=[go.Pie(labels=late_df['late_checkout'])])
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.markdown("**Percentage of canceled rentals per type of checkout**")
    checkout = st.selectbox("Select a type of checkout", ['all', 'mobile', 'connect'], key=2)
    canceled_df = data if checkout == 'all' else data[data["checkin_type"]==checkout]
    canceled_percentage = round(canceled_df['state'].value_counts()[1] / len(canceled_df) * 100)
    st.markdown(f'{canceled_percentage}% of the rentals are canceled with {checkout} type of checkout.')
    fig = go.Figure(data=[go.Pie(labels=canceled_df['state'])])
    st.plotly_chart(fig, use_container_width=True)

st.header("Let's have a look to the delays repartition")
st.markdown('Outliers values were removed so 1440 means that there is at least one day of delay')
fig = px.histogram(late_df, x='delay_at_checkout_in_minutes', range_x=["0","1450"])
st.plotly_chart(fig, use_container_width=True)

st.header("We can now inspect the timedeltas between two car rentals")
st.markdown("""
Here we display the effective timedeltas between tow rentals, that is to say the planned timedelta minus the previous rental delay
""")
consecutive_df = pd.merge(data, data, how='inner', left_on = 'previous_ended_rental_id', right_on = 'rental_id')
consecutive_df.drop(["delay_at_checkout_in_minutes_x", "rental_id_y", "car_id_y", "state_y", "time_delta_with_previous_rental_in_minutes_y", "previous_ended_rental_id_y","late_checkout_x"], axis=1,inplace=True)
consecutive_df.columns = ['rental_id', 'car_id', 'checkin_type', 'state', 'previous_ended_rental_id', 'time_delta_with_previous_rental_in_minutes', 'previous_checkin_type', 'previous_delay_at_checkout_in_minutes', 'previous_late_checkout']
consecutive_df.dropna(subset=['previous_delay_at_checkout_in_minutes'], inplace=True)
consecutive_df['effective_timedelta'] = consecutive_df['time_delta_with_previous_rental_in_minutes'] - consecutive_df['previous_delay_at_checkout_in_minutes']
fig = px.histogram(consecutive_df, x='effective_timedelta', color='state', range_x=["-1000","2000"])
st.plotly_chart(fig, use_container_width=True)

st.markdown("""---""")

st.title('⏰ Threshold delay calculator')
with st.form("Here you can simulate a minimal delay between two rentals and see how it may impact the cancellations"):
    threshold = st.number_input('Enter a minimal delay between two rentals (in minutes)', min_value=0, max_value=1440, step=1)
    checkout = st.selectbox("Select a type of checkout", ['all', 'mobile', 'connect'], key=3)
    submit = st.form_submit_button("submit")
    if submit:
        canceled_df = consecutive_df[(consecutive_df['effective_timedelta'] <= 0) & (consecutive_df['state']=='canceled')]
        canceled_checkin_df = canceled_df if checkout == 'all' else canceled_df[canceled_df["checkin_type"]==checkout]
        avoided_cancellations = round(len(canceled_checkin_df.query(f'effective_timedelta + {threshold} >= 0')) / len(canceled_df) * 100)
        ended_df = consecutive_df[(consecutive_df['effective_timedelta'] >= 0) & (consecutive_df['state']=='ended')]
        ended_checkin_df = ended_df if checkout == 'all' else ended_df[ended_df["checkin_type"]==checkout]
        lost_rentals = round(len(ended_checkin_df.query(f'effective_timedelta <={threshold}')) / len(ended_df) * 100)
        st.markdown(f"With a minimal delay of {threshold} minutes and {checkout} type of checkout :")
        col1, col2 = st.columns(2)
        col1.metric(label=f"Percentage of cancellations avoided", value=f"{avoided_cancellations} %")
        col2.metric(label=f"Percentage of lost rentals", value=f"{lost_rentals} %")

  
