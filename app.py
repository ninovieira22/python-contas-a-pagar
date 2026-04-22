from flask import Flask, render_template, request, jsonify, redirect, url_for
import pandas as pd
import json
import os
from datetime import datetime
import re
import unicodedata
import uuid

app = Flask(__name__)

# Configurações de Arquivos
DB_FILE = 'transacoes_salvas.json'
DB_MAPA = 'aprendizado_manual.json'
DB_MAPA_LEGADO = 'mapeamento_aprendido.json'
DB_CONFIG = 'config.json'
DB_EMOJI = 'emojis.json'
MESES = [
    'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
    'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
]
MESES_INDICE = {nome: i for i, nome in enumerate(MESES)}


# --- UTILITÁRIOS DE ARQUIVO ---
def gerenciar_json(arquivo, acao='ler', dados=None, default=[]):
    if acao == 'ler':
        if os.path.exists(arquivo):
            try:
                with open(arquivo, 'r', encoding='utf-8') as f:
                    conteudo = f.read().strip()
                    if conteudo == '':
                        return default
                    return json.loads(conteudo)
            except (json.JSONDecodeError, OSError):
                return default
        return default
    elif acao == 'salvar':
        with open(arquivo, 'w', encoding='utf-8') as f:
            json.dump(dados, f, indent=4, ensure_ascii=False)


def normalizar_mes(mes):
    if not mes:
        return ''
    return str(mes).strip().title()


def mes_atual_nome():
    return MESES[datetime.now().month - 1]


def ordenar_meses(meses):
    def chave(mes):
        return (MESES_INDICE.get(mes, 99), mes)

    return sorted(set(meses), key=chave)


def garantir_ids_contas_fixas(config):
    alterou = False
    fixas = config.get('fixas_detalhadas', [])
    for item in fixas:
        if not item.get('id'):
            item['id'] = str(uuid.uuid4())
            alterou = True
    return alterou


def normalizar_fixas_detalhadas(fixas):
    fixas_normalizadas = []
    for item in (fixas or []):
        nome = str(item.get('nome', '')).strip()
        if not nome:
            continue
        fixas_normalizadas.append({
            'id': item.get('id') or str(uuid.uuid4()),
            'nome': nome,
            'valor': float(item.get('valor', 0) or 0)
        })
    return fixas_normalizadas


def obter_status_fixas_mes(config, mes_referencia):
    mapa = config.get('fixas_pagas_por_mes', {})
    if not isinstance(mapa, dict):
        return {}
    status_mes = mapa.get(mes_referencia, {})
    return status_mes if isinstance(status_mes, dict) else {}


def normalizar_titulo(texto):
    texto = str(texto or '').strip().lower()
    texto = unicodedata.normalize('NFKD', texto)
    texto = ''.join(ch for ch in texto if not unicodedata.combining(ch))
    texto = re.sub(r'\s+', ' ', texto)
    return texto


def normalizar_categoria(categoria):
    return str(categoria or '').strip().title()


def carregar_mapa_aprendizado():
    # Manual tem prioridade sobre o legado em caso de conflito.
    mapa_legacy = gerenciar_json(DB_MAPA_LEGADO, default={})
    mapa_manual = gerenciar_json(DB_MAPA, default={})

    combinado = {}

    for chave, categoria in mapa_legacy.items():
        combinado[normalizar_titulo(chave)] = normalizar_categoria(categoria)

    for chave, categoria in mapa_manual.items():
        combinado[normalizar_titulo(chave)] = normalizar_categoria(categoria)

    return combinado


