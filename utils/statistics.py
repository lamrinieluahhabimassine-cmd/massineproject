"""
Advanced statistics and analytics for the platform
"""
from datetime import datetime, timedelta, date
from sqlalchemy import func, extract
from models import db, File, User, CoCDetails, Notification

class Statistics:
    """Generate various statistics for the platform"""
    
    @staticmethod
    def get_overview_stats():
        """Get overall platform statistics"""
        today = date.today()
        
        return {
            'total_files': File.query.count(),
            'total_users': User.query.count(),
            'active_users': User.query.filter_by(is_active=True).count(),
            'finalized_files': File.query.filter_by(status='Finalized').count(),
            'pending_files': File.query.filter_by(status='en attente d\'évaluation').count(),
            'overdue_files': File.query.filter(
                File.recall_date <= today,
                File.status != 'Finalized'
            ).count(),
            'files_with_coc': db.session.query(File).join(CoCDetails).count(),
        }
    
    @staticmethod
    def get_files_by_status():
        """Get file count grouped by status"""
        results = db.session.query(
            File.status,
            func.count(File.id).label('count')
        ).group_by(File.status).all()
        
        return [{'status': r.status, 'count': r.count} for r in results]
    
    @staticmethod
    def get_files_by_route():
        """Get file count grouped by route"""
        results = db.session.query(
            File.route,
            func.count(File.id).label('count')
        ).group_by(File.route).all()
        
        return [{'route': r.route, 'count': r.count} for r in results]
    
    @staticmethod
    def get_files_by_country():
        """Get file count grouped by country"""
        results = db.session.query(
            File.country,
            func.count(File.id).label('count')
        ).group_by(File.country).order_by(func.count(File.id).desc()).limit(10).all()
        
        return [{'country': r.country, 'count': r.count} for r in results]
    
    @staticmethod
    def get_files_timeline(days=30):
        """Get file creation timeline for last N days"""
        start_date = date.today() - timedelta(days=days)
        
        results = db.session.query(
            func.date(File.created_at).label('date'),
            func.count(File.id).label('count')
        ).filter(
            File.created_at >= start_date
        ).group_by(func.date(File.created_at)).all()
        
        # Handle both date objects and strings
        formatted_results = []
        for r in results:
            if isinstance(r.date, str):
                date_str = r.date
            else:
                date_str = r.date.strftime('%Y-%m-%d')
            formatted_results.append({'date': date_str, 'count': r.count})
        
        return formatted_results
    
    @staticmethod
    def get_user_performance():
        """Get performance metrics per user"""
        from sqlalchemy import case
        
        results = db.session.query(
            User.id,
            User.username,
            func.count(File.id).label('total_files'),
            func.sum(case((File.status == 'Finalized', 1), else_=0)).label('finalized'),
            func.sum(case((File.recall_date <= date.today(), 1), else_=0)).label('overdue')
        ).join(File, User.id == File.user_id).group_by(User.id, User.username).all()
        
        return [{
            'user_id': r.id,
            'username': r.username,
            'total_files': r.total_files,
            'finalized': r.finalized or 0,
            'overdue': r.overdue or 0,
            'completion_rate': round((r.finalized or 0) / r.total_files * 100, 1) if r.total_files > 0 else 0
        } for r in results]
    
    @staticmethod
    def get_average_processing_time():
        """Calculate average time from creation to finalization"""
        finalized_files = File.query.filter_by(status='Finalized').all()
        
        if not finalized_files:
            return None
        
        total_days = 0
        count = 0
        
        for file in finalized_files:
            days = (file.updated_at - file.created_at).days
            total_days += days
            count += 1
        
        return round(total_days / count, 1) if count > 0 else 0
    
    @staticmethod
    def get_monthly_summary(year=None, month=None):
        """Get summary for a specific month"""
        if not year:
            year = date.today().year
        if not month:
            month = date.today().month
        
        # Files created this month
        files_created = File.query.filter(
            extract('year', File.created_at) == year,
            extract('month', File.created_at) == month
        ).count()
        
        # Files finalized this month
        files_finalized = File.query.filter(
            File.status == 'Finalized',
            extract('year', File.updated_at) == year,
            extract('month', File.updated_at) == month
        ).count()
        
        # CoCs issued this month
        cocs_issued = CoCDetails.query.filter(
            extract('year', CoCDetails.created_at) == year,
            extract('month', CoCDetails.created_at) == month
        ).count()
        
        return {
            'year': year,
            'month': month,
            'files_created': files_created,
            'files_finalized': files_finalized,
            'cocs_issued': cocs_issued
        }
    
    @staticmethod
    def get_yearly_comparison():
        """Compare statistics year over year"""
        current_year = date.today().year
        last_year = current_year - 1
        
        current = db.session.query(
            func.count(File.id)
        ).filter(extract('year', File.created_at) == current_year).scalar()
        
        previous = db.session.query(
            func.count(File.id)
        ).filter(extract('year', File.created_at) == last_year).scalar()
        
        growth = 0
        if previous and previous > 0:
            growth = round(((current - previous) / previous) * 100, 1)
        
        return {
            'current_year': current_year,
            'current_count': current or 0,
            'previous_year': last_year,
            'previous_count': previous or 0,
            'growth_percentage': growth
        }
    
    @staticmethod
    def get_alert_statistics():
        """Get statistics about alerts and recalls"""
        today = date.today()
        
        # Files with upcoming recalls (next 7 days)
        upcoming = File.query.filter(
            File.recall_date > today,
            File.recall_date <= today + timedelta(days=7),
            File.status != 'Finalized'
        ).count()
        
        # Overdue files
        overdue = File.query.filter(
            File.recall_date <= today,
            File.status != 'Finalized'
        ).count()
        
        # Files without recall dates
        no_recall = File.query.filter(
            File.recall_date == None,
            File.status != 'Finalized'
        ).count()
        
        return {
            'upcoming_recalls': upcoming,
            'overdue_recalls': overdue,
            'no_recall_date': no_recall
        }
    
    @staticmethod
    def get_top_importers(limit=10):
        """Get most active importers"""
        results = db.session.query(
            File.importer,
            func.count(File.id).label('count')
        ).group_by(File.importer).order_by(func.count(File.id).desc()).limit(limit).all()
        
        return [{'importer': r.importer, 'count': r.count} for r in results]
    
    @staticmethod
    def get_top_exporters(limit=10):
        """Get most active exporters"""
        results = db.session.query(
            File.exporter,
            func.count(File.id).label('count')
        ).group_by(File.exporter).order_by(func.count(File.id).desc()).limit(limit).all()
        
        return [{'exporter': r.exporter, 'count': r.count} for r in results]


