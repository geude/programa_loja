import PySimpleGUI as sg
import json
import os
from datetime import datetime
from dateutil.relativedelta import relativedelta

# --- Configuração de arquivos de dados ---
CLIENTES_FILE = 'clientes.json'
VENDAS_FILE = 'vendas.json'

def load_json(filename):
    """Carrega dados de um arquivo JSON ou retorna uma lista vazia se não existir."""
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_json(data, filename):
    """Salva dados em um arquivo JSON."""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def calculate_installments(value, num, start_date):
    """Calcula o valor e as datas de vencimento das parcelas."""
    installments_list = []
    parcel_value = round(value / num, 2)
    current_date = start_date
    for i in range(num):
        installment_due_date = current_date + relativedelta(months=i)
        installments_list.append({
            'numero': i + 1,
            'valor': parcel_value,
            'data_vencimento': installment_due_date.strftime("%d/%m/%Y")
        })
    return installments_list

# --- Layout da Interface ---
sg.theme('LightBlue3')

# --- Aba de Cadastro de Clientes ---
tab1_layout = [
    [sg.Text('Cadastro de Cliente', font=('Arial', 16))],
    [sg.Text('Nome Completo:', size=(15, 1)), sg.Input(key='-NOME_CLIENTE-')],
    [sg.Text('CPF:', size=(15, 1)), sg.Input(key='-CPF_CLIENTE-')],
    [sg.Text('Telefone:', size=(15, 1)), sg.Input(key='-TEL_CLIENTE-')],
    [sg.Text('Apelido:', size=(15, 1)), sg.Input(key='-APELIDO_CLIENTE-')],
    [sg.Text('Endereço:', size=(15, 1)), sg.Input(key='-ENDERECO_CLIENTE-')],
    [sg.Button('Salvar Cliente', key='-SALVAR_CLIENTE-')]
]

# --- Aba de Realização da Venda ---
tab2_layout = [
    [sg.Text('Busca de Cliente', font=('Arial', 16))],
    [sg.Text('CPF do Cliente:', size=(15, 1)), sg.Input(key='-CPF_VENDA-'), sg.Button('Buscar Cliente', key='-BUSCAR-')],
    [sg.Text('Cliente Encontrado:', size=(18, 1)), sg.Text('', key='-NOME_CLIENTE_ENCONTRADO-', font=('Arial', 12, 'bold'))],
    [sg.HorizontalSeparator()],
    [sg.Text('Dados da Venda', font=('Arial', 16))],
    [sg.Text('Valor Total (R$):', size=(15, 1)), sg.Input(key='-VALOR_TOTAL-')],
    [sg.Text('Número de Parcelas:', size=(15, 1)), sg.Input(key='-NUM_PARCELAS-')],
    [sg.Text('Data da Compra:', size=(15, 1)), sg.Input(key='-DATA_COMPRA-', default_text=datetime.now().strftime("%d/%m/%Y")), sg.CalendarButton('Escolher Data', target='-DATA_COMPRA-')],
    [sg.Button('Calcular Parcelas', key='-CALCULAR-'), sg.Button('Salvar Venda', key='-SALVAR_VENDA-')]
]

# --- Layout Principal com Abas ---
layout = [
    [sg.TabGroup([
        [sg.Tab('Registrar Cliente', tab1_layout)],
        [sg.Tab('Realizar Venda', tab2_layout)]
    ])]
]

window = sg.Window('Sistema de Gestão de Vendas', layout, finalize=True)

