from .base import *


class EnvironmentException(Exception):
    pass


print(f'{ENVIRONMENT=}')

if ENVIRONMENT == 'prod':
    from .prod import *
elif ENVIRONMENT == 'local':
    from .local import *
else:
    raise EnvironmentException
