import flet as ft
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

def main(page: ft.Page):
    # Configuração da página
    page.title = "Sistema de Gestão de Vendas"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 20
    page.scroll = ft.ScrollMode.ADAPTIVE

    # Variáveis de estado
    calculated_data = None
    cliente_encontrado = None

    # --- Controles para Cadastro de Clientes ---
    nome_cliente_field = ft.TextField(label="Nome Completo", width=400)
    cpf_cliente_field = ft.TextField(label="CPF", width=400)
    tel_cliente_field = ft.TextField(label="Telefone", width=400)
    apelido_cliente_field = ft.TextField(label="Apelido", width=400)
    endereco_cliente_field = ft.TextField(label="Endereço", width=400)

    # --- Controles para Realização de Venda ---
    cpf_venda_field = ft.TextField(label="CPF do Cliente", width=300)
    nome_cliente_encontrado_text = ft.Text("", size=16, weight=ft.FontWeight.BOLD)
    
    valor_total_field = ft.TextField(label="Valor Total (R$)", width=300)
    num_parcelas_field = ft.TextField(label="Número de Parcelas", width=300)
    data_compra_field = ft.TextField(
        label="Data da Compra", 
        width=300,
        value=datetime.now().strftime("%d/%m/%Y")
    )

    # --- Funções de Eventos ---
    def salvar_cliente(e):
        nome = nome_cliente_field.value
        cpf = cpf_cliente_field.value
        tel = tel_cliente_field.value
        apelido = apelido_cliente_field.value
        endereco = endereco_cliente_field.value

        if not all([nome, cpf, tel]):
            mostrar_snackbar("Nome, CPF e Telefone são obrigatórios.", "red")
            return

        clientes = load_json(CLIENTES_FILE)
        
        # Verifica se o cliente já existe pelo CPF
        if any(c['cpf'] == cpf for c in clientes):
            mostrar_snackbar(f"Erro: Já existe um cliente com o CPF {cpf}.", "red")
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
            mostrar_snackbar("Cliente salvo com sucesso!", "green")
            
            # Limpar campos
            nome_cliente_field.value = ""
            cpf_cliente_field.value = ""
            tel_cliente_field.value = ""
            apelido_cliente_field.value = ""
            endereco_cliente_field.value = ""
            page.update()

    def buscar_cliente(e):
        nonlocal cliente_encontrado
        cpf_busca = cpf_venda_field.value
        clientes = load_json(CLIENTES_FILE)
        cliente_encontrado = next((c for c in clientes if c['cpf'] == cpf_busca), None)
        
        if cliente_encontrado:
            nome_cliente_encontrado_text.value = cliente_encontrado['nome']
            mostrar_snackbar("Cliente encontrado!", "green")
        else:
            nome_cliente_encontrado_text.value = "Cliente não encontrado"
            mostrar_snackbar("Cliente não encontrado.", "orange")
        page.update()

    def calcular_parcelas(e):
        nonlocal calculated_data, cliente_encontrado
        
        if not nome_cliente_encontrado_text.value or "não encontrado" in nome_cliente_encontrado_text.value:
            mostrar_snackbar("Primeiro, busque um cliente válido.", "orange")
            return

        try:
            valor_total = float(valor_total_field.value.replace(',', '.'))
            num_parcelas = int(num_parcelas_field.value)
            data_compra = datetime.strptime(data_compra_field.value, "%d/%m/%Y").date()

            if valor_total <= 0 or num_parcelas <= 0:
                mostrar_snackbar("Por favor, insira valores válidos.", "red")
                return

            parcelas = calculate_installments(valor_total, num_parcelas, data_compra)
            
            # Armazena os dados calculados para salvar depois
            calculated_data = {
                'cpf_cliente': cpf_venda_field.value,
                'valor_total': valor_total,
                'data_compra': data_compra_field.value,
                'parcelas': parcelas
            }

            # Exibir resumo em dialog
            mostrar_resumo_venda(parcelas, valor_total, num_parcelas)

        except (ValueError, IndexError):
            mostrar_snackbar("Verifique se os campos estão corretos.", "red")

    def salvar_venda(e):
        nonlocal calculated_data
        
        if calculated_data:
            vendas = load_json(VENDAS_FILE)
            vendas.append(calculated_data)
            save_json(vendas, VENDAS_FILE)
            mostrar_snackbar("Venda salva com sucesso!", "green")
            
            # Limpar campos
            valor_total_field.value = ""
            num_parcelas_field.value = ""
            nome_cliente_encontrado_text.value = ""
            cpf_venda_field.value = ""
            calculated_data = None
            page.update()
        else:
            mostrar_snackbar("Primeiro, calcule os dados da venda.", "orange")

    def mostrar_snackbar(mensagem, cor):
        page.snack_bar = ft.SnackBar(
            content=ft.Text(mensagem),
            bgcolor=cor,
        )
        page.snack_bar.open = True
        page.update()

    def mostrar_resumo_venda(parcelas, valor_total, num_parcelas):
        parcelas_texto = [f"P{p['numero']}: R$ {p['valor']:.2f} (Venc.: {p['data_vencimento']})" for p in parcelas]
        
        conteudo = ft.Column([
            ft.Text(f"Venda para: {nome_cliente_encontrado_text.value}", size=16, weight=ft.FontWeight.BOLD),
            ft.Text(f"Valor: R$ {valor_total:.2f}"),
            ft.Text(f"Parcelas: {num_parcelas} x R$ {parcelas[0]['valor']:.2f}"),
            ft.Divider(),
            ft.Text("Detalhes das Parcelas:", weight=ft.FontWeight.BOLD),
            *[ft.Text(parcela) for parcela in parcelas_texto]
        ], scroll=ft.ScrollMode.ADAPTIVE)

        dialog = ft.AlertDialog(
            title=ft.Text("Resumo da Venda"),
            content=conteudo,
            actions=[
                ft.TextButton("Fechar", on_click=lambda e: fechar_dialog(dialog))
            ]
        )
        
        page.dialog = dialog
        dialog.open = True
        page.update()

    def fechar_dialog(dialog):
        dialog.open = False
        page.update()

    # --- Layout da Aba de Cadastro de Clientes ---
    tab_cadastro = ft.Container(
        content=ft.Column([
            ft.Text("Cadastro de Cliente", size=20, weight=ft.FontWeight.BOLD),
            nome_cliente_field,
            cpf_cliente_field,
            tel_cliente_field,
            apelido_cliente_field,
            endereco_cliente_field,
            ft.ElevatedButton(
                "Salvar Cliente",
                on_click=salvar_cliente,
                color="white",
                bgcolor="blue"
            )
        ], spacing=15)
    )

    # --- Layout da Aba de Realização de Venda ---
    tab_venda = ft.Container(
        content=ft.Column([
            ft.Text("Busca de Cliente", size=20, weight=ft.FontWeight.BOLD),
            ft.Row([
                cpf_venda_field,
                ft.ElevatedButton(
                    "Buscar Cliente",
                    on_click=buscar_cliente,
                    color="white",
                    bgcolor="green"
                )
            ]),
            ft.Row([
                ft.Text("Cliente Encontrado:", size=16),
                nome_cliente_encontrado_text
            ]),
            ft.Divider(),
            ft.Text("Dados da Venda", size=20, weight=ft.FontWeight.BOLD),
            valor_total_field,
            num_parcelas_field,
            data_compra_field,
            ft.Row([
                ft.ElevatedButton(
                    "Calcular Parcelas",
                    on_click=calcular_parcelas,
                    color="white",
                    bgcolor="orange"
                ),
                ft.ElevatedButton(
                    "Salvar Venda",
                    on_click=salvar_venda,
                    color="white",
                    bgcolor="blue"
                )
            ], spacing=20)
        ], spacing=15)
    )

    # --- Tabs Principal ---
    tabs = ft.Tabs(
        selected_index=0,
        animation_duration=300,
        tabs=[
            ft.Tab(
                text="Registrar Cliente",
                content=tab_cadastro
            ),
            ft.Tab(
                text="Realizar Venda",
                content=tab_venda
            )
        ],
        expand=1
    )

    # Adicionar tudo à página
    page.add(tabs)

# Executar o aplicativo
if __name__ == "__main__":
    ft.app(target=main)