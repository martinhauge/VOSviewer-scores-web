from flask import Flask, render_template, request, flash, jsonify
from logic.scores import ScoresHandler, scores_dict

app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

@app.route('/', methods=['GET', 'POST'])
def main():
    if request.method == 'GET':
        return render_template('pg.html', scores=scores_dict)
    else:
        data = ScoresHandler(request.form, request.files.getlist("input"))

        if data.success:
            data.create_df()
        else:
            data.clean_up()
            return render_template('pg.html', scores=scores_dict)
        
        if data.success:
            data.generate_scores()
            data.save_output_files()
        else:
            flash('Could not generate DataFrame. Make sure selected database matches input file(s).', 'danger')

        data.clean_up()
        return render_template('pg.html', scores=scores_dict)

if __name__ == '__main__':
    app.run(host='127.0.0.5', port=5000, debug=True)