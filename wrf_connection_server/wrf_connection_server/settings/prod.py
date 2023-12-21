
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'wfr',
        'USER': 'wfr',
        'PASSWORD': 'Q5PrVPLkXmLu',
        'HOST': '192.168.23.101',
        'PORT': '5432',
    }
}


ALLOWED_HOSTS = ['wrf.getit.rest']
CSRF_TRUSTED_ORIGINS = ['https://wrf.getit.rest']


CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [('127.0.0.1', 6379)],
        }
    },
}
