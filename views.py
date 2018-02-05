import functools
import os
import re
import urllib

from flask import (Flask, flash, Markup, redirect, render_template, request,
                   Response, session, url_for, abort)

from markdown import markdown
from markdown.extensions.codehilite import CodeHiliteExtension
from markdown.extensions.extra import ExtraExtension

from micawber import bootstrap_basic, parse_html
from micawber.cache import Cache as OEmbedCache
from peewee import *
from playhouse.flask_utils import FlaskDB, get_object_or_404, object_list
from playhouse.sqlite_ext import *

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from auth.iaasldap import LDAPUser as LDAPUser

current_user = LDAPUser()

from app import app
import models as models

def login_required(fn):
    @functools.wraps(fn)
    def inner(*args, **kwargs):
        if session.get('logged_in'):
            return fn(*args, **kwargs)
        return redirect(url_for('login', next=request.path))
    return inner

@app.route('/login/', methods=['GET', 'POST'])
def login():
    next_url = request.args.get('next') or request.form.get('next')
    if request.method == 'POST' and request.form.get('password'):
        password = request.form.get('password')
        # TODO: If using a one-way hash, you would also hash the user-submitted
        # password and do the comparison on the hashed versions.
        if password == app.config['ADMIN_PASSWORD']:
            session['logged_in'] = True
            session.permanent = True  # Use cookie to store session.
            flash('You are now logged in.', 'success')
            return redirect(next_url or url_for('index'))
        else:
            flash('Incorrect password.', 'danger')
    return render_template('login.html', next_url=next_url)

@app.route('/logout/', methods=['GET', 'POST'])
def logout():
    if request.method == 'POST':
        session.clear()
        return redirect(url_for('login'))
    return render_template('logout.html')

@app.route('/')
def index():
    search_query = request.args.get('q')
    if search_query:
        query = models.Entry.search(search_query)
    else:
        query = models.Entry.public().order_by(models.Entry.timestamp.desc())

    # The `object_list` helper will take a base query and then handle
    # paginating the results if there are more than 20. For more info see
    # the docs:
    # http://docs.peewee-orm.com/en/latest/peewee/playhouse.html#object_list
    # o= object_list(
    #     'index.html',
    #     query,
    #     search=search_query,
    #     check_bounds=False)
    # return o
    return render_template('index.html',object_list=query.all(),
        search=search_query,
        check_bounds=False)

def _create_or_edit(entry, template, topics):
    if request.method == 'POST':
        entry.title = request.form.get('title') or ''
        entry.content = request.form.get('content') or ''
        entry.published = request.form.get('published') or False
        if not (entry.title and entry.content):
            flash('Title and Content are required.', 'danger')
        else:
            # Wrap the call to save in a transaction so we can roll it back
            # cleanly in the event of an integrity error.
            ret = entry.save()
            if not ret:
                flash('Error: this title is already in use.', 'danger')
            else:
                flash('Entry saved successfully.', 'success')

            topics = models.PageTopic.query.filter_by(topic_id=request.form.get('topic_id'), entry_id=entry.id)
            if topics.count() == 0:
                t = models.PageTopic(int(request.form.get('topic_id')), entry.id)
                models.db.session.add(t)
                models.db.session.commit()

            if entry.published:
                return redirect(url_for('detail', slug=entry.slug))
            else:
                return redirect(url_for('edit', slug=entry.slug))

            # try:
            #     # with database.atomic():
            #     entry.save()
            # except IntegrityError:
            #     flash('Error: this title is already in use.', 'danger')
            # else:
            #     flash('Entry saved successfully.', 'success')
            #     if entry.published:
            #         return redirect(url_for('detail', slug=entry.slug))
            #     else:
            #         return redirect(url_for('edit', slug=entry.slug))

    return render_template(template, entry=entry, topics=topics)

@app.route('/create/', methods=['GET', 'POST'])
@login_required
def create():
    topics = models.Topic.query.all()
    return _create_or_edit(models.Entry(title='', content=''), 'create.html', topics=topics)

@app.route('/drafts/')
@login_required
def drafts():
    query = models.Entry.drafts().order_by(models.Entry.timestamp.desc())
    # return object_list('index.html', query, check_bounds=False)
    return render_template('index.html',object_list=query.all(),
        check_bounds=False)

@app.route('/online_learning/<slug>/')
def detail(slug):
    if session.get('logged_in'):
        # query = models.Entry.query.all()
        entries = models.Entry.query.filter_by(slug=slug)

    else:
        entries = models.Entry.public()

    if entries.count()==0:
        abort(404)
    else:
        entry=entries.first()
    entry.views=entry.views+1
    models.db.session.add(entry)
    models.db.session.commit()
    # entry = models.Entry.query.get_or_404(slug = slug)
    return render_template('detail.html', entry=entry)

