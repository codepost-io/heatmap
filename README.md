# codePost Heatmap

This project helps produce heatmap visualization based on the rubric annotation of
codePost assignment, using the codePost API.

## Dependencies

This library requires seaborn (and thus matplotlib) to draw the actual heatmaps.

## Example

See [example.ipynb](a real example).

## Testing

```python
>>> import heatmap
>>> hmd = heatmap.preprocess.HeatmapData(assignment_id=100)
>>> hmd._c_get_total
531
```

## Plotting a heatmap

```python
>>> import heatmap
>>> hmd100 = heatmap.preprocess.HeatmapData(assignment_id=100)
>>> heatmap100 = heatmap.draw.build_heatmap(
        hmd100,
        x=heatmap.draw.HeatmapXAxis.GRADERS,
        y=heatmap.draw.HeatmapYAxis.COMMENTS,
        section_to_teacher=sections_to_preceptor)
>>> heatmap.draw.render_heatmap_data(
        heatmap100,
        x_caption="Graders",
        y_caption="Rubric Comments --- ID")
```

