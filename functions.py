import pandas as pd
import numpy as np
import mysql.connector
from mysql.connector import Error
import time
import datetime
import os

mydb = mysql.connector.connect(
  host="localhost",
  user="root",
  password="Project@2020",
  database="rpa_portal"
)

'''
def parseCSV(filePath):
      csvData = pd.read_csv(filePath)
      print(csvData.head(2))
'''

ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'csv', 'docx'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def convertToBinaryData(filename):
    # Convert digital data to binary format
    with open(filename, 'rb') as file:
        binaryData = file.read()
    return binaryData

def insertData(filePath, fileName):
    print("Inserting data into rpa_product table")
    try:
        cursor = mydb.cursor()
        csvPath = os.path.join(filePath, fileName)
        csvData = pd.read_csv(csvPath)
        csvData = csvData.replace(np.nan, '', regex=True)
        print(csvData.head(2))

        sql_query = """ INSERT INTO rpa_product
                          (rpa_id, rpa_name, version, asset_type,
                          price, vendor, domain, technology, prerequisites, 
                          description, rpa_link, helping_doc, icon, software_involved,
                          status, date_added, date_modified) 
                          VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""

        for i,row in csvData.iterrows():

            icon = filePath + '/icons/' + str(i+1) + '.png'
            PDF = filePath + '/Helpdoc/' + str(i+1) + '.pdf'

            icon = convertToBinaryData(icon)
            helping_doc = convertToBinaryData(PDF)

            ts = time.time()
            timestamp = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')

            # Convert data into tuple format
            insert_value = (i+1, row['rpa_name'], row['version'], row['asset_type'],
                            row['Price'], row['vendor'], row['domain'], row['technology'],
                            row['prerequisites'], row['description'], row['rpa_link'], 
                            helping_doc, icon, row['software_involved'], 'yes', timestamp, timestamp)
            result = cursor.execute(sql_query, insert_value)
            mydb.commit()
            print("Data inserted successfully", result)

    except mysql.connector.Error as error:
        print("Failed inserting data into MySQL table {}".format(error))

    finally:
        if (mydb.is_connected()):
            cursor.close()
            mydb.close()
            print("MySQL mydb is closed")
