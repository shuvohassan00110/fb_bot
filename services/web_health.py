from flask import Flask, jsonify
import time

def make_app(state, cache, ringlog):
    app = Flask(__name__)
    started = time.time()

    @app.get("/health")
    def health():
        return jsonify({
            "ok": True,
            "uptime_sec": int(time.time() - started),
            "force_join": state.force_join,
            "maintenance": state.maintenance,
            "cache_items": cache.size(),
            "requests": state.requests_count,
        })

    @app.get("/errors")
    def errors():
        return jsonify({"errors": ringlog.tail(50)})

    return app
