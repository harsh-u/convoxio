#!/usr/bin/env python3
"""
Health check script for WhatsApp Business Platform
"""
import requests
import sys
import json
import time
from datetime import datetime

def check_health(url="http://localhost", timeout=10):
    """Check application health"""
    try:
        response = requests.get(f"{url}/", timeout=timeout)
        return {
            'status': 'healthy' if response.status_code == 200 else 'unhealthy',
            'status_code': response.status_code,
            'response_time': response.elapsed.total_seconds(),
            'timestamp': datetime.now().isoformat()
        }
    except requests.exceptions.RequestException as e:
        return {
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

def check_database():
    """Check database connectivity"""
    try:
        import os
        from app import create_app
        from app.models import db
        
        # Load environment
        env = os.environ.get('FLASK_ENV', 'development')
        config = 'production_config.ProductionConfig' if env == 'production' else None
        
        app = create_app(config)
        with app.app_context():
            # Simple query to test connection
            db.engine.execute('SELECT 1')
            return {
                'status': 'healthy',
                'timestamp': datetime.now().isoformat()
            }
    except Exception as e:
        return {
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

def main():
    """Main health check function"""
    print("🏥 Running health checks...")
    
    # Check web application
    web_health = check_health()
    print(f"Web Application: {web_health['status']}")
    
    # Check database
    db_health = check_database()
    print(f"Database: {db_health['status']}")
    
    # Overall health
    overall_healthy = web_health['status'] == 'healthy' and db_health['status'] == 'healthy'
    
    result = {
        'overall_status': 'healthy' if overall_healthy else 'unhealthy',
        'checks': {
            'web': web_health,
            'database': db_health
        },
        'timestamp': datetime.now().isoformat()
    }
    
    # Output JSON for monitoring systems
    if '--json' in sys.argv:
        print(json.dumps(result, indent=2))
    
    # Exit with appropriate code
    sys.exit(0 if overall_healthy else 1)

if __name__ == "__main__":
    main()