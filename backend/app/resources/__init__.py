from flask_restful import Api
from app.resources.products import ProductsResource
from webargs.flaskparser import parser, abort


@parser.error_handler
def handle_request_parsing_error(err, *_unused):
    abort(400, errors=err.messages)


api = Api(prefix='/observatory/api')
api.add_resource(ProductsResource, '/products')