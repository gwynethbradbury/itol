import os
from flask import request
import ldapconfig


class LDAPUser():
    
    def confirmed(self):
        return True
    def is_anonymous(self):
        return False
    
    '''
        Gets the users username credential
        '''
    def uid_trim(self):
        if ldapconfig.test:
            return "cenv0594"
        else:
            import string
            uid = request.remote_user
            uid_stripped = string.split(uid, '@')[0]
            print uid_stripped
            return uid_stripped
    '''
        Gets the users username credential
        '''
    def uid_suffix(self):
        if ldapconfig.test:
            return "development_suffix"
        else:
            import string
            uid = request.remote_user
            uid_stripped = string.split(uid, '@')[1]
            print uid_stripped
            return uid_stripped



# def get_dn(uid):
#     if ldapconfig.test:
#         return ""
#     else:
#         import ldap
#         searchFilter = "(&(uid=%s)(objectClass=posixAccount))" % uid
#         searchAttribute = ["dn"]
#         searchScope = ldap.SCOPE_SUBTREE
#         l = ldap.initialize(ldapconfig.ldaphost)
#         try:
#             l.protocol_version = ldap.VERSION3
#             l.simple_bind_s(ldapconfig.username, ldapconfig.password)
#             valid = True
#         except Exception, error:
#             print error
#         try:
#             ldap_result_id = l.search(ldapconfig.basedn, searchScope, searchFilter, searchAttribute)
#             result_set = []
#             result_type, result_data = l.result(ldap_result_id, 0)
#             print result_data
#             return result_data
#         except ldap.LDAPError, e:
#             print e
#         l.unbind_s()

    '''
    gets a user's full name and returns in the format "Firstname Surname"
    '''
    def get_fullname(self,uid=""):
        if ldapconfig.test:
            return "Firstname Surname"
        else:
            import ldap
            if uid=="":
                uid=self.uid_trim()
            suffix=self.uid_suffix()
            if (suffix=="ox.ac.uk"):
                searchFilter = "(&(objectClass=user)(sAMAccountName=%s))" % uid
                searchAttribute = ["displayName"]
                searchScope = ldap.SCOPE_SUBTREE
                l = ldap.initialize(ldapconfig.ldaphost_ad)
                try:
                    l.protocol_version = ldap.VERSION3
                    l.simple_bind_s(ldapconfig.username_ad, ldapconfig.password_ad)
                    valid = True
                except Exception, error:
                    print error
                try:
                    ldap_result_id = l.search(ldapconfig.basedn_ad, searchScope, searchFilter, searchAttribute)
                    result_type, result_data = l.result(ldap_result_id, 0)
                    try:
                        return result_data[0][1]['displayName'][0]
                    except Exception as e:
                        print(e)
                        return "Firstname Surname"
                except ldap.LDAPError, e:
                    return 'An Error Occurred (AD)'
                l.unbind_s()



            else:
                searchFilter = "(&(uid=%s)(objectClass=posixAccount))" % uid
                searchAttribute = ["cn"]
                searchScope = ldap.SCOPE_SUBTREE
                l = ldap.initialize(ldapconfig.ldaphost)
                try:
                    l.protocol_version = ldap.VERSION3
                    l.simple_bind_s(ldapconfig.username, ldapconfig.password)
                    valid = True
                except Exception, error:
                    print error
                try:
                    ldap_result_id = l.search(ldapconfig.basedn, searchScope, searchFilter, searchAttribute)
                    result_type, result_data = l.result(ldap_result_id, 0)
                    try:
                        return result_data[0][1]['cn'][0]
                    except Exception as e:
                        print(e)
                        return "Firstname Surname"
                except ldap.LDAPError, e:
                    return 'An Error Occurred'
                l.unbind_s()