# --- APP ---
@app.route('/')
def index():
    # 1. Carrega as configurações e transações
    config = gerenciar_json(
        DB_CONFIG,
        default={
            'saldo': 0,
            'sal15': 0,
            'sal30': 0,
            'fixas': 0,
            'fixas_detalhadas': [],
            'receitas_detalhadas': [],
            'pedro_extras_detalhados': []
        }
    )
    db = gerenciar_json(DB_FILE)
    if garantir_ids_contas_fixas(config):
        gerenciar_json(DB_CONFIG, 'salvar', config)
    emojis_raw = gerenciar_json(DB_EMOJI, default={'Revisar': '⚠️', 'Mercado': '🛒', 'Pedro': '👦🏻'})
    emojis = {}
    for categoria, emoji in (emojis_raw or {}).items():
        cat_normalizada = normalizar_categoria(categoria)
        if cat_normalizada:
            emojis[cat_normalizada] = emoji

    # 2. Tratamento de Inputs Financeiros
    def get_fin(key):
        val = request.args.get(key)
        if val is not None:
            try:
                return float(val.replace(',', '.')) if val.strip() != '' else 0.0
            except ValueError:
                return 0.0
        return float(config.get(key, 0))

    # Lógica para múltiplas contas fixas (status de pagamento por mês)
    fixas_originais = config.get('fixas_detalhadas', [])
    fixas_base = normalizar_fixas_detalhadas(fixas_originais)
    if fixas_base != fixas_originais:
        config['fixas_detalhadas'] = fixas_base
        gerenciar_json(DB_CONFIG, 'salvar', config)

    contas_fixas_lista = []
    total_fixas_calculado = 0.0
    total_fixas_pendentes = 0.0

    # 3. Mês selecionado + lista de meses disponíveis
    meses_no_historico = [
        normalizar_mes(t.get('mes_referencia'))
        for t in db
        if normalizar_mes(t.get('mes_referencia'))
    ]
    meses_registrados = [normalizar_mes(m) for m in config.get('meses_registrados', []) if normalizar_mes(m)]
    meses_disponiveis = ordenar_meses(meses_no_historico + meses_registrados)

    if not meses_disponiveis:
        meses_disponiveis = [mes_atual_nome()]

    mes_query = normalizar_mes(request.args.get('mes'))
    mes_selecionado = mes_query if mes_query in meses_disponiveis else meses_disponiveis[-1]
    view_mode = request.args.get('view', 'transacoes')

    status_fixas_mes = obter_status_fixas_mes(config, mes_selecionado)
    contas_fixas_lista = []
    for item in fixas_base:
        item_id = item.get('id')
        pago_mes = bool(status_fixas_mes.get(item_id, False))
        contas_fixas_lista.append({
            'id': item_id,
            'nome': item.get('nome', ''),
            'valor': item.get('valor', 0),
            'pago': pago_mes
        })

    if contas_fixas_lista:
        total_fixas_calculado = sum(
            float(str(item.get('valor', 0)).replace(',', '.'))
            for item in contas_fixas_lista
        )
        total_fixas_pendentes = sum(
            float(str(item.get('valor', 0)).replace(',', '.'))
            for item in contas_fixas_lista
            if not bool(item.get('pago', False))
        )
    else:
        total_fixas_calculado = get_fin('fixas')
        total_fixas_pendentes = total_fixas_calculado

    # 3.1 Receitas por mês (com fallback para estrutura antiga)
    receitas_por_mes = config.get('receitas_por_mes', {})
    receitas_lista = receitas_por_mes.get(mes_selecionado, [])

    if not receitas_lista:
        receitas_lista = config.get('receitas_detalhadas', [])

    if not receitas_lista:
        receitas_lista = [
            {'nome': 'Saldo Inicial', 'valor': get_fin('saldo')},
            {'nome': 'Salário 15', 'valor': get_fin('sal15')},
            {'nome': 'Salário 30', 'valor': get_fin('sal30')}
        ]

    total_receitas_calculado = sum(
        float(str(item.get('valor', 0)).replace(',', '.'))
        for item in receitas_lista
    )

    pedro_extras_por_mes = config.get('pedro_extras_por_mes', {})
    pedro_extras_lista = pedro_extras_por_mes.get(mes_selecionado, [])

    if not pedro_extras_lista:
        pedro_extras_lista = config.get('pedro_extras_detalhados', [])

    total_pedro_extras = sum(
        float(str(item.get('valor', 0)).replace(',', '.'))
        for item in pedro_extras_lista
    )

    fin = {
        'saldo': get_fin('saldo'),
        'sal15': get_fin('sal15'),
        'sal30': get_fin('sal30'),
        'fixas': total_fixas_calculado,
        'receitas': total_receitas_calculado
    }

    # 4. Processamento de dados por mês
    arquivos_historico = sorted(set(
        t.get('arquivo_origem', 'Desconhecido')
        for t in db
        if normalizar_mes(t.get('mes_referencia')) == mes_selecionado
    ))

    transacoes_filtradas = [
        t for t in db
        if normalizar_mes(t.get('mes_referencia')) == mes_selecionado
    ]

    resumo_bruto = {}
    contagem_itens = {}

    for t in transacoes_filtradas:
        cat = str(t.get('categoria', 'Revisar')).strip().title()
        valor = float(t.get('amount', 0) or 0)
        resumo_bruto[cat] = resumo_bruto.get(cat, 0) + valor
        contagem_itens[cat] = contagem_itens.get(cat, 0) + 1

    resumo_ordenado = dict(sorted(resumo_bruto.items(), key=lambda item: item[1], reverse=True))

    # 5. Cálculos dos cards do mês
    receita_total = fin['receitas']
    total_cartao = sum(resumo_ordenado.values())

    total_pedro_cartao = resumo_ordenado.get('Pedro', 0)
    total_pedro = total_pedro_cartao + total_pedro_extras
    total_lucas = total_cartao - total_pedro_cartao
    valor_livre = receita_total - total_lucas - total_fixas_pendentes

    # 6. Dashboard comparativo mensal
    dashboard_mensal = []
    dashboard_categorias = {}
    totais_dashboard = []

    for mes in meses_disponiveis:
        transacoes_mes = [
            t for t in db
            if normalizar_mes(t.get('mes_referencia')) == mes
        ]
        total_mes = sum(float(t.get('amount', 0) or 0) for t in transacoes_mes)
        totais_dashboard.append(total_mes)

        resumo_mes = {}
        for t in transacoes_mes:
            cat = str(t.get('categoria', 'Revisar')).strip().title()
            resumo_mes[cat] = resumo_mes.get(cat, 0) + float(t.get('amount', 0) or 0)
        dashboard_categorias[mes] = resumo_mes

        top_categoria = '-'
        top_valor = 0
        if resumo_mes:
            top_categoria, top_valor = max(resumo_mes.items(), key=lambda item: item[1])

        dashboard_mensal.append({
            'mes': mes,
            'total': total_mes,
            'quantidade': len(transacoes_mes),
            'top_categoria': top_categoria,
            'top_valor': top_valor
        })

    max_total_dashboard = max(totais_dashboard) if totais_dashboard else 0
    for i, item in enumerate(dashboard_mensal):
        item['percentual'] = (item['total'] / max_total_dashboard * 100) if max_total_dashboard > 0 else 0

        if i == 0:
            item['delta'] = 0
            item['delta_percentual'] = 0
        else:
            anterior = dashboard_mensal[i - 1]['total']
            item['delta'] = item['total'] - anterior
            item['delta_percentual'] = ((item['delta'] / anterior) * 100) if anterior > 0 else 0

    media_gastos = (sum(totais_dashboard) / len(totais_dashboard)) if totais_dashboard else 0
    maior_mes = max(dashboard_mensal, key=lambda x: x['total']) if dashboard_mensal else None
    menor_mes = min(dashboard_mensal, key=lambda x: x['total']) if dashboard_mensal else None

    return render_template(
        'index.html',
        transacoes=transacoes_filtradas,
        resumo=resumo_ordenado,
        contagem=contagem_itens,
        mes_atual=mes_selecionado,
        meses_disponiveis=meses_disponiveis,
        view_mode=view_mode,
        arquivos_importados=arquivos_historico,
        fin=fin,
        emojis=emojis,
        fixas_detalhadas=contas_fixas_lista,
        receitas_detalhadas=receitas_lista,
        pedro_extras_detalhados=pedro_extras_lista,
        card_receita_total=receita_total,
        card_total_cartao=total_cartao,
        card_total_pedro=total_pedro,
        card_total_pedro_cartao=total_pedro_cartao,
        card_total_pedro_extras=total_pedro_extras,
        card_total_lucas=total_lucas,
        card_total_fixas_pendentes=total_fixas_pendentes,
        card_contas_mes=fin['fixas'],
        card_livre=valor_livre,
        dashboard_mensal=dashboard_mensal,
        dashboard_categorias=dashboard_categorias,
        dashboard_media=media_gastos,
        dashboard_maior_mes=maior_mes,
        dashboard_menor_mes=menor_mes,
        meses=MESES
    )


