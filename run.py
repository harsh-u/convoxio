import logging
from app import create_app

# Simple logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log')
    ]
)

app = create_app()

if __name__ == "__main__":
    logger = logging.getLogger(__name__)
    logger.info("🚀 Starting Flask application on port 5001...")
    logger.info("🔧 Debug mode: ON")
    app.run(debug=True, port=5001, host='0.0.0.0')