@app.route('/<slug>/edit/', methods=['GET', 'POST'])
@login_required
def edit(slug):
    entry = models.Entry.query.filter_by(slug = slug)
    if entry.count==0:
        abort(404)

    return _create_or_edit(entry.first(), 'edit.html', topics=models.Topic.query.all())

@app.template_filter('clean_querystring')
def clean_querystring(request_args, *keys_to_remove, **new_values):
    # We'll use this template filter in the pagination include. This filter
    # will take the current URL and allow us to preserve the arguments in the
    # querystring while replacing any that we need to overwrite. For instance
    # if your URL is /?q=search+query&page=2 and we want to preserve the search
    # term but make a link to page 3, this filter will allow us to do that.
    querystring = dict((key, value) for key, value in request_args.items())
    for key in keys_to_remove:
        querystring.pop(key, None)
    querystring.update(new_values)
    return urllib.urlencode(querystring)

@app.errorhandler(404)
def not_found(exc):
    return Response('<h3>Not found</h3>'), 404




from jinja2 import TemplateNotFound
import dbconfig

@app.route('/<page>')
def show(page):
    try:
        return render_template("%s.html" % page)
    except TemplateNotFound:
        abort(404)

@app.context_processor
def inject_paths():
    return dict(iaas_url=dbconfig.iaas_route,
                dbas_url=dbconfig.dbas_route,
                LDAPUser=LDAPUser(),
                iaas_db_name=dbconfig.db_name
                )


@app.route('/topics')
def list_topics():
    topics = models.Topic.query.all()

    return render_template("topic.html",
                               topics=topics)


@app.route('/topics/<topic_id>')
def list_pages_in_this_topic(topic_id):
    videos = getTopicResources(topic_id)
    topic = models.Topic.query.filter_by(id=topic_id).first()
    return render_template('topic.html',
                           topic=topic,
                           videos=videos)

@app.route('/tags')
def list_tags():
    tags = models.Tag.query.all()

    return render_template("tag.html",
                           tags=tags)

@app.route('/tags/<tag>')
def list_pages_with_this_tag(tag):
    videos = getTagResources(tag)

    tag = models.Tag.query.filter_by(id=tag).first()

    return render_template("tag.html",
                           tag=tag,
                           videos=videos)

def getTagResources(tag_id):

    # pages = self.getAllPagesByTag(tag_id)

    videos = getVideosByTag(tag_id)

    # topics = self.getTopicsByTag(tag_id)


    return videos

def getVideosByTopic(topic_id):
    pagestmp = models.Entry.query.all()
    videos=[]
    topic = models.Topic.query.filter_by(id=topic_id).first()
    for p in pagestmp:
        if topic in p.topics:
            for v in p.videos:
                videos.append(v)
    return videos

def getVideosByTag(tag_id):
    pagestmp = models.Entry.query.all()
    videos=[]
    tag = models.Tag.query.filter_by(id=tag_id).first()
    for p in pagestmp:
        if tag in p.tags:
            for v in p.videos:
                videos.append(v)
    return videos

def getTopicResources(topic_id):

    # pages = self.getAllPagesByTopic(topic_id)

    videos = getVideosByTopic(topic_id)

    # tags = self.getTagsByTopic(topic_id)

    return videos
#****************************************
# ADMIN

from flask_admin import Admin, AdminIndexView

from flask_admin.contrib.sqla import ModelView


# Flask and Flask-SQLAlchemy initialization here
# from flask_login import current_user


class MyAdminIndexView(AdminIndexView):
    def is_accessible(self):
        return True
        # if hasattr(current_user,'email'):
        #     if current_user.email == 'default' and \
        #             current_user.is_authenticated:
        #         return True
        # return False

    # def inaccessible_callback(self, name, **kwargs):
    #     # redirect to login page if user doesn't have access
    #     return redirect(url_for('signup', next=request.url))


class MyModelView(ModelView):
    def is_accessible(self):
        return True
        # if hasattr(current_user,'email'):
        #     if current_user.email == 'default' and \
        #             current_user.is_authenticated:
        #         return True
        # return False

    # def inaccessible_callback(self, name, **kwargs):
    #     # redirect to login page if user doesn't have access
    #     return redirect(url_for('signup', next=request.url))




admin = Admin(app, name='ADMIN', template_mode='bootstrap3',index_view=MyAdminIndexView())

admin.add_view(MyModelView(models.Entry, models.db.session))
admin.add_view(MyModelView(models.Topic, models.db.session))
admin.add_view(MyModelView(models.Tag, models.db.session))
admin.add_view(MyModelView(models.Comment, models.db.session))
admin.add_view(MyModelView(models.Video, models.db.session))
admin.add_view(MyModelView(models.PageTopic, models.db.session))
admin.add_view(MyModelView(models.PageTag, models.db.session))


