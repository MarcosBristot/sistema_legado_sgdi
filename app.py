from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = '123456'

ORDEM_PRIORIDADE = "CASE prioridade WHEN 'Critica' THEN 1 WHEN 'Alta' THEN 2 WHEN 'Media' THEN 3 WHEN 'Baixa' THEN 4 END"


def get_db():
    conn = sqlite3.connect('demandas.db')
    conn.row_factory = sqlite3.Row
    return conn


@app.route('/')
def index():
    conn = sqlite3.connect('demandas.db')
    cursor = conn.cursor()
    demandas = cursor.execute(
        f'SELECT * FROM demandas ORDER BY {ORDEM_PRIORIDADE}'
    ).fetchall()
    conn.close()
    return render_template('index.html', demandas=demandas)


@app.route('/nova_demanda', methods=['GET', 'POST'])
def nova_demanda():
    if request.method == 'POST':
        titulo = request.form['titulo'].strip()
        descricao = request.form['descricao'].strip()
        solicitante = request.form['solicitante'].strip()
        prioridade = request.form['prioridade'].strip()

        if not titulo or not descricao or not solicitante:
            flash('Todos os campos são obrigatórios.')
            return render_template('nova_demanda.html')

        conn = sqlite3.connect('demandas.db')
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO demandas (titulo, descricao, solicitante, data_criacao, prioridade) VALUES (?, ?, ?, ?, ?)",
            (titulo, descricao, solicitante, datetime.now(), prioridade))
        conn.commit()
        conn.close()

        flash('Demanda salva com sucesso!')
        return redirect('/')

    return render_template('nova_demanda.html')


@app.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar(id):
    conn = sqlite3.connect('demandas.db')
    cursor = conn.cursor()

    if request.method == 'POST':
        titulo = request.form['titulo'].strip()
        descricao = request.form['descricao'].strip()
        solicitante = request.form['solicitante'].strip()
        prioridade = request.form['prioridade'].strip()

        if not titulo or not descricao or not solicitante:
            demanda = cursor.execute('SELECT * FROM demandas WHERE id=?', (id,)).fetchone()
            conn.close()
            flash('Todos os campos são obrigatórios.')
            return render_template('editar.html', demanda=demanda)

        cursor.execute(
            "UPDATE demandas SET titulo=?, descricao=?, solicitante=?, prioridade=? WHERE id=?",
            (titulo, descricao, solicitante, prioridade, id))
        conn.commit()
        conn.close()
        return redirect('/')

    demanda = cursor.execute('SELECT * FROM demandas WHERE id=?', (id,)).fetchone()
    conn.close()
    return render_template('editar.html', demanda=demanda)


@app.route('/deletar/<int:id>')
def deletar(id):
    conn = sqlite3.connect('demandas.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM demandas WHERE id=?', (id,))
    conn.commit()
    conn.close()
    flash('Demanda deletada!')
    return redirect('/')


@app.route('/buscar')
def buscar():
    termo = request.args.get('q', '')
    conn = sqlite3.connect('demandas.db')
    cursor = conn.cursor()
    resultados = cursor.execute(
        f"SELECT * FROM demandas WHERE titulo LIKE ? ORDER BY {ORDEM_PRIORIDADE}",
        (f'%{termo}%',)
    ).fetchall()
    conn.close()
    return render_template('index.html', demandas=resultados)


@app.route('/detalhes/<int:id>')
def detalhes(id):
    conn = sqlite3.connect('demandas.db')
    cursor = conn.cursor()
    demanda = cursor.execute('SELECT * FROM demandas WHERE id=?', (id,)).fetchone()
    comentarios = cursor.execute('SELECT * FROM comentarios WHERE demanda_id=?', (id,)).fetchall()
    conn.close()
    return render_template('detalhes.html', demanda=demanda, comentarios=comentarios)


@app.route('/adicionar_comentario/<int:demanda_id>', methods=['POST'])
def adicionar_comentario(demanda_id):
    comentario = request.form['comentario'].strip()
    autor = request.form['autor'].strip()

    if not comentario or not autor:
        flash('Preencha seu nome e o comentário antes de enviar.')
        return redirect(f'/detalhes/{demanda_id}')

    conn = sqlite3.connect('demandas.db')
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO comentarios (demanda_id, comentario, autor, data) VALUES (?, ?, ?, ?)",
        (demanda_id, comentario, autor, datetime.now()))
    conn.commit()
    conn.close()

    return redirect(f'/detalhes/{demanda_id}')


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')