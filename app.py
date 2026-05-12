from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, Response
import sqlite3
import csv
import io
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import sqlite3
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

app = Flask(__name__)
app.secret_key = 'sgdi_sprint3_secret_2026'

@app.context_processor
def inject_now():
    return {'now_date': datetime.now().strftime('%Y-%m-%d')}

ORDEM_PRIORIDADE = "CASE d.prioridade WHEN 'Alta' THEN 1 WHEN 'Media' THEN 2 WHEN 'Baixa' THEN 3 END"

PRIORIDADES_VALIDAS = {'Alta', 'Media', 'Baixa'}
STATUS_VALIDOS = {'Aberta', 'Concluida', 'Cancelada', 'Atrasada'}


def get_db():
    conn = sqlite3.connect('demandas.db')
    conn.row_factory = sqlite3.Row
    return conn


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario_id' not in session:
            flash('Você precisa estar logado para acessar esta página.')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


# ── Cadastro de usuário ───────────────────────────────────────────────────────
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


# ── Login e sessão ────────────────────────────────────────────────────────────
@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'usuario_id' in session:
        return redirect(url_for('index'))

    if request.method == 'POST':
        email = request.form['email'].strip()
        senha = request.form['senha'].strip()

        conn = get_db()
        usuario = conn.execute('SELECT * FROM usuarios WHERE email = ?', (email,)).fetchone()
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


# ── Index ─────────────────────────────────────────────────────────────────────
@app.route('/')
@login_required
def index():
    prioridade = request.args.get('prioridade', '').strip()
    usuario_filtro = request.args.get('usuario_id', '').strip()
    status_filtro = request.args.get('status', '').strip()

    conn = get_db()

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

    if status_filtro and status_filtro in STATUS_VALIDOS:
        conditions.append("d.status = ?")
        params.append(status_filtro)
    else:
        status_filtro = ''

    if usuario_filtro:
        conditions.append("d.criado_por = ?")
        params.append(usuario_filtro)

    if conditions:
        base_query += " WHERE " + " AND ".join(conditions)

    base_query += f" ORDER BY {ORDEM_PRIORIDADE}"

    demandas = conn.execute(base_query, params).fetchall()
    usuarios = conn.execute('SELECT id, nome, email FROM usuarios ORDER BY nome').fetchall()
    conn.close()

    return render_template(
        'index.html',
        demandas=demandas,
        prioridade_ativa=prioridade,
        status_ativo=status_filtro,
        usuarios=usuarios,
        usuario_filtro_ativo=usuario_filtro
    )


# ── Nova demanda ──────────────────────────────────────────────────────────────
@app.route('/nova_demanda', methods=['GET', 'POST'])
@login_required
def nova_demanda():
    if request.method == 'POST':
        titulo = request.form['titulo'].strip()
        descricao = request.form['descricao'].strip()
        solicitante = request.form['solicitante'].strip()
        prioridade = request.form['prioridade'].strip()
        prazo = request.form.get('prazo', '').strip()

        if not titulo or not descricao or not solicitante:
            flash('Todos os campos são obrigatórios.')
            return render_template('nova_demanda.html')

        conn = get_db()
        conn.execute(
            "INSERT INTO demandas (titulo, descricao, solicitante, data_criacao, prioridade, status, prazo, criado_por) VALUES (?, ?, ?, ?, ?, 'Aberta', ?, ?)",
            (titulo, descricao, solicitante, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), prioridade, prazo or None, session['usuario_id'])
        )
        conn.commit()
        conn.close()

        flash('Demanda salva com sucesso!')
        return redirect('/')

    return render_template('nova_demanda.html')


