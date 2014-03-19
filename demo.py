import pandas
from operator import or_, and_
from dateutil import parser
from flask import Flask, request, render_template, make_response, current_app
from functools import update_wrapper
from datetime import timedelta
import json
import psycopg2
import psycopg2.extras

all = pandas.read_pickle('all.pickle')
comms = pandas.read_pickle('comms.pickle')
fins = pandas.read_pickle('fins.pickle')

app = Flask(__name__)


def cors(resp):
    resp = make_response(resp)
    resp.headers['Access-Control-Allow-Origin'] = '*'
    resp.headers['Content-Type'] = 'application/json'
    return resp


def html(resp):
    resp = make_response(resp)
    resp.headers['Access-Control-Allow-Origin'] = '*'
    resp.headers['Content-Type'] = 'text/html'
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
    return cors(result[offset:offset + limit].to_json(orient='records'))


@app.route('/')
def index():
    return html(render_template('./index.html'))


@app.route('/where')
def where():
    return html(render_template('./where.html'))


@app.route('/data')
def data():
    a = []
    with open('./data/heirTopBookTypes.json') as f:
        for line in f:
            line = line.rstrip('\n')
            a.append(line)
    return cors(''.join(a))


@app.route('/where_data')
def where_data():
    reply = ""
    try:
        reply = "success"
        conn = psycopg2.connect("dbname='hackoregon' user='<user>' password='<password>'")
    except:
        reply = "I am unable to connect to the database"

    types_to_children = {}
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    #Get the result set for SGA
    category = "Selling, General and Administrative Expenses (SGA)"
    sql_statement = \
        "select sub_type, SUM(amount) as amount from raw_committee_transactions where purpose_codes not " \
        "like '%General%' and purpose_codes not like '%radio, tv%' and purpose_codes not like '%Printing%' " \
        "and purpose_codes like '%Wages, Salaries, Benefits%' GROUP BY sub_type"
    process_cursor_results(cursor, sql_statement, types_to_children, category)

    sql_statement = \
        "select sub_type, SUM(amount) as amount from raw_committee_transactions where purpose_codes like '%General%' " \
        "and purpose_codes not like '%radio, tv%' and purpose_codes not like '%Printing%' GROUP BY sub_type"
    process_cursor_results(cursor, sql_statement, types_to_children, category)

    sql_statement = \
        "select sub_type, SUM(amount) as amount from raw_committee_transactions where purpose_codes like '%General%' " \
        "and purpose_codes not like '%radio, tv%' and purpose_codes like '%Printing%' GROUP BY sub_type"
    process_cursor_results(cursor, sql_statement, types_to_children, category)

    #Get the result set for Radio and TV advertising
    category = "Radio and TV advertising"
    sql_statement = \
        "select sub_type, SUM(amount) as amount from raw_committee_transactions where purpose_codes not like '%General%'" \
        " and purpose_codes like '%radio, tv%' and purpose_codes not like '%Printing%' GROUP BY sub_type"
    process_cursor_results(cursor, sql_statement, types_to_children, category)

    sql_statement = \
        "select sub_type, SUM(amount) as amount from raw_committee_transactions where purpose_codes like '%General%' " \
        "and purpose_codes like '%radio, tv%' and purpose_codes not like '%Printing%' GROUP BY sub_type"
    process_cursor_results(cursor, sql_statement, types_to_children, category)

    sql_statement = \
        "select sub_type, SUM(amount) as amount from raw_committee_transactions where purpose_codes not like '%General%'" \
        " and purpose_codes like '%radio, tv%' and purpose_codes like '%Printing%' GROUP BY sub_type"
    process_cursor_results(cursor, sql_statement, types_to_children, category)

    sql_statement = \
        "select sub_type, SUM(amount) as amount from raw_committee_transactions where purpose_codes like '%General%' " \
        "and purpose_codes like '%radio, tv%' and purpose_codes like '%Printing%' GROUP BY sub_type"
    process_cursor_results(cursor, sql_statement, types_to_children, category)

    #Get the result set for Printing
    category = "Printing"
    sql_statement = \
        "select sub_type, SUM(amount) as amount from raw_committee_transactions where purpose_codes not like '%General%'" \
        " and purpose_codes not like '%radio, tv%' and purpose_codes like '%Printing%' GROUP BY sub_type"
    process_cursor_results(cursor, sql_statement, types_to_children, category)

    #Get the result set for Additional printing records
    other_advertising_qualifier = "purpose_codes = 'Other Advertising (yard signs, buttons, etc.)'"
    process_cursor_results(cursor, create_common_sql(other_advertising_qualifier), types_to_children, category)

    #Get the result set for Travel expenses
    category = "Travel Expenses"
    travel_expense_qualifier = "purpose_codes = 'Travel Expenses (need description)'"
    process_cursor_results(cursor, create_common_sql(travel_expense_qualifier), types_to_children, category)

    #Get the result set for Personal Reimbursements
    category = "Personal Reimbursements"
    personal_reimbursement_qualifier = "purpose_codes = 'Reimbursement for Personal Expenditures'"
    process_cursor_results(cursor, create_common_sql(personal_reimbursement_qualifier), types_to_children, category)

    #Get the result set for Fundraising Events
    category = "Fundraising Events"
    fundamental_events_qualifier = "purpose_codes = 'Fundraising Event Expenses'"
    process_cursor_results(cursor, create_common_sql(fundamental_events_qualifier), types_to_children, category)

    #Get the result set for Surveys and Polls
    category = "Surveys and Polls"
    survey_and_polls_qualifier = "purpose_codes = 'Surveys and Polls'"
    process_cursor_results(cursor, create_common_sql(survey_and_polls_qualifier), types_to_children, category)

    #Get the result set for Advertising Agencies
    category = "Advertising Agencies"
    agent_qualifier = "purpose_codes = 'Agent'"
    process_cursor_results(cursor, create_common_sql(agent_qualifier), types_to_children, category)

    advertising_agencies_qualifier = "purpose_codes = 'Preparation and Production of Advertising'"
    process_cursor_results(cursor, create_common_sql(advertising_agencies_qualifier), types_to_children, category)

    #Get the result set for Management Services
    category = "Management Services"
    management_services_qualifier = "purpose_codes = 'Management Services'"
    process_cursor_results(cursor, create_common_sql(management_services_qualifier), types_to_children, category)

    #Get the result set for Postage
    category = "Postage"
    postage_qualifier = "purpose_codes = 'Postage'"
    process_cursor_results(cursor, create_common_sql(postage_qualifier), types_to_children, category)

    #Add utilities to SGA
    utilities_qualifier = "purpose_codes = 'Utilities'"
    process_cursor_results(cursor, create_common_sql(utilities_qualifier), types_to_children, category)

    #Finally everthing else gets tossed in the other bucket
    category = "Other"
    sql_statement = \
        "select sub_type, SUM(amount) as amount from raw_committee_transactions where purpose_codes not " \
        "like '%General%' and purpose_codes not like '%radio, tv%' and purpose_codes not like '%Printing%' " \
		"and not " + other_advertising_qualifier + " " \
		"and not " + travel_expense_qualifier + " " \
		"and not " + personal_reimbursement_qualifier + " " \
		"and not " + fundamental_events_qualifier + " " \
		"and not " + survey_and_polls_qualifier + " " \
		"and not " + agent_qualifier + " " \
		"and not " + advertising_agencies_qualifier + " " \
		"and not " + management_services_qualifier + " " \
		"and not " + postage_qualifier + " " \
		"and not " + utilities_qualifier + " " \
        "and purpose_codes like '%Wages, Salaries, Benefits%' GROUP BY sub_type"
    process_cursor_results(cursor, sql_statement, types_to_children, category)

    # Do not include this. It's contributions because purpose_code is null
    # cursor.execute(
    #     "select sub_type, SUM(amount) as amount from raw_committee_transactions where purpose_codes is null GROUP "
    #     "BY sub_type")
    # for row in cursor:
    #     tok_dict = {}
    #     tok_dict["name"] = row['sub_type']
    #     tok_dict["amount"] = abs(row['amount'])
    #     types_to_children["Other"].append(tok_dict)

