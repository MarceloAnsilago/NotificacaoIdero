import time
import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
import urllib.parse
import pandas as pd
import random
import streamlit as st

from streamlit_option_menu import option_menu






def preprocess_dataframe(df, user_choice):
     

    if user_choice == 'Continuar uma lista anterior':
                # Se tiver mais de 4 colunas, retorna uma mensagem de erro.
        if len(df.columns) > 4:
            return "Para continuar de uma lista anterior, a planilha deve conter apenas as colunas Status, Telefone, Nome e Prazo Brucelose quando for o caso."
        else:
            # Se tiver 4 ou menos colunas, continua o processamento.
            # return df
            return df
# Verifica se as colunas necessárias estão presentes no DataFrame
    required_columns = [
        'Nome do Titular da Ficha de bovideos', 'Nome da Propriedade',
        'Endereço da Prop.', 'Dec. Rebanho', 'Telefone 1', 'Telefone 2', 'Celular'
    ]
    
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise ValueError(f"As seguintes colunas estão faltando na planilha: {missing_columns}")


    # Se a escolha for "Quem não declarou a campanha atual", remove as linhas onde 'Dec. Rebanho' é 0
    if user_choice == 'Quem não declarou a campanha atual':
        df = df[df['Dec. Rebanho'] == 0]
    
    # Se a escolha for "Enviar para todos/Notificar Brucelose" ou "Quem já declarou", mantém todas as linhas
    elif user_choice == 'Enviar para todos/Notificar Brucelose':
        pass  # Não faz nada, mantém todas as linhas

 
    # Aplica o restante do pré-processamento comum a todas as escolhas
            # Definindo as colunas a manter baseado na existência da coluna 'Prazo brucelose'
    if 'Prazo brucelose' in df.columns:
        colunas_a_manter = ['Prazo brucelose', 'Nome do Titular da Ficha de bovideos', 'Nome da Propriedade', 'Endereço da Prop.', 'Dec. Rebanho', 'Telefone 1', 'Telefone 2', 'Celular']
    else:
        colunas_a_manter = ['Nome do Titular da Ficha de bovideos', 'Nome da Propriedade', 'Endereço da Prop.', 'Dec. Rebanho', 'Telefone 1', 'Telefone 2', 'Celular']

    # Atualizando o DataFrame para manter apenas as colunas definidas em 'colunas_a_manter'
    df = df[colunas_a_manter]

    # Colunas a serem derretidas (Telefone 1, Telefone 2 e Celular)
    colunas_para_derreter = ['Telefone 1', 'Telefone 2', 'Celular']
    # Colunas a serem derretidas (Telefone 1, Telefone 2 e Celular)
    df = pd.melt(df, id_vars=[coluna for coluna in df.columns if coluna not in colunas_para_derreter], 
                    value_vars=colunas_para_derreter, value_name='Telefone')

    # Opcional: Remova linhas onde 'Telefone' é None ou NaN
    df.dropna(subset=['Telefone'], inplace=True)

    # Removemos a coluna 'variable' criada automaticamente, já que ela não é necessária
    df.drop(columns=['variable'], inplace=True)

      
    # Combine as colunas 'Nome do Titular da Ficha de bovideos', 'Nome da Propriedade' e 'Endereço da Prop.' em 'Nome'
    df['Nome'] = df.apply(lambda row: f"{row['Nome do Titular da Ficha de bovideos']} - {row['Nome da Propriedade']} - {row['Endereço da Prop.']}", axis=1)
      
    # Exclua as colunas 'Nome do Titular da Ficha de bovideos', 'Nome da Propriedade' e 'Endereço da Prop.'
    df = df.drop(columns=['Nome do Titular da Ficha de bovideos', 'Nome da Propriedade','Endereço da Prop.'])
  
    # Reorganize as colunas para colocar 'Nome' como a primeira coluna
    df = df[['Nome'] + [col for col in df.columns if col != 'Nome']]

    # Suponhamos que sua coluna com números de telefone seja chamada 'telefone'
    df['Telefone'] = df['Telefone'].astype(str)  # Certifique-se de que a coluna seja do tipo string
 
    # Substitua todos os caracteres não numéricos, exceto o hífen, por uma string vazia
    df['Telefone'] = df['Telefone'].str.replace(r'[^0-9-]', '', regex=True)

    # Preencha zeros à esquerda para obter um formato consistente (por exemplo, 1234567890)
    df['Telefone'] = df['Telefone'].str.zfill(10)

    # Use o método str.endswith para verificar se os dois últimos dígitos da direita são '00'
    df = df[~df['Telefone'].str.endswith('00')]

    # Adicione '+55' na frente de todos os números de telefone
    df['Telefone'] = '+55' + df['Telefone']

    df['Telefone'] = df['Telefone'].apply(lambda telefone: telefone[:5] + telefone[6:] if len(telefone) == 15 else telefone)
    
    # Crie a coluna "Status" com valor zero
    df["Status"] = "Fila de envio"

    df = df.drop(columns=['Dec. Rebanho'])
    
    # Reordene as colunas para colocar "Status" antes de "Nome"
    df = df[["Status"] + [col for col in df.columns if col != "Status"]]

    # # Adiciona espaços nas posições desejadas
    df['Telefone'] = df['Telefone'].str[:3] + ' ' + df['Telefone'].str[3:5] + ' ' + df['Telefone'].str[5:]
        
    # Reordene as colunas para colocar "Status" antes de "Nome"
    df = df[["Status"] + [col for col in df.columns if col != "Status"]]
   
    return df  

