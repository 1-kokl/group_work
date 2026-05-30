from flask import Flask

app = Flask(__name__)

@app.route("/")
def hello():
    return "Hello, this is a self-signed HTTPS server!"

if __name__ == "__main__":
    # 关键：用你刚生成的 rootCA.crt 和 rootCA.key 启动 HTTPS
    app.run(
        host="0.0.0.0",
        port=443,
        ssl_context=("rootCA.crt", "rootCA.key")
    )
