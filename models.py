from app import db, app, database
from datetime import datetime

from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, String, Text, Time, text,Boolean
from sqlalchemy.orm import relationship, load_only

from markdown import markdown
from markdown.extensions.codehilite import CodeHiliteExtension
from markdown.extensions.extra import ExtraExtension

from micawber import bootstrap_basic, parse_html
from micawber.cache import Cache as OEmbedCache
from peewee import *

from flask import (Markup)

import re


# Configure micawber with the default OEmbed providers (YouTube, Flickr, etc).
# We'll use a simple in-memory cache so that multiple requests for the same
# video don't require multiple network requests.
oembed_providers = bootstrap_basic(OEmbedCache())


class Tag(db.Model):
    __bind_key__ = 'online_learning'
    # __tablename__ = 'Tag'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100),default='')

    def __init__(self,name="tag"):
        self.name=name

    def __repr__(self):
        return self.name




class Video(db.Model):
    __bind_key__ = 'online_learning'
    # __tablename__ = 'Video'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text,default='#', nullable=True)


    page_inst_id = db.Column(ForeignKey('entry.id'), nullable=True, index=True)
    page_inst = relationship('Entry', back_populates='videos')

    def __init__(self, page_inst, link=""):
        self.name = link
        self.page_inst_id=page_inst.id

    def __repr__(self):
        return self.name

class PageTag(db.Model):
    __bind_key__ = 'online_learning'
    __tablename__ = 'page_tag'
    id = db.Column(db.Integer, primary_key=True)
    tag_id = Column(Integer,ForeignKey('tag.id'))
    page_id = Column(Integer, ForeignKey('entry.id'))

    def __init__(self,tag_id,page_id):
        self.tag_id = tag_id
        self.page_id = page_id

class PageTopic(db.Model):
    __bind_key__ = 'online_learning'
    __tablename__ = 'page_topic'
    id = db.Column(db.Integer, primary_key=True)
    topic_id = Column(Integer, db.ForeignKey('topic.id'))
    entry_id = Column(Integer, db.ForeignKey('entry.id'))
#
    def __init__(self,topic_id,page_id):
        self.topic_id = topic_id
        self.page_id = page_id


class Topic(db.Model):
    __bind_key__ = 'online_learning'
    __tablename__ = 'topic'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100),default='')

    def __init__(self,topic="topic"):
        self.name = topic

    def __repr__(self):
        return self.name


class Comment(db.Model):
    # __tablename__ = 'Comment'
    __bind_key__ = 'online_learning'

    id = Column(Integer, primary_key=True)
    username = Column(String(20))
    title = Column(String(100))
    comment = Column(Text)
    visible = Column(Boolean)
    created_on = Column(DateTime)

    page_inst_id = Column(ForeignKey('entry.id'), nullable=True, index=True)
    page_inst = relationship('Entry', back_populates='comments')


    def __init__(self,page_inst,username="user",comment="comment",
                 visible=False,created_on=datetime.utcnow()):
        self.username=username
        self.comment=comment
        self.visible=visible
        self.created_on=created_on
        self.page_inst_id=page_inst.id

    def __str__(self):
        return self.page_inst.title

    def __repr__(self):
        return self.__str__()

