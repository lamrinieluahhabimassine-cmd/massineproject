"""
Error handlers for the application
"""
from flask import Blueprint, render_template, request
import logging

errors_bp = Blueprint('errors', __name__)
logger = logging.getLogger(__name__)

@errors_bp.app_errorhandler(400)
def bad_request(error):
    """Handle 400 Bad Request"""
    logger.warning(f"Bad request: {request.url} - {error}")
    return render_template('errors/400.html', error=error), 400

@errors_bp.app_errorhandler(401)
def unauthorized(error):
    """Handle 401 Unauthorized"""
    logger.warning(f"Unauthorized access: {request.url}")
    return render_template('errors/401.html', error=error), 401

@errors_bp.app_errorhandler(403)
def forbidden(error):
    """Handle 403 Forbidden"""
    logger.warning(f"Forbidden access: {request.url} by user: {request.remote_addr}")
    return render_template('errors/403.html', error=error), 403

@errors_bp.app_errorhandler(404)
def not_found(error):
    """Handle 404 Not Found"""
    logger.info(f"Page not found: {request.url}")
    return render_template('errors/404.html', error=error), 404

@errors_bp.app_errorhandler(429)
def rate_limit_exceeded(error):
    """Handle 429 Too Many Requests"""
    logger.warning(f"Rate limit exceeded: {request.remote_addr}")
    return render_template('errors/429.html', error=error), 429

@errors_bp.app_errorhandler(500)
def internal_error(error):
    """Handle 500 Internal Server Error"""
    logger.error(f"Internal server error: {request.url} - {error}")
    from models import db
    db.session.rollback()
    return render_template('errors/500.html', error=error), 500

@errors_bp.app_errorhandler(503)
def service_unavailable(error):
    """Handle 503 Service Unavailable"""
    logger.error(f"Service unavailable: {error}")
    return render_template('errors/503.html', error=error), 503