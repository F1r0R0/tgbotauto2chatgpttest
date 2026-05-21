from mangum import Mangum

from api.webhook import app

handler = Mangum(app)
