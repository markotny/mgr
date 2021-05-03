# :8050

import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
import plotly.express as px
import json
from util_data import load_data, load_session
from util_plots import create_fig_scatter, create_fig_topics, create_fig_topics_over_time
from util_elastic import get_topic_dict, get_full_text, remap_embeddings, search_speeches, search_topics

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

df = load_data()

topics = get_topic_dict()
topic_sizes = df['temat'].value_counts().to_dict()
topics = {key: f'{val} ({topic_sizes[key]})' for key, val in topics.items()}

df['opis tematu'] = [topics[t] for t in df.temat]
topic_options = [{"label": val, "value": key} for key, val in topics.items()]

fig_scatter_default = px.scatter(
    template="simple_white",
    width=900, height=800
)

fig_topics = create_fig_topics()

fig_topics_over_time = create_fig_topics_over_time()

scatter_plot_settings = dbc.Row([
    dbc.Col(dbc.DropdownMenu(
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
            label="Kadencje")),
    dbc.Col(dcc.Dropdown(
            id='graph-scatter-dim',
            options=[
                {'label': '2D', 'value': 2},
                {'label': '3D', 'value': 3}
            ],
            value=2)),
    dbc.Col(dcc.Dropdown(
            id='graph-scatter-coloring',
            options=[
                {'label': 'Temat', 'value': 'temat'},
                {'label': 'Klub', 'value': 'klub'},
                {'label': 'Lista', 'value': 'lista'},
                {'label': 'Województwo', 'value': 'województwo'}
            ],
            value='temat')),
    dbc.Col(dbc.RadioItems(
            id='graph-scatter-remap',
            options=[
                {'label': 'Globalne', 'value': 0},
                {'label': 'Przelicz', 'value': 1}
            ],
            value=0)),
    dbc.Col(dbc.Row([
        dbc.Col(dbc.Label('n:', html_for='graph-scatter-remap-neighbors'),
                style={'paddingRight': '0', 'textAlign': 'right'}),
        dbc.Col(dcc.Input(id='graph-scatter-remap-neighbors', type='number', disabled=True,
                          value=10, min=5, max=100, step=5, style={'width': '100%'}))])),
    dbc.Col(dbc.Button("Zastosuj", id='apply-graph-scatter-filter', color="primary", className='ml-auto'), className='d-flex')],
    style={'height': '50px'},
    justify="between",
    align="center",
)
speech_search = dbc.Row([
    dbc.Col(dcc.Input(id="speech-search", type="text", value='',
                      placeholder='Filtruj wypowiedzi', style={'width': '100%'}), width=8),
    dbc.Col(dbc.Label('Próg:', html_for='speech-search-threshold'),
            style={'paddingRight': '0', 'textAlign': 'right'}),
    dbc.Col(dcc.Input(id='speech-search-threshold', type='number',
            value=0.5, min=0.1, max=0.99, step=0.05, style={'width': '100%'})),
    dbc.Col(dbc.Button("Szukaj", id='speech-search-btn',
            color="primary", className='ml-auto'), className='d-flex'),
    dcc.Store(id="speech-search-ids")],
    style={'height': '50px'},
    justify="between",
    align="center",
)

