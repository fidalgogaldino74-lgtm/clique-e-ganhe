import streamlit as st
from supabase import create_client, Client
from datetime import datetime

# ⚙️ PEGA AS CHAVES DO STREAMLIT SECRETS
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_CHAVE = st.secrets["SUPABASE_CHAVE"]

# 🔌 Conectar com o Supabase
try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_CHAVE)
except Exception as e:
    st.error(f"Erro de conexão: {e}")

# ⚙️ Configuração da página
st.set_page_config(
    page_title="Clique e Ganhe",
    page_icon="💰",
    layout="centered"
)

# 📊 Constantes do sistema
VALOR_POR_CLIQUE = 0.02
LIMITE_DIARIO = 50
SAQUE_MINIMO = 15.00

# 📦 Inicializar variáveis da sessão
if 'usuario' not in st.session_state:
    st.session_state.usuario = None

# 🔑 Funções de Autenticação
def cadastrar(email, senha):
    try:
        resposta = supabase.auth.sign_up({"email": email, "password": senha})
        return resposta.user, None
    except Exception as e:
        return None, str(e)

def entrar(email, senha):
    try:
        resposta = supabase.auth.sign_in_with_password({"email": email, "password": senha})
        return resposta.user, None
    except Exception as e:
        return None, str(e)

def sair():
    supabase.auth.sign_out()
    st.session_state.usuario = None
    st.rerun()

# 📊 Carregar dados do usuário
def carregar_dados_usuario():
    user_id = st.session_state.usuario.id
    hoje = datetime.now().strftime("%Y-%m-%d")
    
    try:
        resposta = supabase.table('usuarios').select('*').eq('id', user_id).single().execute()
        dados = resposta.data
        
        # Reset diário de cliques
        if dados.get('ultimo_dia') != hoje:
            supabase.table('usuarios').update({
                'cliques_hoje': 0,
                'ultimo_dia': hoje
            }).eq('id', user_id).execute()
            dados['cliques_hoje'] = 0
            dados['ultimo_dia'] = hoje
            
        return dados
    except Exception:
        # Criar perfil se não existir
        novo_perfil = {
            'id': user_id,
            'saldo': 0.00,
            'cliques_hoje': 0,
            'ultimo_dia': hoje,
            'chave_pix': ''
        }
        supabase.table('usuarios').insert(novo_perfil).execute()
        return novo_perfil

# 🖱️ Registrar clique/anúncio
def registrar_clique():
    dados = carregar_dados_usuario()
    
    if dados['cliques_hoje'] >= LIMITE_DIARIO:
        return False, "Limite diário atingido!"
    
    novo_saldo = dados['saldo'] + VALOR_POR_CLIQUE
    novos_cliques = dados['cliques_hoje'] + 1
    
    supabase.table('usuarios').update({
        'saldo': novo_saldo,
        'cliques_hoje': novos_cliques
    }).eq('id', st.session_state.usuario.id).execute()
    
    return True, f"+R$ {VALOR_POR_CLIQUE:.2f} adicionado!"

# 📤 Solicitar saque
def solicitar_saque(chave_pix):
    dados = carregar_dados_usuario()
    
    if dados['saldo'] < SAQUE_MINIMO:
        return False, f"Saldo insuficiente! Mínimo: R$ {SAQUE_MINIMO:.2f}"
    
    supabase.table('usuarios').update({
        'chave_pix': chave_pix
    }).eq('id', st.session_state.usuario.id).execute()
    
    return True, "✅ Solicitação enviada! Analisaremos em até 48h úteis."

# ==========================================
# 🎨 INTERFACE DO APLICATIVO
# ==========================================

# 🔒 TELA DE LOGIN / CADASTRO
if not st.session_state.usuario:
    st.title("💰 Clique e Ganhe")
    st.divider()
    
    aba_login, aba_cadastro = st.tabs(["🔑 Entrar", "📝 Criar Conta"])
    
    with aba_login:
        st.subheader("Fazer Login")
        email_login = st.text_input("Seu E-mail", key="email_login")
        senha_login = st.text_input("Sua Senha", type="password", key="senha_login")
        
        if st.button("Entrar", type="primary", use_container_width=True):
            if not email_login or not senha_login:
                st.error("❌ Preencha e-mail e senha!")
            else:
                with st.spinner("Entrando..."):
                    usuario, erro = entrar(email_login, senha_login)
                    if usuario:
                        st.session_state.usuario = usuario
                        st.success("✅ Entrou com sucesso!")
                        st.rerun()
                    else:
                        st.error(f"❌ Erro: {erro}")
    
    with aba_cadastro:
        st.subheader("Criar Nova Conta")
        email_cad = st.text_input("Seu E-mail", key="email_cad")
        senha_cad = st.text_input("Senha (mínimo 6 caracteres)", type="password", key="senha_cad")
        
        if st.button("Cadastrar", type="primary", use_container_width=True):
            if not email_cad or len(senha_cad) < 6:
                st.error("❌ Preencha tudo! Senha com pelo menos 6 dígitos.")
            else:
                with st.spinner("Criando conta..."):
                    usuario, erro = cadastrar(email_cad, senha_cad)
                    if usuario:
                        st.success("✅ Conta criada! Fazendo login...")
                        st.session_state.usuario = usuario
                        st.rerun()
                    else:
                        st.error(f"❌ Erro: {erro}")

# ✅ TELA PRINCIPAL — USUÁRIO LOGADO
else:
    dados = carregar_dados_usuario()
    
    # Cabeçalho
    col1, col2 = st.columns([3, 1])
    with col1:
        st.title("💰 Clique e Ganhe")
        st.caption(f"👤 {st.session_state.usuario.email}")
    with col2:
        if st.button("Sair"):
            sair()
    
    st.divider()
    
    # Saldo
    st.subheader("Seu Saldo")
    st.markdown(f"<h1 style='color:#2e7d32; font-size:42px;'>R$ {dados['saldo']:.2f}</h1>", unsafe_allow_html=True)
    st.info(f"📊 Anúncios hoje: {dados['cliques_hoje']}/{LIMITE_DIARIO}")
    
    st.divider()
    
    # Botão Ver Anúncio
    st.subheader("Ganhar Recompensa")
    botao_desativado = dados['cliques_hoje'] >= LIMITE_DIARIO
    
    if st.button("👆 Ver Anúncio", type="primary", use_container_width=True, disabled=botao_desativado):
        with st.spinner("Processando..."):
            sucesso, mensagem = registrar_clique()
            if sucesso:
                st.success(f"🎉 {mensagem}")
                st.rerun()
            else:
                st.warning(f"⚠️ {mensagem}")
    
    if botao_desativado:
        st.warning("⚠️ Limite diário atingido! Volte amanhã 😊")
    
    st.divider()
    
    # Saque
    st.subheader("💳 Solicitar Saque")
    chave_pix = st.text_input("Sua Chave PIX", value=dados.get('chave_pix', ''))
    
    if st.button("📤 Solicitar Saque", use_container_width=True):
        if not chave_pix.strip():
            st.error("❌ Digite sua chave PIX!")
        else:
            sucesso, mensagem = solicitar_saque(chave_pix)
            if sucesso:
                st.success(mensagem)
            else:
                st.warning(mensagem)
    
    st.divider()
    st.caption("© 2026 Clique e Ganhe | Todos os direitos reservados 💚")
            