# --- API / ACTIONS ---
@app.route('/upload', methods=['POST'])
def upload_file():
    file = request.files.get('file')
    mes_selecionado = normalizar_mes(request.form.get('mes')) or mes_atual_nome()
    if mes_selecionado not in MESES:
        mes_selecionado = mes_atual_nome()

    config = gerenciar_json(DB_CONFIG, default={})
    meses_registrados = [normalizar_mes(m) for m in config.get('meses_registrados', []) if normalizar_mes(m)]
    if mes_selecionado not in meses_registrados:
        meses_registrados.append(mes_selecionado)
        config['meses_registrados'] = ordenar_meses(meses_registrados)
        gerenciar_json(DB_CONFIG, 'salvar', config)

    if file and file.filename.endswith('.csv'):
        df = pd.read_csv(file)
        db = gerenciar_json(DB_FILE)
        existentes = {f"{t['date']}-{t['title']}-{t['amount']}-{normalizar_mes(t.get('mes_referencia'))}" for t in db}

        for _, row in df.iterrows():
            if str(row['title']).strip().lower() == 'pagamento recebido':
                continue

            id_compra = f"{row['date']}-{row['title']}-{row['amount']}-{mes_selecionado}"
            if id_compra not in existentes:
                db.append({
                    'date': row['date'],
                    'title': row['title'],
                    'amount': float(row['amount']),
                    'categoria': 'Revisar',
                    'mes_referencia': mes_selecionado,
                    'arquivo_origem': file.filename
                })

        gerenciar_json(DB_FILE, 'salvar', db)

    return redirect(url_for('index', mes=mes_selecionado, view='transacoes'))