class Entry(db.Model):
    __bind_key__ = 'online_learning'
    __tablename__ = 'entry'

    id = db.Column(db.Integer, primary_key=True)
    views = db.Column(db.Integer, default=0)

    title = db.Column(db.String(100),default='')
    slug = db.Column(db.String(100),default='', unique=True)
    content = db.Column(db.Text)
    published = db.Column(db.Boolean, index=True)
    timestamp = db.Column(DateTime,default=datetime.now, index=True)

    topics = relationship(u"Topic",
                          secondary=PageTopic.__table__,
                          backref=u"pagestopics", lazy='dynamic')
    tags = relationship(u"Tag",
                        secondary=PageTag.__table__,
                        backref=u"pagestags", lazy='dynamic')

    comments = db.relationship('Comment', back_populates='page_inst', lazy='dynamic')
    videos = db.relationship('Video', back_populates='page_inst', lazy='dynamic')

    def __init__(self,title="test",content="test",published=False):
        self.title = title
        self.content=content
        self.published=published
        return

    def __str__(self):
        return self.title

    def __repr__(self):
        return self.title

    @property
    def html_content(self):
        """
        Generate HTML representation of the markdown-formatted blog entry,
        and also convert any media URLs into rich media objects such as video
        players or images.
        """
        hilite = CodeHiliteExtension(linenums=False, css_class='highlight')
        extras = ExtraExtension()
        markdown_content = markdown(self.content, extensions=[hilite, extras])
        oembed_content = parse_html(
            markdown_content,
            oembed_providers,
            urlize_all=True,
            maxwidth=app.config['SITE_WIDTH'])
        return Markup(oembed_content)

    def save(self, *args, **kwargs):
        # Generate a URL-friendly representation of the entry's title.
        # if not self.slug:
        self.slug = re.sub('[^\w]+', '-', self.title.lower()).strip('-')
        # ret = super(Entry, self).save(*args, **kwargs)
        entry = Entry.query.filter_by(slug=self.slug)
        if entry.count()>0 and not(entry.first().id==self.id):
            ret=False
            i=1
            while Entry.query.filter_by(slug=self.slug).count()>0:
                self.slug = re.sub('[^\w]+', '-', self.title.lower()).strip('-') + "_" + str(i)
                i=i+1
        else:
            ret=True
            # Store search content.
            self.update_search_index()
        db.session.add(self)
        db.session.commit()
        return ret

    def update_search_index(self):
        # Create a row in the FTSEntry table with the post content. This will
        # allow us to use SQLite's awesome full-text search extension to
        # search our entries.
        exists = (FTSEntry
                  .select(FTSEntry.docid)
                  .where(FTSEntry.docid == self.id)
                  .exists())
        content = '\n'.join((self.title, self.content))
        if exists:
            (FTSEntry
             .update({FTSEntry.content: content})
             .where(FTSEntry.docid == self.id)
             .execute())
        else:
            FTSEntry.insert({
                FTSEntry.docid: self.id,
                FTSEntry.content: content}).execute()

        return


    @classmethod
    def public(cls):
        return Entry.query.filter_by(published = True)

    @classmethod
    def drafts(cls):
        return Entry.query.filter_by(published = False)

    @classmethod
    def search(cls, query):
        words = [word.strip() for word in query.split() if word.strip()]
        if not words:
            # Return an empty query.
            return Entry.query.filter_by(id = 0)
        else:
            search = ' '.join(words)

        # Query the full-text search index for entries matching the given
        # search query, then join the actual Entry data on the matching
        # search result.
        q=FTSEntry.select(FTSEntry.docid).where(FTSEntry.match(search)).order_by(FTSEntry.rank())
        docids=[]
        for e in q:
            docids.append(e.docid-1)
            print e.docid
        return db.session.query(Entry).filter(Entry.id.in_(docids))

        # return (Entry
        #         .select(Entry, FTSEntry.rank().alias('score'))
        #         .join(FTSEntry, on=(Entry.id == FTSEntry.docid))
        #         .where(
        #     FTSEntry.match(search) &
        #     (Entry.published == True))
        #         .order_by(SQL('score').desc()))

from playhouse.sqlite_ext import *
class FTSEntry(FTSModel):
    content = TextField()

    class Meta:
        database = database



# class FTSEntry(db.Model):#FTSModel):
#
#     __bind_key__ = 'online_learning'
#     __tablename__ = 'FTSEntry'
#
#     id = db.Column(db.Integer, primary_key=True)
#
#     entry_id = db.Column(db.Integer)
#     content = db.Column(db.Text)
#
#     # class Meta:
#     #     database = db