def verificar_modal(driver): # Jeito encontrado pra verificar se o numero é invalido ou não
        modal_xpath = "//div[contains(text(), 'O número de telefone compartilhado por url é inválido')]"
        button_xpath = "//button[contains(., 'OK')]"

        try:
            WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, modal_xpath)))
            print("Modal encontrado na página.")
            ok_button = driver.find_element(By.XPATH, button_xpath)
            ok_button.click()
            return False  # Retorna False indicando que o número é inválido
        except Exception as e:
            print(f"Número de telefone válido. Procedendo  o envio")

def disparar(contato, mensagem):
        global driver  # Indique que vamos usar a variável global driver 
        mensagem = urllib.parse.quote(mensagem)
        link = f"https://web.whatsapp.com/send?phone={contato}&text={mensagem}"

        driver.get(link)


        if not verificar_modal(driver):  #Verifica que o numero é valido
                print("Número de telefone inválido. Ação interrompida.")
            
                # exibir_mensagem_personalizada
                processed.at[index, 'Status'] = 'Invalido'
                # filtrar_e_salvar(processed)
                return  # Interrompe a execução se o número for inválido

        while len(driver.find_elements(By.XPATH, '//*[@id="main"]/footer/div[1]/div/span[2]/div/div[2]/div[2]/button/span')) < 1:
                    time.sleep(1)
        time.sleep(2)  # Uma pausa adicional para garantir a estabilidade, se necessário          
        driver.find_element(By.XPATH, '//*[@id="main"]/footer/div[1]/div/span[2]/div/div[2]/div[2]/button/span').click()                                    
        time.sleep(gerar_segundo_aleatorio( st.session_state.segundo_inicial, st.session_state.segundos_finais)) 
        webdriver.ActionChains(driver).send_keys(Keys.ESCAPE).perform()


def gerar_segundo_aleatorio(segundo_inicial, segundo_final):
    # Gera um número aleatório entre segundo_inicial e segundo_final
    segundos = random.randint(segundo_inicial, segundo_final)
    return segundos

def iniciar_whatsapp_web():
    global driver  # Indique que vamos usar a variável global driver
    st.write("Processo de disparos iniciados!")
    
    # Configurações do Chrome para rodar em modo "headless"
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Modo headless (sem interface gráfica)
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    # Especificando a versão do ChromeDriver corretamente
    Servico = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=Servico, options=chrome_options)  # Passando as opções configuradas
    driver.get('https://web.whatsapp.com')
    
    # Aguarda até que o elemento 'side' esteja presente
    while len(driver.find_elements(By.ID, 'side')) < 1:
        time.sleep(1)
    
    time.sleep(2)
    st.write("WhatsApp Web carregado e pronto para uso.")

try:
    iniciar_whatsapp_web()
except Exception as e:
    st.error(f"Ocorreu um erro ao iniciar o WhatsApp Web: {str(e)}")


def calcular_contagens_status(df):
    if 'Status' in df.columns and not df.empty:
        contagem_status = df['Status'].value_counts().reset_index()
        contagem_status.columns = ['Status', 'Quantidade']
        total_linhas = df.shape[0]
        contagem_status['Porcentagem'] = (contagem_status['Quantidade'] / total_linhas * 100).round(2)
        return contagem_status
    else:
        return pd.DataFrame(columns=['Status', 'Quantidade', 'Porcentagem'])



#Exibição

