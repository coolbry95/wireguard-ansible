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

- name: Testing new wireguard module
  wireguard_test:
     server:
         name: wg1.conf
         listen_port: 5222
         peers: "{{ peers }}"

- name: Testing new wireguard module
  wireguard_test:
     server:
         name: wg1.conf
         address: 127.0.2.2
         private_key: 2FH8kqdw106CeIN/uu3SnDJd7ahQwwQNy5i0xY6HAXc=
         listen_port: 5222
         peers:
           - peer: name1 # client config name
               public_key: this is the public key
               allowedIPs: 127.0.1.1
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

def make_client_config(address, dns, private_key, endpoint, public_key):
    config = {}
    config['Interface'] = {}
    config['Peer'] = {}

    config['Interface']['Address'] = address
    config['Interface']['DNS'] = dns
    config['Interface']['PrivateKey'] = private_key


    config['Peer']['AllowedIPs'] = '0.0.0.0/0'
    config['Peer']['PublicKey'] = public_key
    config['Peer']['Endpoint'] = endpoint

def write_interface(config, configFile, section):
    configFile.write('[' + section + ']' + '\n')

    #for key, value in config[section].items():
    for key, value in config[section].items():
        if key == 'PublicKey' and section == 'Interface':
            continue
        configFile.write(key + ' = ' + str(value) + '\n')
    
def write_interface2(config, configFile, section):
    configFile.write('[' + section + ']' + '\n')

    #for key, value in config[section].items():
    for key, value in config.items():
        if key == 'Interface' or key == 'Peer':
            continue
        configFile.write(key + ' = ' + str(value) + '\n')

def make_interface(params):
    # TODO keylen is based on bytes
    #keyLen = 32
    keyLen = 0
    config = {}
    config['Interface'] = {}
    
    # change to fail params?
    if 'address' in params and params['address'] != None:
        if len(params['address'] ) == 1:
            config['Interface']['Address'] = params['address'][0]
        elif len(params['address']) > 1:
            config['Interface']['Address'] = ",".join(params['address'])
            #for add in address:
            #    config['Interface']['Address'] = params['address'] + ","
            
            # TODO: Is this needed
            #config['Interface']['Address'] = config['Interface']['address'][:-1]
    else:
        config['Interface']['Address'] = DEFAULTADDRESS.format(1, 24)
        #module.fail_json(msg='No address specified')

    if 'private_key' in params and params['private_key'] != None:
        # TODO keylen is based on bytes
        if len(params['private_key']) < keyLen:
            module.fail_json(msg='private_key is not correct length ' +
                    str(len(params['private_key'])))
        else:
            config['Interface']['PrivateKey'] = params['private_key']
    else:
        private_key, public_key = generate_keys()
        config['Interface']['PrivateKey'] = private_key
        config['Interface']['PublicKey'] = public_key
        #module.fail_json(msg='No private_key specified')

    if 'saveconfig' in params and params['saveconfig'] != None:
        if params['saveconfig'] == False:
            config['Interface']['SaveConfig'] = 'false'
        else:
            config['Interface']['SaveConfig'] = 'true'

    if 'dns' in params and params['dns'] != None:
        config['Interface']['DNS'] = params['dns']

    if 'listen_port' in params and params['listen_port'] != None:
        config['Interface']['ListenPort'] = params['listen_port']
    else:
        print()
        # dont fail this is not required
        #module.fail_json(msg='No listen_port specified')

    if 'mtu' in params and params['mtu'] != None:
        config['Interface']['MTU'] = params['mtu']

    if 'table' in params and params['table'] != None:
        config['Interface']['Table'] = params['table']

    if 'preup' in params and params['preup'] != None:
        config['Interface']['PreUp'] = params['preup']

    if 'predown' in params and params['predown'] != None:
        config['Interface']['PreDown'] = params['predown']

    if 'postup' in params and params['postup'] != None:
        config['Interface']['PostUp'] = params['preup']

    if 'postdown' in params and params['postdown'] != None:
        config['Interface']['PostDown'] = params['postdown']

    return config

def make_peer(params, address):
    # todo keylen is based on bytes
    #keylen = 32
    keyLen = 0

    config = {}
    config['Peer'] = {}
    config['Interface'] = {}

    # TODO: verify its an IP address?
    #if params['allowedIPs'] != None:
    if 'allowedIPs' in params and params['allowedIPs'] != None:
        if len(params['allowedIPs'] ) == 1:
            config['Peer']['AllowedIPs'] = params['allowedIPs'][0]
        elif len(params['allowedIPs']) > 1:
            config['Peer']['Address'] = ",".join(params['address'])
            #for add in params['allowedIPs']:
            #    config['Peer']['AllowedIPs'] = params['allowedIPs'] + ","
            
            #config['Peer']['AllowedIPs'] = config['Peer']['AllowedIPs'][:-1]
    else:
        # TODO: add ipv6 support
        config['Peer']['AllowedIPs'] = DEFAULTADDRESS.format(address, 32)
        # dont fail add allowedIPs
        #module.fail_json(msg='No allowedIPs specified')

    if 'public_key' in params and params['public_key'] != None:
        if len(params['public_key']) < keyLen:
            module.fail_json(msg='No public_key is not correct length')
        else:
            config['Peer']['PublicKey'] = params['public_key']
    else:
        private_key, public_key = generate_keys()
        config['Interface']['PrivateKey'] = private_key
        config['Interface']['PublicKey'] = public_key
        config['Peer']['PublicKey'] = public_key
        #module.fail_json(msg='No public_key specified')

    if 'preshared_key' in params and  params['preshared_key'] != None:
        if len(params['preshared_key']) != keyLen:
            module.fail_json(msg='No preshared_key is not correct length')
        else:
            config['Peer']['PresharedKey'] = params['preshared_key']

    if 'endpoint' in params and params['endpoint'] != None:
        config['Peer']['Endpoint'] = params['endpoint']

    if 'persistent_keepalive' in params and params['persistent_keepalive'] != None:
        config['Peer']['PersistentKeepalive'] = params['persistent_keepalive']

    return config


