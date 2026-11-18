"""Start only the isolated acceptance server on loopback."""
import argparse
import os
from common import configure, ROOT

parser = argparse.ArgumentParser()
parser.add_argument("--data", required=True)
parser.add_argument("--source", default=str(ROOT))
parser.add_argument("--port", type=int, default=5099)
parser.add_argument("--metrics", required=True)
args = parser.parse_args()
configure(args.data, args.source)
os.environ["APP_METRICS_FILE"] = args.metrics
import run
app = run.app
from app.extensions import db
with app.app_context():
    db.create_all()
    if hasattr(run, "apply_database_indexes"):
        run.apply_database_indexes()
from waitress import serve
serve(app, host="127.0.0.1", port=args.port, threads=16, channel_timeout=30)