#Convert data to json and return
    results = []
    for types in types_to_children:
        jdict = {}
        jdict["name"] = types
        jdict["children"] = types_to_children[types]
        results.append(jdict)

    wrapper = {}

    wrapper["name"] = "Where Did The Money Go"
    wrapper["children"] = results

    return cors(json.dumps(wrapper, sort_keys=True, indent=4))

def process_cursor_results(cursor, sql, types_to_children, category):
    types_to_children[category] = []
    cursor.execute(sql)
    for row in cursor:
        tok_dict = {}
        tok_dict["name"] = row['sub_type']
        tok_dict["amount"] = row['amount']

        if len(types_to_children[category]) > 0:
            # If key is already in list then add to amount otherwise append
            found = False
            for tuple in types_to_children[category]:
                if tuple["name"] == tok_dict["name"]:
                    found = True
                    tuple["amount"] += tok_dict["amount"]
            if not found:
                types_to_children[category].append(tok_dict)
        else:
            types_to_children[category].append(tok_dict)

def create_common_sql(exact_qualifier):
    return \
        "select sub_type, SUM(amount) as amount, purpose_codes from raw_committee_transactions where purpose_codes not " \
        "like '%General%' and purpose_codes not like '%radio, tv%' and purpose_codes not like '%Printing%' and " \
        "purpose_codes not like '%Wages, Salaries, Benefits%' AND " + exact_qualifier + " GROUP BY sub_type, purpose_codes"
		
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
