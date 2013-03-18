from invoke import Collection

from tasks import travis, specs


ns = Collection(travis, specs)
