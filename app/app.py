# :8050

import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
import plotly.express as px
import json
from data_util import load_data, load_topics
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
            dbc.Row([
                dbc.Col(dbc.Label('Mówca'), width=2),
                dbc.Col(html.Span(id='selected-doc-speaker'))
            ]),
            dbc.Row([
                dbc.Col(dbc.Label('Data'), width=2),
                dbc.Col(html.Span(id='selected-doc-date'))
            ]),
            dbc.Row([
                dbc.Col(dbc.Label('Klub'), width=2),
                dbc.Col(html.Span(id='selected-doc-klub'))
            ]),
            dbc.Row([
                dbc.Col(dbc.Label('Lista'), width=2),
                dbc.Col(html.Span(id='selected-doc-lista'))
            ]),
            dbc.Row([
                dbc.Col(dbc.Label('Partia'), width=2),
                dbc.Col(html.Span(id='selected-doc-partia'))
            ]),
            dbc.Row([
                dbc.Col(dbc.Label('Opis'), width=2),
                dbc.Col(html.Span(id='selected-doc-desc'))
            ]),
            dbc.Row([
                dbc.Col(dbc.Label('Treść'), width=2),
                dbc.Col(dcc.Loading(html.Div(id='selected-doc-fullText')))
            ])
        ]
    ),
    className="mt-3",
)

app.layout = dbc.Container(
    dbc.Tabs(
        [
            dbc.Tab(tab1_content, label="Tematy", tab_id='tab-main'),
            dbc.Tab(tab2_content, label="Tematy w czasie", tab_id='tab-time'),
            dbc.Tab(tab3_content, label="Wybrana wypowiedź",
                    disabled=True, id='tab-selected', tab_id='tab-selected')
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
    [Output("tabs", "active_tab"), Output('tab-selected', 'disabled'),
     Output('selected-doc-id', 'data'),
     Output('selected-doc-speaker', 'children'),
     Output('selected-doc-date', 'children'),
     Output('selected-doc-klub', 'children'),
     Output('selected-doc-lista', 'children'),
     Output('selected-doc-partia', 'children'),
     Output('selected-doc-desc', 'children')],
    Input("graph-scatter", "clickData"))
def on_doc_selected(clickData):
    if clickData is None:
        return 'tab-main', True, *(None,)*7

    doc_id = clickData['points'][0]['customdata'][-1]
    doc = df[df.id == doc_id].squeeze()
    doc = tuple(
        doc[['id', 'mówca', 'data', 'klub', 'lista', 'partia', 'opis']].tolist())

    return 'tab-selected', False, *doc


@app.callback(
    Output('selected-doc-fullText', 'children'),
    Input('selected-doc-id', 'data'))
def load_doc_text(doc_id):
    if doc_id is not None:
        return get_full_text(doc_id)
    else:
        return 'Nie wybrano dokumentu'

# @app.callback(
#     Output('click-data','children'),
#     Input('graph-topics','clickData'))
# def onClick(clickData):
#     return json.dumps(clickData, indent=2)


if __name__ == '__main__':
    app.run_server(debug=True)