@app.route('/atualizar_categoria', methods=['POST'])
def atualizar():
    data = request.json
    titulo = data.get('title')

    # Padronização: Remove espaços e força "Primeira Letra Maiúscula"
    nova_cat = data.get('categoria').strip().title()

    # 1. Atualiza o Mapa de Inteligência (Aprendizado Manual)
    mapa = gerenciar_json(DB_MAPA, default={})
    mapa[titulo] = nova_cat
    gerenciar_json(DB_MAPA, 'salvar', mapa)

    # 2. Atualiza o Banco de Transações
    db = gerenciar_json(DB_FILE)
    for t in db:
        if t['title'] == titulo:
            t['categoria'] = nova_cat

    gerenciar_json(DB_FILE, 'salvar', db)

    return jsonify({
        'status': 'success',
        'categoria_padronizada': nova_cat
    })


@app.route('/atualizar_status_conta_fixa', methods=['POST'])
def atualizar_status_conta_fixa():
    data = request.json or {}
    conta_id = data.get('id')
    pago = bool(data.get('pago', False))
    mes_referencia = normalizar_mes(data.get('mes_referencia'))

    if not conta_id:
        return jsonify({'status': 'error', 'message': 'ID da conta fixa é obrigatório'}), 400
    if not mes_referencia:
        return jsonify({'status': 'error', 'message': 'Mês de referência é obrigatório'}), 400

    config = gerenciar_json(DB_CONFIG, default={})
    fixas = config.get('fixas_detalhadas', [])
    alterou = False
    for item in fixas:
        if item.get('id') == conta_id:
            alterou = True
            break

    if not alterou:
        return jsonify({'status': 'error', 'message': 'Conta fixa não encontrada'}), 404

    mapa = config.get('fixas_pagas_por_mes', {})
    if not isinstance(mapa, dict):
        mapa = {}
    status_mes = mapa.get(mes_referencia, {})
    if not isinstance(status_mes, dict):
        status_mes = {}
    status_mes[conta_id] = pago
    mapa[mes_referencia] = status_mes
    config['fixas_pagas_por_mes'] = mapa
    gerenciar_json(DB_CONFIG, 'salvar', config)
    return jsonify({'status': 'success'})


@app.route('/categorizar_em_lote', methods=['POST'])
def categorizar_em_lote():
    data = request.json
    mes_atual = normalizar_mes(data.get('mes'))

    mapa = carregar_mapa_aprendizado()
    db = gerenciar_json(DB_FILE)

    contador = 0
    for t in db:
        if normalizar_mes(t.get('mes_referencia')) != mes_atual:
            continue

        titulo = t['title']
        titulo_norm = normalizar_titulo(titulo)
        categoria_atual = str(t.get('categoria', '')).strip().title()

        # 1. Busca no histórico de aprendizado (reaplica padronização no mês todo)
        if titulo_norm in mapa:
            nova_categoria = mapa[titulo_norm]
            if categoria_atual != nova_categoria:
                t['categoria'] = nova_categoria
                contador += 1
        # 2. Regras fixas rápidas para itens ainda sem categoria definida
        elif categoria_atual == 'Revisar':
            t_up = titulo.upper()
            if 'PEDRO' in t_up:
                t['categoria'] = 'Pedro'
                contador += 1
            elif 'VITORIA' in t_up or 'VITÓRIA' in t_up:
                t['categoria'] = 'Vitória'
                contador += 1

    gerenciar_json(DB_FILE, 'salvar', db)
    if contador == 0:
        return jsonify({'message': 'Auto-categorização concluída. Nenhum item precisou de ajuste neste mês.'})
    return jsonify({'message': f'Sucesso! {contador} itens foram categorizados automaticamente.'})


