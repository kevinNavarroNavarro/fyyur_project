#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#
from enum import unique
import json
from os import abort
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from wtforms.validators import Length
from forms import *
from flask_migrate import Migrate
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)

migrate = Migrate(app, db)

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#


class Show(db.Model):
    __tablename__ = 'shows'

    venue_id = db.Column(db.Integer, db.ForeignKey(
        'venues.id'), primary_key=True)
    artist_id = db.Column(db.Integer, db.ForeignKey(
        'artists.id'), primary_key=True)
    start_time = db.Column(db.DateTime, primary_key=True)


class Venue(db.Model):
    __tablename__ = 'venues'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(), nullable=False, unique=True)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    genres = db.Column(db.ARRAY(db.String()), nullable=False)
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120), nullable=False)
    website = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean, nullable=False, default=False)
    seeking_description = db.Column(db.String(120))

    shows = db.relationship('Show', backref='venue', lazy=True)

    def __repr__(self):
      return f"<Venue {self.id}>"


class Artist(db.Model):
    __tablename__ = 'artists'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(), nullable=False, unique=True)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120), nullable=False)
    genres = db.Column(db.ARRAY(db.String()), nullable=False)
    image_link = db.Column(db.String(500), unique=True)
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean, nullable=False, default=False)
    seeking_description = db.Column(db.String(120))

    shows = db.relationship('Show', backref='artist', lazy=True)

    def __repr__(self):
      return f"<Artis {self.id}"

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#


def format_datetime(value, format='medium'):
    date = dateutil.parser.parse(value)
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format, locale='en')


app.jinja_env.filters['datetime'] = format_datetime

# #----------------------------------------------------------------------------#
# # Controllers.
# #----------------------------------------------------------------------------#


@app.route('/')
def index():
    return render_template('pages/home.html')

# search past shows by venue_id
def past_shows_by_venue(venue):
    past_shows = []

    shows = Show.query.filter_by(venue_id=venue.id).all()

    for show in shows:
        if show.start_time < datetime.now():
            artist = Artist.query.filter_by(id=show.artist_id).one()
            past_shows.append({
                "artist_id": artist.id,
                "artist_name": artist.name,
                "artist_image_link": artist.image_link,
                "start_time": str(show.start_time)
            })

    return past_shows

# search upcoming shows by venue_id
def upcoming_shows_by_venue(venue):
    upcoming_shows = []

    shows = Show.query.filter_by(venue_id=venue.id).all()

    for show in shows:
        if show.start_time >= datetime.now():
            artist = Artist.query.filter_by(id=show.artist_id).one()
            upcoming_shows.append({
                "artist_id": artist.id,
                "artist_name": artist.name,
                "artist_image_link": artist.image_link,
                "start_time": str(show.start_time)
            })

    return upcoming_shows

# search upcoming shows by artist_id
def upcoming_shows_by_artist(artist):
    upcoming_shows = []

    shows = Show.query.filter_by(artist_id=artist.id).all()

    for show in shows:
        if show.start_time >= datetime.now():
            venue = Venue.query.filter_by(id=show.venue_id).one()
            upcoming_shows.append({
                "venue_id": venue.id,
                "venue_name": venue.name,
                "venue_image_link": venue.image_link,
                "start_time": str(show.start_time)
            })

    return upcoming_shows

 # search past shows by artist_id
def past_shows_by_artist(artist):
    past_shows = []

    shows = Show.query.filter_by(artist_id=artist.id).all()

    for show in shows:
        if show.start_time < datetime.now():
            venue = Venue.query.filter_by(id=show.venue_id).one()
            past_shows.append({
                "venue_id": venue.id,
                "venue_name": venue.name,
                "venue_image_link": venue.image_link,
                "start_time": str(show.start_time)
            })

    return past_shows
#  Venues
#  ----------------------------------------------------------------

# View venues
@app.route('/venues')
def venues():
    venues = Venue.query.all()

    data = []
    locations = set()

    # Take locations
    for venue in venues:
        locations.add((venue.city, venue.state))

    # Create data structured and add city-state
    for location in locations:
        data.append({
            "city": location[0],
            "state": location[1],
            "venues": []
        })

    # add others data like venue.id - venue.name - venue.num_upcoming_shows
    for venue in venues:
        num_upcoming_shows = len(upcoming_shows_by_venue(venue))
        for location_venue in data:
            if venue.city == location_venue['city'] and venue.state == location_venue["state"]:
                location_venue["venues"].append({
                    "id": venue.id,
                    "name": venue.name,
                    "num_upcoming_shows": num_upcoming_shows
                })

    return render_template('pages/venues.html', areas=data)

