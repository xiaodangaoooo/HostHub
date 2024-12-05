import os
from flask import Flask
from app import create_app
from app.utils.db import init_db

app = create_app()

def init_db_command():
    """Clear existing data and create new tables."""
    with app.app_context():
        init_db()
        print('Initialized the database.')

# Register the command
app.cli.command('init-db')(init_db_command)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 3000))
    app.run(
        host='0.0.0.0',
        port=port,
        debug=True
    )