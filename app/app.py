# :8050

import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
import plotly.express as px
import json
from data_util import load_data, load_session
from plots_util import create_fig_scatter, create_fig_topics, create_fig_topics_over_time
from elastic_util import get_embeddings, get_full_text, remap_embeddings

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

df = load_data()

fig_topics = create_fig_topics()

fig_topics_over_time = create_fig_topics_over_time()

scatter_plot_settings = dbc.Row(
    [
        dbc.Col(
            dbc.DropdownMenu(
                dcc.Checklist(
                    id='graph-scatter-kads',
                    options=[
                        {'label': 'I (1991-1993)', 'value': 1},
                        {'label': 'II (1993-1997)', 'value': 2},
                        {'label': 'III (1997-2001)', 'value': 3},
                        {'label': 'IV (2001-2005)', 'value': 4},
                        {'label': 'V (2005-2007)', 'value': 5},
                        {'label': 'VI (2007-2011)', 'value': 6},
                        {'label': 'VII (2011-2015)', 'value': 7},
                        {'label': 'VIII (2015-2019)', 'value': 8},
                    ],
                    value=[1, 2, 3, 4, 5, 6, 7, 8]
                ),
                label="Kadencje",
            )
        ),
        dbc.Col(
            dcc.Dropdown(
                id='graph-scatter-dim',
                options=[
                    {'label': '2D', 'value': 2},
                    {'label': '3D', 'value': 3}
                ],
                value=2
            )
        ),
        dbc.Col(
            dcc.Dropdown(
                id='graph-scatter-coloring',
                options=[
                    {'label': 'Temat', 'value': 'temat_str'},
                    {'label': 'Klub', 'value': 'klub'},
                    {'label': 'Lista', 'value': 'lista'},
                    {'label': 'Okręg', 'value': 'okręg'}
                ],
                value='temat_str'
            )
        ),
        dbc.Col(
            dcc.RadioItems(
                id='graph-scatter-remap',
                options=[
                    {'label': 'Globalne', 'value': 0},
                    {'label': 'Przelicz', 'value': 1}
                ],
                value=0
            )
        ),
        dbc.Button("Zastosuj", id='apply-graph-scatter-filter', color="primary")
    ],
    justify="between",
)

tab1_content = dbc.Card(
    dbc.CardBody(
        [
            dbc.Row(
                [
                    dbc.Col([
                        scatter_plot_settings,
                        html.Div(id='selected-topics',
                                 style={'white-space': 'pre-line'}),
                        dcc.Store(id='selected-topics-ids'),
                        dcc.Loading(dcc.Graph(id='graph-scatter'))
                    ]),
                    dbc.Col(dcc.Graph(
                        id='graph-topics',
                        figure=fig_topics
                    ))
                ]
            ),
            # dbc.Row(html.Div([
            #     dcc.Markdown("""
            #     **Click Data**

            #     Click on points in the graph.
            #     """),
            #     html.Pre(id='click-data')]))
        ]
    ),
    className="mt-3",
)

tab2_content = dbc.Card(
    dbc.CardBody(
        [
            dcc.Graph(
                id='graph-topics-over-time',
                figure=fig_topics_over_time
            )
        ]
    ),
    className="mt-3",
)

tab3_content = dbc.Card(
    dbc.CardBody(
        [
            dcc.Store(id='selected-doc-id'),
            dbc.Row(dbc.Col(id='selected-doc')),
            dbc.Button("Pokaż kontekst", id='show-session',
                       style={'position': 'absolute', 'right': '20px', 'top': '20px'}),
            dbc.Row([
                dbc.Col(dbc.Label('treść'), width=2),
                dbc.Col(dcc.Loading(html.Div(id='selected-doc-fullText')))
            ])
        ]
    ),
    className="mt-3",
)

tab4_content = dbc.Card([
    dcc.Store(id='scrollto-div-id'),
    dcc.Loading(dbc.CardBody(dbc.Col([
        dbc.Row(dbc.Button('Pokaż wybraną wypowiedź',
                id='scrollto-button', color='primary')),
        dbc.Row(dbc.Col(id='tab-session-content'))])))],
    className="mt-3",
)

app.layout = dbc.Container(
    dbc.Tabs(
        [
            dbc.Tab(tab1_content, label="Tematy", tab_id='tab-main'),
            dbc.Tab(tab2_content, label="Tematy w czasie", tab_id='tab-time'),
            dbc.Tab(tab3_content, label="Wybrana wypowiedź",
                    disabled=True, id='tab-selected', tab_id='tab-selected'),
            dbc.Tab(tab4_content, label="Kontekst wypowiedzi",
                    disabled=True, id='tab-session', tab_id='tab-session')
        ],
        id='tabs',
        active_tab='tab-main'
    ),
    fluid=True
)


