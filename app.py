import os.path
from datetime import datetime

from flask import Flask, render_template, request, redirect
import json

app = Flask(__name__)
BLOGPOSTS = 'blog_posts.json'


def load_blogposts():
    if not os.path.exists(BLOGPOSTS):
        return []
    with open(BLOGPOSTS, 'r', encoding='utf-8') as file:
        return json.load(file)


def save_blogposts(blogposts):
    with open(BLOGPOSTS, 'w', encoding='utf-8') as file:
        json.dump(blogposts, file, indent=4, ensure_ascii=False)


def generate_post_id(blogposts):
    if not blogposts:
        return 1
    return max(post["id"] for post in blogposts) + 1


@app.route('/')
def index():
    blogposts = load_blogposts()
    return render_template('index.html', posts=blogposts)


@app.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        blogposts = load_blogposts()

        new_blogpost = {
            "id": generate_post_id(blogposts),
            "author": request.form.get("author"),
            "title": request.form.get("title"),
            "content": request.form.get("content"),
            "date": datetime.now().strftime("%d.%m.%Y"),
            "time": datetime.now().strftime("%H:%M:%S")
        }

        blogposts.append(new_blogpost)
        save_blogposts(blogposts)
        return redirect('/')

    return render_template('add.html')


@app.route('/delete/<int:post_id>', methods=['POST'])
def delete(post_id):
    blogposts = load_blogposts()
    blogposts = [post for post in blogposts if post["id"] != post_id]
    save_blogposts(blogposts)
    return redirect('/')


@app.route('/update/<int:post_id>', methods=['GET', 'POST'])
def update(post_id):
    blogposts = load_blogposts()
    post = next((p for p in blogposts if p["id"] == post_id), None)
    if post is None:
        return "Post not found", 404

    if request.method == 'POST':
        post["author"] = request.form.get("author")
        post["title"] = request.form.get("title")
        post["content"] = request.form.get("content")
        post["date"] = datetime.now().strftime("%d.%m.%Y")
        post["time"] = datetime.now().strftime("%H:%M:%S")
        save_blogposts(blogposts)
        return redirect('/')

    return render_template('update.html', post=post)


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5001, debug=True)