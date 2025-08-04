import streamlit as st
import os
import json
import re
from dotenv import load_dotenv
from streamlit_option_menu import option_menu
from PIL import Image

import database_utils as db
from agent_logic import get_angela_response

# --- CONFIGURAÇÃO INICIAL ---
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# [ALTERAÇÃO] Layout alterado para 'centered' para melhor responsividade
st.set_page_config(page_title="Equojus - Triagem Jurídica",
                   page_icon="⚖️", layout="centered")

db.init_db()

# --- INICIALIZAÇÃO DO SESSION STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Olá! Sou a Angela, sua assistente jurídica da Equojus. Para começarmos, qual o seu nome?"}]
if "conversation_stage" not in st.session_state:
    st.session_state.conversation_stage = "collecting"
if "dossie_data" not in st.session_state:
    st.session_state.dossie_data = None

# --- FUNÇÃO PARA EXTRAIR JSON ---


def extract_json_from_text(text):
    match = re.search(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            return None
    return None


# --- UI E NAVEGAÇÃO ---
try:
    logo = Image.open("assets/logo.png")
    # [ALTERAÇÃO] Centraliza o logo usando colunas
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image(logo)
except FileNotFoundError:
    st.title("⚖️ Equojus - Triagem Jurídica")


with st.sidebar:
    selected = option_menu(
        menu_title="Menu Principal",
        options=["Triagem com Angela", "Consultar Casos"],
        icons=["chat-dots-fill", "journal-text"],
        menu_icon="cast",
        default_index=0,
    )

# --- LÓGICA DAS PÁGINAS ---
if selected == "Triagem com Angela":
    st.subheader(
        "Converse com nossa assistente para iniciar sua triagem", divider='blue')

    # [ALTERAÇÃO] Cria um contêiner para o chat com altura fixa e borda
    chat_container = st.container(height=400, border=True)

    with chat_container:
        # Exibe o histórico do chat
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    # Lógica de confirmação do dossiê
    if st.session_state.conversation_stage == "confirming":
        st.info("Por favor, verifique se as informações abaixo estão corretas.")

        dossie = st.session_state.dossie_data
        st.markdown(f"""
        - **Nome:** {dossie.get('nome_usuario', 'N/A')}
        - **Cidade/Estado:** {dossie.get('cidade_estado', 'N/A')}
        - **Tel./WhatsApp:** {dossie.get('telefone_whatsapp', 'N/A')}
        - **Área do Direito (sugerida):** {dossie.get('area_direito_inferida', 'N/A')}
        - **Resumo da Demanda:** {dossie.get('demanda', 'N/A')}
        """)

        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Sim, estão corretas", use_container_width=True):
                if db.add_case(dossie):
                    success_message = "Perfeito! Seu dossiê foi registrado e enviado para nossa equipe. Em breve, um de nossos especialistas entrará em contato. A Equojus agradece sua confiança."
                    st.session_state.messages.append(
                        {"role": "assistant", "content": success_message})
                    st.session_state.conversation_stage = "finished"
                    st.rerun()
                else:
                    st.error(
                        "Houve um erro ao salvar seu dossiê. Por favor, tente novamente.")
        with col2:
            if st.button("❌ Não, quero corrigir", use_container_width=True):
                correction_prompt = "Entendido. Por favor, me diga o que precisa ser corrigido para que eu possa ajustar."
                st.session_state.messages.append(
                    {"role": "assistant", "content": correction_prompt})
                st.session_state.conversation_stage = "collecting"
                st.session_state.dossie_data = None
                st.rerun()

    # Lógica do Chat principal, desabilitada após o fim da conversa
    chat_disabled = st.session_state.conversation_stage in [
        "confirming", "finished"]
    if prompt := st.chat_input("Digite sua resposta aqui...", disabled=chat_disabled):
        st.session_state.messages.append({"role": "user", "content": prompt})

        # [ALTERAÇÃO] Adiciona a nova mensagem do usuário ao contêiner de chat imediatamente
        with chat_container:
            with st.chat_message("user"):
                st.markdown(prompt)

        # O rerun não é ideal aqui, então vamos processar e exibir a resposta na mesma execução
        with st.spinner("Angela está analisando..."):
            response = get_angela_response(
                OPENAI_API_KEY, st.session_state.messages)
            dossie_data = extract_json_from_text(response)

            if dossie_data:
                st.session_state.dossie_data = dossie_data
                st.session_state.conversation_stage = "confirming"
                st.rerun()  # Rerun é necessário para mostrar os botões de confirmação
            else:
                st.session_state.messages.append(
                    {"role": "assistant", "content": response})
                with chat_container:
                    with st.chat_message("assistant"):
                        st.markdown(response)

elif selected == "Consultar Casos":
    st.subheader("Painel de Casos Registrados", divider='blue')
    casos_df = db.get_all_cases()
    
    # [CORREÇÃO] Adiciona um contador para confirmar que todos os dados foram lidos
    st.caption(f"Total de {len(casos_df)} caso(s) registrado(s) no banco de dados.")

    if casos_df.empty:
        st.info("Nenhum caso registrado.")
    else:
        # A simples remoção de qualquer parâmetro de altura faz com que ele mostre todos os dados.
        st.dataframe(
            casos_df,
            column_config={
                "id": "ID",
                "timestamp": st.column_config.DatetimeColumn("Data/Hora", format="D/M/YYYY, HH:mm"),
                "nome_usuario": "Nome do Usuário",
                "cidade_estado": "Cidade/Estado",
                "telefone_whatsapp": "Tel./WhatsApp",
                "demanda": "Demanda",
                "area_direito_inferida": "Área Inferida",
            },
            use_container_width=True,
            hide_index=True
        )

