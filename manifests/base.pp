exec { "apt-get update":
    command => "/usr/bin/apt-get update",
}

file { "/etc/profile.d/admin_settings.sh":
		path => '/etc/profile.d/admin_settings.sh',
		ensure => present,
		content => 'export ADMINISTRATOR_SETTINGS=/home/vagrant/admin.ini',
		require => File['admin.ini'],
}

file { "/home/vagrant":
	path => '/home/vagrant',
	ensure => directory,
}

file { "admin.ini":
	path => '/home/vagrant/admin.ini',
    ensure => present,
    source => "/vagrant/config/admin.ini",
    require => File['/home/vagrant'],
}

exec {"init db":
	path => ['/usr/bin/',],
	cwd => '/vagrant/',
	creates => '/tmp/administrator.db',
	command => 'python manage.py init_db',
	require => [Package['Flask-Script'],
				Package['python'],
				File["/etc/profile.d/admin_settings.sh"]],
}

# handle difference between AWS and local by adding both users to a common group

group {"server":
	ensure => present,
}

user {"vagrant":
	ensure => present,
	gid => 'server',
	managehome => true,
	home => "/home/vagrant",
	require => [Group["server"],],
}

user {"ubuntu":
	ensure => present,
	gid => 'server',
	managehome => true,
	home => "/home/ubuntu",
	require => [Group["server"],],
}

file {"database":
	path => '/tmp/administrator.db',
	group => 'server',
	mode => '660',
	require => [Group["server"],
				Exec["init db"]],
}

package {"nginx":
    ensure => present,
	require => Exec['apt-get update'],
}

package {"make":
    ensure => present,
	require => Exec['apt-get update'],
}

package {"gunicorn":
	ensure => present,
	require => Exec['apt-get update'],
}

package {"python":
	ensure => present,
	require => Exec['apt-get update'],
}

package {"python-pip":
	ensure => present,
	require => [Exec['apt-get update'],
			    Package['python']],
}

package { "flask": 
    require => Package["python-pip"],
    ensure  => latest,
    provider => pip,
}

package { "Flask-Script": 
    require => Package["python-pip"],
    ensure  => latest,
    provider => pip,
}

service { 'nginx':
	ensure => running,
	enable => true,
	require => [Package['nginx'],
				File["administrator_nginx"]],
	# I don't know what these do
	# hasstatus => true,
	# hasrestart => true,
}

file {"nginx-default":
    path => '/etc/nginx/sites-enabled/default',
    ensure => absent,
    require => Package['nginx'],
}

file {"administrator_nginx":
    path => '/etc/nginx/sites-enabled/administrator_nginx',
    ensure => present,
    require => Package['nginx'],
    source => "/vagrant/config/administrator_nginx",
}