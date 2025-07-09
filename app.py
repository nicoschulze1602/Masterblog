import os.path
from datetime import datetime

from flask import Flask, render_template, request, redirect, session, flash, url_for
import json

app = Flask(__name__)
import secrets
from dotenv import load_dotenv

load_dotenv()
app.secret_key = os.environ.get('FLASK_SECRET_KEY', secrets.token_hex(16))
BLOGPOSTS = 'blog_posts.json'


def load_blogposts():
    """
    Loads all blog posts from the JSON file.
    Returns an empty list if the file does not exist or if an error occurs.
    """
    if not os.path.exists(BLOGPOSTS):
        return []
    try:
        with open(BLOGPOSTS, 'r', encoding='utf-8') as file:
            return json.load(file)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error loading blog posts: {e}")
        return []


def time_since_posted(post_date_str, post_time_str):
    """
    Converts a datetime string into a relative time string
    like 'X min ago', 'X h ago', or 'X d ago'.
    """
    if not post_date_str or not post_time_str:
        return ""

    try:
        post_datetime_str = f"{post_date_str} {post_time_str}"
        post_time = datetime.strptime(post_datetime_str, "%d.%m.%Y %H:%M:%S")
        now = datetime.now()
        delta = now - post_time

        seconds = int(delta.total_seconds())
        minutes = seconds // 60
        hours = minutes // 60
        days = hours // 24

        if seconds < 60:
            return "just now"
        elif minutes < 60:
            return f"{minutes} min ago"
        elif hours < 24:
            return f"{hours} h ago"
        else:
            return f"{days} d ago"
    except (ValueError, TypeError) as e:
        print(
            f"Error parsing timestamp in time_since_posted: {e} for date '{post_date_str}' time '{post_time_str}'")
        return ""


@app.route('/comment/<int:post_id>', methods=['POST'])
def comment(post_id):
    """
    Handles the submission of a new comment for a specific blog post.

    Args:
        post_id (int): The ID of the blog post to add the comment to.

    Returns:
        werkzeug.wrappers.response.Response: A redirect to the home page or
                                             back to the post if an error occurs.
    """
    blogposts = load_blogposts()
    post_found = False
    for post in blogposts:
        if post["id"] == post_id:
            post_found = True
            comment_text = request.form.get("comment", "").strip()
            if comment_text:
                full_timestamp = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
                comment_entry = {
                    "text": comment_text,
                    "timestamp": full_timestamp,
                }
                post.setdefault("comments", []).append(comment_entry)
                flash('Comment added successfully!', 'success')
            else:
                flash('Comment cannot be empty.', 'error')
            break

    if not post_found:
        flash(f'Error: Blog post with ID {post_id} not found.', 'error')
        return redirect(url_for('index'))

    save_blogposts(blogposts)
    return redirect(url_for('index', _anchor=f'post-{post_id}'))


def save_blogposts(blogposts):
    """
    Saves the provided list of blog posts to the JSON file.

    Args:
        blogposts (list): A list of dictionaries, where each dictionary represents a blog post.
    """
    try:
        with open(BLOGPOSTS, 'w', encoding='utf-8') as file:
            json.dump(blogposts, file, indent=4, ensure_ascii=False)
    except IOError as e:
        print(f"Error saving blog posts: {e}")


def generate_post_id():
    """
    Generates a unique, chronologically sortable post ID based on the current timestamp.
    """
    try:
        return int(datetime.now().strftime("%Y%m%d%H%M%S%f"))
    except ValueError:
        blogposts = load_blogposts()
        if blogposts:
            return max(p.get('id', 0) for p in blogposts) + 1
        return 1


@app.route('/')
def index():
    """
    Renders the main page displaying all blog posts.
    Supports optional sorting via ?sort=asc or ?sort=desc.
    """
    sort_order = request.args.get('sort', 'desc')
    blogposts = load_blogposts()
    for post in blogposts:
        if "time" in post and "date" in post:
            post["time_ago"] = time_since_posted(post.get('date'), post.get('time'))
        else:
            post["time_ago"] = ""
    blogposts.sort(key=lambda x: int(x.get('id', 0)), reverse=(sort_order == 'desc'))

    return render_template('index.html', posts=blogposts, sort_order=sort_order, now=datetime.now())


