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