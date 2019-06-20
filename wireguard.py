#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Bryan Hendryx <coolbry95@gmail.com>
# MIT License

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: wireguard

short_description: This is a wireguard module that takes configuration done in yaml and converts it into a wireguard config.

version_added: "0.0.1"

description:
    - "This is my longer description explaining my sample module"

options:
    name:
        description:
            - This is the message to send to the sample module
    server:
        description:
            - This is a server configuration object
        required: false

        server=dict(type='dict', required=False, options=dict(
            name:
                description:
                    - This is the name of the interface to make. It will also name the config file with this name + .conf
            private_key:
                description:
                    - This is the private key for this interface to use
            public_key:
                description:
                    - This is the public key for this interface to use. This must match the private key.
            address:
                description:
                    - This is the address for this interface to use
            listen_port:
                description:
                    - This is the port for this interface to listen on
            table:
                description:
                    - This is the fwmark for this interface to use
            dns:
                description:
                    - This is the dns address for this interface to use
            mtu:
                description:
                    - This is the mtu size address for this interface to use
            preup:
                description:
                    - This is the preup command for this interface to use. This only works when doing wg-quick
            predown
                description:
                    - This is the predown command for this interface to use. This only works when doing wg-quick
            postup
                description:
                    - This is the postup command for this interface to use. This only works when doing wg-quick
            postdown
                description:
                    - This is the postdown command for this interface to use. This only works when doing wg-quick
            saveconfig:
                description:
                    - This sets whether to save the config for this interface. This only works when doing wg-quick
            peers:
                description:
                    - This is the name of the peer.
                public_key:
                    description:
                        - This is the public key of this peer.
                preshared_key:
                    description:
                        - This is the preshared key of this peer.
                allowedIPs:
                    description:
                        - This is the allowedIPs for this peer.
                endpoint:
                    description:
                        - This is the enpoint of this peer.
                persistent_keepalive:
                    description:
                        - This is the persistent keepalive value for this peer

author:
    - Bryan Hendryx (@coolbry95)
'''

EXAMPLES = '''
# tasks file for wireguardtest
- name: set peers
  set_fact:
    peers:
      - peer: name1 # client config name
        #public_key: this is the public key
        #private_key: this is the private key
      - peer: name2
        #public_key: this is the public key2
        #private_key: this is the private key2
'''

RETURN = '''
original_message:
    description: The original name param that was passed in
    type: str
    returned: always
message:
    description: The output message that the sample module generates
    type: str
    returned: always
'''

from ansible.module_utils.basic import AnsibleModule
import json
import os
import subprocess

# TODO: change this add ipv6 support
DEFAULTADDRESS = "10.200.200.{}/{}"

def generate_keys():
    # TODO: check errors
    private_key_gen = subprocess.run(['wg', 'genkey'], stdout=subprocess.PIPE)

    private_key = private_key_gen.stdout

    public_key_gen = subprocess.run(['wg', 'pubkey'], stdout=subprocess.PIPE, input=private_key)

    private_key = private_key_gen.stdout.decode('utf-8')
    public_key = public_key_gen.stdout.decode('utf-8')

    return str(private_key).strip(), str(public_key).strip()

def generate_private():
    private_key_gen = subprocess.run(['wg', 'genkey'], stdout=subprocess.PIPE)

    private_key = private_key_gen.stdout

    return str(private_key).strip()

def generate_public(private_key):
    public_key_gen = subprocess.run(['wg', 'pubkey'], stdout=subprocess.PIPE, input=private_key, text=True)

    public_key = public_key_gen.stdout

    return str(public_key).strip()

class Config():

    def __init__(self):
        self.name = ""
        self.interface = Interface()
        self.peers = []

    def ToWgQuick(self):
        output = ""

        output += "[Interface]\n"

        output += "PrivateKey = {:s}\n".format(self.interface.private_key)

        if self.interface.listen_port != None:
            output += "ListenPort = {:d}\n".format(self.interface.listen_port)

        if len(self.interface.addresses) > 0:
            output += "Address = {:s}\n".format(", ".join(self.interface.addresses))

        if len(self.interface.dns) > 0:
            output += "DNS = {:s}\n".format(", ".join(self.interface.dns))

        if self.interface.mtu != None:
            pass
            #output += "MTU = {:d}\n".format(self.interface.mtu)

        for peer in self.peers:
            output += "\n[Peer]\n"

            output += "PublicKey = {:s}\n".format(peer.public_key)

            if peer.preshared_key != None:
                pass
                #output += "PresharedKey = {:s}\n".format(peer.preshared_key)

            if len(peer.allowedIPs) > 0:
                output += "AllowedIPs = {:s}\n".format(", ".join(peer.allowedIPs))

            if peer.endpoint != None:
                if peer.endpoint != "":
                    output += "Endpoint = {:s}\n".format(peer.endpoint)

            if peer.persistent_keepalive != None:
                pass
                #output += "PersistentKeepalive = {:d}\n".format(peer.persistent_keepalive)

            return output

class Interface():

    def __init__(self):
        self.private_key = None
        self.addresses = []
        self.listen_port = None
        self.mtu = None
        self.dns = []

class Peer():

    def __init__(self):
        self.public_key = None
        self.preshared_key = None
        self.allowedIPs = []
        self.endpoint = None
        self.persistent_keepalive = None

def run_module():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        server=dict(type='dict', required=False, options=dict(
            name=dict(type='str', required=True),
            private_key = dict(type='str', required=False),
            addresses = dict(type='list', required=False),
            listen_port = dict(type='int', required=False),
            endpoint = dict(type='str', required=False),
            # not handled currently
            mtu = dict(type='int', required=False),
            preup = dict(type='str', required=False),
            predown = dict(type='str', required=False),
            postup = dict(type='str', required=False),
            postdown = dict(type='str', required=False),
            table = dict(type='str', required=False),
            saveconfig = dict(type='bool', required=False, default=False),

            peers = dict(type='list', required=False, options=dict(
                addresses = dict(type='list', required=False),
                private_key = dict(type='str', required=False),
                dns = dict(type='list', required=False),
                allowedIPs = dict(type='list', required=False),
                endpoint = dict(type='str', required=False),
                # not handled currently
                preshared_key = dict(type='str', required=False),
                persistent_keepalive = dict(type='int', required=False),
                )),
            )),

        generatepeers = dict(type='bool', required=False, default=False),
    )

    # seed the result dict in the object
    # we primarily care about changed and state
    # change is if this module effectively modified the target
    # state will include any data that you want your module to pass back
    # for consumption, for example, in a subsequent task
    result = dict(
        changed=False,
        original_message='',
        message=''
    )

    # the AnsibleModule object will be our abstraction working with Ansible
    # this includes instantiation, a couple of common attr would be the
    # args/params passed to the execution, as well as if the module
    # supports check mode
    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    # if the user is working with this module in only check mode we do not
    # want to make any changes to the environment, just return the current
    # state with no modifications
    if module.check_mode:
        module.exit_json(**result)

    if 'name' not in module.params['server']:
        module.fail_json(msg='name is not specified')

    config_dir = "/etc/wireguard/"
    server = module.params['server']

    # we want to make a server config and all of the peer configs
    if module.params['generatepeers']:
        # check for things needed for the peers first
        if 'private_key' in server and server['private_key'] == None:
            private_key, public_key = generate_keys()
            server['private_key'] = private_key
            server['public_key'] = public_key

        if 'listen_port' in server and server['listen_port'] == None:
            module.params['server']['listen_port'] = 5222

        if 'endpoint' in module.params['server'] and module.params['server']['endpoint'] == None:
            module.fail_json(msg='endpoint is not specified')

        peerConfigs = []
        # the first address goes to the server
        address_count = 2
        for peer in module.params['server']['peers']:
            conf = Config()
            conf.name = peer['peer']

            if 'private_key' not in peer or peer['private_key'] == None:
                private_key, public_key = generate_keys()
                conf.interface.private_key = private_key
            else:
                conf.interface.private_key = peer['private_key']

            if 'addresses' not in peer or peer['addresses'] == None:
                conf.interface.addresses.append(DEFAULTADDRESS.format(address_count, 24))
            else:
                if len(peer['addresses']) > 1:
                    conf.interface.addresses = peer['addresses']
                else:
                    conf.interface.addresses.append(peer['addresses'][0])

            if 'dns' in peer and peer['dns'] != None:
                if len(peer['dns']) > 1:
                    conf.interface.dns = peer['dns']
                else:
                    conf.interface.dns.append(peer['dns'][0])


            p = Peer()
            p.endpoint = module.params['server']['endpoint']

            if 'public_key' not in server or server['public_key'] == None:
                p.public_key = generate_public(server['private_key'])
            else:
                p.public_key = server['public_key']

            if 'allowedIPs' in peer and peer['allowedIPs'] != None:
                if len(peer['allowedIPs']) > 1:
                    p.allowedIPs = peer['allowedIPs']
                else:
                    p.allowedIPs.append(peer['allowedIPs'][0])
            else:
                p.allowedIPs.append("0.0.0.0/0")

            conf.peers.append(p)
            peerConfigs.append(conf)

            address_count += 1

            with open(config_dir + conf.name, "w+") as fh:
                fh.write(conf.ToWgQuick())
                fh.close()

            os.chmod(config_dir + conf.name, 0o600)

        # now make the server config now that we have all of the peers and theirkeys
        conf = Config()
        #conf.name = config_dir + server['name']
        conf.name = server['name']

        if 'addresses' not in server or server['addresses'] == None:
            conf.interface.addresses.append(DEFAULTADDRESS.format(1, 24))
        else:
            if len(server['addresses']) > 1:
                conf.interface.addresses = server['addresses']
            else:
                conf.interface.addresses.append(server['addresses'][0])

        conf.interface.listen_port = server['listen_port']
        conf.interface.private_key = server['private_key']

        for peer in peerConfigs:
            p = Peer()
            p.public_key = generate_public(peer.interface.private_key)
            p.allowedIPs.append(DEFAULTADDRESS.format(0,24))
            conf.peers.append(p)

        with open(config_dir + conf.name, "w+") as fh:
            fh.write(conf.ToWgQuick())
            fh.close()

        os.chmod(config_dir + conf.name, 0o600)

    # use whatever logic you need to determine whether or not this module
    # made any modifications to your target
    if module.params['server']:
        result['changed'] = True

    result['changed'] = True

    # during the execution of the module, if there is an exception or a
    # conditional state that effectively causes a failure, run
    # AnsibleModule.fail_json() to pass in the message and the result
    #if module.params['name'] == 'fail me':
    #    module.fail_json(msg='You requested this to fail', **result)

    # in the event of a successful module execution, you will want to
    # simple AnsibleModule.exit_json(), passing the key/value results
    module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()
