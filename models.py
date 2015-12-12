#!/usr/bin/env python
# coding: utf-8
"""
    models.py
    ~~~~~~~~~~

"""
import os
import re
import json
import base64
import hashlib
import markdown2

from sqlalchemy_wrapper import SQLAlchemy
from sqlalchemy import or_

import config


db = SQLAlchemy(config.SQLALCHEMY_DATABASE_URI,
                pool_recycle=config.SQLALCHEMY_POOL_RECYCLE)


class User(db.Model):

    """setting = {
    page
    }
    """

    __tablename__ = "user"

    username = db.Column(db.String(20), primary_key=True)
    password = db.Column(db.String(256))
    salt = db.Column(db.String(20))
    config = db.Column(db.Text)

    @classmethod
    def get_config(cls):
        user = cls.query(cls).first()
        if user and user.config:
            return json.loads(user.config)
        return None

    @classmethod
    def get_by_name(cls, username):
        return cls.query(cls).filter_by(username=username).first()

    @classmethod
    def get_one(cls):
        return cls.query(cls).first()

    def validate(self, password):
        sha512 = hashlib.sha512()
        sha512.update(self.salt)
        sha512.update(password)

        hashed_password = base64.urlsafe_b64encode(sha512.digest())
        return hashed_password == self.password

    def save(self):
        db.session.add(self)
        db.session.commit()


