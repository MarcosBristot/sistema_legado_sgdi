from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

app = Flask(__name__)
app.secret_key = 'sgdi_sprint3_secret_2026'

ORDEM_PRIORIDADE = "CASE prioridade WHEN 'Critica' THEN 1 WHEN 'Alta' THEN 2 WHEN 'Media' THEN 3 WHEN 'Baixa' THEN 4 END"

PRIORIDADES_VALIDAS = {'Critica', 'Alta', 'Media', 'Baixa'}


def get_db():
    conn = sqlite3.connect('demandas.db')
    conn.row_factory = sqlite3.Row
    return conn


# ── Card 4: Decorator de proteção de rotas ────────────────────────────────────
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario_id' not in session:
            flash('Você precisa estar logado para acessar esta página.')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


# ── Card 2: Cadastro de usuário ───────────────────────────────────────────────
@app.route('/novo_usuario', methods=['GET', 'POST'])
def novo_usuario():
    if request.method == 'POST':
        nome = request.form['nome'].strip()
        email = request.form['email'].strip()
        senha = request.form['senha'].strip()

        if not nome or not email or not senha:
            flash('Todos os campos são obrigatórios.')
            return render_template('novo_usuario.html')

        senha_hash = generate_password_hash(senha)
        data_criacao = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        conn = get_db()
        existente_nome = conn.execute('SELECT id FROM usuarios WHERE nome = ?', (nome,)).fetchone()
        existente_email = conn.execute('SELECT id FROM usuarios WHERE email = ?', (email,)).fetchone()
        if existente_nome:
            conn.close()
            flash('Este nome de usuário já está em uso. Escolha outro.')
            return render_template('novo_usuario.html')
        if existente_email:
            conn.close()
            flash('Este e-mail já está cadastrado.')
            return render_template('novo_usuario.html')
        try:
            conn.execute(
                "INSERT INTO usuarios (nome, email, senha_hash, cargo, data_criacao) VALUES (?, ?, ?, 'comum', ?)",
                (nome, email, senha_hash, data_criacao)
            )
            conn.commit()
            flash('Usuário cadastrado com sucesso! Faça login.')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Erro ao cadastrar. Verifique os dados e tente novamente.')
            return render_template('novo_usuario.html')
        finally:
            conn.close()

    return render_template('novo_usuario.html')


# ── Card 3: Login e sessão ────────────────────────────────────────────────────
@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'usuario_id' in session:
        return redirect(url_for('index'))

    if request.method == 'POST':
        email = request.form['email'].strip()
        senha = request.form['senha'].strip()

        conn = get_db()
        usuario = conn.execute(
            'SELECT * FROM usuarios WHERE email = ?', (email,)
        ).fetchone()
        conn.close()

        if usuario and check_password_hash(usuario['senha_hash'], senha):
            session['usuario_id'] = usuario['id']
            session['usuario_nome'] = usuario['nome']
            session['usuario_cargo'] = usuario['cargo']
            flash(f'Bem-vindo, {usuario["nome"]}!')
            return redirect(url_for('index'))
        else:
            flash('E-mail ou senha inválidos.')

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('Você saiu do sistema.')
    return redirect(url_for('login'))


# ── Card 4 + 6 + 8: Index com proteção, JOIN e filtro por usuário ─────────────
@app.route('/')
@login_required
def index():
    prioridade = request.args.get('prioridade', '').strip()
    usuario_filtro = request.args.get('usuario_id', '').strip()

    conn = get_db()

    # Card 6: JOIN com usuarios para exibir nome do criador
    base_query = f"""
        SELECT d.*, u.nome AS nome_criador, u.email AS email_criador
        FROM demandas d
        LEFT JOIN usuarios u ON d.criado_por = u.id
    """

    conditions = []
    params = []

    if prioridade and prioridade in PRIORIDADES_VALIDAS:
        conditions.append("d.prioridade = ?")
        params.append(prioridade)
    else:
        prioridade = ''

    # Card 8: filtro por usuário específico
    if usuario_filtro:
        conditions.append("d.criado_por = ?")
        params.append(usuario_filtro)

    if conditions:
        base_query += " WHERE " + " AND ".join(conditions)

    base_query += f" ORDER BY {ORDEM_PRIORIDADE}"

    demandas = conn.execute(base_query, params).fetchall()

    # Card 8: lista de usuários para o filtro no template
    usuarios = conn.execute('SELECT id, nome, email FROM usuarios ORDER BY nome').fetchall()
    conn.close()

    return render_template(
        'index.html',
        demandas=demandas,
        prioridade_ativa=prioridade,
        usuarios=usuarios,
        usuario_filtro_ativo=usuario_filtro
    )


# ── Card 4 + 5: Nova demanda com proteção e registro do criador ───────────────
@app.route('/nova_demanda', methods=['GET', 'POST'])
@login_required
def nova_demanda():
    if request.method == 'POST':
        titulo = request.form['titulo'].strip()
        descricao = request.form['descricao'].strip()
        solicitante = request.form['solicitante'].strip()
        prioridade = request.form['prioridade'].strip()

        if not titulo or not descricao or not solicitante:
            flash('Todos os campos são obrigatórios.')
            return render_template('nova_demanda.html')

        conn = get_db()
        conn.execute(
            "INSERT INTO demandas (titulo, descricao, solicitante, data_criacao, prioridade, criado_por) VALUES (?, ?, ?, ?, ?, ?)",
            (titulo, descricao, solicitante, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), prioridade, session['usuario_id'])
        )
        conn.commit()
        conn.close()

        flash('Demanda salva com sucesso!')
        return redirect('/')

    return render_template('nova_demanda.html')


