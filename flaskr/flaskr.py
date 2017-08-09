#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sqlite3
from flask import Flask, request, session, g, \
    redirect, url_for, render_template, flash
from flask_uploads import UploadSet, configure_uploads, \
    IMAGES, patch_request_class
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import SubmitField, SelectField
from flaskr.tag_recognition.preprocess import getResizedImage
from flaskr.tag_recognition.json_analyze import json_result
from flaskr.tag_recognition.gcv_api import gcv_result

app = Flask(__name__)
app.config.from_object(__name__)

app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'flaskr.db'),
    SECRET_KEY='development key',
    USERNAME='admin',
    PASSWORD='admin'
))
app.config.from_envvar('FLASKR_SETTINGS', silent=True)


def connect_db():
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv


def get_db():
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db


@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()


def init_db():
    db = get_db()
    with app.open_resource('schema.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()


@app.cli.command('initdb')
def initdb_command():
    init_db()
    print('Initialized the database.')


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['username'] != app.config['USERNAME']:
            error = 'Invalid username'
        elif request.form['password'] != app.config['PASSWORD']:
            error = 'Invalid password'
        else:
            session['logged_in'] = True
            flash('You were logged in')
            return redirect(url_for('upload_file'))
    return render_template('login.html', error=error)


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You were logged out')
    return redirect(url_for('login'))


app.config['UPLOADED_PHOTOS_DEST'] = os.getcwd() + '/upload'
with open('.apikey', 'r') as f:
    app.config['API_KEY'] = f.read()
photos = UploadSet('photos', IMAGES)
configure_uploads(app, photos)
patch_request_class(app)  # set maximum file size, default is 16MB
id_rule_dict = {
    'BEAMS': [2, 2, 4, 3, 2, 2],
    'OWD': [12],
    'SHIPS': [3,2,4,4],
    'TML': [2,2,2,7],
    'UA': [4,3,4,4],
    'Sanyo': [5, 3, 2],
    'alcali': [11],
    'CONVERSE TOKYO': [11],
    'Liess': [11],
    'martinique': [11],
    'MENS MELROSE': [10],
    'Soffitto': [10],
    'Unknown13': [13]
}


def get_id_rule_choice(k):
    v = id_rule_dict[k]
    return k + ': ' + '-'.join(['X' * vi for vi in v])


class UploadForm(FlaskForm):
    photo = FileField(validators=[
        FileAllowed(photos, 'Only pictures are allowed'),
        FileRequired('Please select file！')])
    submit = SubmitField('Upload')
    select = SelectField(
        'ID Rule:',
        choices=[
            (0, get_id_rule_choice('Unknown13')),
            (1, get_id_rule_choice('BEAMS')),
            (2, get_id_rule_choice('OWD')),
            (3, get_id_rule_choice('SHIPS')),
            (4, get_id_rule_choice('TML')),
            (5, get_id_rule_choice('UA')),
            (6, get_id_rule_choice('Sanyo')),
            (7, get_id_rule_choice('alcali')),
            (8, get_id_rule_choice('CONVERSE TOKYO')),
            (9, get_id_rule_choice('Liess')),
            (10, get_id_rule_choice('martinique')),
            (11, get_id_rule_choice('MENS MELROSE')),
            (12, get_id_rule_choice('Soffitto'))
        ], default=0
    )


@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    form = UploadForm()
    entries = []
    if form.is_submitted() and form.photo.validate(form.photo.validators):
        file_dir = app.config['UPLOADED_PHOTOS_DEST']
        file_list = os.listdir(file_dir)
        allowed_ext = {'jpeg', 'jpg', 'png', 'bmp'}
        file_list = list(filter(lambda s: s.lower().split('.')[-1] \
                                          in allowed_ext, file_list))
        filename, fileext = os.path.splitext(form.photo.data.filename)
        filename = ''.join([filename, fileext.lower()])
        db = get_db()
        fetch_query = "select * from entries where title='" +\
                      filename.split('.')[0] + "';"
        cur = db.execute(fetch_query)
        entries = cur.fetchall()
        if filename not in file_list:
            filename = photos.save(form.photo.data)
        columns = ['title', 'ProductId', 'Origin',
                   'Part', 'Material', 'Percent',
                   'Filename', 'FullText']
        fname, fext = os.path.splitext(filename)
        img_resized = getResizedImage(file_dir + '/' + fname + fext)
        img_resized.save(file_dir + '/' + fname + '_maxHeight600' + fext)
        del img_resized
        fname_resized = fname + '_maxHeight600'
        fname_json = fname_resized + fext + '.json'
        if fname_json not in os.listdir(file_dir):
            gcv_result(file_dir + '/' + fname_resized + fext,
                       api_key=app.config['API_KEY'])
        res = json_result(fname_json, [3, 3, 3, 3])
        query_excuted = 'replace into entries (' +\
                        ','.join(columns) +\
                        ') values (?, ?, ?, ?, ?, ?, ?, ?)'
        db.execute(query_excuted,
                   [fname] + [res['ID'][1],
                              ', '.join(res['Origin']),
                              ', '.join(res['Part']),
                              ', '.join(res['Material']),
                              ', '.join(res['Percent']),
                              filename,
                              res['FullText']])
        db.commit()
        file_url = photos.url(filename)
        cur = db.execute(fetch_query)
        entries = cur.fetchall()
        db.commit()
    else:
        file_url = None
    return render_template('upload.html',
                           form=form,
                           file_url=file_url,
                           entries=entries)