tab1_content = dbc.Card(
    dbc.CardBody([dbc.Row([
        dbc.Col([
            speech_search,
            scatter_plot_settings,
            dcc.Store(id="graph-filter-data"),
            dcc.Loading(html.Div(id="speech-search-result",
                style={'textAlign': 'right', 'height': '50px'})),
            dbc.Row(dcc.Graph(id='graph-scatter', figure=fig_scatter_default))], width=6),
        dbc.Col([
            dcc.Input(id="topic-search", type="text", value='',
                      placeholder='Filtruj tematy', style={'width': '100%'}),
            dcc.Loading(dcc.Dropdown(id="topic-select", value=[],
                        options=topic_options, placeholder='Wybierz tematy', multi=True)),
            dcc.Graph(id='graph-topics', figure=fig_topics)], width=6)
    ]),
        # dbc.Row(html.Div([
        #     dcc.Markdown("""
        #     **Click Data**

        #     Click on points in the graph.
        #     """),
        #     html.Pre(id='click-data')]))
    ]),
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


def apply_filter(speechIds, topicIds, kads):
    filtered_df = df[df['kadencja'].isin(kads)]
    if speechIds is not None and len(speechIds) > 0:
        filtered_df = filtered_df[filtered_df['id'].isin(speechIds)]

    if isinstance(topicIds, str):
        topicIds = [topicIds]
    if topicIds is not None and len(topicIds) > 0:
        filtered_df = filtered_df[filtered_df['temat'].isin(topicIds)]

    return filtered_df


@ app.callback(
    [Output('speech-search-result', 'children'),
     Output('graph-scatter', 'figure'),
     Output('graph-filter-data', 'data')],
    Input('apply-graph-scatter-filter', 'n_clicks'),
    [State('speech-search-ids', 'data'),
     State("topic-select", "value"),
     State('graph-scatter-remap', 'value'),
     State('graph-scatter-remap-neighbors', 'value'),
     State('graph-scatter-kads', 'value'),
     State('graph-scatter-dim', 'value'),
     State('graph-scatter-coloring', 'value')])
def update_scatter_fig(n, speechIds, topicIds, remap, map_neighbors, kads, dim, coloring):
    if n is None or n < 0:
        raise PreventUpdate

    filter_data = dict(speechIds=speechIds, topicIds=topicIds, kads=kads)
    filtered_df = apply_filter(speechIds, topicIds, kads)

    if len(filtered_df) == 0:
        return 'Nie znaleziono żadnych pasujących wypowiedzi', fig_scatter_default, filter_data

    if remap == 1:
        filtered_df = remap_embeddings(filtered_df, dim, map_neighbors)

    fig = create_fig_scatter(filtered_df, dim, coloring)

    return f'Wypowiedzi na wykresie: {len(filtered_df)}', fig, filter_data


@ app.callback(
    [Output('speech-search-result', 'children'),
     Output('speech-search-ids', 'data')],
    [Input('speech-search', 'n_submit'),
     Input('speech-search-btn', 'n_clicks')],
    [State('speech-search', 'value'),
     State('speech-search-threshold', 'value'),
     State('graph-filter-data', 'data')],
    prevent_initial_call=True)
def update_speeches(n_sub, n_clk, value, threshold, filter_data):
    if value is None or len(value) < 1:
        return '', []
    matched_speeches = search_speeches(value, threshold)

    ids = [s['_id'] for s in matched_speeches]

    if filter_data is not None:
        filtered_df = apply_filter(
            ids, filter_data['topicIds'], filter_data['kads'])
        return f'Znaleziono: {len(ids)}. Z filtrami: {len(filtered_df)}', ids

    return f'Znaleziono: {len(ids)}', ids


@ app.callback(
    [Output('graph-topics', 'figure'),
     Output("topic-select", "options"), Output("topic-select", "value")],
    Input("topic-search", "n_submit"),
    [State("topic-search", "value"), State('graph-topics', 'figure')],
    prevent_initial_call=True)
def update_topics(n, value, figure):
    if value is None or len(value) < 1:
        return fig_topics, topic_options, []

    matched_topics = search_topics(value)

    options = [{"label": '{:.2f}: {}'.format(t['_score']-1.0, topics[t['_id']]),
                "value": t['_id']} for t in matched_topics]

    topic_ids = [t['_id'] for t in matched_topics]
    figure['data'][0]['marker']['opacity'] = [
        0.5 if t in topic_ids else 0.1 for t in topics.keys() if t != '-1']
    return figure, options, []


@ app.callback(
    Output('topic-select', 'value'),
    [Input("graph-topics", "clickData"),
     Input('graph-topics', 'selectedData')],
    State('topic-select', 'options'),
    prevent_initial_call=True)
def update_selected_topic(clickData, selectionData, options):
    ctx = dash.callback_context
    if ctx.triggered is None or ctx.triggered[0]['value'] is None:
        raise PreventUpdate

    valid_ids = [opt['value'] for opt in options]

    if ctx.triggered[0]['prop_id'] == 'graph-topics.clickData':
        topic_index = str(clickData['points'][0]['pointIndex'])
        if topic_index not in valid_ids:
            raise PreventUpdate
        return str(topic_index)
    else:
        topic_indexes = [str(point['pointIndex'])
                         for point in selectionData['points']]
        topic_indexes = [t for t in topic_indexes if t in valid_ids]
        if len(topic_indexes) < 1:
            raise PreventUpdate
        return topic_indexes


@ app.callback(
    [Output("tabs", "active_tab"),
     Output('tab-selected', 'disabled'),
     Output('selected-doc-id', 'data'),
     Output('selected-doc', 'children')],
    Input("graph-scatter", "clickData"),
    prevent_initial_call=True)
def on_doc_selected(clickData):
    if clickData is None:
        raise PreventUpdate

    doc_id = clickData['points'][0]['customdata'][-1]
    doc = df[df.id == doc_id].squeeze()

    children = [dbc.Row([
        dbc.Col(dbc.Label(item[0]), width=2), dbc.Col(html.Span(item[1]))
    ]) for item in doc[['id', 'mówca', 'data', 'klub', 'lista', 'partia', 'opis']].items()]

    return 'tab-selected', False, doc_id, children


@ app.callback(
    Output('graph-scatter-remap-neighbors', 'disabled'),
    Input('graph-scatter-remap', 'value'))
def enable_remap_input(value):
    return value == 0


@ app.callback(
    Output('selected-doc-fullText', 'children'),
    Input('selected-doc-id', 'data'),
    prevent_initial_call=True)
def load_doc_text(doc_id):
    if doc_id is not None:
        return get_full_text(doc_id)
    else:
        return 'Nie wybrano dokumentu'


@ app.callback(
    [Output('tab-session-content', 'children'),
     Output('scrollto-div-id', 'data')],
    Input('show-session', 'n_clicks'),
    State('selected-doc-id', 'data'),
    prevent_initial_call=True)
def load_session_tab(_, doc_id):
    if doc_id is None:
        raise PreventUpdate

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
    [Output("tabs", "active_tab"), Output('tab-session', 'disabled')],
    Input('show-session', 'n_clicks'),
    prevent_initial_call=True)
def switch_to_session_tab(n):
    if n is not None and n > 0:
        return 'tab-session', False

    raise PreventUpdate


app.clientside_callback(
    """
    function(id, _) {
        if (id) {
            let element = document.getElementById(id);
            element.scrollIntoView({behavior:'smooth'});
        }
        return id;
    }
    """,
    Output('scrollto-div-id', 'children'),
    [Input('scrollto-div-id', 'data'),
     Input('scrollto-button', 'n_clicks')],
    prevent_initial_call=True
)

app.clientside_callback(
    """
    function(data) {
        console.log(data)
        return 'ok';
    }
    """,
    Output('graph-filter-data', 'children'),
    Input('graph-filter-data', 'data'),
    prevent_initial_call=True
)

if __name__ == '__main__':
    app.run_server(debug=True)
