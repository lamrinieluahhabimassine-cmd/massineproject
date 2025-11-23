"""
Advanced search and filtering utilities
"""
from datetime import datetime, date
from sqlalchemy import or_, and_
from models import File, User

class FileSearchFilter:
    """Advanced search and filter for files"""
    
    def __init__(self, query=None):
        """Initialize with base query or create new one"""
        self.query = query or File.query
    
    def by_file_number(self, file_number):
        """Filter by file number (partial match)"""
        if file_number:
            self.query = self.query.filter(
                File.file_number.ilike(f'%{file_number}%')
            )
        return self
    
    def by_status(self, status):
        """Filter by exact status"""
        if status:
            self.query = self.query.filter_by(status=status)
        return self
    
    def by_route(self, route):
        """Filter by route"""
        if route:
            self.query = self.query.filter_by(route=route)
        return self
    
    def by_user(self, user_id):
        """Filter by user"""
        if user_id:
            self.query = self.query.filter_by(user_id=user_id)
        return self
    
    def by_country(self, country):
        """Filter by country (partial match)"""
        if country:
            self.query = self.query.filter(
                File.country.ilike(f'%{country}%')
            )
        return self
    
    def by_importer(self, importer):
        """Filter by importer (partial match)"""
        if importer:
            self.query = self.query.filter(
                File.importer.ilike(f'%{importer}%')
            )
        return self
    
    def by_exporter(self, exporter):
        """Filter by exporter (partial match)"""
        if exporter:
            self.query = self.query.filter(
                File.exporter.ilike(f'%{exporter}%')
            )
        return self
    
    def by_date_range(self, start_date=None, end_date=None):
        """Filter by receipt date range"""
        if start_date:
            self.query = self.query.filter(File.receipt_date >= start_date)
        if end_date:
            self.query = self.query.filter(File.receipt_date <= end_date)
        return self
    
    def by_recall_status(self, overdue_only=False):
        """Filter by recall status"""
        if overdue_only:
            today = date.today()
            self.query = self.query.filter(
                and_(
                    File.recall_date <= today,
                    File.status != 'Finalized'
                )
            )
        return self
    
    def has_coc(self, has_coc=None):
        """Filter by CoC presence"""
        if has_coc is True:
            from models import CoCDetails
            self.query = self.query.join(CoCDetails)
        elif has_coc is False:
            from models import CoCDetails
            self.query = self.query.outerjoin(CoCDetails).filter(
                CoCDetails.id == None
            )
        return self
    
    def search_all(self, search_term):
        """
        Global search across multiple fields
        Searches in: file_number, importer, exporter, country, SOR, SOL
        """
        if search_term:
            search_pattern = f'%{search_term}%'
            self.query = self.query.filter(
                or_(
                    File.file_number.ilike(search_pattern),
                    File.importer.ilike(search_pattern),
                    File.exporter.ilike(search_pattern),
                    File.country.ilike(search_pattern),
                    File.sor_number.ilike(search_pattern),
                    File.sol_number.ilike(search_pattern)
                )
            )
        return self
    
    def order_by(self, field='created_at', direction='desc'):
        """Order results"""
        order_field = getattr(File, field, File.created_at)
        if direction == 'desc':
            self.query = self.query.order_by(order_field.desc())
        else:
            self.query = self.query.order_by(order_field.asc())
        return self
    
    def paginate(self, page=1, per_page=20):
        """Paginate results"""
        return self.query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
    
    def all(self):
        """Get all results"""
        return self.query.all()
    
    def count(self):
        """Count results"""
        return self.query.count()


def search_files(filters):
    """
    Main search function with dictionary of filters
    
    Args:
        filters: Dictionary with filter parameters
        
    Returns:
        Filtered query
        
    Example:
        filters = {
            'file_number': 'VOC',
            'status': 'Finalized',
            'route': 'A',
            'start_date': '2025-01-01',
            'end_date': '2025-12-31',
            'search': 'import',
            'overdue_only': True
        }
    """
    search = FileSearchFilter()
    
    # Apply filters
    search.by_file_number(filters.get('file_number'))
    search.by_status(filters.get('status'))
    search.by_route(filters.get('route'))
    search.by_user(filters.get('user_id'))
    search.by_country(filters.get('country'))
    search.by_importer(filters.get('importer'))
    search.by_exporter(filters.get('exporter'))
    search.by_recall_status(filters.get('overdue_only', False))
    search.has_coc(filters.get('has_coc'))
    
    # Date range
    if filters.get('start_date'):
        try:
            start_date = datetime.strptime(filters['start_date'], '%Y-%m-%d').date()
            search.by_date_range(start_date=start_date)
        except ValueError:
            pass
    
    if filters.get('end_date'):
        try:
            end_date = datetime.strptime(filters['end_date'], '%Y-%m-%d').date()
            search.by_date_range(end_date=end_date)
        except ValueError:
            pass
    
    # Global search
    if filters.get('search'):
        search.search_all(filters['search'])
    
    # Ordering
    order_by = filters.get('order_by', 'created_at')
    direction = filters.get('direction', 'desc')
    search.order_by(order_by, direction)
    
    return search


def get_filter_options():
    """Get available options for filters (for dropdowns)"""
    return {
        'statuses': [
            'en attente d\'évaluation',
            'en cours d\'évaluation',
            'ready to invoice',
            'payed',
            'en cours de traitement',
            'à compléter',
            'transfert à l\'inspection',
            'Finalized'
        ],
        'routes': ['A', 'B', 'C'],
        'users': User.query.order_by(User.username).all()
    }