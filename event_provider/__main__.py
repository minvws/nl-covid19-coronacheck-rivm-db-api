"""Main file to handle Flask start"""
from event_provider import check_config, create_app

if __name__ == "__main__":
    check_config()
    app = create_app()
    host = app.config["DEFAULT"].get("host", "127.0.0.1")
    port = app.config["DEFAULT"].get("port", 5000)
    app.run(host=host, port=port)
