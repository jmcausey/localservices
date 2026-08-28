import os
from flask import (
    Blueprint, current_app, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort
from werkzeug.utils import secure_filename
from flaskr.auth import login_required
from flaskr.db import get_db

bp = Blueprint('blog', __name__)

# Allowed file extensions for image uploads
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_uploaded_image(file):
    """Saves uploaded image to static/media folder and returns the relative web path."""
    if file and file.filename != '' and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        upload_folder = os.path.join(current_app.static_folder, 'media')
        os.makedirs(upload_folder, exist_ok=True)
        
        filepath = os.path.join(upload_folder, filename)
        file.save(filepath)
        return f"/static/media/{filename}"
    return None

def create_post(title, body, author_id, image_file=None):
    """Core function to create a blog post directly from Python or HTTP request."""
    # Append image HTML if an image was uploaded
    if image_file:
        image_url = save_uploaded_image(image_file)
        if image_url:
            img_tag = f'<p><img src="{image_url}" alt="Uploaded Image" style="max-width:100%; height:auto;"></p>'
            body = f"{img_tag}\n{body}" if body else img_tag

    db = get_db()
    db.execute(
        'INSERT INTO post (title, body, author_id)'
        ' VALUES (?, ?, ?)',
        (title, body, author_id)
    )
    db.commit()

@bp.route('/')
def index():
    db = get_db()
    posts = db.execute(
        'SELECT p.id, title, body, created, author_id, username'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' ORDER BY created DESC'
    ).fetchall()
    return render_template('blog/index.html', posts=posts)

@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        image_file = request.files.get('image')
        error = None

        if not title:
            error = 'Title is required.'

        if error is not None:
            flash(error)
        else:
            create_post(title, body, g.user['id'], image_file=image_file)
            return redirect(url_for('blog.index'))

    return render_template('blog/create.html')

def get_post(id, check_author=True):
    post = get_db().execute(
        'SELECT p.id, title, body, created, author_id, username'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' WHERE p.id = ?',
        (id,)
    ).fetchone()

    if post is None:
        abort(404, f"Post id {id} doesn't exist.")

    if check_author and post['author_id'] != g.user['id']:
        abort(403)

    return post

@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    post = get_post(id)

    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        image_file = request.files.get('image')
        error = None

        if not title:
            error = 'Title is required.'

        if error is not None:
            flash(error)
        else:
            if image_file:
                image_url = save_uploaded_image(image_file)
                if image_url:
                    # Change max-width from 100% to a smaller footprint
                    img_tag = f'<p><img src="{image_url}" alt="Uploaded Image" style="max-width:150px; width:100%; height:auto; display:block; margin:0 auto;"></p>'
                    #img_tag = f'<p><img src="{image_url}" alt="Uploaded Image" style="max-width:100%; height:auto;"></p>'
                    body = f"{img_tag}\n{body}" if body else img_tag

            db = get_db()
            db.execute(
                'UPDATE post SET title = ?, body = ?'
                ' WHERE id = ?',
                (title, body, id)
            )
            db.commit()
            return redirect(url_for('blog.index'))

    return render_template('blog/update.html', post=post)

@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    get_post(id)
    db = get_db()
    db.execute('DELETE FROM post WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('blog.index'))
