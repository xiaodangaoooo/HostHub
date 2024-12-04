
import os
from app import create_app
from app.utils.db import init_db
from app.utils.db import test_connection

# Add this before app.run()
if test_connection():
    print("Database connection successful!")
else:
    print("Failed to connect to database!")
app = create_app()

@app.cli.command("init-db")
def init_db_command():
    """Clear existing data and create new tables."""
    init_db()
    print('Initialized the database.')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 3000))
    app.run(
        host='0.0.0.0',
        port=port,
        debug=True  # Set to False in production
    )