# Copyright 2012 - John Calixto
#
# This file is part of bang.
#
# bang is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# bang is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with bang.  If not, see <http://www.gnu.org/licenses/>.
import pymysql
from novaclient.client import Client as NovaClient

from ... import attributes as A, resources as R
from ...util import log, poll_with_timeout
from ..openstack import (OpenStack, Nova, RedDwarf,
        DEFAULT_STORAGE_SIZE_GB, DEFAULT_TIMEOUT_S, db_to_dict)
from .reddwarf import HPDbaas
from .load_balancer import HPLoadBalancer


class HPRedDwarf(RedDwarf):
    def create_db(self, instance_name, instance_type,
            admin_username, admin_password, security_groups=None, db_name=None,
            storage_size_gb=DEFAULT_STORAGE_SIZE_GB,
            timeout_s=DEFAULT_TIMEOUT_S):
        """
        Creates a database instance.

        This method blocks until the db instance is active, or until
        :attr:`timeout_s` has elapsed.

        By default, hpcloud *assigns* an automatically-generated set of
        credentials for an admin user.  In addition to launching the db
        instance, this method uses the autogenerated credentials to login to
        the server and create the intended admin user based on the credentials
        supplied as method arguments.

        :param str instance_name:  A name to assign to the db instance.

        :param str instance_type:  The server instance type (e.g. ``medium``).

        :param str admin_username:  The admin username.

        :param str admin_password:  The admin password.

        :param security_groups:  *Not used in hpcloud*.

        :param str db_name:  The database name.  If this is not specified, the
            database will be named the same as the :attr:`instance_name`.

        :param int storage_size_gb:  The size of the storage volume in GB.

        :param float timeout_s:  The number of seconds to poll for an active
            database server before failing.  This value is also used when
            attempting to connect to the running mysql server.

        :rtype:  :class:`dict`

        """
        db = self._create_db(instance_name, instance_type,
                storage_size_gb)

        # hang on to these... hpcloud only provides a way to generate a new
        # set of username/password - there is no way to retrieve the originals.
        default_creds = db.credential
        log.debug('Credentials for %s: %s' % (instance_name, default_creds))

        instance = self._poll_instance_status(db, timeout_s)

        # we're taking advantage of a security bug in hpcloud's dbaas security
        # group rules.  the default *security* is to allow connections from
        # everywhere in the world.
        def connect():
            try:
                return pymysql.connect(
                        host=instance.hostname,
                        port=instance.port,
                        # db=self.database,
                        user=default_creds['username'],
                        passwd=default_creds['password'],
                        connect_timeout=timeout_s,
                        )
            except:
                log.warn("Could not connect to db, %s" % instance_name)
                # log.debug("Connection exception", exc_info=True)

        log.info("Connecting to %s..." % instance_name)
        db = poll_with_timeout(timeout_s, connect, 10)
        cur = db.cursor()
        cur.execute(
                "grant all privileges on *.* "
                "to '%s'@'%%' identified by '%s' "
                "with grant option"
                % (admin_username, admin_password)
                )
        cur.execute("flush privileges")
        return db_to_dict(instance)

class HPCloud(OpenStack):

    REDDWARF_SERVICE_TYPE = 'hpext:dbaas'
    REDDWARF_CLIENT_CLASS = HPDbaas

    def __init__(self, *args, **kwargs):
        super(HPCloud, self).__init__(*args, **kwargs)
        cm = self.CONSUL_MAP
        cm[R.SERVERS] = Nova
        cm[R.DATABASES] = HPRedDwarf
        cm[R.LOAD_BALANCERS] = HPLoadBalancer
        cm[R.DYNAMIC_LB_SEC_GROUPS] = Nova

    @property
    def load_balancer_client(self):
        return self.CONSUL_MAP[R.LOAD_BALANCERS](self)

    def _get_nova_client(self):
        args = self.get_nova_client_args()
        if 'access_key_id' in self.creds and 'secret_access_key' in self.creds:
            # this pluggable auth requires api version 2
            args[0] = '2'

        kwargs = self.get_nova_client_kwargs()
        if 'access_key_id' in self.creds and 'secret_access_key' in self.creds:
            kwargs['auth_system'] = 'secretkey'

        nc = NovaClient(*args, **kwargs)
        return nc

    def authenticate(self):
        """
        Authenticate against the HP Cloud Identity Service.  This is the first
        step in any hpcloud.com session, although this method is automatically
        called when accessing higher-level methods/attributes.

        **Examples of Credentials Configuration**

        - Bare minimum for authentication using HP API keys::

            deployer_credentials:
              hpcloud:
                auth_url: https://region-a.geo-1.identity.hpcloudsvc.com:35357/v2.0/
                tenant_name: farley.mowat-tenant1
                access_key_id: MZOFIE9S83FOS248FIE3
                secret_access_key: EU859vjksor73gkY378f9gkslbkrabcxwfyW2loo

        - With multiple *compute* availability zones activated, the region must
          also be specified (due to current limitations in the OpenStack client
          libraries)::

            deployer_credentials:
              hpcloud:
                auth_url: https://region-a.geo-1.identity.hpcloudsvc.com:35357/v2.0/
                tenant_name: farley.mowat-tenant1
                access_key_id: MZOFIE9S83FOS248FIE3
                secret_access_key: EU859vjksor73gkY378f9gkslbkrabcxwfyW2loo
                region_name: az-1.region-a.geo-1

        - Using ``username`` and ``password`` is also allowed, but
          discouraged::

            deployer_credentials:
              hpcloud:
                auth_url: https://region-a.geo-1.identity.hpcloudsvc.com:35357/v2.0/
                tenant_name: farley.mowat-tenant1
                username: farley.mowat
                password: NeverCryW0lf

        When both API keys and ``username+password`` are specified, the API
        keys are used.

        """
        log.info("Authenticating to HP Cloud...")
        creds = self.creds
        access_key_id = creds.get('access_key_id', '')
        secret_access_key = creds.get('secret_access_key', '')
        # prefer api key + secret key, but fallback to username + password
        if access_key_id and secret_access_key:
            self.nova_client.client.os_access_key_id = access_key_id
            self.nova_client.client.os_secret_key = secret_access_key
        self.nova_client.authenticate()