# Search venue by name or character
@app.route('/venues/search', methods=['POST'])
def search_venues():

    response = []
    data = []
    search_term = request.form.get('search_term', '')
    venues = Venue.query.filter(Venue.name.ilike(f'%{search_term}%'))

    for venue in venues:
        num_upcoming_shows = len(upcoming_shows_by_venue(venue))
        data.append({
            "id": venue.id,
            "name": venue.name,
            "num_upcoming_shows": num_upcoming_shows
        })

    response.append({
        "venue_count": venues.count(),
        "data": data
    })

    return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

# Show venue by Id
@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):

    data = []
    venue = Venue.query.filter_by(id=venue_id).one()

    data.append({
        "id": venue.id,
        "name": venue.name,
        "genres": venue.genres,
        "address": venue.address,
        "city": venue.city,
        "state": venue.state,
        "phone": venue.phone,
        "website": venue.website,
        "facebook_link": venue.facebook_link,
        "seeking_talent": venue.seeking_talent,
        "seeking_description": venue.seeking_description,
        "image_link": venue.image_link,
        "past_shows": past_shows_by_venue(venue),
        "upcoming_shows": upcoming_shows_by_venue(venue),
        "past_shows_count": len(past_shows_by_venue(venue)),
        "upcoming_shows_count": len(upcoming_shows_by_venue(venue))
    })

    return render_template('pages/show_venue.html', venue=data)

#  Create Venue
@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)

# Create new Venue
@app.route('/venues/create', methods=['POST'])
def create_venue_submission():

    try:
        form = VenueForm()
        venue = Venue(
                      name=form.name.data,
                      city=form.city.data,
                      state=form.state.data,
                      address=form.address.data,
                      phone=form.phone.data,
                      image_link=form.image_link.data,
                      genres=form.genres.data,
                      facebook_link=form.facebook_link.data,
                      seeking_description=form.seeking_description.data,
                      website=form.website_link.data,
                      seeking_talent=form.seeking_talent.data)
        db.session.add(venue)
        db.session.commit()
        flash('Venue ' + request.form['name'] + ' was successfully listed!')
    except():
        db.session.rollback()
        flash('An error occurred. Venue ' +
              request.form['name'] + ' could not be listed.')
    finally:
        db.session.close()

    return render_template('pages/home.html')

# delete venues by id
@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    try:
        Venue.query.filter_by(id=venue_id).delete()
        db.session.commit()
    except:
        db.session.rollback()
    finally:
        db.session.close()

    return redirect(url_for('index'))


#  Artists
#  ----------------------------------------------------------------
#View artist
@app.route('/artists')
def artists():
    artists = Artist.query.all()
    data = []

    # add data
    for artist in artists:
        data.append({
            "id": artist.id,
            "name": artist.name,
        })

    return render_template('pages/artists.html', artists=data)

# Search artists by name or character
@app.route('/artists/search', methods=['POST'])
def search_artists():
    response = []
    data = []

    search_term = request.form.get('search_term', '')
    artists = Artist.query.filter(Artist.name.ilike(f'%{search_term}%'))

    for artist in artists:
        num_upcoming_shows = len(upcoming_shows_by_artist(artist))
        data.append({
            "id": artist.id,
            "name": artist.name,
            "num_upcoming_shows": num_upcoming_shows
        })

    response.append({
        "count": artists.count(),
        "data": data
    })

    return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

# Show venue by Id
@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):

    data = []
    artist = Artist.query.filter_by(id=artist_id).one()

    data.append({
        "id": artist.id,
        "name": artist.name,
        "genres": artist.genres,
        "city": artist.city,
        "state": artist.state,
        "phone": artist.phone,
        "website": artist.website,
        "facebook_link": artist.facebook_link,
        "seeking_venue": artist.seeking_venue,
        "seeking_description": artist.seeking_description,
        "image_link": artist.image_link,
        "past_shows": past_shows_by_artist(artist),
        "upcoming_shows": upcoming_shows_by_artist(artist),
        "past_shows_count": len(past_shows_by_artist(artist)),
        "upcoming_shows_count": len(upcoming_shows_by_artist(artist))
    })

    return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------

