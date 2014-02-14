import pandas
from operator import or_, and_
from dateutil import parser
from json import dumps
from flask import Flask, request, render_template, make_response

all = pandas.read_pickle('all.pickle')

app = Flask(__name__)

def cors(resp):
    resp = make_response(resp)
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp

@app.route('/search', methods=['POST'])
def search():
    columns = request.form.getlist('columns')
    if not columns:
        columns = ['Committee Name']
    query = request.form['query']
    offset = int(request.form.get('offset', 0))
    limit = min(int(request.form.get('limit', 10)), 100)
    from_date = request.form.get('from_date')
    to_date = request.form.get('to_date')
    dates = []
    result = all

    if from_date:
        from_data = all['Tran Date'] > parser.parse(from_date)
        dates.append(from_data)
    if to_date:
        to_data = all['Tran Date'] < parser.parse(to_date)
        dates.append(to_data)

    if dates:
        result = result[reduce(and_, dates)]
    result = result[reduce(or_, [result[c].str.lower().str.contains(query) for c in columns])]
    return cors(result[offset:offset+limit].to_json(orient='records'))

@app.route('/')
def index():
    return cors(render_template('./index.html'))

if __name__ == '__main__':
    app.run(host='0.0.0.0')