# # For testing
# superusers_usernames=["cenv0594",
#                       "cenv0252",
#                       "hert1424"]

    '''gets a list of the groups for which this user is a member'''
    def get_groups(self):
        uid = self.uid_trim()
        groups = ['all_users']
        if ldapconfig.test:
            # return[]
            groups.append("superusers")
            # groups.append("onlinelrn")
            return groups
        else:
            import ldap
            searchFilter = '(|(&(objectClass=*)(memberUid=%s)))' % uid
            searchAttribute = ["cn"]
            searchScope = ldap.SCOPE_SUBTREE
            l = ldap.initialize(ldapconfig.ldaphost)
            try:
                l.protocol_version = ldap.VERSION3
                l.simple_bind_s(ldapconfig.username, ldapconfig.password)
                valid = True
            except Exception, error:
                print error
            try:
                result_set = l.search_s(ldapconfig.basedn, searchScope, searchFilter, searchAttribute)
                # result_set is a list containing lists of tuples, each containing a list - fun!
                for res in result_set:
                    # disentangle the various nested stuff!
                    groups.append(((res[1])['cn'])[0])
                # print groups
                return groups
            except ldap.LDAPError, e:
                return []
            l.unbind_s()

    '''
    filters this users groups for a given service
    '''
    def get_groups_filtered(self, filter):
        uid = self.uid_trim()
        import string
        if ldapconfig.test:
            return ["filteredgroup1", "filteredgroup2"]
        else:
            groups=[]
            result_set = self.get_groups()
            # result_set is a list containing lists of tuples, each containing a list - fun!
            for res in result_set:
                if res.find(filter) != -1:
                    groups.append(res)
            print groups
            return groups


    '''
    check whether this user is authorised against the given project
    '''
    def is_authenticated(self):
        #todo: complete authentication rules
        return True

    def is_active(self):
        return True
    
    def has_role(self,role):
        if role in self.get_groups():
            return True
        return False
    
    '''
        Determines whether a user is authorised to view this project
        caveat: if this is an admin-only page, _admin is added to the group name
        '''
    def is_authorised(self, service_name, is_admin_only_page=False):
        if "development_uid" == self.uid_trim():
            return True
        
        usersgroups = self.get_groups()
        if "superusers" in usersgroups:
            return True
        if is_admin_only_page:
            service_name = service_name + "_admin"
        if service_name in usersgroups:
            return True
        return False

    def change_password(self, old_password, new_password, repeat_password):
        success = 0
        msg = "Could not change password. "
        if self.is_correct_password(old_password):
            if new_password == repeat_password:
                # change the password
                change_password(self.uid_trim(), old_password, new_password,repeat_password,isAD=False)
                msg = "Password changed successfully"
                success = 1
            else:
                msg = msg + "New password inconsistent."
        else:
            msg = msg + "Old password does not match."

        return success, msg






def is_correct_password(current_pass):
    return True

def change_password( user='hert1424', current_pass='foo', new_pass='bar', repeat_password='bar', isAD=True):




    import ldap
    import ldap.modlist as modlist
    import base64

    success = 0
    msg = "Could not change password. "
    if is_correct_password(current_pass):
        if new_pass == repeat_password:
            # change the password

            try:
                ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_NEVER)

                host=ldapconfig.ldaphost#iaas
                if isAD:
                    host=ldapconfig.ldaphost_ad
                l = ldap.initialize(host)

                l.protocol_version = ldap.VERSION3

                #IAAS
                dn="uid=" + user + ",ou=ITStaff,dc=iaas,dc=ouce,dc=ox,dc=ac,dc=uk"
                #AD
                if isAD:
                    dn = "cn=" + user + ",cn=users,dc=ouce,dc=ox,dc=ac,dc=uk"

                # l.simple_bind_s(dn,current_pass)
                l.simple_bind_s(ldapconfig.username, ldapconfig.password)


                #IAAS
                add_pass = [(ldap.MOD_REPLACE, 'userPassword', [new_pass])]#IAAS
                #AD
                if isAD:
                    # unicode_pass = unicode('\"' + new_pass + '\"', 'iso-8859-1')# input is already unicode
                    unicode_pass = new_pass
                    password_value = unicode_pass.encode('utf-16-le')
                    add_pass = [(ldap.MOD_REPLACE, 'unicodePwd', [password_value])]


                l.modify_s(dn, add_pass)
                l.unbind_s()

                # self._set_password(self.uid_trim(), current_pass, new_pass)
                msg = "Password changed successfully"
                success = 1

            except Exception as e:
                print(e)
                success = 0
                msg = msg + e.__str__()
        else:
            msg = msg + "New password inconsistent."
    else:
        msg = msg + "Old password does not match."

    return success, msg