#Edit artist by id
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    form = ArtistForm()
    artist = Artist.query.get(artist_id)

    artist = {
        "id": artist.id,
        "name": artist.name,
        "genres": artist.genres,
        "city": artist.city,
        "state": artist.state,
        "phone": artist.phone,
        "website": artist.website,
        "facebook_link": artist.facebook_link,
        "seeking_venue": artist.seeking_venue,
        "seeking_description": artist.seeking_description,
        "image_link": artist.image_link
    }

    return render_template('forms/edit_artist.html', form=form, artist=artist)

#Edit artist by id
@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    form = ArtistForm()
    artist = Artist.query.get(artist_id)
    try:
        artist.name = form.name.data
        artist.genres = form.genres.data
        artist.city = form.city.data
        artist.state = form.state.data
        artist.phone = form.phone.data
        artist.website = form.website_link.data
        artist.facebook_link = form.facebook_link.data
        artist.seeking_venue = form.seeking_venue.data
        artist.seeking_description = form.seeking_description.data
        artist.image_link = form.image_link.data

        db.session.commit()
    except:
        db.session.rollback()
    finally:
        db.session.close()

    return redirect(url_for('show_artist', artist_id=artist_id))

#Edit venues by id
@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    form = VenueForm()

    venue = Venue.query.get(venue_id)

    venue = {
        "id": venue.id,
        "name": venue.name,
        "genres": venue.genres,
        "address": venue.address,
        "city": venue.city,
        "state": venue.state,
        "phone": venue.phone,
        "website": venue.website,
        "facebook_link": venue.facebook_link,
        "seeking_talent": venue.seeking_talent,
        "seeking_description": venue.seeking_description,
        "image_link": venue.image_link
    }

    return render_template('forms/edit_venue.html', form=form, venue=venue)

#Edit venues by id
@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    form = VenueForm()
    venue = Venue.query.get(venue_id)
    try:
        venue.name = form.name.data
        venue.genres = form.genres.data
        venue.city = form.city.data
        venue.state = form.state.data
        venue.address = form.address.data
        venue.phone = form.phone.data
        venue.website = form.website_link.data
        venue.facebook_link = form.facebook_link.data
        venue.seeking_talent = form.seeking_talent.data
        venue.seeking_description = form.seeking_description.data
        venue.image_link = form.image_link.data

        db.session.commit()
    except:
        db.session.rollback()
    finally:
        db.session.close()

    return redirect(url_for('show_venue', venue_id=venue_id))


#  Create Artist
@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()

    return render_template('forms/new_artist.html', form=form)

# Create new Artist
@app.route('/artists/create', methods=['POST'])
def create_artist_submission():

    try:
        form = ArtistForm()
        artist = Artist(
                        name=form.name.data,
                        city=form.city.data,
                        state=form.state.data,
                        phone=form.phone.data,
                        image_link=form.image_link.data,
                        genres=form.genres.data,
                        facebook_link=form.facebook_link.data,
                        seeking_description=form.seeking_description.data,
                        website=form.website_link.data,
                        seeking_venue=form.seeking_venue.data)
        db.session.add(artist)
        db.session.commit()
        flash('Artist ' + request.form['name'] + ' was successfully listed!')
    except():
        db.session.rollback()
        flash('An error occurred. Artist ' +
              request.form['name'] + ' could not be listed.')
    finally:
        db.session.close()

    return render_template('pages/home.html')

# Delete artists by id
@app.route('/artist/<artist_id>', methods=['DELETE'])
def delete_artist(artist_id):
    try:
        Artist.query.filter_by(id=artist_id).delete()
        db.session.commit()
    except:
        db.session.rollback()
    finally:
        db.session.close()

    return redirect(url_for('index'))


#  Shows
#  ----------------------------------------------------------------
#View Shows
@app.route('/shows')
def shows():

    shows = Show.query.all()
    data = []

    # add data
    for show in shows:
        artist = Artist.query.get(show.artist_id)
        venue = Venue.query.get(show.venue_id)
        data.append({
            "venue_id": show.venue_id,
            "venue_name": venue.name,
            "artist_id": show.artist_id,
            "artist_name": artist.name,
            "artist_image_link": artist.image_link,
            "start_time": str(show.start_time)
        })

    return render_template('pages/shows.html', shows=data)


@app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)

#Create new Show
@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    try:
        form = ShowForm()
        show = Show(
                    artist_id=form.artist_id.data,
                    venue_id=form.venue_id.data,
                    start_time=form.start_time.data
        )
        db.session.add(show)
        db.session.commit()
        flash('Show was successfully listed!')
    except():
        db.session.rollback()
        flash('An error occurred. Show could not be listed.')
    finally:
        db.session.close()
   
    return render_template('pages/home.html')


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
