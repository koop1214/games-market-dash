import dash
import numpy as np
import pandas as pd
import plotly.express as px
from dash import dcc
from dash import html
from dash import dcc
from dash import html
from dash.dependencies import Input, Output

df = pd.read_csv('games.csv', dtype={'Year_of_Release': 'Int64'})
df['User_Score'] = df['User_Score'].str.replace('tbd', 'nan').astype(float)

# сначала создаем индикатор для признаков с пропущенными данными
for col in df.columns:
    missing = df[col].isnull()
    num_missing = np.sum(missing)

    if num_missing > 0:
        df['{}_ismissing'.format(col)] = missing

ismissing_cols = [col for col in df.columns if 'ismissing' in col]
df['num_missing'] = df[ismissing_cols].sum(axis=1)

# отбрасываем строки с большим количеством пропусков
ind_missing = df[df['num_missing'] > 0].index
df = df.drop(ind_missing, axis=0)

# исключить проекты ранее 2000 года
df = df[df['Year_of_Release'] >= 2000]

available_genres = df['Genre'].unique()
available_ratings = df['Rating'].unique()


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

server = app.server

app.layout = html.Div(children=[
    html.H1(children='Games market'),

    html.Div(children='''
        История состояния игровой индустрии. Укажите жанр, возрастной рейтинг, года выпуска.
    ''', className="row"),

    html.Div([
        html.Div([
            html.H6('Жанр'),
            dcc.Dropdown(
                id='genre-filter',
                options=[{'label': i, 'value': i} for i in available_genres],
                multi=True,
                # placeholder="Выберите жанр",
            ),
        ], className='six columns'),
        html.Div([
            html.H6('Возрастной рейтинг'),
            dcc.Dropdown(
                id='rating-filter',
                options=[{'label': i, 'value': i} for i in available_ratings],
                multi=True,
                # placeholder="Выберите возрастной рейтинг",
            )
        ], className='six columns'),
    ], className="row"),

    html.Div([
        html.H6('Число игр: ', id='num-games'),
    ], className="row"),

    html.Div([
        html.Div([
            html.H6('Выпуск игр по годам и платформам'),
            dcc.Graph(
                id='graph-platform'
            ),
        ], className='six columns'),
        html.Div([
            html.H6('Рейтинг по жанрам'),
            dcc.Graph(
                id='graph-rating'
            ),
        ], className='six columns'),
    ], className="row"),

    dcc.RangeSlider(
        id='year-slider',
        min=df['Year_of_Release'].min(),
        max=df['Year_of_Release'].max(),
        value=[df['Year_of_Release'].min(), df['Year_of_Release'].max()],
        marks={str(year): str(year) for year in df['Year_of_Release'].unique()},
        allowCross=False,
        step=None
    )
])


@app.callback(
    Output('num-games', 'children'),
    Output('graph-platform', 'figure'),
    Output('graph-rating', 'figure'),
    Input('genre-filter', 'value'),
    Input('rating-filter', 'value'),
    Input('year-slider', 'value'))
def update_graph(genres, ratings, years):
    filters = []

    if genres:
        filters.append('Genre in @genres')

    if ratings:
        filters.append('Rating in @ratings')

    if years:
        filters.append('Year_of_Release >= @years[0] and Year_of_Release <= @years[1]')

    query = ' and '.join(filters)

    if query:
        dff = df.query(query)
    else:
        dff = df.copy()

    rating_fig = px.scatter(dff, x="User_Score", y="Critic_Score", color="Genre",
                            labels={'User_Score': 'User score', 'Critic_Score': 'Critic score'})
    rating_fig.update_layout(transition_duration=500)

    grouped_df = dff.groupby(['Year_of_Release', 'Platform'], as_index=False).agg({'Name': 'count'}).rename(columns={'Name': 'Count'})
    platform_fig = px.area(grouped_df, x="Year_of_Release", y="Count", color="Platform",
                           labels={'Year_of_Release': 'Year'})
    platform_fig.update_layout(transition_duration=500)

    return 'Число игр: {}'.format(dff.shape[0]), platform_fig, rating_fig


if __name__ == '__main__':
    app.run_server(debug=True)
