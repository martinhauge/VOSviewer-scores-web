from flask import Flask, render_template, request, flash
from logic.scores import ScoresHandler
from time import sleep

ALLOWED_EXTENSIONS = ['csv', 'txt', 'xls']

app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

@app.route('/', methods=['GET', 'POST'])
def main():
    if request.method == 'GET':
        return render_template('pg.html')
    else:
        data = ScoresHandler(request.form, request.files.getlist("input"))
        #data.summary()
        if data.success:
            #data.summary()
            data.create_df()
        else:
            data.clean_up()
            return render_template('pg.html')
        if data.success:
            data.generate_scores()
            #print(data.scores_df.head())
            data.save_output_files()
        else:
            flash('Could not generate DataFrame. Make sure selected database matches input file(s).', 'danger')
        #sleep(3)
        data.clean_up()
        #for item in data.messages:
        #    flash(item, 'warning')
        return render_template('pg.html')

if __name__ == '__main__':
    app.run(host='127.0.0.5', port=5000, debug=True)