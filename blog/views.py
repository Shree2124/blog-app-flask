import os
from flask import Blueprint, jsonify, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user

from .models import Post, User, Comments, Like
from . import db
from werkzeug.utils import secure_filename

views = Blueprint("view", __name__)

UPLOAD_FOLDER = 'blog/static/uploads/'  
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@views.route("/home")
@views.route("/")
@login_required
def home():
    try:
        posts = Post.query.all()
        for p in posts:
            print(p.date_created)
    except Exception as e:
        print("Error: ", e)
    return render_template("home.html", user=current_user, posts=posts)


@views.route("/create-post", methods=["GET", "POST"])
@login_required
def create():
    if request.method == "POST":
        text = request.form.get("text")
        image = request.files.get("image")
        
        print("Received request.files:", request.files)
        print("Image file object:", image)

        filename = None
        if image and allowed_file(image.filename):
            try:
                filename = secure_filename(image.filename)
                image_path = os.path.join(UPLOAD_FOLDER, filename)
                
                print(f"Saving file to: {image_path}")
                image.save(image_path)

                flash("File uploaded successfully", category="success")
            except Exception as e:
                print("Error while uploading file:", e)
                flash("File upload failed", category="error")

        if not text:
            flash("Post cannot be empty", category="error")
        else:
            try:
                new_post = Post(author=current_user.id, text=text, image=filename)
                db.session.add(new_post)
                db.session.commit()
                flash("Post created successfully", category="success")
                return redirect(url_for("view.home"))
            except Exception as e:
                print("Database error:", e)
                flash("Some error occurred", category="error")

    return render_template("create_post.html", user=current_user)


@views.route("/delete-post/<id>", methods=["POST", "GET"])
@login_required
def delete_post(id):
    try:
        post = Post.query.filter_by(id=id).first()

        if not post:
            flash("Post doest not exist", category="error")
        elif current_user.id != post.author:
            flash("You do not have permission to delete this post.", category="error")
        else:
            db.session.delete(post)
            db.session.commit()
            flash("Post deleted.", category="success")
        return redirect(url_for("view.home"))
    except Exception as e:
        print("Error: ", e)
        flash("Some error occurred ", category="error")


@views.route("/edit-post/<post_id>", methods=["GET", "POST"])
@login_required
def edit_post(post_id):
    post = Post.query.get_or_404(post_id)

    if post.author != current_user.id:
        flash("You do not have permission to edit this post.", category="error")
        return redirect(url_for("view.home"))

    if request.method == "POST":
        text = request.form.get("text")
        remove_image = request.form.get("remove_image") 
        image = request.files.get("image")

        if not text:
            flash("Post text cannot be empty!", category="error")
            return redirect(url_for("views.edit_post", post_id=post.id))

        post.text = text 

        if remove_image and post.image:
            old_image_path = os.path.join(UPLOAD_FOLDER, post.image)
            if os.path.exists(old_image_path):
                os.remove(old_image_path)
            post.image = None

        if image and allowed_file(image.filename):
            try:
                filename = secure_filename(image.filename)
                image_path = os.path.join(UPLOAD_FOLDER, filename)
                image.save(image_path)

                
                if post.image:
                    old_image_path = os.path.join(UPLOAD_FOLDER, post.image)
                    if os.path.exists(old_image_path):
                        os.remove(old_image_path)

                post.image = filename  
                flash("File uploaded successfully!", category="success")
            except Exception as e:
                flash(f"Error while uploading file: {e}", category="error")

        db.session.commit()
        flash("Post updated successfully!", category="success")
        return redirect(url_for("view.home"))

    return render_template("edit_post.html", user=current_user, post=post)
@views.route("/posts/<username>")
@login_required
def posts(username):
    try:
        user = User.query.filter_by(username=username).first()
        if not user:
            flash("No user with that username exists.", category="error")
            return redirect(url_for("view.home"))
        else:
            posts = user.post
            return render_template(
                "posts.html", user=current_user, posts=posts, username=username
            )
    except Exception as e:
        print("Error: ", e)
        flash("Some error occurred", category="error")
        return redirect(url_for("view.home"))


@views.route("/create-comment/<post_id>", methods=["POST", "GET"])
@login_required
def create_comment(post_id):
    try:
        text = request.form.get("text")
        if not text:
            flash("Text is required", category="error")
            return redirect(url_for("view.home"))
        else:
            post = Post.query.filter_by(id=post_id)
            if not post:
                flash("Post does not exist.", category="error")
            else:
                comment = Comments(text=text, author=current_user.id, post_id=post_id)
                db.session.add(comment)
                db.session.commit()

        return redirect(url_for("view.home"))

    except Exception as e:
        print("Error: ", e)
        flash("Some error occurred", category="error")
        return redirect(url_for("view.home"))


@views.route("/delete-comment/<comment_id>", methods=["DELETE", "GET"])
@login_required
def delete_comment(comment_id):
    try:
        comment = Comments.query.filter_by(id=comment_id).first()
        if not comment:
            flash("Comment does not exist", category="error")
        elif (
            current_user.id != comment.author and current_user.id != comment.post.author
        ):
            flash(
                "You do not have permission to delete this comment.", category="error"
            )
        else:
            db.session.delete(comment)
            db.session.commit()
        return redirect(url_for("view.home"))
    except Exception as e:
        print("Error: ", e)
        flash("Some error occurred", category="error")
        return redirect(url_for("view.home"))

@views.route("/like-post/<int:post_id>", methods=["POST"])
@login_required
def like_post(post_id):
    try:
        post = Post.query.get(post_id)  
        if not post:
            return jsonify({'error': 'Post does not exist.'}), 400

        like = Like.query.filter_by(author=current_user.id, post_id=post_id).first()

        if like:
            db.session.delete(like)
            db.session.commit()
        else:
            new_like = Like(author=current_user.id, post_id=post_id)
            db.session.add(new_like)
            db.session.commit()

        return jsonify({
            "likes": len(post.likes), 
            "liked": any(like.author== current_user.id for like in post.likes)
        })

    except Exception as e:
        print("Error:", e)
        return jsonify({'error': 'Some error occurred'}), 500 
