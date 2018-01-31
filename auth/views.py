
from flask import flash
from flask import render_template, abort
from jinja2 import TemplateNotFound

import dbconfig
from main.auth.iaasldap import LDAPUser as LDAPUser

current_user = LDAPUser()




if dbconfig.test:
    from ..sqla.core.mock_access_helper import MockAccessHelper as AccessHelper
else:
    from ..sqla.core.access_helper import AccessHelper
AH = AccessHelper()

from .forms import ChangePWForm




def set_auth_views(app):


    @app.route('/changepassword', methods=["GET", "POST"])
    def change_ldap_password():
        if current_user.is_authenticated():


            form = ChangePWForm()
            if form.validate_on_submit():
                user=current_user
                # user = User(username=form.username.data,
                #             email=form.username.data,
                #             password=form.password.data)
                success,ret = current_user.change_password(form.oldpw,form.password,form.password2)
                if success:
                    flash(ret,category='message')
                else:
                    flash(ret,category="error")

                # return redirect(url_for('index'))

            try:
                return render_template("changepassword.html", form=form)
            except TemplateNotFound:
                abort(404)

        else:
            abort(403)