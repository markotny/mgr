import plotly.express as px
import numpy as np
from util_data import load_plot_topics, load_plot_topics_over_time

hover_data = {'mówca': True, 'temat': True, 'opis tematu': True, 'id': True}
hide_axis=dict(showticklabels=False)
labels={
        "2x": "D1",
        "2y": "D2",
        "3x": "D1",
        "3y": "D2",
        "3z": "D3"
    }
def create_fig_scatter(df, dim=2, color_category='temat'):
    if dim == 2:
        fig = px.scatter(
            df, x='2x', y='2y',
            hover_name='opis',
            color=color_category,
            color_discrete_map={'-1': 'rgba(0,0,0, 0.1)'},
            hover_data={
                '2x': False, '2y': False, **hover_data
            },
            template="simple_white",
            labels=labels,
            width=900, height=900
        )
        fig.update_xaxes(**hide_axis)
        fig.update_yaxes(**hide_axis)
    else:
        fig = px.scatter_3d(
            df, x='3x', y='3y', z='3z',
            hover_name='opis',
            color=color_category,
            color_discrete_map={'-1': 'rgba(0,0,0, 0.1)'},
            hover_data={
                '3x': False, '3y': False, '3z': False, **hover_data
            },
            template="simple_white",
            labels=labels,
            width=900, height=900
        )
        fig.update_layout(
            scene=dict(
                xaxis=hide_axis,
                yaxis=hide_axis,
                zaxis=hide_axis,
            )
        )
    fig.update_traces(marker_size=2, marker_opacity=0.5)
    fig.update_layout(
        showlegend=False,
        sliders=[
            dict(
                active=1,
                currentvalue={"prefix": "Rozmiar: "},
                steps=[dict(args=["marker.size", x], label=x,
                            method="restyle") for x in range(1, 11)]
            ),
            dict(
                active=4,
                currentvalue={"prefix": "Alfa: "},
                steps=[dict(args=["marker.opacity", x], label="%.1f" %
                            x, method="restyle") for x in np.arange(0.1, 1.1, 0.1)],
                pad={'t': 100}
            )
        ]
    )

    return fig


def create_fig_topics():
    fig = load_plot_topics()
    fig.update_layout(width=900, height=900, title=None)
    fig['layout']['sliders'] = []
    return fig


def create_fig_topics_over_time():
    fig = load_plot_topics_over_time()
    fig.update_layout(width=1800, height=900)
    return fig