st.set_page_config( page_title="Envio whatsapp")
# Definição inicial dos valores padrão no estado da sessão
# Para usar em outras abas
if 'segundo_inicial' not in st.session_state:
    st.session_state.segundo_inicial = 10
if 'segundos_finais' not in st.session_state:
    st.session_state.segundos_finais = 15
if "MsgAenviar"not in st.session_state:
    st.session_state.MsgAenviar =  "Olá, tudo bem? Essa é uma mensagem da IDARON"     
if 'processed' not in st.session_state:
    st.session_state['processed'] = None    
 




selecao = option_menu(
    menu_title="Disparar Mensagens e Notificações",
    options=["Contatos", "Configuração","Envio", "Estatisticas"],
    icons=['book', 'gear', 'send ',"grid"],
    orientation='horizontal',
    menu_icon='cast'
)



# Conteúdo da aba "Contatos"
if selecao == "Contatos":
    st.write('Contatos')

    user_choice = st.radio(
        "Enviar para:",
        ('Quem não declarou a campanha atual',
         'Enviar para todos/Notificar Brucelose',
         'Continuar uma lista anterior'),
        key='user_choice_key'
    )

    uploaded_file = st.file_uploader("Escolha um arquivo de dados", type=['xlsx', 'xls', 'ods'], key='file_uploader_key')

    if uploaded_file is not None:
        try:
          
            df = pd.read_excel(uploaded_file, engine='openpyxl')
            processed = preprocess_dataframe(df, user_choice)
            
            if isinstance(processed, str):
                st.error(processed)
            else:
                st.session_state['processed'] = processed  # Armazena no estado da sessão
        except Exception as e:
            st.error(f"Ocorreu um erro: {e}")
     # Exibe o DataFrame se já estiver definido
    
    if st.session_state['processed'] is not None:
        st.dataframe(st.session_state['processed'])  






# Conteúdo da aba "Configuração"
elif selecao == "Configuração":
    st.write("Configurações")
    st.write("Informe o segundo inicial e final para o delay entre as mensagens:")
    st.session_state.segundo_inicial = st.number_input("De, segundo inicial", min_value=0, value=st.session_state.segundo_inicial, step=1, key='start_seconds')
    st.session_state.segundos_finais = st.number_input("Até, segundos finais", min_value=0, value=st.session_state.segundos_finais, step=1, key='end_seconds')
    # Informações sobre como formular a mensagem
    st.write("Informe a mensagem que deseja enviar")  
    st.write("Use -Num para o número do contato") 
    st.write("Use -Cont para o nome do contato") 
    st.write("Use -Praz para prazo em dias de brucelose quando for o caso") 
    st.session_state.MsgAenviar = st.text_area(
        "Digite sua mensagem aqui",
        value=st.session_state.MsgAenviar,  # Este argumento já define o valor inicial
        height=300
    )
        





# Conteúdo da aba "envios"
elif selecao == "Envio":
    st.write("Disparar Mensagens")
    
    # Verifica se os dados processados estão disponíveis e são um DataFrame
    if 'processed' in st.session_state and isinstance(st.session_state['processed'], pd.DataFrame) and not st.session_state['processed'].empty:
        if st.button('Iniciar WhatsApp Web'):
            iniciar_whatsapp_web()
            st.session_state['whatsapp_web_started'] = True
            for index, row in st.session_state['processed'].iterrows():
                if row['Status'] == 'Fila de envio':
                    telefone = row['Telefone']
                    produtor = row['Nome']




    else:
        # Mensagem quando não há dados processados disponíveis
        st.write("Aguardando dados processados para iniciar o envio. Por favor, vá para a aba 'Contatos' e processe os dados necessários primeiro.")
        st.button('Iniciar WhatsApp Web', disabled=True)  # Botão desabilitado para evitar ação quando não há dados












elif selecao == "Estatisticas":
   
    st.write("Estatísticas")
    if 'processed' in st.session_state and isinstance(st.session_state['processed'], pd.DataFrame) and not st.session_state['processed'].empty:
        df_contagens = calcular_contagens_status(st.session_state['processed'])
        if not df_contagens.empty:
            st.write("Contagem de Status e Proporção Total:")
            st.dataframe(df_contagens)
            for index, row in df_contagens.iterrows():
                st.metric(label=f"Status: {row['Status']}",
                          value=f"{row['Quantidade']} entradas",
                          delta=f"{row['Porcentagem']}% do total")
        else:
            st.write("Nenhuma contagem de status para exibir.")
    else:
        st.write("Nenhum dado processado disponível para exibir.")