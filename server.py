from flask import Flask, render_template, request
from os.path import join, dirname
from werkzeug.utils import secure_filename
import tempfile

server = Flask(__name__)


@server.route('/')
@server.route('/home')
def home():
    return render_template('home.html')


@server.route('/upload')
def test():
    return render_template('upload.html')


@server.route('/result', methods=['GET', 'POST'])
def result():
    classifier_names = [
        'label(score)', 'sa', 'da', 'sp', 'dp', 'pr', 'pkt_in', 'pkt_out'
    ]
    if request.method == 'POST':
        print(request.files.get('upload'))
        is_upload = False
        if request.files.get('upload') != None:
            upload = request.files.get('upload')
            dir_name = tempfile.mkdtemp()
            upload.save(dir_name + '/' + secure_filename(upload.filename))
            is_upload = True
            file_dir_name = str(dir_name + '/' +
                                secure_filename(upload.filename))
            print(file_dir_name)
            return render_template(
                'result.html',
                file_dir_name=file_dir_name,
                results=None,
                num_flows=None,
                t=None,
                classifier_names=classifier_names)
        else:
            return render_template(
                'result.html',
                file_dir_name=None,
                results=None,
                num_flows=None,
                t=None,
                classifier_names=classifier_names)
    else:
        return render_template(
            'result.html',
            file_dir_name=None,
            results=None,
            num_flows=None,
            t=None,
            classifier_names=classifier_names)


server.run(port=5000, debug=True)
