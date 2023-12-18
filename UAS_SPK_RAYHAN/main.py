from http import HTTPStatus
from flask import Flask, request, abort
from flask_restful import Resource, Api 
from models import monitor as monitorModel
from engine import engine
from sqlalchemy import select
from sqlalchemy.orm import Session

session = Session(engine)

app = Flask(__name__)
api = Api(app)        

class BaseMethod():

    def __init__(self):
        self.raw_weight = {'reputasi_brand': 3, 'refresh_rate': 7, 'resolusi': 4, 'harga': 2, 'ukuran_layar': 3}

    @property
    def weight(self):
        total_weight = sum(self.raw_weight.values())
        return {k: round(v/total_weight, 2) for k, v in self.raw_weight.items()}

    @property
    def data(self):
        query = select(monitorModel.nama_monitor, monitorModel.reputasi_brand, monitorModel.refresh_rate, monitorModel.resolusi, monitorModel.harga, monitorModel.ukuran_layar)
        result = session.execute(query).fetchall()
        print(result)
        return [{'nama_monitor': monitor.nama_monitor, 'reputasi_brand': monitor.reputasi_brand, 'refresh_rate': monitor.refresh_rate, 'resolusi': monitor.resolusi, 'harga': monitor.harga, 'ukuran_layar': monitor.ukuran_layar} for monitor in result]

    @property
    def normalized_data(self):
        reputasi_brand_values = []
        refresh_rate_values = []
        resolusi_values = []
        harga_values = []
        ukuran_layar_values = []

        for data in self.data:
            reputasi_brand_values.append(data['reputasi_brand'])
            refresh_rate_values.append(data['refresh_rate'])
            resolusi_values.append(data['resolusi'])
            harga_values.append(data['harga'])
            ukuran_layar_values.append(data['ukuran_layar'])

        return [
            {'nama_monitor': data['nama_monitor'],
             'reputasi_brand': min(reputasi_brand_values) / data['reputasi_brand'],
             'refresh_rate': data['refresh_rate'] / max(refresh_rate_values),
             'resolusi': data['resolusi'] / max(resolusi_values),
             'harga': data['harga'] / max(harga_values),
             'ukuran_layar': data['ukuran_layar'] / max(ukuran_layar_values)
             }
            for data in self.data
        ]

    def update_weights(self, new_weights):
        self.raw_weight = new_weights

class WeightedProductCalculator(BaseMethod):
    def update_weights(self, new_weights):
        self.raw_weight = new_weights

    @property
    def calculate(self):
        normalized_data = self.normalized_data
        produk = []

        for row in normalized_data:
            product_score = (
                row['reputasi_brand'] ** self.raw_weight['reputasi_brand'] *
                row['refresh_rate'] ** self.raw_weight['refresh_rate'] *
                row['resolusi'] ** self.raw_weight['resolusi'] *
                row['harga'] ** self.raw_weight['harga'] *
                row['ukuran_layar'] ** self.raw_weight['ukuran_layar']
            )

            produk.append({
                'nama_monitor': row['nama_monitor'],
                'produk': product_score
            })

        sorted_produk = sorted(produk, key=lambda x: x['produk'], reverse=True)

        sorted_data = []

        for product in sorted_produk:
            sorted_data.append({
                'nama_monitor': product['nama_monitor'],
                'score': product['produk']
            })

        return sorted_data


class WeightedProduct(Resource):
    def get(self):
        calculator = WeightedProductCalculator()
        result = calculator.calculate
        return result, HTTPStatus.OK.value
    
    def post(self):
        new_weights = request.get_json()
        calculator = WeightedProductCalculator()
        calculator.update_weights(new_weights)
        result = calculator.calculate
        return {'data': result}, HTTPStatus.OK.value
    

class SimpleAdditiveWeightingCalculator(BaseMethod):
    @property
    def calculate(self):
        weight = self.weight
        result = {row['nama_monitor']:
                  round(row['reputasi_brand'] * weight['reputasi_brand'] +
                        row['refresh_rate'] * weight['refresh_rate'] +
                        row['resolusi'] * weight['resolusi'] +
                        row['harga'] * weight['harga'] +
                        row['ukuran_layar'] * weight['ukuran_layar'], 2)
                  for row in self.normalized_data
                  }
        sorted_result = dict(
            sorted(result.items(), key=lambda x: x[1], reverse=True))
        return sorted_result

    def update_weights(self, new_weights):
        self.raw_weight = new_weights

class SimpleAdditiveWeighting(Resource):
    def get(self):
        saw = SimpleAdditiveWeightingCalculator()
        result = saw.calculate
        return result, HTTPStatus.OK.value

    def post(self):
        new_weights = request.get_json()
        saw = SimpleAdditiveWeightingCalculator()
        saw.update_weights(new_weights)
        result = saw.calculate
        return {'data': result}, HTTPStatus.OK.value


class monitor(Resource):
    def get_paginated_result(self, url, list, args):
        page_size = int(args.get('page_size', 10))
        page = int(args.get('page', 1))
        page_count = int((len(list) + page_size - 1) / page_size)
        start = (page - 1) * page_size
        end = min(start + page_size, len(list))

        if page < page_count:
            next_page = f'{url}?page={page+1}&page_size={page_size}'
        else:
            next_page = None
        if page > 1:
            prev_page = f'{url}?page={page-1}&page_size={page_size}'
        else:
            prev_page = None
        
        if page > page_count or page < 1:
            abort(404, description=f'Halaman {page} tidak ditemukan.') 
        return {
            'page': page, 
            'page_size': page_size,
            'next': next_page, 
            'prev': prev_page,
            'Results': list[start:end]
        }

    def get(self):
        query = select(monitorModel)
        data = [{'nama_monitor': monitor.nama_monitor, 'reputasi_brand': monitor.reputasi_brand, 'refresh_rate': monitor.refresh_rate, 'resolusi': monitor.resolusi, 'harga': monitor.harga, 'ukuran_layar': monitor.ukuran_layar} for monitor in session.scalars(query)]
        return self.get_paginated_result('monitor/', data, request.args), HTTPStatus.OK.value


api.add_resource(monitor, '/monitor')
api.add_resource(WeightedProduct, '/wp')
api.add_resource(SimpleAdditiveWeighting, '/saw')

if __name__ == '__main__':
    app.run(port='5005', debug=True)