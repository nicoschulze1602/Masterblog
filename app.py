from flask import Flask, render_template
import json

app = Flask(__name__)

with open('blog_posts.json', 'r') as file:
    blog_posts = json.load(file)


@app.route('/')
def index():
    print("Hello There!")
    return render_template('index.html', posts=blog_posts)


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5001, debug=True)