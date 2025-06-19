from .jobs_per_technician import render_jobs_per_technician_chart
from .jobs_trend import render_jobs_trend_chart
from .service_type_pie import render_service_type_pie
from .activity_heatmap import render_activity_heatmap

__all__ = [
    "render_jobs_per_technician_chart",
    "render_jobs_trend_chart",
    "render_service_type_pie",
    "render_activity_heatmap",
]

GRAPH_OPTIONS = {
    "technicians": render_jobs_per_technician_chart,
    "trend": render_jobs_trend_chart,
    "pie": render_service_type_pie,
    "heatmap": render_activity_heatmap,
}
