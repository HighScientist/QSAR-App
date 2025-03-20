import streamlit as st
import pandas as pd
from PIL import Image
import subprocess
import os
import base64
import pickle

def desc_calc():
    # Comando Java para calcular os descritores
    bashCommand = "/usr/lib/jvm/java-11-openjdk-amd64/bin/java -Xms2G -Xmx2G -Djava.awt.headless=true -jar ./PaDEL-Descriptor/PaDEL-Descriptor.jar -removesalt -standardizenitro -fingerprints -descriptortypes ./PaDEL-Descriptor/PubchemFingerprinter.xml -dir ./ -file descriptors_output.csv"
    
    try:
        # Executa o comando no subprocesso, capturando a saída e erros
        process = subprocess.run(bashCommand, shell=True, check=True, capture_output=True, text=True)
        
        # Log de saída
        st.write("Saída do comando:", process.stdout)
        if process.stderr:
            st.write("Erros:", process.stderr)
        
        # Verifica se o arquivo foi criado
        if os.path.exists('descriptors_output.csv'):
            st.write("Arquivo de descritores gerado com sucesso!")
        else:
            st.write("Erro: O arquivo descriptors_output.csv não foi gerado.")
    
    except subprocess.CalledProcessError as e:
        st.write(f"Erro ao executar o comando. Código de erro: {e.returncode}")
        st.write(f"Saída de erro: {e.stderr}")
        st.write(f"Saída padrão: {e.stdout}")

# Caminho absoluto para garantir que o arquivo seja salvo no diretório correto
output_file_path = os.path.join(os.getcwd(), 'descriptors_output.csv')

# Verifique se o arquivo foi gerado
if os.path.exists(output_file_path):
    desc = pd.read_csv(output_file_path)
    st.write(desc)
    st.write(desc.shape)
else:
    st.error("Erro: o arquivo descriptors_output.csv não foi encontrado!")

# File download
def filedownload(df):
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()  # strings <-> bytes conversions
    href = f'<a href="data:file/csv;base64,{b64}" download="prediction.csv">Download Predictions</a>'
    return href

# Model building
def build_model(input_data):
    # Lê o modelo de regressão salvo
    load_model = pickle.load(open('MGMT_model.pkl', 'rb'))
    
    # Aplica o modelo para fazer previsões
    prediction = load_model.predict(input_data)
    st.header('**Prediction output**')
    prediction_output = pd.Series(prediction, name='pIC50')
    molecule_name = pd.Series(load_data[1], name='molecule_name')  # Assumindo que 'load_data' tem um nome de molécula na posição 1
    df = pd.concat([molecule_name, prediction_output], axis=1)
    st.write(df)
    st.markdown(filedownload(df), unsafe_allow_html=True)

# Logo image
image = Image.open('logo.png')
st.image(image, use_container_width=True)

# Page title
st.markdown("""
# Bioactivity Prediction App (MGMT)

This app allows you to predict the bioactivity towards inhibting the `MGMT` enzyme. `MGMT` is a drug target for High Grade Gliomas.

**Credits**
- Descriptor calculated using [PaDEL-Descriptor](http://www.yapcwsoft.com/dd/padeldescriptor/) [[Read the Paper]](https://doi.org/10.1002/jcc.21707).
- Dataset and Machine Learning Model adaptation by [HighScientist](https://github.com/HighScientist) from [Chanin Nantasenamat](https://medium.com/@chanin.nantasenamat)
---
""")

# Sidebar
with st.sidebar.header('1. Upload your CSV data'):
    uploaded_file = st.sidebar.file_uploader("Upload your input file", type=['txt'])
    st.sidebar.markdown("""
[Example input file](https://github.com/HighScientist/Project-MGMT/blob/main/AI/lomeguatrib.txt)
""")

if st.sidebar.button('Predict'):
    load_data = pd.read_table(uploaded_file, sep=' ', header=None)
    load_data.to_csv('molecule.smi', sep = '\t', header = False, index = False)

    st.header('**Original input data**')
    st.write(load_data)

    with st.spinner("Calculating descriptors..."):
        desc_calc()

    # Read in calculated descriptors and display the dataframe
    st.header('**Calculated molecular descriptors**')
    if os.path.exists('descriptors_output.csv'):
        desc = pd.read_csv('descriptors_output.csv')
        st.write(desc)
        st.write(desc.shape)

        # Read descriptor list used in previously built model
        st.header('**Subset of descriptors from previously built models**')
        Xlist = list(pd.read_csv('descriptor_list.csv').columns)  # Obtém a lista de descritores
        desc_subset = desc[Xlist]  # Filtra os descritores conforme o modelo
        st.write(desc_subset)
        st.write(desc_subset.shape)

        # Apply trained model to make prediction on query compounds
        build_model(desc_subset)
    else:
        st.error("Erro: O arquivo descriptors_output.csv não foi encontrado!")
else:
    st.info('Upload input data in the sidebar to start!')