class Post(db.Model):
    __tablename__ = "post"
    post_id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(512),  primary_key=False)
    title = db.Column(db.String(512))
    # raw_content =content.strip_HTML_tags()
    raw_content = db.Column(db.Text)
    content = db.Column(db.Text)
    keywords = db.Column(db.String(256))
    metacontent = db.Column(db.String(256))
    create_time = db.Column(db.DateTime)
    update_time = db.Column(db.DateTime)
    # tag seperated by comma
    tags = db.Column(db.String(256))
    # editor html or markdown
    editor = db.Column(db.String(10))
    allow_visit = db.Column(db.Boolean)
    allow_comment = db.Column(db.Boolean)
    need_key = db.Column(db.Boolean)
    is_original = db.Column(db.Boolean)
    num_lookup = db.Column(db.Integer)

    def __init__(self):
        """setup default value
        """
        self.url = ""
        self.title = ""
        self.content = ""
        self.keywords = ""
        self.metacontent = ""
        self.tags = ""
        self.allow_visit = False
        self.allow_comment = True
        self.need_key = False
        self.is_original = True
        self.num_lookup = 0

    @classmethod
    def get_page(cls, offset, limit, **kargs):
        """If pubic_only == False , return posts even if allow_visit = False
        """
        query = cls.query(cls)
        for key in kargs:
            query = query.filter(cls.__dict__[key] == kargs[key])

        query = query.order_by(cls.post_id.desc())
        return query.limit(limit).offset(offset).all()

    @classmethod
    def count(cls, **kargs):
        query = cls.query(cls)
        for key in kargs:
            query = query.filter(cls.__dict__[key] == kargs[key])
        return query.count()

    @classmethod
    def get_by_id(cls, post_id, public_only=True):
        if public_only is True:
            return cls.query(cls).filter_by(
                allow_visit=True, post_id=post_id).first()
        else:
            return cls.query(cls).filter_by(
                post_id=post_id).first()

    @classmethod
    def get_by_url(cls, url, public_only=True):
        if public_only is True:
            return cls.query(cls).filter_by(url=url, allow_visit=True).first()
        else:
            return cls.query(cls).filter_by(url=url).first()

    @classmethod
    def tag_search(cls, keyword, offset, limit):
        if not keyword:
            return []
        return cls.query(cls).filter_by(allow_visit=True).\
            filter(cls.tags.like("%,"+keyword+",%")).\
            order_by(cls.post_id.desc()).offset(offset).limit(limit).all()

    @classmethod
    def tag_search_count(cls, keyword):
        if not keyword:
            return 0
        return cls.query(cls).filter_by(allow_visit=True).\
            filter(cls.tags.like("%,"+keyword+",%")).count()

    @classmethod
    def text_search(cls, words, offset, limit):
        if len(words) == 0 or len(words) > 5:
            return []
        query = cls.query(cls).filter_by(allow_visit=True)
        for word in words:
            query = query.filter(or_(
                cls.raw_content.like("%" + word + "%"),
                cls.title.like("%" + word + "%")
            ))
        return query.order_by(
            cls.post_id.desc()).offset(offset).limit(limit).all()

    @classmethod
    def text_search_count(cls, words):
        if len(words) == 0 or len(words) > 5:
            return 0
        query = cls.query(cls).filter_by(allow_visit=True)
        for word in words:
            query = query.filter(or_(
                cls.raw_content.like("%" + word + "%"),
                cls.title.like("%" + word + "%")
            ))
        return query.count()

    @classmethod
    def get_last_x(cls, limit):
        return cls.query(cls).filter_by(allow_visit=True).\
            order_by(cls.post_id.desc()).all()

    @classmethod
    def gen_raw_content(cls, content, editor):
        """Remove unused mark up tags, so that mysql is able to do text search
        a silly way to convert MarkDown to plain text:
            1. MarkDown to HTML
            2. HTML to text
        """
        if editor == "markdown":
            content = markdown2.markdown(content)
            return re.sub('<[^<]+?>', "", content)
        elif editor == "html":
            return re.sub('<[^<]+?>', "", content)

    def get_tags(self):
        taglist = self.tags.split(",")
        taglist = [tag for tag in taglist if tag]
        return taglist

    def to_tags(self, taglist):
        tags = ",".join(taglist)
        return "," + tags + ","

    @property
    def html_content(self):
        if self.editor == "html":
            return self.content
        elif self.editor == "markdown":
            data = markdown2.markdown(self.content)
            return data
        else:
            return ""

    @property
    def plain_content(self):
            return self.raw_content

    def update_tags(self, new_string):
        """ Post.tags is a string in which multi tags are seperated by ",", we
        will seperate them and save to database. Use this method when you want
        to update or create a post
        Input:
            "abc,abc, abc,123"
        Output:
            ",abc,123,"
            sum for abc and 123 will increase by 1 ,We append comma before
            and after "abc,123", so we can do the follwoing mysql search
                `select * from tag where name like '%,tagname,%'`
        """
        duptags = new_string.split(",")
        newtags = set()
        for item in duptags:
            if item.strip() and item.strip() not in newtags:
                newtags.add(item.strip())

        oldtags = self.get_tags()
        addlist = [item for item in newtags if item not in oldtags]
        minuslist = [item for item in oldtags if item not in newtags]

        Tag.add(addlist)
        Tag.minus(minuslist)

        self.tags = self.to_tags(newtags)
        return self.tags

    def delete_tags(self):
        """Set Post.tags to "", this function will also deduce the count in Tag
        """
        return self.update_tags("")

    def delete_comments(self):
        commentlist = Comment.get_by_post_id(self.post_id)
        for comment in commentlist:
            comment.delete()

    def save(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        self.delete_tags()
        self.delete_comments()
        db.session.delete(self)
        db.session.commit()


class Tag(db.Model):
    __tablename__ = "tag"

    name = db.Column(db.String(64), primary_key=True)
    count = db.Column(db.Integer)

    def __init__(self, name, count=1):
        self.name = name
        self.count = count

    @classmethod
    def get_one(cls, name):
        return cls.query(cls).filter_by(name=name).first()

    @classmethod
    def add(cls, taglist):
        """never use this method directly , use Post.update_tags instead
        """
        for item in taglist:
            if item:
                tag = Tag.get_one(item)
                if tag:
                    tag.count += 1
                    # items in uppercase and lowercase are treated as one tag.
                    # update name to get the most recent version
                    tag.name = item
                else:
                    tag = Tag(name=item)
                    db.session.add(tag)
        db.session.commit()

    @classmethod
    def minus(cls, taglist):
        for item in taglist:
            tag = Tag.get_one(item)
            if tag:
                if tag.count > 1:
                    tag.count -= 1
                else:
                    db.session.delete(tag)

        db.session.commit()

    @classmethod
    def get_first_X(cls, count):
        return cls.query(cls).order_by(cls.count.desc()).limit(count).all()


class Comment(db.Model):
    __tablename__ = "comment"
    comment_id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer)
    url = db.Column(db.String(64))
    email = db.Column(db.String(64))
    nickname = db.Column(db.String(20))
    content = db.Column(db.String(1024))
    refid = db.Column(db.Integer)
    to = db.Column(db.String(20))
    create_time = db.Column(db.DateTime)
    ip = db.Column(db.String(64))
    website = db.Column(db.String(64))

    @classmethod
    def get_by_post_id(cls, post_id):
        result = cls.query(cls).filter_by(post_id=post_id).all()
        for i in range(len(result)):
            result[i].content = result[i].content.replace(" ", "&nbsp;")
            result[i].content = result[i].content.replace("\n", "<br>")
        return result

    @classmethod
    def get_by_id(cls, comment_id):
        return Comment.query.filter_by(comment_id=comment_id).first()

    @classmethod
    def get_by_url(cls, url):
        post = Post.get_by_url(url)
        if post:
            return cls.get_by_post_id(post.post_id)
        else:
            return None

    @classmethod
    def count(cls, post_id=None):
        if post_id is None:
            return cls.query(cls).count()
        else:
            return cls.query(cls).filter_by(post_id=post_id).count()

    @classmethod
    def get_last_X(cls, count):
        return cls.query(cls).order_by(cls.comment_id.desc()).limit(count).all()

    @classmethod
    def get_page(cls, offset, limit, post_id=-1):
        if post_id == -1:
            commentlist = cls.query(cls).order_by(cls.comment_id.desc()).\
                offset(offset).limit(limit).all()
        else:
            commentlist = cls.query(cls).order_by(cls.comment_id.desc()).\
                filter_by(post_id=post_id).offset(offset).limit(limit).all()
        return commentlist

    def save(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()


class Link(db.Model):
    __tablename__ = "link"
    link_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    href = db.Column(db.String(1024))
    description = db.Column(db.String(64))
    create_time = db.Column(db.DateTime)
    display = db.Column(db.Boolean)

    @classmethod
    def count(cls):
        return cls.query(cls).count()

    @classmethod
    def get_page(cls, offset, limit):
        return cls.query(cls).offset(offset).limit(limit).all()

    @classmethod
    def get_X(cls, limit):
        return cls.query(cls).filter_by(display=True).limit(limit).all()

    @classmethod
    def get_by_id(cls, link_id):
        return cls.query(cls).filter_by(link_id=int(link_id)).first()

    @classmethod
    def get_by_href(cls, href):
        return cls.query(cls).filter_by(href=href).first()

    def save(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()


class Media(db.Model):
    fileid = db.Column(db.String(64), primary_key=True)
    filename = db.Column(db.String(64))
    # For a give filename , there could be multi file exits
    version = db.Column(db.Integer)
    content_type = db.Column(db.String(32))
    size = db.Column(db.Integer)
    create_time = db.Column(db.DateTime)
    display = db.Column(db.Boolean)

    @classmethod
    def count(cls):
        return cls.query(cls).count()

    @classmethod
    def get_page(cls, offset, limit):
        medialist = cls.query(cls).order_by(cls.create_time.desc()).\
            offset(offset).limit(limit).all()
        return medialist

    @classmethod
    def get_by_id(cls, fileid):
        return cls.query(cls).filter_by(fileid=fileid).first()

    @classmethod
    def get_by_fileid(cls, fileid):
        return cls.query(cls).filter_by(fileid=fileid).first()

    @classmethod
    def get_version(cls, filename):
        media = cls.query(cls).filter_by(filename=filename).\
            order_by(cls.create_time.desc()).first()

        if media:
            return media.version + 1
        else:
            return 0

    @classmethod
    def new_local_filename(cls, filename, version):
        """for given filename ,return a filename that can be saved to disk
            input: abc.jpg
            output:

        """
        return "f" + str(version) + filename

    def filepath(self, upload_folder):
        return os.path.join(upload_folder, self.local_filename)

    @property
    def local_filename(self):
        return "f"+str(self.version)+self.filename

    def save(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        import config
        filepath = self.filepath(config.UPLOAD_FOLDER)
        try:
            os.remove(filepath)
        except Exception:
            pass
        db.session.delete(self)
        db.session.commit()


def gen_sidebar(config):
    rr = {
        "taglist": None,
        "commentlist": None,
        "linklist": None
    }

    taglist = Tag.get_first_X(config["TAG_COUNT"])
    rr["taglist"] = taglist
    commentlist = Comment.get_last_X(config["COMMENT_COUNT"])
    rr["commentlist"] = commentlist
    linklist = Link.get_X(config["LINK_COUNT"])
    rr["linklist"] = linklist

    announce = Post.get_by_id(config["ANNOUNCE_ID"])
    rr["announce"] = announce
    rr["announce_length"] = config["ANNOUNCE_LENGTH"]
    return rr


def export_all():
    """export all blog data"""
    postlist = Post.query(Post).all()
    linklist = Link.query(Link).all()
    medialist = Media.query(Media).all()

    ex_post = []
    for post in postlist:
        # Back up all comments
        ex_comment = []
        commentlist = Comment.get_by_post_id(post.post_id)
        for comment in commentlist:
            ex_comment.append({
                "comment_id": comment.comment_id,
                "post_id": comment.post_id,
                "url": comment.url,
                "email": comment.email,
                "nickname": comment.nickname,
                "content": comment.content,
                "to": comment.to,
                "refid": comment.refid,
                "create_time": int(comment.create_time.strftime("%s")),
                "ip": comment.ip,
                "website": comment.website
            })

        ex_post.append({
            "post_id": post.post_id,
            "url": post.url,
            "title": post.title,
            "content": post.content,
            "keywords": post.keywords,
            "metacontent": post.metacontent,
            "create_time": int(post.create_time.strftime("%s")),
            "update_time": int(post.update_time.strftime("%s")),
            "tags": post.tags,
            "allow_visit": post.allow_visit,
            "allow_comment": post.allow_comment,
            "need_key": post.need_key,
            "is_original": post.is_original,
            "num_lookup": post.num_lookup,
            "commentlist": ex_comment
        })

    # Backup all links
    ex_link = []
    for link in linklist:
        ex_link.append({
            "link_id": link.link_id,
            "name": link.name,
            "href": link.href,
            "description": link.description,
            "create_time": int(link.create_time.strftime("%s")),
            "display": link.display,
        })

    # Backup all media
    ex_media = []
    for media in medialist:
        ex_media.append({
            "fileid": media.fileid,
            "filename": media.filename,
            "version": media.version,
            "content_type": media.content_type,
            "size": media.size,
            "create_time": int(media.create_time.strftime("%s")),
            "display": media.display
        })

    return json.dumps(
        {
            "links": ex_link,
            "posts": ex_post,
            "medias": ex_media
        },
        sort_keys=True,
        indent=4,
        separators=(',', ': '))
