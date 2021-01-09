from main import app
from flask import Flask, send_from_directory, flash, request, redirect, url_for, render_template
import os
from werkzeug.utils import secure_filename
import functions as fn

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Root URL
@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and fn.allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.abspath(app.config['UPLOAD_FOLDER'])
            file.save(os.path.join(file_path,filename))
            print(file_path)
            fn.insertData(file_path,filename)
            return redirect(url_for('uploaded_file',
                                    filename=filename))
    # Set The upload HTML template '\templates\uploadForm.html'
    return render_template('uploadForm.html')


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'],
                               filename)