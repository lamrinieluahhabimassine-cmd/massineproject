"""
KPI calculation utilities for temporal metrics
"""
from datetime import datetime, timedelta, date
from models import db, File, StatusHistory, User
from sqlalchemy import func, and_

class TemporalKPI:
    """Calculate temporal KPIs"""
    
    @staticmethod
    def get_average_processing_time():
        """Calculate average time from creation to finalization"""
        finalized_files = File.query.filter_by(status='Finalized').all()
        
        if not finalized_files:
            return None
        
        total_days = 0
        count = 0
        
        for file in finalized_files:
            # Get finalization date from status history
            finalization = StatusHistory.query.filter_by(
                file_id=file.id,
                new_status='Finalized'
            ).first()
            
            if finalization:
                delta = (finalization.changed_at - file.created_at).total_seconds() / 86400  # Convert to days
                total_days += delta
                count += 1
        
        return round(total_days / count, 1) if count > 0 else None
    
    @staticmethod
    def get_average_time_by_stage():
        """Calculate average time spent in each stage"""
        stages = [
            'en attente d\'évaluation',
            'en cours d\'évaluation',
            'ready to invoice',
            'payed',
            'en cours de traitement',
            'transfert à l\'inspection',
            'Finalized'
        ]
        
        stage_times = {}
        
        for stage in stages:
            # Get all transitions FROM this stage
            transitions = StatusHistory.query.filter_by(old_status=stage).all()
            
            if not transitions:
                stage_times[stage] = None
                continue
            
            total_time = 0
            count = 0
            
            for transition in transitions:
                # Find when file entered this stage
                entry = StatusHistory.query.filter_by(
                    file_id=transition.file_id,
                    new_status=stage
                ).order_by(StatusHistory.changed_at.desc()).first()
                
                if entry:
                    delta = (transition.changed_at - entry.changed_at).total_seconds() / 86400
                    if delta >= 0:  # Ignore negative deltas
                        total_time += delta
                        count += 1
            
            stage_times[stage] = round(total_time / count, 1) if count > 0 else None
        
        return stage_times
    
    @staticmethod
    def get_weekly_trend(weeks=4):
        """Get weekly file creation and completion trend"""
        today = date.today()
        trends = []
        
        for i in range(weeks):
            week_start = today - timedelta(days=7 * (i + 1))
            week_end = today - timedelta(days=7 * i)
            
            created = File.query.filter(
                and_(
                    File.created_at >= week_start,
                    File.created_at < week_end
                )
            ).count()
            
            finalized = StatusHistory.query.filter(
                and_(
                    StatusHistory.new_status == 'Finalized',
                    StatusHistory.changed_at >= week_start,
                    StatusHistory.changed_at < week_end
                )
            ).count()
            
            trends.append({
                'week': f"{week_start.strftime('%d/%m')} - {week_end.strftime('%d/%m')}",
                'created': created,
                'finalized': finalized
            })
        
        return list(reversed(trends))
    
    @staticmethod
    def get_monthly_trend(months=6):
        """Get monthly file creation and completion trend"""
        today = date.today()
        trends = []
        
        for i in range(months):
            # Calculate month
            month = today.month - i
            year = today.year
            
            if month <= 0:
                month += 12
                year -= 1
            
            # Month start and end
            month_start = date(year, month, 1)
            if month == 12:
                month_end = date(year + 1, 1, 1)
            else:
                month_end = date(year, month + 1, 1)
            
            created = File.query.filter(
                and_(
                    File.created_at >= month_start,
                    File.created_at < month_end
                )
            ).count()
            
            finalized = StatusHistory.query.filter(
                and_(
                    StatusHistory.new_status == 'Finalized',
                    StatusHistory.changed_at >= month_start,
                    StatusHistory.changed_at < month_end
                )
            ).count()
            
            month_name = month_start.strftime('%B %Y')
            
            trends.append({
                'month': month_name,
                'created': created,
                'finalized': finalized
            })
        
        return list(reversed(trends))
    
    @staticmethod
    def get_deadline_compliance_rate():
        """Calculate percentage of files completed before recall_date"""
        files_with_recall = File.query.filter(
            File.recall_date.isnot(None),
            File.status == 'Finalized'
        ).all()
        
        if not files_with_recall:
            return None
        
        on_time = 0
        
        for file in files_with_recall:
            # Get finalization date
            finalization = StatusHistory.query.filter_by(
                file_id=file.id,
                new_status='Finalized'
            ).first()
            
            if finalization:
                finalization_date = finalization.changed_at.date()
                if finalization_date <= file.recall_date:
                    on_time += 1
        
        return round((on_time / len(files_with_recall)) * 100, 1)
    
    @staticmethod
    def get_current_overdue_files():
        """Get files currently overdue"""
        today = date.today()
        
        overdue = File.query.filter(
            File.recall_date < today,
            File.status != 'Finalized'
        ).all()
        
        return overdue
    
    @staticmethod
    def get_bottleneck_stages():
        """Identify stages where files spend most time"""
        stage_times = TemporalKPI.get_average_time_by_stage()
        
        # Filter out None values and sort
        valid_times = {k: v for k, v in stage_times.items() if v is not None}
        
        if not valid_times:
            return []
        
        sorted_stages = sorted(valid_times.items(), key=lambda x: x[1], reverse=True)
        
        return sorted_stages[:3]  # Top 3 bottlenecks