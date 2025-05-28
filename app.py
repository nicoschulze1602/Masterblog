import os.path

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


def generate_user_id(blogposts):
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
            "id": generate_user_id(blogposts),
            "autor": request.form.get("author"),
            "title": request.form.get("title"),
            "content": request.form.get("content")
        }
        blogposts.append(new_blogpost)
        save_blogposts(blogposts)
        return redirect('/')

    return render_template('add.html')


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5001, debug=True)