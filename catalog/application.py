# -*- coding: utf-8 -*-

from models import Base, Vinyl, Style

from flask import Flask, request, render_template, redirect, url_for, flash
from flask import make_response, jsonify
from flask import session as login_session

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import relationship, sessionmaker

from flask.ext.httpauth import HTTPBasicAuth
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError

import httplib2
import json
import requests
import random
import string

auth = HTTPBasicAuth()

engine = create_engine('sqlite:///myvinyls.db', encoding="utf-8")

Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()
app = Flask(__name__)

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "La Discotheque"


# GOOGLE AUTHENTICATION
@app.route('/gconnect', methods=['POST'])
def gconnect():

    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token={}'
           .format(access_token))
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already ' +
                                            'connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    welcome = True
    styles = session.query(Style).all()

    return render_template('login.html', welcome=welcome, styles=styles)


# DISCONNECT - Revoke a current user's token and reset their login_session
@app.route('/gdisconnect')
def gdisconnect():
    access_token = login_session.get('access_token')
    if access_token is None:
        flash("You are not signed in as any user.")
        return redirect('/')
    url = 'https://accounts.google.com/o/oauth2/revoke?token={}'.format(
        login_session['access_token'])
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        flash("You've been successfully disconnected")
        return redirect('/')
    else:
        flash("Failed to disconnect user.")
        return redirect('/')


@app.route('/')
def homePage():
    if request.method == "GET":
        vinyls = session.query(Vinyl).order_by(Vinyl.id.desc()).limit(9)
        styles = session.query(Style).all()
        pagetitle = 'Last albums added:'
        return render_template("index.html", vinyls=vinyls, styles=styles, pagetitle=pagetitle)

@app.route('/allalbums')
def allAlbums():
    if request.method == "GET":
        vinyls = session.query(Vinyl).order_by(Vinyl.name).all()
        styles = session.query(Style).all()
        pagetitle = 'These are all your albums:'
        return render_template("index.html", vinyls=vinyls, styles=styles, pagetitle=pagetitle)


@app.route('/styles/<style>/')
def styleAlbums(style):
    if request.method == "GET":
        styles = session.query(Style).all()
        style_filtered = session.query(Style).filter_by(name=style).all()[0]
        vinyls = session.query(Vinyl).filter(Vinyl.styles.contains(
            style_filtered)).all()
        if vinyls == []:
            return "there are no vinyls"
        else:
            pagetitle = style_filtered.name
            return render_template('index.html', vinyls=vinyls, styles=styles, pagetitle=pagetitle)


@app.route('/add', methods=['GET', 'POST'])
def addAlbum():
    if 'username' not in login_session:
        return redirect('/login')

    if request.method == "GET":
        styles = session.query(Style).all()
        return render_template('addAlbum.html', styles=styles)

    elif request.method == "POST":
        name = request.form['name']
        band = request.form['band']
        year = request.form['year']
        imglink = request.form['imglink']
        tracklist = request.form['tracklist']
        if request.form.getlist('style') != []:
            styles = request.form.getlist('style')
            print(styles)
        else:
            styles = {request.form['styleAdd']}
            print(styles)
            if styles == [u'']:
                print("estavazio")
                styles.append("Outros")
        new_album = Vinyl(name=name, band=band, year=year, imglink=imglink,
                          tracklist=tracklist)

        # adds styles to the album
        for style in styles:
            try:
                querystyle = session.query(Style).filter_by(name=style).one()
                new_album.styles.append(querystyle)
            # if the style does not exist, creates it
            except:
                newstyle = Style(name=style)
                session.add(newstyle)
                session.commit
                new_album.styles.append(newstyle)
        # adds album to db
        session.add(new_album)
        session.commit()
        flash("You've just sucessfully added '{}' to the database.".format(new_album.name))
        return redirect('/')


@app.route('/JSON')
def jsonAlbums():
    albums = session.query(Vinyl).all()
    return jsonify(album=[i.serialize for i in albums])


@app.route('/albums/<int:id>')
def albumName(id):
    if request.method == "GET":
        album = session.query(Vinyl).filter_by(id=id).one()
        styles = session.query(Style).all()
        if not album:
            return "there are no vinyls with that name. Sorry"
        else:
            return render_template('albumName.html', album=album,
                                   styles=styles)


@app.route('/albums/<int:id>/JSON')
def jsonAlbumName(id):
    album = session.query(Vinyl).filter_by(id=id).one()
    return jsonify(album=album.serialize)


@app.route('/albums/edit/<int:id>', methods=['GET', 'POST'])
def editAlbum(id):
    if 'username' not in login_session:
        return redirect('/login')
    styles = session.query(Style).all()
    old_album = session.query(Vinyl).filter_by(id=id).one()
    if request.method == "GET":
        return render_template('editAlbum.html', album=old_album,
                               styles=styles)
    elif request.method == "POST":
        edit_album = old_album
        edit_album.name = request.form['name']
        edit_album.band = request.form['band']
        edit_album.year = request.form['year']
        edit_album.imglink = request.form['imglink']
        edit_album.tracklist = request.form['tracklist']
        session.add(edit_album)
        session.commit()
        flash("You've just sucessfully edited '{}'.".format(old_album.name))
        return redirect('/')


@app.route('/albums/delete/<int:id>', methods=['GET', 'POST'])
def deleteAlbum(id):
    if 'username' not in login_session:
        return redirect('/login')
    album = session.query(Vinyl).filter_by(id=id).one()
    if request.method == "GET":
        styles = session.query(Style).all()
        return render_template('deleteAlbum.html', album=album.name, styles=styles)
    elif request.method == "POST":
        session.delete(album)
        session.commit()

        # CHECKING TO SEE THERE IS NO VINYLS UNDER SPECIFIC STYLE.
        # IF THERE ARE, THEY'RE ERASED
        for style in album.styles:
            styleCheck = session.query(Style).filter_by(name=style.name).one()
            try:
                session.query(Vinyl).filter(Vinyl.styles.contains(
                                            styleCheck)).one()
            except:
                session.delete(styleCheck)
                session.commit()
        flash("You've just sucessfully deleted '{}'.".format(album.name))
        return redirect('/')


@app.route('/login')
def login():
    state = ''.join(random.choice(string.ascii_uppercase +
                                  string.digits) for x in xrange(32))
    login_session['state'] = state
    styles = session.query(Style).all()
    return render_template('login.html', STATE=state, styles=styles)


if __name__ == '__main__':
    app.secret_key = 'this_is_secret'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