# ── Editar ────────────────────────────────────────────────────────────────────
@app.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar(id):
    conn = get_db()

    if request.method == 'POST':
        titulo = request.form['titulo'].strip()
        descricao = request.form['descricao'].strip()
        solicitante = request.form['solicitante'].strip()
        prioridade = request.form['prioridade'].strip()
        status = request.form.get('status', '').strip()
        prazo = request.form.get('prazo', '').strip()

        demanda_atual = conn.execute('SELECT * FROM demandas WHERE id=?', (id,)).fetchone()

        if not titulo or not descricao or not solicitante:
            flash('Todos os campos são obrigatórios.')
            conn.close()
            return render_template('editar.html', demanda=demanda_atual)

        data_conclusao = demanda_atual['data_conclusao']
        if status in ('Concluida', 'Cancelada') and demanda_atual['status'] not in ('Concluida', 'Cancelada'):
            data_conclusao = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        elif status == 'Aberta':
            data_conclusao = None

        campos = {
            'titulo': (demanda_atual['titulo'], titulo),
            'descricao': (demanda_atual['descricao'], descricao),
            'solicitante': (demanda_atual['solicitante'], solicitante),
            'prioridade': (demanda_atual['prioridade'], prioridade),
            'status': (demanda_atual['status'] or 'Aberta', status),
            'prazo': (demanda_atual['prazo'] or '', prazo),
        }
        agora = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        for campo, (anterior, novo) in campos.items():
            if anterior != novo:
                conn.execute(
                    "INSERT INTO historico_edicoes (demanda_id, usuario_id, data, campo_alterado, valor_anterior, valor_novo) VALUES (?, ?, ?, ?, ?, ?)",
                    (id, session['usuario_id'], agora, campo, anterior, novo)
                )

        conn.execute(
            "UPDATE demandas SET titulo=?, descricao=?, solicitante=?, prioridade=?, status=?, data_conclusao=?, prazo=? WHERE id=?",
            (titulo, descricao, solicitante, prioridade, status, data_conclusao, prazo or None, id)
        )
        conn.commit()
        conn.close()
        flash('Demanda atualizada com sucesso!')
        return redirect('/')

    demanda = conn.execute('SELECT * FROM demandas WHERE id=?', (id,)).fetchone()
    conn.close()
    return render_template('editar.html', demanda=demanda)


# ── Cancelar demanda (substitui deletar) ──────────────────────────────────────
@app.route('/cancelar/<int:id>')
@login_required
def cancelar(id):
    conn = get_db()
    demanda = conn.execute('SELECT * FROM demandas WHERE id=?', (id,)).fetchone()
    if not demanda:
        conn.close()
        flash('Demanda não encontrada.')
        return redirect('/')
    eh_admin = session.get('usuario_cargo') == 'admin'
    eh_dono = demanda['criado_por'] == session['usuario_id']
    if not eh_admin and not eh_dono:
        conn.close()
        flash('Você não tem permissão para cancelar esta demanda.')
        return redirect('/')
    agora = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    conn.execute(
        "UPDATE demandas SET status='Cancelada', data_conclusao=? WHERE id=?",
        (agora, id)
    )
    conn.execute(
        "INSERT INTO historico_edicoes (demanda_id, usuario_id, data, campo_alterado, valor_anterior, valor_novo) VALUES (?, ?, ?, 'status', ?, 'Cancelada')",
        (id, session['usuario_id'], agora, demanda['status'] or 'Aberta')
    )
    conn.commit()
    conn.close()
    flash('Demanda cancelada.')
    return redirect(request.referrer or '/')


# ── Concluir demanda (ação rápida) ────────────────────────────────────────────
@app.route('/concluir/<int:id>')
@login_required
def concluir(id):
    conn = get_db()
    demanda = conn.execute('SELECT * FROM demandas WHERE id=?', (id,)).fetchone()
    if not demanda:
        conn.close()
        flash('Demanda não encontrada.')
        return redirect('/')

    agora = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    conn.execute(
        "UPDATE demandas SET status='Concluida', data_conclusao=? WHERE id=?",
        (agora, id)
    )
    conn.execute(
        "INSERT INTO historico_edicoes (demanda_id, usuario_id, data, campo_alterado, valor_anterior, valor_novo) VALUES (?, ?, ?, 'status', ?, 'Concluida')",
        (id, session['usuario_id'], agora, demanda['status'] or 'Aberta')
    )
    conn.commit()
    conn.close()
    flash('Demanda concluída com sucesso!')
    return redirect(request.referrer or '/')


