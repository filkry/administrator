exec { "apt-get update":
    command => "/usr/bin/apt-get update",
}

file { "/etc/profile.d/admin_settings.sh":
		path => '/etc/profile.d/admin_settings.sh',
		ensure => present,
		content => 'export ADMINISTRATOR_SETTINGS=/home/vagrant/admin.ini',
		require => File['admin.ini'],
}

file { "admin.ini":
	path => '/home/vagrant/admin.ini',
    ensure => present,
    source => "/vagrant/config/admin.ini",
}

exec {"init db":
	path => '/vagrant/',
	command => 'python manage.py init_db',
	require => Package['Flask-Script'],
}

package {"nginx":
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
	require => Package['nginx'],
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