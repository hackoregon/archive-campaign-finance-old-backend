import pandas
from operator import or_, and_
from dateutil import parser
from json import dumps
from flask import Flask, request, render_template, make_response

all = pandas.read_pickle('all.pickle')
comms = pandas.read_pickle('comms.pickle')
fins = pandas.read_pickle('fins.pickle')

app = Flask(__name__)


def cors(resp):
    resp = make_response(resp)
    resp.headers['Access-Control-Allow-Origin'] = '*'
    resp.headers['Content-Type'] = 'application/json'
    return resp


def get_result():
    columns = request.form.getlist('columns')
    if not columns:
        columns = ['Committee Name']
    query = request.form.get('query', '')
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

    if query:
        result = result[reduce(or_, [result[c].str.lower().str.contains(query) for c in columns])]
    return result, offset, limit


@app.route('/search', methods=['POST'])
def search():
    result, offset, limit = get_result()
    return cors(result[offset:offset+limit].to_json(orient='records'))


@app.route('/')
def index():
    return cors(render_template('./index.html'))


@app.route('/CC/<id>')
def cc(id):
    return 


@app.route('/top/<com_type>/<sub_type>')
def top(com_type, sub_type):
    # select committees
    cs = comms[comms['Committee Type'] == com_type]
    
    fs = fins[fins['Filer Id'].isin(cs.index) &
              (fins['Sub Type'] == sub_type)]
    
    result_name = 'Total %s' % sub_type
    cs[result_name] = fs.groupby('Filer Id').Amount.sum()
    cs = cs.dropna(subset=[result_name])
    cs = cs.sort(result_name, ascending=False)
    return cors(cs[:50].to_json(orient='records'))

if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0')
