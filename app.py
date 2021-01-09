from flask import Flask, render_template, redirect, url_for, session, request, logging
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators, SelectField
from passlib.hash import sha256_crypt
from functools import wraps
from flask_uploads import UploadSet, configure_uploads, IMAGES
import timeit
import datetime
from flask_mail import Mail, Message
import os
from wtforms.fields.html5 import EmailField
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel
import json


app = Flask(__name__)


# Config MySQL
mysql = MySQL()
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'Project@2020'
app.config['MYSQL_DB'] = 'rpa_portal'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'


# Initialize the app for use with this MySQL class
mysql.init_app(app)

class filterForm(Form):  # Create Filter Form
    version = SelectField('Version',
                       render_kw={'autofocus': True, 'placeholder': 'Version'})
    assettype = SelectField('Asset Type',
                       render_kw={'autofocus': True, 'placeholder': 'Asset Type'})
    vendor = SelectField('Vendor',
                       render_kw={'autofocus': True, 'placeholder': 'Vendor'})
    domain = SelectField('Domain',
                       render_kw={'autofocus': True, 'placeholder': 'Domain'})
    technology = SelectField('Technology',
                       render_kw={'autofocus': True, 'placeholder': 'Technology'})
    industry = SelectField('Industry',
                       render_kw={'autofocus': True, 'placeholder': 'Industry'})


