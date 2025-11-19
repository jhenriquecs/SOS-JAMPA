from flask import Flask, flash, render_template, redirect, request, flash, g
import json, ast,os

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'henrique'

    @app.route("/")
    def home():
        return render_template("index.html")





































    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)