import bokeh.plotting as bpl
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors
from bokeh.models import CustomJS, TextInput
from bokeh.layouts import column

def _to_hex(arr):
    return [matplotlib.colors.to_hex(c) for c in arr]
    
def plot_bokeh(
    points,
    labels=None,
    hover_data=None,
    width=800,
    height=800,
    color_key_cmap="Spectral",
    point_size=None,
    alpha=None,
    interactive_text_search=False,
):
    data = pd.DataFrame(points, columns=("x", "y"))

    data["label"] = labels

    unique_labels = np.unique(labels)
    num_labels = unique_labels.shape[0]
    color_key = _to_hex(
        plt.get_cmap(color_key_cmap)(np.linspace(0, 1, num_labels))
    )

    if isinstance(color_key, dict):
        data["color"] = pd.Series(labels).map(color_key)
    else:
        unique_labels = np.unique(labels)
        if len(color_key) < unique_labels.shape[0]:
            raise ValueError(
                "Color key must have enough colors for the number of labels"
            )

        new_color_key = {k: color_key[i] for i, k in enumerate(unique_labels)}
        data["color"] = pd.Series(labels).map(new_color_key)

    colors = "color"

    if hover_data is not None:
        tooltip_dict = {}
        for col_name in hover_data:
            data[col_name] = hover_data[col_name]
            tooltip_dict[col_name] = "@{" + col_name + "}"
        tooltips = list(tooltip_dict.items())
    else:
        tooltips = None

    if alpha is not None:
        data["alpha"] = alpha
    else:
        data["alpha"] = 1

    data_source = bpl.ColumnDataSource(data)

    plot = bpl.figure(
        width=width,
        height=height,
        tooltips=tooltips
    )
    plot.circle(
        x="x",
        y="y",
        source=data_source,
        color=colors,
        size=point_size,
        alpha="alpha",
        legend_field='label'
    )

    plot.grid.visible = False
    plot.axis.visible = False

    if interactive_text_search:
        text_input = TextInput(value="", title="Search:")

        interactive_text_search_columns = []
        if hover_data is not None:
            interactive_text_search_columns.extend(hover_data.columns)
        if labels is not None:
            interactive_text_search_columns.append("label")

        callback = CustomJS(
            args=dict(
                source=data_source,
                matching_alpha=0.95,
                non_matching_alpha=1 - 0.95,
                search_columns=interactive_text_search_columns,
            ),
            code="""
            var data = source.data;
            var text_search = cb_obj.value;
            
            var search_columns_dict = {}
            for (var col in search_columns){
                search_columns_dict[col] = search_columns[col]
            }
            
            // Loop over columns and values
            // If there is no match for any column for a given row, change the alpha value
            var string_match = false;
            for (var i = 0; i < data.x.length; i++) {
                string_match = false
                for (var j in search_columns_dict) {
                    if (String(data[search_columns_dict[j]][i]).includes(text_search) ) {
                        string_match = true
                    }
                }
                if (string_match){
                    data['alpha'][i] = matching_alpha
                }else{
                    data['alpha'][i] = non_matching_alpha
                }
            }
            source.change.emit();
        """,
        )

        text_input.js_on_change("value", callback)

        plot = column(text_input, plot)

    return plot