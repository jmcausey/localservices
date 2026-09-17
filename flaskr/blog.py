import io
import os
from bs4 import BeautifulSoup
from flask import (
    Blueprint, current_app, flash, g, jsonify, redirect, 
    render_template, request, send_file, url_for
)
from gtts import gTTS
from werkzeug.exceptions import abort
from werkzeug.utils import secure_filename

from flaskr.auth import login_required
from flaskr.db import get_db

bp = Blueprint('blog', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
VALID_STATUSES = {'new', 'pending', 'complete'}


# --- Helper Functions ---

def allowed_file(filename):
    """Checks if the uploaded file extension is permitted."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def save_uploaded_image(file):
    """Saves an uploaded image file to static media directory and returns its relative URL."""
    if file and file.filename != '' and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        upload_folder = os.path.join(current_app.static_folder, 'media')
        os.makedirs(upload_folder, exist_ok=True)
        
        filepath = os.path.join(upload_folder, filename)
        file.save(filepath)
        return f"/static/media/{filename}"
    return None


def decode_post_bytes(post):
    """Converts a sqlite3.Row object to a dict and decodes BLOB bytes to string."""
    if post is None:
        return None
    post_dict = dict(post)
    if isinstance(post_dict.get('body'), bytes):
        post_dict['body'] = post_dict['body'].decode('utf-8', errors='ignore')
    return post_dict


def get_post(id, check_author=True):
    """Fetches a post by ID, decodes BLOB data, and checks author authorization."""
    raw_post = get_db().execute(
        'SELECT p.id, title, body, status, created, author_id, username'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' WHERE p.id = ?',
        (id,)
    ).fetchone()

    if raw_post is None:
        abort(404, f"Post id {id} doesn't exist.")

    post = decode_post_bytes(raw_post)

    if check_author and post['author_id'] != g.user['id']:
        abort(403)

    return post


def create_post(title, body, author_id, status='new', image_file=None):
    """Inserts a new post into the database, processing image uploads if present."""
    if image_file:
        image_url = save_uploaded_image(image_file)
        if image_url:
            img_tag = f'<p><img src="{image_url}" alt="Uploaded Image" style="max-width:100%; height:auto; display:block; margin:10px 0;"></p>'
            body = f"{img_tag}\n{body}" if body else img_tag

    db = get_db()
    db.execute(
        'INSERT INTO post (title, body, status, author_id) VALUES (?, ?, ?, ?)',
        (title, body, status, author_id)
    )
    db.commit()


# --- View Routes ---

@bp.route('/')
def index():
    db = get_db()
    raw_posts = db.execute(
        'SELECT p.id, title, body, status, created, author_id, username'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' ORDER BY created DESC'
    ).fetchall()
    
    posts = [decode_post_bytes(p) for p in raw_posts]
    return render_template('blog/index.html', posts=posts)


@bp.route('/scrolling')
def scrolling_view():
    db = get_db()
    raw_posts = db.execute(
        'SELECT p.id, title, body, status, created, author_id, username'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' ORDER BY created DESC'
    ).fetchall()
    
    posts = [decode_post_bytes(p) for p in raw_posts]
    return render_template('blog/index-scrolling.html', posts=posts)


@bp.route('/kiosk')
def kiosk_view():
    db = get_db()
    raw_posts = db.execute(
        'SELECT p.id, title, body, status, created, author_id, username'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' ORDER BY created DESC'
    ).fetchall()
    
    posts = [decode_post_bytes(p) for p in raw_posts]
    return render_template('blog/index_speak_scroll.html', posts=posts)


@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        status = request.form.get('status', 'new').lower()
        image_file = request.files.get('image')

        if not title:
            flash('Title is required.')
        else:
            create_post(title, body, g.user['id'], status=status, image_file=image_file)
            return redirect(url_for('blog.index'))

    return render_template('blog/create.html')


@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    post = get_post(id)

    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        status = request.form.get('status', post['status']).lower()
        image_file = request.files.get('image')

        if not title:
            flash('Title is required.')
        else:
            if image_file:
                image_url = save_uploaded_image(image_file)
                if image_url:
                    img_tag = f'<p><img src="{image_url}" alt="Uploaded Image" style="max-width:100%; height:auto; display:block; margin:10px 0;"></p>'
                    body = f"{img_tag}\n{body}" if body else img_tag

            db = get_db()
            db.execute(
                'UPDATE post SET title = ?, body = ?, status = ? WHERE id = ?',
                (title, body, status, id)
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


@bp.route('/<int:id>/status/<string:new_status>', methods=('POST', 'GET'))
@login_required
def change_status(id, new_status):
    new_status = new_status.lower()
    if new_status == 'completed':
        new_status = 'complete'

    if new_status not in VALID_STATUSES:
        flash('Invalid status update request.')
        return redirect(url_for('blog.index'))

    get_post(id)  # Verify post exists & author authorization
    db = get_db()
    db.execute('UPDATE post SET status = ? WHERE id = ?', (new_status, id))
    db.commit()

    flash(f"Status updated to '{new_status}'.")
    return redirect(url_for('blog.index'))


# --- API & Media Services ---

@bp.route('/api/latest-post-id')
def latest_post_id():
    db = get_db()
    row = db.execute('SELECT id FROM post ORDER BY created DESC LIMIT 1').fetchone()
    return jsonify({"latest_id": row['id'] if row else 0})


@bp.route('/audio/<int:id>')
def get_post_audio(id):
    db = get_db()
    raw_post = db.execute('SELECT title, body FROM post WHERE id = ?', (id,)).fetchone()
    if not raw_post:
        return "Post not found", 404

    post = decode_post_bytes(raw_post)
    clean_title = BeautifulSoup(post['title'], "html.parser").get_text()
    clean_body = BeautifulSoup(post['body'], "html.parser").get_text()
    text_to_speak = f"{clean_title}. {clean_body}"

    tts = gTTS(text=text_to_speak, lang='en')
    fp = io.BytesIO()
    tts.write_to_fp(fp)
    fp.seek(0)

    return send_file(fp, mimetype='audio/mpeg')