class Config():

    def __init__(self):
        self.name = ""
        self.interface = Interface()
        self.peers = []

    def ToWgQuick():
        output = ""

        output += "[Interface]\n"

        if self.interface.listen_port != None:
            output += "ListenPort = {:d}\n".format(self.interface.listen_port)

        if len(self.interface.addresses) > 0:
            output += "Address = {:s}\n".format(", ".join(self.interface.addresses))

        if len(self.interface.addresses) > 0:
            output += "DNS = {:s}\n".format(", ".join(self.interface.dns))

        if self.interface.mtu != None:
            output += "MTU = {:d}\n".format(self.interface.mtu)

        for peer in self.peers:
            output += "\n[Peer]\n"

            output += "PublicKey = {:s}\n".format(peer.public_key)

            if peer.preshared_key != None:
                output += "PresharedKey = {:s}\n".format(peer.preshared_key)

            if len(peer.allowedIPs) > 0:
                output += "AllowedIPs = {:s}\n".format(", ".join(peer.allowedIPs))

            if peer.endpoint != None:
                output += "Endpoint = {:s}\n".format(peer.endpoint)

            if peer.persistent_keepalive != None:
                output += "PersistentKeepalive = {:d}\n".format(peer.persistent_keepalive)
            return output

class Interface():

    def __init__(self):
        self.private_key = ""
        self.addresses = []
        self.listen_port = 0
        self.mtu = 0
        self.dns = []

class Peer():

    def __init__(self):
        self.public_key = ""
        self.preshared_key = ""
        self.allowedIPs = []
        self.endpoint = ""
        self.persistent_keepalive = 0


def run_module():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        server=dict(type='dict', required=False, options=dict(
            name=dict(type='str', required=True),
            private_key = dict(type='str', required=False),
            address = dict(type='list', required=False),
            listen_port = dict(type='int', required=False),
            public_key = dict(type='str', required=False),
            table = dict(type='str', required=False),
            dns = dict(type='int', required=False),
            mtu = dict(type='int', required=False),
            preup = dict(type='str', required=False),
            predown = dict(type='str', required=False),
            postup = dict(type='str', required=False),
            postdown = dict(type='str', required=False),
            # TODO: still need a replace peers
            # is this the same thing as replace peers
            saveconfig = dict(type='bool', required=False, default=False),
            peers = dict(type='list', required=False, options=dict(
                public_key = dict(type='str', required=False),
                preshared_key = dict(type='str', required=False),
                #TODO: pretty sure this is required test
                allowedIPs = dict(type='list', required=False), 
                endpoint = dict(type='str', required=False),
                persistent_keepalive = dict(type='int', required=False),
                )),
            )),

        generatepeers = dict(type='bool', required=False, default=False),
        new=dict(type='bool', required=False, default=False),
        test=dict(type='list', required=False),
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


    #name = "/etc/wireguard/" + module.params['server']['name']
    name = module.params['server']['name']
    nameclient = "/etc/wireguard/"
    name = nameclient + name

    #print(module.params['peers'])
    #module.fail_json(msg='name is not specified')

    conf = Config()
    conf.name = name

    if 'server' in module.params:
        address_count = 2

        #print(params)
        #module.fail_json(msg='name is not specified')
        interface = make_interface(module.params['server'])
        #conf.make_interface(module.params['server'])

        if 'peers' not in module.params['server']:
            module.fail_json(msg='peers not specified')

        # problem is how to make peer configs from stratch

        peers = []
        for peer in module.params['server']['peers']:
            #print(peer)
            #module.fail_json(msg='name is not specified')

            p = make_peer(peer, address_count)
            p['Interface']['Address'] = DEFAULTADDRESS.format(address_count, 32)
            peers.append(p)
            #conf.peers.append(p)
            address_count += 1

        with open(name, "w+") as fh:
            write_interface(interface, fh, 'Interface')
            for peer in peers:
                write_interface(peer, fh, 'Peer')

        os.chmod(name, 0o600)

        if module.params['generatepeers']:
            address_count = 2
            for peer in peers:
                interface2 = {}

                interface2['Address'] = peer['Interface']['Address']
                interface2['PrivateKey'] = peer['Interface']['PrivateKey']

                params_interface = {
                        'DNS' : '10.200.200.1'
                        }

                params_peer = {
                        'PublicKey' : interface['Interface']['PublicKey'],
                        'AllowedIPs' : '0.0.0.0/0',
                        'Endpoint' : 'dns.shellcode.in:5222'
                        }

                for k,v in params_peer.items():
                    peer[k] = v

                for k,v in params_interface.items():
                    interface2[k] = v

                address_count += 1

                n = nameclient + "name{}".format(address_count)
                with open(n, "w+") as fh:
                    write_interface2(interface2, fh, 'Interface')
                    write_interface2(peer, fh, 'Peer')

    # use whatever logic you need to determine whether or not this module
    # made any modifications to your target
    if module.params['new']:
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