# ── Card 4 + 7: Editar com proteção e registro de histórico ──────────────────
@app.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar(id):
    conn = get_db()

    if request.method == 'POST':
        titulo = request.form['titulo'].strip()
        descricao = request.form['descricao'].strip()
        solicitante = request.form['solicitante'].strip()
        prioridade = request.form['prioridade'].strip()

        demanda_atual = conn.execute('SELECT * FROM demandas WHERE id=?', (id,)).fetchone()

        if not titulo or not descricao or not solicitante:
            flash('Todos os campos são obrigatórios.')
            conn.close()
            return render_template('editar.html', demanda=demanda_atual)

        # Card 7: registrar histórico de cada campo alterado
        campos = {
            'titulo': (demanda_atual['titulo'], titulo),
            'descricao': (demanda_atual['descricao'], descricao),
            'solicitante': (demanda_atual['solicitante'], solicitante),
            'prioridade': (demanda_atual['prioridade'], prioridade),
        }
        agora = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        for campo, (anterior, novo) in campos.items():
            if anterior != novo:
                conn.execute(
                    "INSERT INTO historico_edicoes (demanda_id, usuario_id, data, campo_alterado, valor_anterior, valor_novo) VALUES (?, ?, ?, ?, ?, ?)",
                    (id, session['usuario_id'], agora, campo, anterior, novo)
                )

        conn.execute(
            "UPDATE demandas SET titulo=?, descricao=?, solicitante=?, prioridade=? WHERE id=?",
            (titulo, descricao, solicitante, prioridade, id)
        )
        conn.commit()
        conn.close()
        flash('Demanda atualizada com sucesso!')
        return redirect('/')

    demanda = conn.execute('SELECT * FROM demandas WHERE id=?', (id,)).fetchone()
    conn.close()
    return render_template('editar.html', demanda=demanda)


@app.route('/deletar/<int:id>')
@login_required
def deletar(id):
    conn = get_db()
    demanda = conn.execute('SELECT criado_por FROM demandas WHERE id=?', (id,)).fetchone()
    if not demanda:
        conn.close()
        flash('Demanda não encontrada.')
        return redirect('/')
    eh_admin = session.get('usuario_cargo') == 'admin'
    eh_dono = demanda['criado_por'] == session['usuario_id']
    if not eh_admin and not eh_dono:
        conn.close()
        flash('Você não tem permissão para excluir esta demanda.')
        return redirect('/')
    conn.execute('DELETE FROM demandas WHERE id=?', (id,))
    conn.commit()
    conn.close()
    flash('Demanda deletada!')
    return redirect('/')


# ── Card 4 + 8: Buscar com proteção e filtro por usuário ─────────────────────
@app.route('/buscar')
@login_required
def buscar():
    termo = request.args.get('q', '')
    prioridade = request.args.get('prioridade', '').strip()
    usuario_filtro = request.args.get('usuario_id', '').strip()

    conn = get_db()

    base_query = f"""
        SELECT d.*, u.nome AS nome_criador, u.email AS email_criador
        FROM demandas d
        LEFT JOIN usuarios u ON d.criado_por = u.id
        WHERE d.titulo LIKE ?
    """
    params = [f'%{termo}%']

    if prioridade and prioridade in PRIORIDADES_VALIDAS:
        base_query += " AND d.prioridade = ?"
        params.append(prioridade)
    else:
        prioridade = ''

    if usuario_filtro:
        base_query += " AND d.criado_por = ?"
        params.append(usuario_filtro)

    base_query += f" ORDER BY {ORDEM_PRIORIDADE}"

    resultados = conn.execute(base_query, params).fetchall()
    usuarios = conn.execute('SELECT id, nome, email FROM usuarios ORDER BY nome').fetchall()
    conn.close()

    return render_template(
        'index.html',
        demandas=resultados,
        prioridade_ativa=prioridade,
        termo_busca=termo,
        usuarios=usuarios,
        usuario_filtro_ativo=usuario_filtro
    )


# ── Card 4 + 6: Detalhes com proteção e exibição do criador ──────────────────
@app.route('/detalhes/<int:id>')
@login_required
def detalhes(id):
    conn = get_db()
    demanda = conn.execute(
        """SELECT d.*, u.nome AS nome_criador, u.email AS email_criador
           FROM demandas d
           LEFT JOIN usuarios u ON d.criado_por = u.id
           WHERE d.id=?""",
        (id,)
    ).fetchone()
    comentarios = conn.execute('SELECT * FROM comentarios WHERE demanda_id=?', (id,)).fetchall()
    historico = conn.execute(
        """SELECT h.*, u.nome AS nome_editor, u.email AS email_editor
           FROM historico_edicoes h
           LEFT JOIN usuarios u ON h.usuario_id = u.id
           WHERE h.demanda_id = ?
           ORDER BY h.data DESC""",
        (id,)
    ).fetchall()
    conn.close()
    return render_template('detalhes.html', demanda=demanda, comentarios=comentarios, historico=historico)


@app.route('/adicionar_comentario/<int:demanda_id>', methods=['POST'])
@login_required
def adicionar_comentario(demanda_id):
    comentario = request.form['comentario'].strip()
    autor = request.form['autor'].strip()

    if not comentario or not autor:
        flash('Preencha seu nome e o comentário antes de enviar.')
        return redirect(f'/detalhes/{demanda_id}')

    conn = get_db()
    conn.execute(
        "INSERT INTO comentarios (demanda_id, comentario, autor, data) VALUES (?, ?, ?, ?)",
        (demanda_id, comentario, autor, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    )
    conn.commit()
    conn.close()

    return redirect(f'/detalhes/{demanda_id}')


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