@app.route('/add', methods=['GET', 'POST'])
def add():
    """
    Handles adding a new blog post.
    Validates form data and either displays the form or processes the submission.
    """
    if request.method == 'POST':
        author = request.form.get("author")
        title = request.form.get("title")
        content = request.form.get("content")

        if not author or not title or not content:
            flash("Author, title, and content are required fields.", "error")
            return render_template('add.html', author=author, title=title, content=content)

        blogposts = load_blogposts()

        new_blogpost = {
            "id": generate_post_id(),
            "author": author,
            "title": title,
            "content": content,
            "date": datetime.now().strftime("%d.%m.%Y"),
            "time": datetime.now().strftime("%H:%M:%S"),
            "likes": 0,
            "comments": []
        }

        blogposts.append(new_blogpost)
        save_blogposts(blogposts)
        flash('New post added successfully!', 'success')
        return redirect('/')

    return render_template('add.html')


@app.route('/delete/<int:post_id>', methods=['POST'])
def delete(post_id):
    """
    Deletes a specific blog post.

    Args:
        post_id (int): The ID of the blog post to delete.

    Returns:
        werkzeug.wrappers.response.Response: A redirect to the home page.
    """
    blogposts = load_blogposts()
    original_len = len(blogposts)
    blogposts = [post for post in blogposts if post["id"] != post_id]
    if len(blogposts) < original_len:
        save_blogposts(blogposts)
        flash('Post deleted successfully!', 'success')
    else:
        flash(f'Error: Post with ID {post_id} not found.', 'error')
    return redirect('/')


@app.route('/update/<int:post_id>', methods=['GET', 'POST'])
def update(post_id):
    """
    Handles updating an existing blog post.

    Args:
        post_id (int): The ID of the blog post to update.

    Returns:
        werkzeug.wrappers.response.Response: A redirect to the home page after update,
                                             or renders the update form.
        str: "Post not found" with a 404 status if the post does not exist.
    """
    blogposts = load_blogposts()
    post = next((p for p in blogposts if p["id"] == post_id), None)
    if post is None:
        flash(f"Error: Post with ID {post_id} not found.", "error")
        return redirect(url_for('index'))

    if request.method == 'POST':
        author = request.form.get("author")
        title = request.form.get("title")
        content = request.form.get("content")

        if not author or not title or not content:
            flash("Author, title, and content are required fields.", "error")
            return render_template('add.html', post=post)

        post["author"] = author
        post["title"] = title
        post["content"] = content
        post["date"] = datetime.now().strftime("%d.%m.%Y")
        post["time"] = datetime.now().strftime("%H:%M:%S")
        save_blogposts(blogposts)
        flash('Post updated successfully!', 'success')
        return redirect(url_for('index', _anchor=f'post-{post_id}'))

    return render_template('add.html', post=post)


@app.route('/like/<int:post_id>', methods=['POST'])
def like(post_id):
    """
    Toggles the like status for a specific blog post for the current user session.
    Increases or decreases the like count based on whether the post has already been liked.
    """
    blogposts = load_blogposts()
    session.setdefault('liked_posts', [])
    liked_posts = session['liked_posts']

    post_found = False
    for post in blogposts:
        if post["id"] == post_id:
            post_found = True
            if post_id in liked_posts:
                post["likes"] = max(0, post.get("likes", 0) - 1)
                liked_posts.remove(post_id)
                flash('Post unliked!', 'info')
            else:
                post["likes"] = post.get("likes", 0) + 1
                liked_posts.append(post_id)
                flash('Post liked!', 'success')
            break

    if not post_found:
        flash(f'Error: Blog post with ID {post_id} not found.', 'error')

    session['liked_posts'] = liked_posts
    save_blogposts(blogposts)
    return redirect(url_for('index', _anchor=f'post-{post_id}'))


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5001, debug=os.environ.get('FLASK_DEBUG') == '1')