"""
KPI routes: temporal metrics and analytics
"""
from flask import Blueprint, render_template
from flask_login import login_required, current_user
from utils.kpi import TemporalKPI

kpi_bp = Blueprint('kpi', __name__, url_prefix='/kpi')

@kpi_bp.before_request
@login_required
def require_login():
    """All KPI routes require login"""
    pass


@kpi_bp.route('/temporal')
def temporal():
    """Temporal KPIs dashboard"""
    # Calculate all KPIs
    avg_processing_time = TemporalKPI.get_average_processing_time()
    stage_times = TemporalKPI.get_average_time_by_stage()
    weekly_trend = TemporalKPI.get_weekly_trend(weeks=8)
    monthly_trend = TemporalKPI.get_monthly_trend(months=6)
    deadline_compliance = TemporalKPI.get_deadline_compliance_rate()
    overdue_files = TemporalKPI.get_current_overdue_files()
    bottlenecks = TemporalKPI.get_bottleneck_stages()
    
    return render_template('kpi/temporal.html',
                         avg_processing_time=avg_processing_time,
                         stage_times=stage_times,
                         weekly_trend=weekly_trend,
                         monthly_trend=monthly_trend,
                         deadline_compliance=deadline_compliance,
                         overdue_files=overdue_files,
                         bottlenecks=bottlenecks)