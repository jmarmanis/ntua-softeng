import itertools
from datetime import date
from flask_restful import Resource
from flask import request
from webargs import fields
from webargs.flaskparser import use_args
from marshmallow import validate, ValidationError
from marshmallow.decorators import post_dump, pre_dump
from app.models import Product, Shop, Price, db, ma
from sqlalchemy import asc, desc

SORT_CHOICE = list(map('|'.join, itertools.product(['geoDist', 'price', 'date'],
                                                   ['ASC', 'DESC'])))

ids_field = fields.List(fields.Int())
bad_request = '', 400
not_found = '', 404


class PricesResource(Resource):
    class PriceSchema(ma.ModelSchema):
        class ProductSchema(ma.ModelSchema):
            productId = fields.Int(attribute="id")
            productName = fields.String(attribute="name")
            productTags = fields.Str(attribute="tags")

        class ShopSchema(ma.ModelSchema):
            shopId = fields.Int(attribute='id')
            shopName = fields.Str(attribute='name')
            shopTags = fields.DelimitedList(fields.Str(), attribute='tags')
            shopAddress = fields.Str(attribute='address')

        price = fields.Float()
        date = fields.Date()
        product = fields.Nested(ProductSchema)
        shop = fields.Nested(ShopSchema)
        shopDist = fields.Float(attribute='dist')

        @pre_dump
        def handle_tuple(self, data):
            # if with_geo: query result = list of tuple(product, distance)
            if not isinstance(data, tuple):
                return data
            data[0].dist = data[1]
            return data[0]

        @post_dump
        def refactor(self, data):
            # flatten shop, product entries of data dict
            t_shop = data['shop']
            t_prod = data['product']
            del data['shop']
            del data['product']
            data.update(t_shop)
            data.update(t_prod)
            return data

    @use_args({
        'start': fields.Int(missing=1, location='query'),
        'count': fields.Int(missing=20, location='query'),
        'geoDist': fields.Float(missing=None, location='query'),
        'geoLng': fields.Float(missing=None, location='query'),
        'geoLat': fields.Float(missing=None, location='query'),
        'dateFrom': fields.Date(missing=None, location='query'),
        'dateTo': fields.Date(missing=None, location='query'),
        'sort': fields.Str(missing='price|ASC', location='query',
                           many=True, validate=validate.OneOf(SORT_CHOICE)),
        'format': fields.Str(location='query', validate=validate.Equal('json'))
    })
    def get(self, args):
        shops_param = request.args.getlist('shops')
        products_param = request.args.getlist('products')
        try:
            shop_ids = ids_field.deserialize(shops_param)
            products_ids = ids_field.deserialize(products_param)
        except ValidationError:
            return bad_request
        # Couldn't find easier way to parse duplicate arguments...

        with_geo = args['geoDist'] is not None and args['geoLng'] is not None and args['geoLat'] is not None
        no_geo = args['geoDist'] is None and args['geoLng'] is None and args['geoLat'] is None
        if not (with_geo or no_geo):
            return bad_request

        with_date = args['dateFrom'] is not None and args['dateTo'] is not None
        no_date = args['dateFrom'] is None and args['dateTo'] is None
        if not (with_date or no_date):
            return bad_request

        sort = args['sort'].split('|')
        if (sort[0] == 'geoDist' and no_geo) or (sort[0] == 'date' and no_date):
            return bad_request

        # extra validation, some combinations are illegal

        if with_geo:
            dist = Shop.distance(args['geoLat'], args['geoLng']).label('dist')
            query = db.session.query(Price, dist).filter(dist < args['geoDist'])
        else:
            dist = None
            query = Price.query

        query = query.join(Price.product, Price.shop)
        today = date.today()
        date_from = args['dateFrom'] if args['dateFrom'] else today
        date_to = args['dateTo'] if args['dateTo'] else today
        query = query.filter(date_from <= Price.date, Price.date <= date_to)

        if shop_ids:
            query = query.filter(Shop.id.in_(shop_ids))
        if products_ids:
            query = query.filter(Product.id.in_(products_ids))

        # TODO tags
        # maybe leave them as comma separated attribute

        sort_field = {
            'geoDist': dist,
            'price': Price.price,
            'date': Price.date
        }[sort[0]]

        sort_order = {
            'ASC' : asc,
            'DESC': desc
        }[sort[1]]

        query = query.order_by(sort_order(sort_field))
        prices = query.all()
        return PricesResource.PriceSchema(many=True).dump(prices).data

    @use_args({
        'price': fields.Float(required=True, location='json'),
        'date': fields.Date(required=True, location='json'),
        'productId': fields.Int(required=True, attribute='product_id', location='json'),
        'shopId': fields.Int(required=True, attribute='shop_id', location='json')
    })
    def post(self, args):
        shop = Shop.query.filter_by(id=args['shop_id']).first()
        product = Product.query.filter_by(id=args['shop_id']).first()
        if not (shop and product):
            return bad_request
        new_price = Price(**args)
        db.session.add(new_price)
        db.session.commit()
        return PricesResource.PriceSchema().dump(new_price).data