@app.route('/salvar_emoji', methods=['POST'])
def salvar_emoji():
    dados = request.json
    emojis = gerenciar_json(DB_EMOJI, default={}) or {}
    categoria = normalizar_categoria(dados.get('categoria'))
    if not categoria:
        return jsonify({'status': 'error', 'message': 'Categoria inválida'}), 400
    emojis[categoria] = dados.get('emoji', '🏷️')
    gerenciar_json(DB_EMOJI, 'salvar', emojis)
    return jsonify({'status': 'success'})


@app.route('/atualizar_financas', methods=['POST'])
def atualizar_financas():
    dados = request.json
    config = gerenciar_json(DB_CONFIG, default={})
    if isinstance(dados, dict) and 'fixas_detalhadas' in dados:
        dados['fixas_detalhadas'] = normalizar_fixas_detalhadas(dados.get('fixas_detalhadas'))
    config.update(dados)
    garantir_ids_contas_fixas(config)
    gerenciar_json(DB_CONFIG, 'salvar', config)
    return jsonify({'status': 'success'})


@app.route('/remover_arquivo', methods=['POST'])
def remover_arquivo():
    arquivo = request.json.get('arquivo')
    mes = normalizar_mes(request.json.get('mes'))
    db_atual = gerenciar_json(DB_FILE)

    db = [
        t for t in db_atual
        if not (
            t.get('arquivo_origem') == arquivo and
            (not mes or normalizar_mes(t.get('mes_referencia')) == mes)
        )
    ]

    gerenciar_json(DB_FILE, 'salvar', db)
    return jsonify({'status': 'success'})


@app.route('/salvar_config', methods=['POST'])
def salvar_config():
    dados = request.json or {}
    emojis = dados.pop('emojis', None)
    mes_referencia = normalizar_mes(dados.pop('mes_referencia', ''))
    receitas_detalhadas = dados.pop('receitas_detalhadas', None)
    fixas_detalhadas = dados.pop('fixas_detalhadas', None)
    pedro_extras_detalhados = dados.pop('pedro_extras_detalhados', None)

    config = gerenciar_json(DB_CONFIG, default={})

    if isinstance(receitas_detalhadas, list):
        if mes_referencia:
            receitas_por_mes = config.get('receitas_por_mes', {})
            receitas_por_mes[mes_referencia] = receitas_detalhadas
            config['receitas_por_mes'] = receitas_por_mes
        else:
            config['receitas_detalhadas'] = receitas_detalhadas

    if isinstance(fixas_detalhadas, list):
        config['fixas_detalhadas'] = normalizar_fixas_detalhadas(fixas_detalhadas)

    if isinstance(pedro_extras_detalhados, list):
        pedro_extras_normalizados = []
        for item in pedro_extras_detalhados:
            nome = str(item.get('nome', '')).strip()
            if not nome:
                continue
            pedro_extras_normalizados.append({
                'nome': nome,
                'valor': float(item.get('valor', 0) or 0)
            })

        if mes_referencia:
            pedro_extras_por_mes = config.get('pedro_extras_por_mes', {})
            pedro_extras_por_mes[mes_referencia] = pedro_extras_normalizados
            config['pedro_extras_por_mes'] = pedro_extras_por_mes
        else:
            config['pedro_extras_detalhados'] = pedro_extras_normalizados

    config.update(dados)
    garantir_ids_contas_fixas(config)
    gerenciar_json(DB_CONFIG, 'salvar', config)

    if isinstance(emojis, dict):
        emojis_atual = gerenciar_json(DB_EMOJI, default={}) or {}
        emojis_normalizados = {}
        for categoria, emoji in emojis_atual.items():
            cat_normalizada = normalizar_categoria(categoria)
            if cat_normalizada:
                emojis_normalizados[cat_normalizada] = emoji
        for categoria, emoji in emojis.items():
            cat_normalizada = normalizar_categoria(categoria)
            if cat_normalizada:
                emojis_normalizados[cat_normalizada] = emoji
        gerenciar_json(DB_EMOJI, 'salvar', emojis_normalizados)

    return jsonify({'status': 'success'})


if __name__ == '__main__':
    app.run(debug=True)
