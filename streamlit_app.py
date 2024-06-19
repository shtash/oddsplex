import streamlit as st
import numpy as np
import pandas as pd
import altair as alt
import google_drive as gd
import subprocess
import streamlit_authenticator as stauth
import hmac

def check_password():
    """Returns `True` if the user had the correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if hmac.compare_digest(st.session_state["password"], st.secrets["password"]):
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Don't store the password.
        else:
            st.session_state["password_correct"] = False

    # Return True if the password is validated.
    if st.session_state.get("password_correct", False):
        return True

    # Show input for password.
    st.text_input(
        "Password", type="password", on_change=password_entered, key="password"
    )
    if "password_correct" in st.session_state:
        st.error("😕 Password incorrect")
    return False

def logout():
    """Logs out the user by clearing the session state."""
    for key in st.session_state.keys():
        del st.session_state[key]
    st.experimental_rerun()

if not check_password():
    st.stop()  # Do not continue if check_password is not True.

# Layout with columns to place the logout button on the top right
col1, col2, col3 = st.columns([1, 6, 1])
with col1:
    st.write("")
with col2:
    st.write("")
with col3:
    if st.button("Logout"):
        logout()


# Load data
df = pd.read_csv('data/movies_genres_summary.csv')
df.year = df.year.astype('int')

# Input widgets
## Genres selection
genres_list = df.genre.unique()
genres_selection = st.multiselect('Select sports', genres_list, ['Action', 'Adventure', 'Biography', 'Comedy', 'Drama', 'Horror'])

## Year selection
year_list = df.year.unique()
year_selection = st.slider('Select year duration', 1986, 2006, (2000, 2016))
year_selection_list = list(np.arange(year_selection[0], year_selection[1]+1))

df_selection = df[df.genre.isin(genres_selection) & df['year'].isin(year_selection_list)]
reshaped_df = df_selection.pivot_table(index='year', columns='genre', values='gross', aggfunc='sum', fill_value=0)
reshaped_df = reshaped_df.sort_values(by='year', ascending=False)


# Display DataFrame
df_editor = st.data_editor(reshaped_df, height=212, use_container_width=True,
                            column_config={"year": st.column_config.TextColumn("Year")},
                            num_rows="dynamic")
df_chart = pd.melt(df_editor.reset_index(), id_vars='year', var_name='genre', value_name='gross')

# Display chart
chart = alt.Chart(df_chart).mark_line().encode(
            x=alt.X('year:N', title='Year'),
            y=alt.Y('gross:Q', title='Gross earnings ($)'),
            color='genre:N'
            ).properties(height=320)
st.altair_chart(chart, use_container_width=True)


# Display another sample table with some random data
st.subheader('Sample table')
sample_data = pd.DataFrame(np.random.randn(10, 5), columns=list('ABCDE'))

# Create three columns
col1, col2, col3 = st.columns([1,2,1])  # The middle column is twice as wide as the side columns

# Display the dataframe in the middle column
with col2:
    st.dataframe(sample_data)

gd.main()

def run_script():
    result = subprocess.run(['python', 'scrape_oddstrader.py'], capture_output=True, text=True)
    st.write(result.stdout)
    st.write(result.stderr)

st.title("Run External Script")

if st.button('Run Script'):
    run_script()