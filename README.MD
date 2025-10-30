# 📊 Sistema de Gestão de Vendas - Controle de Dívidas

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Flet](https://img.shields.io/badge/Flet-0.22.0-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)
![Status](https://img.shields.io/badge/Status-Em%20Desenvolvimento-orange.svg)

Um sistema completo e intuitivo para gestão de vendas a prazo, controle de dívidas e recebimentos, desenvolvido em Python com interface moderna usando Flet.



## ✨ Características Principais

### 🎯 Funcionalidades Essenciais
- **👥 Cadastro Completo de Clientes** - Dados completos com CPF, telefone e endereço
- **🛒 Registro de Vendas/Dívidas** - Controle detalhado de vendas a prazo
- **💰 Gestão Inteligente de Pagamentos** - Sistema FIFO para quitação automática
- **📊 Histórico Detalhado** - Visualização completa do histórico financeiro
- **🧾 Cupons Automáticos** - Geração de comprovantes em TXT

### 💡 Diferenciais
- ✅ **Interface moderna e responsiva**
- ✅ **Controle por saldo total** (não por venda individual)
- ✅ **Sistema FIFO automático** - Abate sempre a dívida mais antiga
- ✅ **Backup automático em JSON**
- ✅ **Relatórios detalhados com observações**
- ✅ **Multiplataforma** (Windows, Linux, macOS)

## 🛠️ Tecnologias Utilizadas

- **Python 3.8+** - Linguagem principal
- **Flet** - Framework para interface gráfica
- **JSON** - Armazenamento de dados
- **UUID** - Geração de IDs únicos
- **Dateutil** - Manipulação de datas

## 📦 Instalação

### Pré-requisitos
- Python 3.8 ou superior
- pip (gerenciador de pacotes do Python)

### Passo a Passo

1. **Clone o repositório**
```bash
git clone https://github.com/geude/programa_loja.git
cd programa_loja
```

2. **Crie um ambiente virtual (recomendado)**
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

3. **Instale as dependências**
```bash
pip install -r requirements.txt
```

4. **Execute o sistema**
```bash
python programa_loja.py
```

## 📋 Estrutura do Projeto

```
gestao-vendas/
├── 📁 dist/
│   └── 🚀 GestaoDeVendas.exe
├── 📁 cupons_txt/
├── 📄 seu_arquivo.py                 # SEU CÓDIGO PRINCIPAL
├── 📄 requirements.txt              # 👈 ESTE ARQUIVO NOVO
├── 📄 clientes.json
├── 📄 vendas.json
├── 📄 README.md
├── 📄 LICENSE
├── 📄 build.bat
└── 🖼️ icone.ico
```

## 🎮 Como Usar

### 1. 👥 Cadastro de Clientes
- Acesse a aba "Clientes"
- Preencha os dados obrigatórios: **Nome, CPF e Telefone**
- Adicione informações complementares como apelido e endereço
- Clique em "Salvar Cliente"

### 2. 🛒 Registrar Nova Dívida
- Vá para a aba "Dívidas (Vendas)"
- Busque o cliente por nome, CPF ou apelido
- Informe o valor total da dívida
- Adicione observações (opcional)
- Confirme a venda

### 3. 💰 Registrar Pagamentos
- Acesse a aba "Pagamentos"
- Busque o cliente desejado
- O sistema mostrará automaticamente o **saldo devedor total**
- Informe o valor do pagamento e meio de pagamento
- O sistema aplicará automaticamente nas dívidas mais antigas (FIFO)

### 4. 📊 Acompanhamento
- Visualize o histórico completo na aba de pagamentos
- Consulte o status de cada venda individual
- Acompanhe os pagamentos realizados
- Gere cupons automaticamente

## 🔧 Compilação para Executável

### Criar Executável Windows

1. **Instale o PyInstaller**
```bash
pip install pyinstaller
```

2. **Execute o comando de build**
```bash
pyinstaller --onefile --windowed --name="GestaoDeVendas" --icon=icone.ico seu_arquivo.py
```

3. **O executável estará em:**
```
dist/GestaoDeVendas.exe
```

### Script de Build Automático
Crie um arquivo `build.bat`:
```batch
@echo off
pyinstaller --onefile --windowed --name="GestaoDeVendas" --icon=icone.ico seu_arquivo.py
echo Executável criado em: dist\GestaoDeVendas.exe
pause
```

## 📁 Estrutura de Dados

### Clientes (clientes.json)
```json
{
  "nome": "João Silva",
  "cpf": "123.456.789-00",
  "telefone": "(11) 99999-9999",
  "apelido": "João",
  "endereco": "Rua Exemplo, 123"
}
```

### Vendas (vendas.json)
```json
{
  "id": "abc123",
  "cliente": { ... },
  "valor_total": 150.00,
  "data_compra": "15/01/2024",
  "observacao": "Compra de materiais",
  "pagamentos": [
    {
      "valor": 50.00,
      "data_pagamento": "20/01/2024 14:30",
      "meio": "PIX",
      "observacao": "Pagamento parcial"
    }
  ]
}
```

## 🎨 Personalização

### Modificar Cores e Tema
No código, você pode personalizar as cores editando as propriedades:

```python
# Exemplo de personalização
page.theme = ft.Theme(
    color_scheme=ft.ColorScheme(
        primary=ft.Colors.BLUE,
        secondary=ft.Colors.GREEN,
    )
)
```

### Adicionar Novos Meios de Pagamento
Edite a lista na aba de pagamentos:

```python
meio_pagamento_dropdown = ft.Dropdown(
    options=[
        ft.dropdown.Option("PIX"),
        ft.dropdown.Option("DINHEIRO"),
        ft.dropdown.Option("CARTÃO DÉBITO"),
        ft.dropdown.Option("CARTÃO CRÉDITO"),
        ft.dropdown.Option("TRANSFERÊNCIA"),  # Novo método
    ]
)
```

## 🐛 Solução de Problemas

### Problemas Comuns

1. **Erro de Módulo Não Encontrado**
```bash
pip install flet dateutil
```

2. **Arquivos JSON Corrompidos**
- Delete `clientes.json` e `vendas.json`
- O sistema criará novos arquivos automaticamente

3. **Problemas de Permissão**
- Execute como administrador se necessário
- Verifique permissões de escrita na pasta

### Logs e Debug
Os erros são salvos automaticamente no console. Para debug detalhado, adicione:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 🤝 Contribuindo

Contribuições são sempre bem-vindas! 

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📝 Roadmap

- [ ] 🔄 Sincronização em nuvem
- [ ] 📈 Relatórios gráficos
- [ ] 📧 Notificações por e-mail
- [ ] 🔐 Sistema de backup automático
- [ ] 📱 Versão mobile
- [ ] 🌐 Versão web

## 👨‍💻 Desenvolvedor

**Seu Nome**
- GitHub: [@geude](https://github.com/geude)
- Email: geude@hotmail.com



## 🆘 Suporte

Encontrou um problema ou tem uma sugestão?
- 📧 Abra uma [issue](https://github.com/geude/programa_loja/issues)
- 💬 Entre em contato por email geude@hotmail.com

---

**⭐ Se este projeto te ajudou, deixe uma estrela no GitHub!**

---

<div align="center">
  
### 📊 Estatísticas

![GitHub forks](https://img.shields.io/github/forks/geude/programa_loja?style=social)
![GitHub stars](https://img.shields.io/github/stars/geude/programa_loja?style=social)
![GitHub issues](https://img.shields.io/github/issues/geude/programa_loja)

**Feito com ❤️ e Python**

</div>

## 🎯 Próximos Passos

1. **⭐ Dê uma estrela** no repositório se gostou do projeto
2. **🐛 Reporte bugs** abrindo uma issue
3. **💡 Sugira melhorias** para versões futuras
4. **🔀 Faça um fork** e adapte para suas necessidades

---

*Última atualização: Dezembro 2025*