# ── Deletar ───────────────────────────────────────────────────────────────────

# ── Buscar ────────────────────────────────────────────────────────────────────
@app.route('/buscar')
@login_required
def buscar():
    termo = request.args.get('q', '')
    prioridade = request.args.get('prioridade', '').strip()
    usuario_filtro = request.args.get('usuario_id', '').strip()
    status_filtro = request.args.get('status', '').strip()

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

    if status_filtro and status_filtro in STATUS_VALIDOS:
        base_query += " AND d.status = ?"
        params.append(status_filtro)
    else:
        status_filtro = ''

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
        status_ativo=status_filtro,
        termo_busca=termo,
        usuarios=usuarios,
        usuario_filtro_ativo=usuario_filtro
    )


# ── Detalhes ──────────────────────────────────────────────────────────────────
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


# ── Dashboard Gerencial ───────────────────────────────────────────────────────
@app.route('/dashboard')
@login_required
def dashboard():
    conn = get_db()

    # Filtros
    periodo = request.args.get('periodo', '30')  # dias
    usuario_filtro = request.args.get('usuario_id', '')
    prioridade_filtro = request.args.get('prioridade', '')
    status_filtro = request.args.get('status', '')

    try:
        dias = int(periodo)
    except:
        dias = 30

    data_limite = (datetime.now() - timedelta(days=dias)).strftime('%Y-%m-%d %H:%M:%S')
    hoje = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Base conditions
    cond_periodo = "d.data_criacao >= ?"
    params_base = [data_limite]

    cond_extra = []
    if usuario_filtro:
        cond_extra.append("d.criado_por = ?")
        params_base.append(usuario_filtro)
    if prioridade_filtro and prioridade_filtro in PRIORIDADES_VALIDAS:
        cond_extra.append("d.prioridade = ?")
        params_base.append(prioridade_filtro)
    if status_filtro and status_filtro in STATUS_VALIDOS:
        cond_extra.append("d.status = ?")
        params_base.append(status_filtro)

    where_clause = "WHERE " + cond_periodo
    if cond_extra:
        where_clause += " AND " + " AND ".join(cond_extra)

    # KPI: Total de demandas
    total = conn.execute(
        f"SELECT COUNT(*) as c FROM demandas d {where_clause}", params_base
    ).fetchone()['c']

    # KPI: Por status
    por_status = conn.execute(
        f"""SELECT COALESCE(d.status, 'Aberta') as status, COUNT(*) as c
            FROM demandas d {where_clause}
            GROUP BY COALESCE(d.status, 'Aberta')""",
        params_base
    ).fetchall()

    status_map = {'Aberta': 0, 'Concluida': 0, 'Cancelada': 0, 'Atrasada': 0}
    for row in por_status:
        status_map[row['status']] = row['c']

    # Identificar atrasadas:
    # - Se tem prazo definido: abertas com prazo vencido (prazo < hoje)
    # - Se não tem prazo: abertas criadas há mais de 7 dias (fallback)
    atrasadas = conn.execute(
        f"""SELECT COUNT(*) as c FROM demandas d
            {where_clause}
            AND (d.status = 'Aberta' OR d.status IS NULL)
            AND (
                (d.prazo IS NOT NULL AND d.prazo < ?)
                OR
                (d.prazo IS NULL AND d.data_criacao < ?)
            )""",
        params_base + [hoje, (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')]
    ).fetchone()['c']
    status_map['Atrasada'] = atrasadas

    # KPI: Demandas críticas (Alta prioridade abertas)
    criticas = conn.execute(
        f"""SELECT d.*, u.nome AS nome_criador FROM demandas d
            LEFT JOIN usuarios u ON d.criado_por = u.id
            {where_clause}
            AND d.prioridade = 'Alta'
            AND (d.status = 'Aberta' OR d.status IS NULL)
            ORDER BY d.data_criacao ASC
            LIMIT 10""",
        params_base
    ).fetchall()

    # KPI: Por responsável
    por_responsavel = conn.execute(
        f"""SELECT u.nome, u.email, COUNT(*) as total,
                   SUM(CASE WHEN (d.status = 'Aberta' OR d.status IS NULL) THEN 1 ELSE 0 END) as abertas,
                   SUM(CASE WHEN d.status = 'Concluida' THEN 1 ELSE 0 END) as concluidas
            FROM demandas d
            LEFT JOIN usuarios u ON d.criado_por = u.id
            {where_clause}
            GROUP BY d.criado_por, u.nome, u.email
            ORDER BY abertas DESC
            LIMIT 10""",
        params_base
    ).fetchall()

    # KPI: Tempo médio de resolução (excluindo canceladas)
    tempo_medio_row = conn.execute(
        f"""SELECT AVG(
                JULIANDAY(d.data_conclusao) - JULIANDAY(d.data_criacao)
            ) as media_dias
            FROM demandas d
            {where_clause}
            AND d.status = 'Concluida'
            AND d.data_conclusao IS NOT NULL""",
        params_base
    ).fetchone()
    tempo_medio = round(tempo_medio_row['media_dias'] or 0, 1)

    # KPI: Por prioridade
    por_prioridade = conn.execute(
        f"""SELECT d.prioridade, COUNT(*) as c
            FROM demandas d {where_clause}
            GROUP BY d.prioridade""",
        params_base
    ).fetchall()

    prio_map = {'Alta': 0, 'Media': 0, 'Baixa': 0}
    for row in por_prioridade:
        if row['prioridade'] in prio_map:
            prio_map[row['prioridade']] = row['c']

    # Evolução temporal (últimos N dias agrupado por semana)
    evolucao = conn.execute(
        f"""SELECT
                strftime('%Y-%W', d.data_criacao) as semana,
                COUNT(*) as criadas,
                SUM(CASE WHEN d.status = 'Concluida' THEN 1 ELSE 0 END) as concluidas
            FROM demandas d {where_clause}
            GROUP BY semana
            ORDER BY semana""",
        params_base
    ).fetchall()

    # Demandas sem responsável
    sem_responsavel = conn.execute(
        f"""SELECT COUNT(*) as c FROM demandas d
            {where_clause}
            AND d.criado_por IS NULL""",
        params_base
    ).fetchone()['c']

    # Lista todos usuários para filtro
    usuarios = conn.execute('SELECT id, nome, email FROM usuarios ORDER BY nome').fetchall()

    conn.close()

    return render_template(
        'dashboard.html',
        total=total,
        status_map=status_map,
        atrasadas=atrasadas,
        criticas=criticas,
        por_responsavel=por_responsavel,
        tempo_medio=tempo_medio,
        prio_map=prio_map,
        evolucao=evolucao,
        sem_responsavel=sem_responsavel,
        periodo=periodo,
        usuarios=usuarios,
        usuario_filtro_ativo=usuario_filtro,
        prioridade_ativa=prioridade_filtro,
        status_ativo=status_filtro,
    )


# ── Exportar críticas CSV ─────────────────────────────────────────────────────
@app.route('/exportar_criticas_csv')
@login_required
def exportar_criticas_csv():
    hoje = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    sete_dias_atras = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')

    conn = get_db()
    criticas = conn.execute("""
        SELECT d.id, d.titulo, d.solicitante, u.nome AS responsavel,
               d.data_criacao, d.prazo, d.status
        FROM demandas d
        LEFT JOIN usuarios u ON d.criado_por = u.id
        WHERE d.prioridade = 'Alta'
          AND (d.status = 'Aberta' OR d.status IS NULL)
          AND (
              (d.prazo IS NOT NULL AND d.prazo < ?)
              OR
              (d.prazo IS NULL AND d.data_criacao < ?)
          )
        ORDER BY d.data_criacao ASC
    """, (hoje, sete_dias_atras)).fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Título', 'Solicitante', 'Responsável',
                     'Data Criação', 'Prazo', 'Status'])
    for d in criticas:
        writer.writerow([
            d['id'], d['titulo'], d['solicitante'], d['responsavel'] or '—',
            d['data_criacao'], d['prazo'] or 'sem prazo', d['status'] or 'Aberta'
        ])

    output.seek(0)
    nome_arquivo = f"criticas_atrasadas_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
    return Response(
        output.getvalue().encode('utf-8-sig'),  # utf-8-sig abre corretamente no Excel
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename={nome_arquivo}'}
    )


