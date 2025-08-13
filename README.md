# CAVALA postagem App

Uma aplicação interativa desenvolvida em Python com Tkinter para auxiliar jogadores de **Uma Musume: Pretty Derby**.<br>
O app permite selecionar uma **cavala** e até **6 cartas de suporte**, exibindo seus respectivos **eventos** de forma interativa e organizada.
Dificuldades pra saber qual opção escolher? Confuso com qual evento vai aparecer e qual recompensa vai conceder? <br>
Vem comigo que vou evitar sua cavala de virar cola o/ 

## 🖼️ Funcionalidades
- Seleção de cavala com imagens;
- Escolha de até 6 cartas de suporte, organizadas por tipo (Speed, Power, Wisdom etc.);
- O jogo te deu uma carta que você não escolheu? Escolha uma carta avulsa sem problemas;
- Exibição dos eventos da cavala e das cartas selecionadas, com botões expansíveis;
- Interface visual com tema escuro, textos brancos, scroll funcional;
- Filtro para procurar evento pelo nome e ganhar tempo;
- Aplicação extremamente leve (.exe pesa menos de 30mb);
- Tela de inicio personalizada demonstrando o quão insano eu sou (você tem 1% de chances de me ouvir relinchar ao iniciar o app);
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
├── imagens/                    # imagens aleatorias em formato .gif para o menu
├── sounds/                     # sons de inicializacao em formato .wav
├── src                         # arquivos em python referente a aplicação
├── CAVALA postagem App.txt     # link para o .exe da beta 1.1 do app
├── README.md                   # este belo arquivo mal formatado
├── launcher.py                 # launcher do app em python
└── requirements.txt            # dependencias a serem instaladas para rodar a aplicação
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
