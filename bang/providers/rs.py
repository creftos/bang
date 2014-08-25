import rightscale
import time

from requests import HTTPError
from .. import TimeoutError, resources as R, attributes as A
from ..util import log, poll_with_timeout
from .bases import Provider, Consul

# because rs is slower than aws and aws' default is 120
DEFAULT_TIMEOUT_S = 180


def server_to_dict(server):
    """
    Returns the :class:`dict` representation of a server object.

    The returned :class:`dict` is meant to be consumed by
    :class:`~bang.deployers.cloud.ServerDeployer` objects.

    """
    soul = server.soul
    return {
            A.server.ID: server.href,
            A.server.PUBLIC_IPS: soul.get('public_ip_addresses', []),
            A.server.PRIVATE_IPS: soul.get('private_ip_addresses', []),
            }


def find_exact(collection, **kwargs):
    filters = ['%s==%s' % (k, v) for k, v in kwargs.iteritems()]
    fuzzy_matches = collection.index(params={'filter[]': filters})
    for f in fuzzy_matches:
        exact = True
        for k, v in kwargs.iteritems():
            if f.soul[k] != v:
                exact = False
                break
        if exact:
            return f


class Servers(Consul):
    """The consul for the RightScale servers."""
    def __init__(self, *args, **kwargs):
        super(Servers, self).__init__(*args, **kwargs)
        creds = self.provider.creds
        self.api = rightscale.RightScale(
                api_endpoint=creds[A.creds.API_ENDPOINT],
                refresh_token=creds[A.creds.REFRESH_TOKEN],
                )
        self.region_name = ''
        self._cloud = None
        self.deployment = None

    def create_stack(self, name):
        """
        Creates stack if necessary.
        """
        deployment = find_exact(self.api.deployments, name=name)
        if not deployment:
            try:
                # TODO: replace when python-rightscale handles non-json
                self.api.client.post(
                        '/api/deployments',
                        data={'deployment[name]': name},
                        )
            except HTTPError as e:
                log.error(
                        'Failed to create stack %s. '
                        'RightScale returned %d:\n%s'
                        % (name, e.response.status_code, e.response.content)
                        )

    def find_servers(self, tags, running=True):
        # TODO: make stack and role be explicit args to find_servers instead of
        # {'stack': 'foo', 'role': 'bar'}
        name = tags[A.tags.ROLE]
        filters = ['name==%s' % name]
        if running:
            filters.extend([
                'state<>decommisioning',
                'state<>terminating',
                'state<>terminated',
                'state<>stopping',
                'state<>inactive',
                ])
        self.deployment = find_exact(
                self.api.deployments,
                name=tags[A.STACK],
                )
        filters.append('deployment_href==' + self.deployment.href)
        params = {'filter[]': filters}
        instances = self.cloud.instances.index(params=params)
        return [server_to_dict(i) for i in instances if i.soul['name'] == name]

    def find_running(self, server_attrs, timeout_s):
        href = server_attrs[A.server.ID]
        res_id = href.split('/')[-1]

        def find_running_instance():
            instance = self.cloud.instances.show(res_id=res_id)
            if instance.soul['state'] == 'operational':
                return instance

        running = poll_with_timeout(timeout_s, find_running_instance, 20)
        if not running:
            raise TimeoutError('Server not operational within allotted time.')
        return server_to_dict(running)

    def set_region(self, region_name):
        self.region_name = region_name

    @property
    def cloud(self):
        if not self._cloud:
            self._cloud = find_exact(
                    self.api.clouds,
                    name=self.region_name,
                    )
        return self._cloud

    def find_server_defs(self, basename):
        """
        Finds *usable* server definitions by name.

        A server definition is *usable* if it doesn't have a current instance.

        NOTE: This might result in extra server definitions if some servers are
        in various non-operational states (e.g. terminating).
        """
        filters = ['name==%s' % basename]
        fuzzy = self.deployment.servers.index(params={'filter[]': filters})
        matches = []
        for f in fuzzy:
            if basename != f.soul['name']:
                continue
            if 'current_instance' not in f.links:
                matches.append(f.href)
        if matches:
            self.basename = basename
        return matches

    def define_server(
            self, basename, server_tpl, server_tpl_rev, instance_type,
            ssh_key_name, tags=None, availability_zone=None,
            security_groups=None,
            ):
        """
        Creates a new server instance.  This call blocks until the server is
        created and available for normal use, or :attr:`timeout_s` has elapsed.

        :param str basename:  An identifier for the server.

        :param str server_tpl:  The name of the server template to use.

        :param str server_tpl_rev:  The revision of the server template to use.
            For ``HEAD``, set this to ``0``.

        :param str instance_type:  The name of an instance type.  E.g.
            ``m3.xlarge``.

        :param str ssh_key_name:  The name of the ssh key to inject into the
            target server's ``authorized_keys`` file.  The key must already
            have been registered in the RightScale datacenter
            (e.g. ``EC2 us-east-1``).

        :param tags:  Key-value pairs of arbitrary strings to use as *tags* for
            the server instance.
        :type tags:  :class:`Mapping`

        :param str availability_zone:  The name of the availability zone
            (a.k.a. datacenter in RightScale lingo) in which to place the
            server.

        :param list security_groups: The security groups to which this server
            should belong.

        :rtype:  :class:`dict`

        """
        log.info('Defining server %s...' % basename)
        self.basename = basename
        tpl = find_exact(
                self.api.server_templates,
                name=server_tpl,
                revision=server_tpl_rev,
                )
        itype = find_exact(
                self.cloud.instance_types,
                name=instance_type,
                )
        datacenter = find_exact(
                self.cloud.datacenters,
                name=availability_zone,
                )
        sshkey = find_exact(
                self.cloud.ssh_keys,
                resource_uid=ssh_key_name,
                )
        secgroup_hrefs = [
                find_exact(self.cloud.security_groups, name=n).href
                for n in security_groups
                ]
        data = {
                'server[deployment_href]': self.deployment.href,
                'server[instance][cloud_href]': self.cloud.href,
                'server[instance][datacenter_href]': datacenter.href,
                'server[instance][instance_type_href]': itype.href,
                'server[instance][security_group_hrefs][]': secgroup_hrefs,
                'server[instance][server_template_href]': tpl.href,
                'server[instance][ssh_key_href]': sshkey.href,
                'server[name]': basename,
                }
        # TODO: replace when python-rightscale no longer blows up due to empty
        # response body.
        try:
            response = self.api.client.post('/api/servers', data=data)
            return response.headers['location']
        except HTTPError as e:
            log.error(
                    'Definition failed.  RightScale returned %d:\n%s'
                    % (e.response.status_code, e.response.content)
                    )

    def create_server(self, href, inputs, timeout_s=DEFAULT_TIMEOUT_S):
        log.info(
                'Launching server %s... this could take a while...'
                % self.basename
                )
        data = dict([
                ('inputs[%s]' % k, 'text:%s' % v)
                for k, v in inputs.iteritems()
                ])
        try:
            response = self.api.client.post(href + '/launch', data=data)
        except HTTPError as e:
            log.error('Creation of %s failed.  RightScale returned %d:\n%s' % (
                    href,
                    e.response.status_code,
                    e.response.content,
                    ))
            raise
        instance_href = response.headers['location']
        res_id = instance_href.split('/')[-1]

        # we're too fast for rs/ec2... slow down a little bit, twice
        time.sleep(2)

        def find_running_instance():
            instance = self.cloud.instances.show(res_id=res_id)
            if instance.soul['state'] == 'operational':
                return instance

        running = poll_with_timeout(timeout_s, find_running_instance, 20)
        if not running:
            raise TimeoutError('Could not launch server within allotted time.')
        return server_to_dict(running)


class SecGroups(Consul):
    pass


class SecGroupRules(Consul):
    pass


class RightScale(Provider):
    CONSUL_MAP = {
            R.SERVERS: Servers,
            R.SERVER_SECURITY_GROUPS: SecGroups,
            R.SERVER_SECURITY_GROUP_RULES: SecGroupRules,
            }