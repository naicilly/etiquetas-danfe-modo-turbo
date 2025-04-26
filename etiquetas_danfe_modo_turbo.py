
import streamlit as st
import fitz  # PyMuPDF
from PyPDF2 import PdfReader, PdfWriter
import re
import io

st.set_page_config(page_title="ETIQUETAS + DANFE MODO TURBO 🚀", page_icon="🚀")
st.title("📦 ETIQUETAS + DANFE MODO TURBO 🚀")

st.markdown("Faça upload dos arquivos de Etiquetas e DANFEs para organizá-los automaticamente!")

# Upload dos arquivos
uploaded_etiqueta = st.file_uploader("📄 Upload do arquivo de ETIQUETAS", type=["pdf"])
uploaded_danfe = st.file_uploader("📄 Upload do arquivo de DANFEs", type=["pdf"])

if uploaded_etiqueta and uploaded_danfe:
    if st.button("🚀 Processar Arquivos"):
        # Ler PDFs
        pdf_etiquetas = fitz.open(stream=uploaded_etiqueta.read(), filetype="pdf")
        pdf_danfes = fitz.open(stream=uploaded_danfe.read(), filetype="pdf")

        def extrair_nome_etiqueta(texto):
            for linha in texto.splitlines():
                if "destinatário" in linha.lower():
                    partes = linha.split(":")
                    if len(partes) > 1 and partes[1].strip():
                        return partes[1].strip().lower()
            linhas = texto.splitlines()
            for i, linha in enumerate(linhas):
                if "destinatário" in linha.lower() and i + 1 < len(linhas):
                    nome = linhas[i + 1].strip().lower()
                    if nome:
                        return nome
            return None

        def extrair_nome_danfe(texto):
            for linha in texto.splitlines():
                if "endereço de entrega:" in linha.lower():
                    depois = linha.split(":", 1)[-1].strip()
                    nome_cliente = depois.split(",")[0].strip()
                    return nome_cliente.lower()
            return None

        def mapear_nomes(pdf, extrator_func):
            nomes = {}
            for i in range(len(pdf)):
                texto = pdf[i].get_text()
                nome = extrator_func(texto)
                if nome:
                    nomes[nome] = i
            return nomes

        mapa_etiquetas = mapear_nomes(pdf_etiquetas, extrair_nome_etiqueta)
        mapa_danfes = mapear_nomes(pdf_danfes, extrair_nome_danfe)

        def normalizar(nome):
            nome = nome.strip().upper()
            nome = re.sub(r'\s+', ' ', nome)
            return nome

        def chave_reduzida(nome, max_caracteres=25):
            return normalizar(nome)[:max_caracteres]

        danfes_por_nome = {}
        for nome, idx in mapa_danfes.items():
            key = chave_reduzida(nome)
            danfes_por_nome.setdefault(key, []).append(idx)

        pares = []
        etiquetas_sem_danfe = []
        danfes_usadas = set()

        for nome, idx_etiqueta in mapa_etiquetas.items():
            key = chave_reduzida(nome)
            if key in danfes_por_nome and danfes_por_nome[key]:
                idx_danfe = danfes_por_nome[key].pop(0)
                pares.append((nome, idx_etiqueta, idx_danfe))
                danfes_usadas.add(idx_danfe)
            else:
                etiquetas_sem_danfe.append(idx_etiqueta)

        danfes_sem_etiqueta = [idx for nome, idx in mapa_danfes.items() if idx not in danfes_usadas]

        pares.sort(key=lambda x: normalizar(x[0]))

        # Reabrir PDFs
        uploaded_etiqueta.seek(0)
        uploaded_danfe.seek(0)
        reader_etiquetas = PdfReader(io.BytesIO(uploaded_etiqueta.read()))
        reader_danfes = PdfReader(io.BytesIO(uploaded_danfe.read()))
        writer = PdfWriter()

        for _, idx_etiqueta, idx_danfe in pares:
            writer.add_page(reader_etiquetas.pages[idx_etiqueta])
            writer.add_page(reader_danfes.pages[idx_danfe])

        for idx in etiquetas_sem_danfe:
            writer.add_page(reader_etiquetas.pages[idx])

        for idx in danfes_sem_etiqueta:
            writer.add_page(reader_danfes.pages[idx])

        # Salvar arquivo
        output_buffer = io.BytesIO()
        writer.write(output_buffer)
        output_buffer.seek(0)

        # Mostrar Resumo
        st.success("✅ Organização Concluída!")
        st.info(f"🔢 Total de etiquetas casadas com DANFE: {len(pares)}")
        st.info(f"📦 Total de etiquetas sem DANFE: {len(etiquetas_sem_danfe)}")
        st.info(f"🧾 Total de DANFEs sem etiqueta: {len(danfes_sem_etiqueta)}")

        # Botão para download
        st.download_button(
            label="📥 Baixar Arquivo Organizado",
            data=output_buffer,
            file_name="Etiquetas_DANFEs_Combinadas_Final.pdf",
            mime="application/pdf"
        )
