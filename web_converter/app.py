import os
from flask import Flask, render_template, request, send_from_directory, flash, redirect, url_for
from werkzeug.utils import secure_filename
from convert_to_lines import process_dxf

# Basic Flask app configuration
app = Flask(__name__)
app.config['SECRET_KEY'] = 'supersecretkey'
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
app.config['PROCESSED_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'processed')
app.config['ALLOWED_EXTENSIONS'] = {'dxf'}

# File to store the conversion count
COUNT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'conversion_count.txt')

# Ensure upload and processed folders exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['PROCESSED_FOLDER'], exist_ok=True)

# --- Helper Functions ---

def allowed_file(filename):
    """Check if the file has an allowed extension."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def get_conversion_count():
    """Reads the current conversion count from a file."""
    try:
        with open(COUNT_FILE, 'r') as f:
            return int(f.read().strip())
    except (IOError, ValueError):
        return 0

def increment_conversion_count():
    """Increments the conversion count in a file."""
    count = get_conversion_count() + 1
    with open(COUNT_FILE, 'w') as f:
        f.write(str(count))

# --- Routes ---

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    conversion_count = get_conversion_count()
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            input_filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            
            try:
                file.save(input_filepath)
                
                try:
                    tolerance = float(request.form.get('tolerance', '0.01'))
                    if tolerance <= 0:
                        raise ValueError("Tolerance must be a positive number.")
                except (ValueError, TypeError) as e:
                    flash(f'Invalid tolerance value: {e}')
                    return redirect(request.url)

                base, ext = os.path.splitext(filename)
                output_filename = f"{base}_Converted_by_Aji-SWG_Dev.dxf"
                output_filepath = os.path.join(app.config['PROCESSED_FOLDER'], output_filename)

                success, message, logs = process_dxf(input_filepath, output_filepath, tolerance)

                if success:
                    increment_conversion_count()
                    # Update count for the current request
                    conversion_count = get_conversion_count()

                return render_template('index.html', 
                                         logs=logs, 
                                         download_url=url_for('download_file', filename=output_filename) if success else None,
                                         conversion_done=True,
                                         conversion_count=conversion_count)
            finally:
                # Ensure the uploaded file is deleted after processing
                if os.path.exists(input_filepath):
                    os.remove(input_filepath)

    return render_template('index.html', conversion_done=False, conversion_count=conversion_count)

@app.route('/downloads/<filename>')
def download_file(filename):
    return send_from_directory(app.config['PROCESSED_FOLDER'], filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
