administrator
=============

A web server that manages a pool of jobs. Jobs are posted, requested and completed via API requests.

## Configuration

administrator was developed in a build environment constructed with Vagrant and Puppet, and tested in an Amazon EC2 instance. If you want to deploy administrator to your own Amazon EC2 instance, you'll need to do a little legwork outside of just cloning and running ``vagrant up``.

Vagrant uses a heirarchy of Vagrantfiles. Because the given file doesn't include Amazon credentials, you'll have to create your own at ``~/.vagrant.d/Vagrantfile``. Here's what it should look like:

```ruby
Vagrant.configure("2") do |config|
  config.vm.provider :aws do |aws, override|
    aws.access_key_id = "KEY"
    aws.secret_access_key = "SECRET"
    aws.keypair_name = "KEYPAIR NAME"
    override.ssh.private_key_path = "PRIVATE KEY PATH"
  end
end
```

You also need a configuration file specifically for administrator. There is a sample in ``config/admin.ini.sample``:

	DATABASE='/tmp/administrator.db'
	PASSWORD_HASH= <KEY>
	SECRET_KEY= <KEY>
	TRACK_SESSION = False

The ``PASSWORD_HASH`` is used for adding jobs. ``SECRET_KEY`` is used to sign cookies created by Flask.

You can generate a good secret key by doing this at a python prompt:

	import os
	os.urandom(24)

To generate a hash of a password, at the same prompt, enter:

	import hashlib
	hashlib.sha224("password").hexdigest()