@app.route('/', methods=['GET', 'POST'])
@app.route('/home.html', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        return redirect(url_for('home'))
    return render_template('home.html')


def content_based_filtering(item_id, num):
    curso = mysql.connection.cursor()
    curso.execute("SELECT rpa_id,domain FROM rpa_product ORDER BY rpa_id ASC")
    allrpa = curso.fetchall()
    curso.close()
    df = pd.DataFrame.from_dict(allrpa)
    df['domain'].replace(to_replace=[r"\\n","\n"], value=[", ",", "], regex=True, inplace = True)

    tf = TfidfVectorizer(analyzer='word', ngram_range=(1, 3), min_df=0, stop_words='english')
    tfidf_matrix = tf.fit_transform(df['domain'])

    cosine_similarities = linear_kernel(tfidf_matrix, tfidf_matrix)

    results = {}

    for idx, row in df.iterrows():
        similar_indices = cosine_similarities[idx].argsort()[:-100:-1]
        similar_items = [(cosine_similarities[idx][i], df['rpa_id'][i]) for i in similar_indices]
        results[row['rpa_id']] = similar_items[1:]

    # Just reads the results out of the dictionary
    print(results)
    item_id = int(item_id)
    recs = results[item_id][:num]
    print(recs)
    recommend_id = []
    for rec in recs:
        recommend_id.append(rec[-1])
    return recommend_id


@app.route('/send-message', methods=['POST'])
def sendMesage():
    if(request.method == 'POST'): 
        data = request.get_json()
        # Create Cursor
        curs = mysql.connection.cursor()
        curs.execute("INSERT INTO user(first_name, last_name, email, message) "
                         "VALUES(%s, %s, %s, %s)",
                         (data['firstName'], data['lastName'], data['email'], data['message']))
        # Commit cursor
        mysql.connection.commit()

        # Close Connection
        curs.close()
        return 'Success',200

@app.route('/apply-filter', methods=['POST'])
def filter():
    if(request.method == 'POST'): 
        data = request.get_json()
        # Create Cursor
        curs = mysql.connection.cursor()
        curs.execute("SELECT A.rpa_id, A.rpa_name FROM rpa_product AS A INNER JOIN ind_pdt_mapping AS B ON A.rpa_id = B.rpa_id  INNER JOIN industry AS C ON C.ind_id = B.ind_id WHERE A.version = %s AND A.asset_type = %s AND A.vendor = %s AND A.domain = %s AND A.technology = %s AND C.ind_name = %s ORDER BY A.rpa_id ASC",
                         (data['version'], data['assetType'], data['vendor'], data['domain'], data['technology'], data['industry']))
        row_headers=[x[0] for x in curs.description]
        rpaproducts = curs.fetchall()
        curs.close()
        
        json_data=[]
        for result in rpaproducts:
            #print(result)
            reslist = result.values()
            json_data.append(dict(zip(row_headers,reslist)))
            print(json_data)
        return json.dumps(json_data)
        # Close Connection
        


    
@app.route('/solution.html', methods=['GET', 'POST'])
def solution():
    print(request.method)
    # Create cursor
    cur = mysql.connection.cursor()
    # Get message
    cur.execute("SELECT DISTINCT version FROM rpa_product ")
    listVersion = [item['version'] for item in cur.fetchall()]
    cur.execute("SELECT DISTINCT asset_type FROM rpa_product ")
    listAssettype = [item['asset_type'] for item in cur.fetchall()]
    cur.execute("SELECT DISTINCT vendor FROM rpa_product ")
    listVendor = [item['vendor'] for item in cur.fetchall()]
    cur.execute("SELECT DISTINCT domain FROM rpa_product ")
    listDomain = [item['domain'] for item in cur.fetchall()]
    cur.execute("SELECT DISTINCT technology FROM rpa_product ")
    listTechnology = [item['technology'] for item in cur.fetchall()]
    cur.execute("SELECT DISTINCT ind_name FROM industry ")
    listIndustry = [item['ind_name'] for item in cur.fetchall()]
    # Close Connection
    cur.close()
    print(listIndustry)

    if 'src' in request.args:
        domain = request.args['src']
        curso = mysql.connection.cursor()
        curso.execute("SELECT * FROM rpa_product WHERE domain=%s ORDER BY rpa_id ASC", (domain,))
        rpaproducts = curso.fetchall()
        curso.close()
        return render_template('solution.html', products=rpaproducts, listVersion=listVersion,listAssettype=listAssettype, listDomain = listDomain, listVendor = listVendor, listTechnology = listTechnology, listIndustry = listIndustry )
    
    if 'value' in request.args:
        search_term = '%' + request.args['value'] + '%'
        curso = mysql.connection.cursor()
        curso.execute("SELECT * FROM rpa_product WHERE CONCAT(rpa_name,asset_type,vendor,domain,technology,description,software_involved) like %s ORDER BY rpa_id ASC", (search_term,))
        print(search_term)
        rpaproducts = curso.fetchall()
        curso.close()
        return render_template('solution.html', products=rpaproducts, listVersion=listVersion,listAssettype=listAssettype, listDomain = listDomain, listVendor = listVendor, listTechnology = listTechnology, listIndustry = listIndustry )
    
    if request.method == 'GET':
        curso = mysql.connection.cursor()
        curso.execute("SELECT * FROM rpa_product ORDER BY rpa_id ASC")
        rpaproducts = curso.fetchall()
        curso.close()
        return render_template('solution.html', products=rpaproducts, listVersion=listVersion,listAssettype=listAssettype, listDomain = listDomain, listVendor = listVendor, listTechnology = listTechnology, listIndustry = listIndustry )
    
    
@app.route('/details.html', methods=['POST', 'GET'])
def details():
    if 'id' in request.args:
        rpaid = request.args['id']
        curso = mysql.connection.cursor()
        curso.execute("SELECT * FROM rpa_product WHERE rpa_id=%s", (rpaid,))
        rpadetails = curso.fetchall()
        curso.execute("SELECT ind_name FROM industry AS A INNER JOIN ind_pdt_mapping AS B ON A.ind_id = B.ind_id INNER JOIN rpa_product AS C ON B.rpa_id = C.rpa_id WHERE C.rpa_id = %s", (rpaid,))
        list_industries = [item['ind_name'] for item in curso.fetchall()]
        print(list_industries)
        curso.close()
        recommend_id = content_based_filtering(item_id=rpaid, num=5)
        cur = mysql.connection.cursor()
        placeholders = ','.join((str(n) for n in recommend_id))
        query = 'SELECT * FROM rpa_product WHERE rpa_id IN (%s)' % placeholders
        cur.execute(query)
        recommendlist = cur.fetchall()
        #return render_template('solution.html', x=x, tshirts=products)
        return render_template('details.html', rpadetails=rpadetails, listOfIndustries=list_industries, recommendlist = recommendlist )

@app.route('/about_us.html', methods=['GET', 'POST'])
def about_us():
    return render_template('about_us.html')

if __name__ == '__main__':
    app.run(debug=True)