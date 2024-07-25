from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import text
import os

app = Flask(__name__)

# Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL') or 'postgresql://username:password@localhost:5432/yourdatabase'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

def get_db_metrics():
    metrics = {}
    
    with db.engine.connect() as connection:
        # Number of database connections
        result = connection.execute(text("SELECT COUNT(*) FROM pg_stat_activity;"))
        metrics['num_connections'] = result.scalar()
        
        # Cache hit ratio
        result = connection.execute(text(
            "SELECT SUM(blks_hit) / (SUM(blks_hit) + SUM(blks_read)) AS cache_hit_ratio FROM pg_stat_database;"
        ))
        metrics['cache_hit_ratio'] = result.scalar()
        
        # Proportion of index scans over total scans
        result = connection.execute(text(
            "SELECT SUM(idx_scan) / (SUM(idx_scan) + SUM(seq_scan)) AS index_scan_ratio FROM pg_stat_user_tables;"
        ))
        metrics['index_scan_ratio'] = result.scalar()
        
        # Fetch, insert, update, and delete throughput
        result = connection.execute(text(
            "SELECT SUM(tup_returned) AS fetches, SUM(tup_inserted) AS inserts, SUM(tup_updated) AS updates, SUM(tup_deleted) AS deletes FROM pg_stat_database;"
        ))
        row = result.fetchone()
        metrics['fetches'] = row['fetches']
        metrics['inserts'] = row['inserts']
        metrics['updates'] = row['updates']
        metrics['deletes'] = row['deletes']
        
        # Rate of deadlock creation
        result = connection.execute(text(
            "SELECT SUM(deadlocks) AS deadlocks FROM pg_stat_database;"
        ))
        metrics['deadlocks'] = result.scalar()
        
        # Replication delay in bytes
        result = connection.execute(text(
            "SELECT COALESCE(MAX(pg_wal_lsn_diff(pg_current_wal_lsn(), replay_lsn)), 0) AS replication_delay FROM pg_stat_replication;"
        ))
        metrics['replication_delay'] = result.scalar()
    
    return metrics

@app.route('/')
def index():
    metrics = get_db_metrics()
    return render_template('index.html', metrics=metrics)

if __name__ == '__main__':
    app.run(debug=True)
