from app import create_app, db
from flask_migrate import Migrate
import logging
from datetime import datetime

app = create_app()
migrate = Migrate(app, db)

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Add global template context
@app.context_processor
def utility_processor():
    return {
        'now': datetime.utcnow()  # Call the function here
    }

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=True)