@app.route('/exportar_criticas_pdf')
@login_required
def exportar_criticas_pdf():
    hoje = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    sete_dias_atras = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')

    conn = get_db()
    criticas = conn.execute("""
        SELECT d.id, d.titulo, d.solicitante, u.nome AS responsavel,
               d.data_criacao, d.prazo
        FROM demandas d
        LEFT JOIN usuarios u ON d.criado_por = u.id
        WHERE d.prioridade = 'Alta'
          AND (d.status = 'Aberta' OR d.status IS NULL)
          AND (
              (d.prazo IS NOT NULL AND d.prazo < ?)
              OR
              (d.prazo IS NULL AND d.data_criacao < ?)
          )
        ORDER BY d.data_criacao ASC
    """, (hoje, sete_dias_atras)).fetchall()
    conn.close()

    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import cm

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            leftMargin=2*cm, rightMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)

    styles = getSampleStyleSheet()
    elements = []

    # Título e data
    elements.append(Paragraph("Demandas Críticas Atrasadas — Alta Prioridade", styles['Title']))
    agora_fmt = datetime.now().strftime('%d/%m/%Y às %H:%M')
    elements.append(Paragraph(f"Gerado em {agora_fmt}", styles['Normal']))
    elements.append(Spacer(1, 0.5*cm))

    # Tabela
    cabecalho = ['ID', 'Título', 'Solicitante', 'Responsável', 'Criado em', 'Prazo']
    dados = [cabecalho]
    for d in criticas:
        dados.append([
            f"#{d['id']}",
            d['titulo'],
            d['solicitante'],
            d['responsavel'] or '—',
            d['data_criacao'],
            d['prazo'] or 'sem prazo',
        ])

    if len(dados) == 1:
        elements.append(Paragraph("Nenhuma demanda crítica atrasada encontrada.", styles['Normal']))
    else:
        tabela = Table(dados, colWidths=[1.2*cm, 5.5*cm, 3*cm, 3*cm, 3.5*cm, 2.8*cm])
        tabela.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e3a8a')),
            ('TEXTCOLOR',  (0, 0), (-1, 0), colors.white),
            ('FONTNAME',   (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE',   (0, 0), (-1, 0), 9),
            ('FONTSIZE',   (0, 1), (-1, -1), 8),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9fafb')]),
            ('GRID',       (0, 0), (-1, -1), 0.4, colors.HexColor('#e5e7eb')),
            ('VALIGN',     (0, 0), (-1, -1), 'MIDDLE'),
            ('PADDING',    (0, 0), (-1, -1), 6),
        ]))
        elements.append(tabela)
        elements.append(Spacer(1, 0.3*cm))
        elements.append(Paragraph(
            f"Total: {len(criticas)} demanda{'s' if len(criticas) != 1 else ''}",
            styles['Normal']
        ))

    doc.build(elements)
    buffer.seek(0)
    nome_arquivo = f"criticas_atrasadas_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
    return Response(
        buffer.getvalue(),
        mimetype='application/pdf',
        headers={'Content-Disposition': f'attachment; filename={nome_arquivo}'}
    )
    
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')