@app.callback(
    Output('graph-scatter', 'figure'),
    [Input('apply-graph-scatter-filter', 'n_clicks'),
     Input("selected-topics-ids", "data")],
    [State('graph-scatter-remap', 'value'),
     State('graph-scatter-kads', 'value'),
     State('graph-scatter-dim', 'value'),
     State('graph-scatter-coloring', 'value')])
def update_scatter_fig(_, topicIds, remap, kads, dim, coloring):
    filtered_df = df[df['kadencja'].isin(kads)]
    opacity = 0.1
    if topicIds is not None and len(topicIds) > 0:
        filtered_df = filtered_df[filtered_df['temat'].isin(topicIds)]
        opacity = 1.0
        if remap == 1:
            filtered_df = remap_embeddings(filtered_df, dim)

    fig = create_fig_scatter(filtered_df, dim, coloring, opacity)

    return fig


@app.callback(
    [Output('selected-topics', 'children'),
     Output('selected-topics-ids', 'data')],
    [Input("graph-topics", "clickData"), Input('graph-topics', 'selectedData')])
def update_selected_topic(clickData, selectionData):
    ctx = dash.callback_context
    if ctx.triggered is None or ctx.triggered[0]['value'] is None:
        return 'Aby wybrać temat klinkij na prawym wykresie', []

    if ctx.triggered[0]['prop_id'] == 'graph-topics.clickData':
        topic_index = clickData['points'][0]['pointIndex']
        topic_words = clickData['points'][0]['customdata'][3]
        return f'Wybrany temat: {topic_index} - {topic_words}', [topic_index]
    else:
        topic_indexes = [point['pointIndex']
                         for point in selectionData['points']]
        topics = ',\n'.join(
            [f"{point['pointIndex']} - {point['customdata'][3]}" for point in selectionData['points']])
        return f'Wybrane tematy: {topics}', topic_indexes


@app.callback(
    [Output("tabs", "active_tab"),
     Output('tab-selected', 'disabled'),
     Output('selected-doc-id', 'data'),
     Output('selected-doc', 'children')],
    Input("graph-scatter", "clickData"))
def on_doc_selected(clickData):
    if clickData is None:
        return 'tab-main', True, *(None,)*2

    doc_id = clickData['points'][0]['customdata'][-1]
    doc = df[df.id == doc_id].squeeze()

    children = [dbc.Row([
        dbc.Col(dbc.Label(item[0]), width=2), dbc.Col(html.Span(item[1]))
    ]) for item in doc[['id', 'mówca', 'data', 'klub', 'lista', 'partia', 'opis']].items()]

    return 'tab-selected', False, doc_id, children


@app.callback(
    Output('selected-doc-fullText', 'children'),
    Input('selected-doc-id', 'data'))
def load_doc_text(doc_id):
    if doc_id is not None:
        return get_full_text(doc_id)
    else:
        return 'Nie wybrano dokumentu'


@app.callback(
    [Output('tab-session-content', 'children'),
     Output('scrollto-div-id', 'data')],
    Input('show-session', 'n_clicks'),
    State('selected-doc-id', 'data'))
def load_session_tab(_, doc_id):
    if doc_id is None:
        return None, None

    title, texts, speech_id = load_session(doc_id)

    speech_number = next(i for i, t in enumerate(texts)
                         if t['id'] == speech_id)

    children = [
        dbc.Row(html.H2(title, style={'margin': '20px 0'})),
        * [dbc.Row([
            dbc.Col(html.H4(t['id'][4:]), width=1,
                    style={'textAlign': 'right'}),
            dbc.Col([dbc.Row([
                dbc.Col(s['speaker'], width=2),
                dbc.Col(s['text'])], style={'borderBottom': '1px solid grey'}) for s in t['speeches']])
        ], id=t['id'], style={'border': '1px solid red'} if t['id'] == speech_id else None)
            for i, t in enumerate(texts) if abs(i - speech_number) <= 20]
    ]
    return children, speech_id


@app.callback(
    Output("tabs", "active_tab"),
    Input('show-session', 'n_clicks'))
def switch_to_session_tab(n):
    if n == 0:
        return 'tab-main'

    return 'tab-session'


app.clientside_callback(
    """
    function  scrollto(id, _) {
        if (id) {
            let element = document.getElementById(id);
            element.scrollIntoView({behavior:'smooth'});
        }
        return id;
    }
    """,
    Output('scrollto-div-id', 'children'),
    [Input('scrollto-div-id', 'data'),
     Input('scrollto-button', 'n_clicks')]
)

# @app.callback(
#     Output('click-data','children'),
#     Input('graph-topics','clickData'))
# def onClick(clickData):
#     return json.dumps(clickData, indent=2)


if __name__ == '__main__':
    app.run_server(debug=True)
