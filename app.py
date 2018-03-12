from playhouse.sqlite_ext import *


from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from playhouse.flask_utils import FlaskDB, get_object_or_404, object_list


import dbconfig

app = Flask(__name__,template_folder='templates')


# Create dummy secrey key so we can use sessions
app.config['SECRET_KEY'] = '123456790'

# iaas_uri = '{}://{}:{}@{}/{}' \
#         .format('mysql+pymysql',
#                 'cenv0594',
#                 'keVRN7tVkP4DxR2sAlqq',
#                 'IAAS-gateway.ouce.ox.ac.uk:1564',
#                 'online_learning')

iaas_uri = '{}://{}:{}@{}/{}' \
        .format(dbconfig.db_engine,
                dbconfig.db_user,
                dbconfig.db_password,
                dbconfig.db_hostname,
                'online_learning')

app.config['SQLALCHEMY_DATABASE_URI'] =iaas_uri
app.config['DATABASE_URL'] =iaas_uri

SQLALCHEMY_BINDS={'online_learning':iaas_uri}
app.config['SQLALCHEMY_BINDS'] =SQLALCHEMY_BINDS
onlinelearningdb = SQLAlchemy(app)
db = onlinelearningdb


# The playhouse.flask_utils.FlaskDB object accepts database URL configuration.
APP_DIR = os.path.dirname(os.path.realpath(__file__))
app.config['DATABASE'] = 'sqliteext:///%s' % os.path.join(APP_DIR, 'blog.db')
DEBUG = False


# FlaskDB is a wrapper for a peewee database that sets up pre/post-request
# hooks for managing database connections.
flask_db = FlaskDB(app)

# The `database` is the actual peewee database, as opposed to flask_db which is
# the wrapper.
database = flask_db.database

app.config['UPLOAD_FOLDER'] = dbconfig.upload_folder

# Blog configuration values.

# You may consider using a one-way hash to generate the password, and then
# use the hash again in the login view to perform the comparison. This is just
# for simplicity.
app.config['ADMIN_PASSWORD'] = 'secret'
# app.config['APP_DIR'] = os.path.dirname(os.path.realpath(__file__))

# The playhouse.flask_utils.FlaskDB object accepts database URL configuration.
# app.config['DATABASE'] = 'sqliteext:///%s' % os.path.join(app.config['APP_DIR'], 'blog.db')
# app.config['DEBUG'] = False

# The secret key is used internally by Flask to encrypt session data stored
# in cookies. Make this unique for your app.
app.config['SECRET_KEY'] = 'shhh, secret!'

# This is used by micawber, which will attempt to generate rich media
# embedded objects with maxwidth=800.
app.config['SITE_WIDTH'] = 800

from auth.iaasldap import LDAPUser as LDAPUser

current_user = LDAPUser()





# Create a Flask WSGI app and configure it using values from the module.
# app = Flask(__name__)
# app.config.from_object(__name__)

# FlaskDB is a wrapper for a peewee database that sets up pre/post-request
# hooks for managing database connections.
# flask_db = FlaskDB(app)

# The `database` is the actual peewee database, as opposed to flask_db which is
# the wrapper.
# database = flask_db.database



# from models import *

from views import *
import filters
#
def main():
    database.create_tables([ models.FTSEntry], safe=True)
    db.create_all()
    # run_seed()
    app.run(debug=True,port=5000)


if __name__ == '__main__':
    main()
