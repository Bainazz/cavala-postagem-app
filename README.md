# UmaMusume Companion (ou CAVALA trainer para os chegados)

Uma aplicação interativa desenvolvida em Python com Tkinter para auxiliar jogadores de **Uma Musume: Pretty Derby**.<br>
O app permite selecionar uma **cavala** e até **6 cartas de suporte**, exibindo seus respectivos **eventos** de forma interativa e organizada.
Dificuldades pra saber qual opção escolher? Confuso com qual evento vai aparecer e qual recompensa vai conceder? <br>
Vem comigo que vou evitar sua cavala de virar cola o/ 

## 🖼️ Funcionalidades
- Seleção de cavala com imagens;
- Escolha de até 6 cartas de suporte, organizadas por tipo (Speed, Power, Wisdom etc.);
- Exibição dos eventos da cavala e das cartas selecionadas, com botões expansíveis;
- Interface visual com tema escuro, textos brancos, scroll funcional;
- Aplicação extremamente leve (soma-se menos de 5mb no momento);
- Eventos separados por categoria, com detalhes formatados para melhor visualização e experiência. 

## 📁 Estrutura de Pastas

```
📁 cavala-trainer/
│
├── cartas/                     # arquivos .json com os eventos das cartas
├── cavalas/                    # arquivos .json com os eventos das cavalas                   
├── icon_cartas/                # icones das cartas em formato .png organizados por pastas
├── icon_cavalas/               # icones das cavalas em formato .png
├── icon_geral/                 # icones gerais em formato .ico
├── icon_tipos/                 # icones dos tipos das cartas em formato .png
├── sounds/                     # sons de inicializacao em formato .wav
├── CAVALA_Trainer.exe          # aplicação em fase beta
├── README.md                   # este belo arquivo mal formatado
├── requirements.txt            # dependencias a serem instaladas para rodar a aplicação
└── umamusume_app.py            # código base
```

## ▶️ Como usar
1. Clone ou baixe este repositório ou, caso não seja familiarizado com o github, baixe todos os arquivos e xunxe numa pasta que dá bom 
2. Certifique-se de ter o Python instalado.
3. Instale as dependências:

   ```bash
   pip install -r requirements.txt
   ```

4. Execute o app:
   ```bash
   python umamusume_app.py
   ```

## 🛠️ Requisitos
- Python 3.10+
- Tkinter
- Pillow

## 💡 Observações
- As imagens e arquivos `.json` das cavalas e cartas presentes podem sofrer alteração.
- O app utiliza imagens em `.png` para exibição visual redimensionadas em 128x128.
- Caso queira você mesmo adicionar novas cavalas/ cartas, cada uma deve seguir o modelo de estrutura JSON definido.
- BETA DO APP JÁ DISPONÍVEL! 
