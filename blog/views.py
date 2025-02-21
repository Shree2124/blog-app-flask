from flask import Blueprint, jsonify, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from .models import Post, User, Comments, Like
from . import db

views = Blueprint("view", __name__)


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
        if not text:
            flash("Post cannot be empty", category="error")
        else:
            try:
                post = Post(text=text, author=current_user.id)
                db.session.add(post)
                db.session.commit()
                flash("Post created successfully", category="success")
                return redirect(url_for("view.home"))
            except Exception as e:
                print("error: ", e)
                flash("Some error occurred", category="error")
    return render_template("create_post.html", user=current_user)


@views.route("/delete-post/<id>", methods=["DELETE"])
@login_required
def delete_post(id):
    try:
        post = Post.query.filter_by(id=id).first()

        if not post:
            flash("Post doest not exist", category="error")
        elif current_user.id != post.id:
            flash("You do not have permission to delete this post.", category="error")
        else:
            db.session.delete(post)
            db.session.commit()
            flash("Post deleted.", category="success")
        return redirect(url_for("view.home"))
    except Exception as e:
        print("Error: ", e)
        flash("Some error occurred ", category="error")


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


@views.route("/delete-comment/<comment_id>", methods=["POST", "GET"])
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
