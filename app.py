# Versão Final (100x100mm com Admin)
import os
import pandas as pd
from flask import Flask, render_template, request, send_file, redirect, url_for
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import io
from reportlab.platypus import Paragraph
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT

app = Flask(__name__)
CSV_PATH = 'destinos.csv'

# --- CONFIGURAÇÕES DE FONTE ---
try:
    pdfmetrics.registerFont(TTFont('Arial', 'arial.ttf'))
    pdfmetrics.registerFont(TTFont('Arial-Bold', 'arialbd.ttf'))
except Exception as e:
    print(f"AVISO: Não foi possível carregar fontes: {e}")

# --- FUNÇÕES DE MANIPULAÇÃO DE DADOS ---
def carregar_dataframe():
    if not os.path.exists(CSV_PATH):
        colunas = ['sigla', 'nome_recebedor', 'cnpj_recebedor', 'endereco_recebedor', 'cidade_recebedor', 'uf_recebedor', 'cep_recebedor', 'pais_recebedor']
        return pd.DataFrame(columns=colunas)
    return pd.read_csv(CSV_PATH)

def salvar_dataframe(df):
    df.to_csv(CSV_PATH, index=False)

# --- ROTA PRINCIPAL (GERAR ETIQUETAS) ---
@app.route('/', methods=['GET', 'POST'])
def index():
    df = carregar_dataframe()
    if not df.empty and 'sigla' in df.columns:
        df = df.dropna(subset=['sigla'])
        destinos_dict = df.set_index('sigla').to_dict('index')
    else:
        destinos_dict = {}

    if request.method == 'POST':
        sigla = request.form.get('sigla').upper()
        quantidade = int(request.form.get('quantidade'))
        dados_recebedor = destinos_dict[sigla]

        buffer = io.BytesIO()
        # Tamanho da página padronizado para 100x100 mm
        c = canvas.Canvas(buffer, pagesize=(100 * mm, 100 * mm))
        styles = getSampleStyleSheet()
        # Fonte do parágrafo um pouco menor para caber no novo layout
        style_normal = ParagraphStyle(name='Normal', parent=styles['Normal'], fontName='Arial', fontSize=9, leading=11)

        for i in range(1, quantidade + 1):
            margem_h = 4 * mm
            largura_maxima = 92 * mm 

            # Coordenadas e fontes ajustadas para o layout 100x100
            c.setFont('Arial-Bold', 32)
            c.drawString(margem_h, 82 * mm, sigla)

            numero_str = f"#{i}"
            c.setFont('Arial-Bold', 34)
            largura_texto_num = c.stringWidth(numero_str, 'Arial-Bold', 34)
            c.drawString((100 * mm) - margem_h - largura_texto_num, 82 * mm, numero_str)

            c.setFont('Arial-Bold', 34)
            c.drawString(margem_h, 68 * mm, "OVERPACK")
            c.drawString(margem_h, 57 * mm, "USED")

            expedidor_text = "<b>EXPEDIDOR:</b> NEW POST LOGISTICA ENDEREÇO: R UBALDO FAGGEANI, 355,0 - JARDIM RESIDENCIAL LAS PALMAS MUNICÍPIO: PORTO FERREIRA - SP CEP: 13660-000 CNPJ/CPF: 28.678.104/0001-79 IE: 555074223110 UF: SP PAÍS: BRASIL"
            recebedor_text = f"<b>RECEBEDOR:</b> {dados_recebedor['nome_recebedor']} CNPJ {dados_recebedor['cnpj_recebedor']} ENDEREÇO: {dados_recebedor['endereco_recebedor']}, {dados_recebedor['cidade_recebedor']} - {dados_recebedor['uf_recebedor']} CEP: {dados_recebedor['cep_recebedor']}"

            p_expedidor = Paragraph(expedidor_text, style_normal)
            p_expedidor.wrapOn(c, largura_maxima, 40 * mm)
            p_expedidor.drawOn(c, margem_h, 28 * mm)

            p_recebedor = Paragraph(recebedor_text, style_normal)
            p_recebedor.wrapOn(c, largura_maxima, 25 * mm)
            p_recebedor.drawOn(c, margem_h, 5 * mm)

            c.showPage()

        c.save()
        buffer.seek(0)
        return send_file(buffer, as_attachment=True, download_name=f'etiquetas_{sigla}_100x100.pdf', mimetype='application/pdf')

    return render_template('index.html', destinos=destinos_dict.keys())

# --- ROTAS DE ADMINISTRAÇÃO ---
@app.route('/admin')
def admin():
    df = carregar_dataframe()
    df = df.dropna(subset=['sigla'])
    destinos_dict = df.set_index('sigla').to_dict('index')
    return render_template('admin.html', destinos=destinos_dict)

@app.route('/add', methods=['GET', 'POST'])
def add_destino():
    if request.method == 'POST':
        df = carregar_dataframe()
        nova_linha = pd.DataFrame([request.form.to_dict()]).fillna('')
        df = pd.concat([df, nova_linha], ignore_index=True)
        salvar_dataframe(df)
        return redirect(url_for('admin'))
    return render_template('destino_form.html')

@app.route('/delete/<sigla>')
def delete_destino(sigla):
    df = carregar_dataframe()
    df = df[df.sigla != sigla.upper()]
    salvar_dataframe(df)
    return redirect(url_for('admin'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)