def generate_dashboard_data():
    """Generate all data needed for dashboard charts"""
    stats = Statistics()
    
    return {
        'overview': stats.get_overview_stats(),
        'by_status': stats.get_files_by_status(),
        'by_route': stats.get_files_by_route(),
        'by_country': stats.get_files_by_country(),
        'timeline': stats.get_files_timeline(30),
        'user_performance': stats.get_user_performance(),
        'avg_processing_time': stats.get_average_processing_time(),
        'monthly': stats.get_monthly_summary(),
        'yearly': stats.get_yearly_comparison(),
        'alerts': stats.get_alert_statistics(),
        'top_importers': stats.get_top_importers(5),
        'top_exporters': stats.get_top_exporters(5)
    }


class InvoiceStatistics:
    """Statistics specific to invoicing"""
    
    @staticmethod
    def get_invoice_stats():
        """Get invoice-related statistics"""
        today = date.today()
        
        return {
            'ready_to_invoice': File.query.filter_by(status='ready to invoice').count(),
            'invoiced_total': File.query.filter_by(status='payed').count(),
            'invoiced_today': File.query.filter(
                File.status == 'payed',
                File.invoiced_at >= datetime.now().replace(hour=0, minute=0, second=0)
            ).count(),
            'invoiced_this_week': File.query.filter(
                File.status == 'payed',
                File.invoiced_at >= datetime.now() - timedelta(days=7)
            ).count(),
            'invoiced_this_month': File.query.filter(
                File.status == 'payed',
                db.func.extract('month', File.invoiced_at) == today.month,
                db.func.extract('year', File.invoiced_at) == today.year
            ).count()
        }
    
    @staticmethod
    def get_monthly_invoice_summary(year=None, month=None):
        """Get invoice summary for a specific month"""
        if not year:
            year = date.today().year
        if not month:
            month = date.today().month
        
        invoiced = File.query.filter(
            File.status == 'payed',
            db.func.extract('year', File.invoiced_at) == year,
            db.func.extract('month', File.invoiced_at) == month
        ).count()
        
        return {
            'year': year,
            'month': month,
            'invoiced_count': invoiced
        }
    
    @staticmethod
    def get_invoices_by_user():
        """Get invoice count by invoicing team member"""
        results = db.session.query(
            User.username,
            db.func.count(File.id).label('count')
        ).join(File, User.id == File.invoiced_by).filter(
            File.status == 'payed'
        ).group_by(User.username).all()
        
        return [{'username': r.username, 'count': r.count} for r in results]