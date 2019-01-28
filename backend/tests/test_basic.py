import pytest
from app.models import User
from tests import url_for, auth_header
from tests import data
from collections import Counter


def valid_response(real_data, json):
    for attr in real_data.keys():
        if isinstance(real_data[attr], list):
            assert Counter(real_data[attr]) == Counter(json[attr])
        else:
            assert real_data[attr] == json[attr]


@pytest.mark.usefixtures("user1", "root")
class TestBasic(object):
    def test_login(self, client, user1):
        rv = client.post(url_for('/login'))
        assert rv.status_code == 400

        rv = client.post(url_for('/login'), data=user1)
        assert rv.status_code == 200
        assert rv.json['token'] == User.query.filter(User.username == user1['username']).first().token

    @pytest.mark.parametrize("product_data", data.products)
    def test_add_product(self, client, product_data, user1_token):
        rv = client.post(
            url_for('/products'),
            headers=auth_header(user1_token),
            data=product_data
        )
        assert rv.status_code == 200
        valid_response(product_data, rv.json)

    def test_list_products(self, client, user1_token):
        rv = client.get(
            url_for("/products?start=0&count=10&status=ACTIVE&sort=id%7CASC"),
            headers=auth_header(user1_token)
        )

        assert rv.status_code == 200
        assert rv.json['start'] == 0
        assert rv.json['count'] == 2
        assert rv.json['total'] == 2
        assert len(rv.json['products']) == 2
        for i, product in enumerate(data.products):
            valid_response(product, rv.json['products'][i])

    def test_update_product(self, client, user1_token):
        prod1upd = data.products[0].copy()
        prod1upd.update({
            "name": 'bar-foo',
            "description": '4217a'
        })

        rv = client.put(
            url_for("/products/1"),
            headers=auth_header(user1_token),
            data=prod1upd
        )

        assert rv.status_code == 200
        valid_response(prod1upd, rv.json)

    def test_get_product(self, client, user1_token):
        rv = client.get(
            url_for("/products/2"),
            headers=auth_header(user1_token)
        )

        assert rv.status_code == 200
        valid_response(data.products[1], rv.json)

    def test_patch_product(self, client, user1_token):
        prod2patch = data.products[1].copy()
        prod2patch.update({'tags': ['nope']})
        rv = client.patch(
            url_for("/products/2"),
            headers=auth_header(user1_token),
            data={'tags': prod2patch['tags']}
        )

        assert rv.status_code == 200
        valid_response(prod2patch, rv.json)

    def test_delete_product(self, client, user1_token):
        rv = client.delete(
            url_for("/products/2"),
            headers=auth_header(user1_token)
        )

        assert rv.status_code == 200
        assert rv.json['message'] == "OK"

    @pytest.mark.parametrize("shop_data", data.shops)
    def test_add_shop(self, client, shop_data, user1_token):
        rv = client.post(
            url_for('/shops'),
            headers=auth_header(user1_token),
            data=shop_data
        )

        assert rv.status_code == 200
        valid_response(shop_data, rv.json)

    def test_list_shops(self, client, user1_token):
        rv = client.get(
            url_for("/shops?start=0&count=10&status=ACTIVE&sort=id%7CASC"),
            headers=auth_header(user1_token)
        )

        assert rv.status_code == 200
        assert rv.json['start'] == 0
        assert rv.json['count'] == 2
        assert rv.json['total'] == 2
        assert len(rv.json['shops']) == 2
        for i, shop_data in enumerate(data.shops):
            valid_response(shop_data, rv.json['shops'][i])

    def test_update_shop(self, client, user1_token):
        shop1upd = data.shops[0].copy()
        shop1upd.update({
            "name": 'baz-foo',
            "lng": 420
        })

        rv = client.put(
            url_for("/shops/1"),
            headers=auth_header(user1_token),
            data=shop1upd
        )

        assert rv.status_code == 200
        valid_response(shop1upd, rv.json)

    def test_get_shop(self, client, user1_token):
        rv = client.get(
            url_for("/shops/2"),
            headers=auth_header(user1_token)
        )

        assert rv.status_code == 200
        valid_response(data.shops[1], rv.json)

    def test_path_shop(self, client, user1_token):
        shop2patch = data.shops[1].copy()
        shop2patch.update({'lat': 99})
        rv = client.patch(
            url_for("/shops/2"),
            headers=auth_header(user1_token),
            data={'lat': shop2patch['lat']}
        )

        assert rv.status_code == 200
        valid_response(shop2patch, rv.json)

    def test_delete_shop(self, client, user1_token):
        rv = client.delete(
            url_for("/shops/2"),
            headers=auth_header(user1_token)
        )

        assert rv.status_code == 200
        assert rv.json['message'] == "OK"

    def test_logout(self, client, user1):
        token = User.query.filter(User.username == user1['username']).first().token

        rv = client.post(url_for('/logout'))
        assert rv.status_code == 403

        rv = client.post(url_for('/logout'), headers=auth_header(token))

        assert rv.status_code == 200
        assert not User.query.filter(User.username == user1['username']).first().token
        assert rv.json['message'] == "OK"


# TODO /price test