# --- Loop Principal para Lidar com Eventos ---
while True:
    event, values = window.read()

    if event == sg.WIN_CLOSED:
        break

    # --- Lógica da Aba de Cadastro de Clientes ---
    if event == '-SALVAR_CLIENTE-':
        nome = values['-NOME_CLIENTE-']
        cpf = values['-CPF_CLIENTE-']
        tel = values['-TEL_CLIENTE-']
        apelido = values['-APELIDO_CLIENTE-']
        endereco = values['-ENDERECO_CLIENTE-']

        if not all([nome, cpf, tel]):
            sg.popup('Nome, CPF e Telefone são obrigatórios.', title='Erro')
            continue

        clientes = load_json(CLIENTES_FILE)
        
        # Verifica se o cliente já existe pelo CPF
        if any(c['cpf'] == cpf for c in clientes):
            sg.popup(f'Erro: Já existe um cliente com o CPF {cpf}.', title='Erro')
        else:
            novo_cliente = {
                'nome': nome,
                'cpf': cpf,
                'telefone': tel,
                'apelido': apelido,
                'endereco': endereco
            }
            clientes.append(novo_cliente)
            save_json(clientes, CLIENTES_FILE)
            sg.popup('Cliente salvo com sucesso!', title='Sucesso')
            window['-NOME_CLIENTE-'].update('')
            window['-CPF_CLIENTE-'].update('')
            window['-TEL_CLIENTE-'].update('')
            window['-APELIDO_CLIENTE-'].update('')
            window['-ENDERECO_CLIENTE-'].update('')

    # --- Lógica da Aba de Realização da Venda ---
    if event == '-BUSCAR-':
        cpf_busca = values['-CPF_VENDA-']
        nome_busca = values['-NOME_CLIENTE-']
        apelido_busca = values['-APELIDO_CLIENTE-']
        clientes = load_json(CLIENTES_FILE)
        cliente_encontrado = next((c for c in clientes if c['cpf'] == cpf_busca), None)
        cliente_encontrado = next((c for c in clientes if c['nome'] == nome_busca), None)
        cliente_encontrado = next((c for c in clientes if c['apelido'] == apelido_busca), None)
        
        if cliente_encontrado:
            window['-NOME_CLIENTE_ENCONTRADO-'].update(cliente_encontrado['nome'])
        else:
            window['-NOME_CLIENTE_ENCONTRADO-'].update('Cliente não encontrado')
            sg.popup('Cliente não encontrado.', title='Erro')

    if event == '-CALCULAR-':
        try:
            cpf_venda = values['-CPF_VENDA-']
            if not values['-NOME_CLIENTE_ENCONTRADO-'] or "não encontrado" in values['-NOME_CLIENTE_ENCONTRADO-']:
                sg.popup('Primeiro, busque um cliente válido.', title='Atenção')
                continue
                
            valor_total = float(values['-VALOR_TOTAL-'].replace(',', '.'))
            num_parcelas = int(values['-NUM_PARCELAS-'])
            data_compra = datetime.strptime(values['-DATA_COMPRA-'], "%d/%m/%Y").date()

            if valor_total <= 0 or num_parcelas <= 0:
                sg.popup('Por favor, insira valores válidos.', title='Erro')
                continue

            parcelas = calculate_installments(valor_total, num_parcelas, data_compra)
            
            # Armazena os dados calculados para salvar depois
            window.write_event_value('-CALCULATED_DATA-', {
                'cpf_cliente': cpf_venda,
                'valor_total': valor_total,
                'data_compra': values['-DATA_COMPRA-'],
                'parcelas': parcelas
            })

            # Exibe o resumo (pode ser em um popup ou na própria tela)
            resumo = f"Venda para: {values['-NOME_CLIENTE_ENCONTRADO-']}\n" \
                     f"Valor: R$ {valor_total:.2f}\n" \
                     f"Parcelas: {num_parcelas} x R$ {parcelas[0]['valor']:.2f}\n"
            
            parcelas_texto = [f"P{p['numero']}: R$ {p['valor']:.2f} (Venc.: {p['data_vencimento']})" for p in parcelas]
            sg.popup(resumo + "\nDetalhes das Parcelas:\n" + "\n".join(parcelas_texto), title="Resumo da Venda")


        except (ValueError, IndexError):
            sg.popup('Por favor, verifique se os campos "Valor Total", "Número de Parcelas" e "Data" estão corretos.', title='Erro')

    if event == '-SALVAR_VENDA-':
        if '-CALCULATED_DATA-' in values:
            vendas = load_json(VENDAS_FILE)
            nova_venda = values['-CALCULATED_DATA-']
            vendas.append(nova_venda)
            save_json(vendas, VENDAS_FILE)
            sg.popup('Venda salva com sucesso!', title='Sucesso')
            window['-VALOR_TOTAL-'].update('')
            window['-NUM_PARCELAS-'].update('')
            window['-NOME_CLIENTE_ENCONTRADO-'].update('')
            window['-CPF_VENDA-'].update('')
        else:
            sg.popup('Primeiro, calcule os dados da venda para salvar.', title='Atenção')

window.close()