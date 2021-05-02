import plotly.express as px
from data_util import load_plot_topics, load_plot_topics_over_time

hover_data={'temat_str': False, 'mówca': True, 'temat': True, 'opis tematu': True, 'rozmiar tematu': True, 'id': True}

def create_fig_scatter(df, dim=2, color_category='temat_str', opacity=0.1):
    if dim == 2:
        fig = px.scatter(
            df, x='2x', y='2y',
            hover_name='opis',
            color=color_category,
            color_discrete_map={'-1': 'rgba(0,0,0, 0.01)'},
            hover_data={
                '2x': False, '2y': False, **hover_data
            },
            width=900, height=900
        )
        marker_sizes = [2, 5, 10]
    else:
        fig = px.scatter_3d(
            df, x='3x', y='3y', z='3z',
            hover_name='opis',
            color=color_category,
            color_discrete_map={'-1': 'rgba(0,0,0, 0.01)'},
            hover_data={
                '3x': False, '3y': False, '3z': False, **hover_data
            },
            width=900, height=900
        )
        marker_sizes = [1, 2, 3]
    fig.update_traces(marker_size=marker_sizes[0], marker_opacity=opacity)
    fig.update_layout(
        showlegend=False,
        updatemenus=[
            dict(
                type="buttons",
                direction="left",
                buttons=list([
                    dict(
                        args=["marker.size", marker_sizes[0]],
                        label="Small",
                        method="restyle"
                    ),
                    dict(
                        args=["marker.size", marker_sizes[1]],
                        label="Medium",
                        method="restyle"
                    ),
                    dict(
                        args=["marker.size", marker_sizes[2]],
                        label="Large",
                        method="restyle"
                    )
                ]),
                pad={"r": 10, "t": 10},
                showactive=True,
                x=0.11,
                xanchor="left",
                y=1.1,
                yanchor="top"
            ),
        ]
    )
    fig.update_xaxes(visible=False, showticklabels=False)
    fig.update_yaxes(visible=False, showticklabels=False)

    return fig

def create_fig_topics():
    fig = load_plot_topics()
    fig.update_layout(width=900, height=900)
    return fig

def create_fig_topics_over_time():
    fig = load_plot_topics_over_time()
    fig.update_layout(width=1800, height=900)
    return fig