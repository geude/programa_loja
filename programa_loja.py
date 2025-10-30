import flet as ft
import json
import os
from datetime import datetime
import uuid
import math
from dateutil.relativedelta import relativedelta 

# Arquivos e pastas
CLIENTES_FILE = 'clientes.json'
VENDAS_FILE = 'vendas.json'
CUPONS_DIR = 'cupons_txt'

os.makedirs(CUPONS_DIR, exist_ok=True)


# Helpers de JSON

def load_json(filename):
    if os.path.exists(filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Erro ao carregar {filename}: {e}")
            return []
    return []

def save_json(data, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


# Lógica de formatação

def formatar_moeda(valor):
    if valor is None:
        return "R$ 0,00"
    try:
        # Arredonda para 2 casas e garante a formatação BRL
        return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (ValueError, TypeError):
        return "R$ ERRO"


# Geração de cupom .txt

def gerar_cupom_txt(venda, tipo="venda", pagamento_info=None, saldo_devedor=None):
    cliente = venda['cliente']
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    venda_id = venda.get('id', 'SEM_ID')
    nome_cliente = cliente.get('nome','').strip().replace(" ", "_")[:30] or "CLIENTE"
    filename = f"{tipo}_v{venda_id}_{nome_cliente}_{timestamp}.txt"
    path = os.path.join(CUPONS_DIR, filename)

    linhas = []
    linhas.append("======= CUPOM / COMPROVANTE DE COMPRA / PAGAMENTO =======")
    linhas.append(f"Emitido em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    linhas.append(f"ID Venda: {venda_id}")
    linhas.append("-----------------------------------------")
    linhas.append(f"Cliente: {cliente.get('nome','')}")
    linhas.append(f"CPF: {cliente.get('cpf','')}")
    linhas.append("-----------------------------------------")
    linhas.append(f"Data Compra: {venda.get('data_compra')}")
    linhas.append(f"VALOR ORIGINAL DA COMPRA: {formatar_moeda(venda.get('valor_total', 0))}")
    if venda.get('observacao'):
        linhas.append(f"Observação: {venda.get('observacao')}")
    linhas.append("-----------------------------------------")
    
    if tipo == "pagamento" and pagamento_info:
        linhas.append("== PAGAMENTO REGISTRADO ==")
        linhas.append(f"Valor pago: {formatar_moeda(pagamento_info.get('valor',0))}")
        linhas.append(f"Data pagamento: {pagamento_info.get('data_pagamento')}")
        linhas.append(f"Meio: {pagamento_info.get('meio','')}")
        linhas.append(f"Observação: {pagamento_info.get('observacao', 'Nenhuma')}")
        linhas.append("-----------------------------------------")
        linhas.append(f"SALDO DEVEDOR ATUAL: {formatar_moeda(saldo_devedor)}")

    elif tipo == "venda":
        linhas.append("STATUS: DÍVIDA TOTAL EM ABERTO")

    linhas.append("=========================================")

    with open(path, 'w', encoding='utf-8') as f:
        f.write("\n".join(linhas))

    return os.path.abspath(path)


# Função auxiliar para calcular saldo
def calcular_saldo(venda):
    valor_total = venda.get('valor_total', 0)
    pagamentos = venda.get('pagamentos', [])
    valor_pago = sum(p.get('valor', 0) for p in pagamentos)
    return round(valor_total - valor_pago, 2)



# Aplicação Flet

def main(page: ft.Page):
    page.title = "Sistema de Gestão de Vendas (Saldo Devedor Simples)"
    page.padding = 20
    page.theme_mode = ft.ThemeMode.LIGHT
    
    
    cliente_encontrado = None
    cliente_selecionado_dividas = None
    
    # aba 3
    info_cliente_dividas = ft.Card(
        content=ft.Container(
            content=ft.Column([
                ft.Text("Cliente Selecionado", size=16, weight=ft.FontWeight.BOLD),
                ft.Text("Nenhum cliente selecionado", color=ft.Colors.GREY_700)
            ]),
            padding=15
        ),
        visible=False
    )
    
    # Visualização do Saldo Total
    saldo_display = ft.Row([
        ft.Text("SALDO DEVEDOR TOTAL:", size=20, weight=ft.FontWeight.BOLD),
        ft.Text("R$ 0,00", size=30, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_700)
    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
    
    # Campos de Pagamento
    valor_pagamento_field = ft.TextField(label="Valor a Pagar (R$)", width=200, disabled=True, border_color=ft.Colors.GREEN)
    meio_pagamento_dropdown = ft.Dropdown(
        label="Meio de Pagamento *",
        options=[
            ft.dropdown.Option("PIX"), ft.dropdown.Option("DINHEIRO"), 
            ft.dropdown.Option("CARTÃO DÉBITO"), ft.dropdown.Option("CARTÃO CRÉDITO"), 
        ],
        width=200,
        disabled=True
    )
    obs_pagamento_field = ft.TextField(
        label="Observação do pagamento (opcional)",
        multiline=True,
        width=400,
        disabled=True
    )
    btn_pagar = ft.ElevatedButton("✅ CONFIRMAR PAGAMENTO", on_click=lambda e: registrar_pagamento_simples(e), 
                                    bgcolor=ft.Colors.GREEN, color=ft.Colors.WHITE, disabled=True, style=ft.ButtonStyle(padding=15))
    
    # Histórico de Pagamentos e Dívidas (Detalhes)
    container_detalhes_debitos = ft.Column([ft.Text("Detalhes de todas as dívidas.")], scroll=ft.ScrollMode.ADAPTIVE, height=400)


    
    # Funções utilitárias
    
    def mostrar_mensagem(mensagem, cor="blue"):
        page.snack_bar = ft.SnackBar(ft.Text(mensagem), bgcolor=cor)
        page.snack_bar.open = True
        page.update()

    def fechar_dialog(e=None):
        if page.dialog:
            page.dialog.open = False
            page.update()

    
    # ABA 1: CADASTRO DE CLIENTES
    
    nome_field = ft.TextField(label="Nome Completo", width=400, border_color=ft.Colors.BLUE)
    cpf_field = ft.TextField(label="CPF", width=400, border_color=ft.Colors.BLUE)
    tel_field = ft.TextField(label="Telefone", width=400, border_color=ft.Colors.BLUE)
    apelido_field = ft.TextField(label="Apelido", width=400, border_color=ft.Colors.BLUE)
    endereco_field = ft.TextField(label="Endereço", width=400, border_color=ft.Colors.BLUE)

    def salvar_cliente(e):
        if not nome_field.value or not cpf_field.value or not tel_field.value:
            mostrar_mensagem("Nome, CPF e Telefone são obrigatórios", "red")
            return

        clientes = load_json(CLIENTES_FILE)
        
        if any(c.get('cpf') == cpf_field.value for c in clientes):
            mostrar_mensagem("CPF já cadastrado", "red")
            return

        novo_cliente = {
            'nome': nome_field.value,
            'cpf': cpf_field.value,
            'telefone': tel_field.value,
            'apelido': apelido_field.value,
            'endereco': endereco_field.value
        }
        
        clientes.append(novo_cliente)
        save_json(clientes, CLIENTES_FILE)
        
        nome_field.value = ""
        cpf_field.value = ""
        tel_field.value = ""
        apelido_field.value = ""
        endereco_field.value = ""
        
        mostrar_mensagem("Cliente salvo com sucesso!", "green")
        page.update()

    aba_cadastro = ft.Column([
        ft.Text("Cadastro de Clientes", size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE),
        ft.Container(
            content=ft.Column([
                nome_field,
                cpf_field,
                tel_field,
                apelido_field,
                endereco_field,
                ft.ElevatedButton("Salvar Cliente", on_click=salvar_cliente, 
                                bgcolor=ft.Colors.BLUE, color=ft.Colors.WHITE, width=200)
            ]),
            padding=20,
            border=ft.border.all(2, ft.Colors.BLUE),
            border_radius=10
        )
    ], spacing=20)
    
    
    # ABA 2: VENDAS (Simplificada)
    
    busca_cliente_field = ft.TextField(label="Digite nome, CPF ou apelido do cliente", width=500, border_color=ft.Colors.GREEN)
    
    info_cliente_card = ft.Card(
        content=ft.Container(
            content=ft.Column([
                ft.Text("Informações do Cliente", size=16, weight=ft.FontWeight.BOLD),
                ft.Text("Nenhum cliente selecionado", size=14, color=ft.Colors.GREY_700)
            ]),
            padding=15
        ),
        visible=False
    )
    
    valor_venda_field = ft.TextField(label="Valor Total da Dívida (R$)", width=400, border_color=ft.Colors.RED)
    data_venda_field = ft.TextField(label="Data da Compra", width=400, 
                                   value=datetime.now().strftime("%d/%m/%Y"), border_color=ft.Colors.RED)
    obs_venda_field = ft.TextField(label="Observação (opcional)", width=400, multiline=True, border_color=ft.Colors.RED)

    def buscar_cliente_venda(e):
        nonlocal cliente_encontrado
        termo = busca_cliente_field.value.strip()
        
        clientes = load_json(CLIENTES_FILE)
        cliente_encontrado = next((c for c in clientes if termo.lower() in c.get('nome', '').lower() or termo == c.get('cpf', '') or termo.lower() in c.get('apelido', '').lower()), None)

        if cliente_encontrado:
            info_cliente_card.content.content.controls[1] = ft.Column([
                ft.Text(f"{cliente_encontrado['nome']}", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN),
                ft.Text(f"CPF: {cliente_encontrado['cpf']}"),
            ])
            info_cliente_card.visible = True
            mostrar_mensagem("Cliente encontrado!", "green")
        else:
            info_cliente_card.content.content.controls[1] = ft.Text("Cliente não encontrado", color=ft.Colors.RED)
            info_cliente_card.visible = True
            mostrar_mensagem("Cliente não encontrado", "red")
        
        page.update()

    def confirmar_venda_unica(e):
        nonlocal cliente_encontrado
        
        if not cliente_encontrado:
            mostrar_mensagem("Primeiro busque um cliente", "orange")
            return

        try:
            valor = float(valor_venda_field.value.replace(",", "."))
            data_compra = data_venda_field.value
            
            if valor <= 0:
                mostrar_mensagem("Valor deve ser maior que zero", "red")
                return

            venda_id = str(uuid.uuid4())[:8]
            nova_venda = {
                'id': venda_id,
                'cliente': cliente_encontrado,
                'valor_total': valor, # Valor total da dívida
                'data_compra': data_compra,
                'observacao': obs_venda_field.value,
                'pagamentos': [] # Lista para armazenar pagamentos parciais
            }

            def salvar_e_fechar(e):
                vendas = load_json(VENDAS_FILE)
                vendas.append(nova_venda)
                save_json(vendas, VENDAS_FILE)
                
                caminho = gerar_cupom_txt(nova_venda, tipo="venda", saldo_devedor=valor)
                mostrar_mensagem(f"Venda salva! Dívida de {formatar_moeda(valor)}. Cupom: {caminho}", "green")
                
                # Limpar campos e estado
                valor_venda_field.value = ""
                obs_venda_field.value = ""
                busca_cliente_field.value = ""
                info_cliente_card.visible = False
                cliente_encontrado = None
                
                fechar_dialog()
                page.update()

            page.dialog = ft.AlertDialog(
                title=ft.Text("Confirmar Nova Dívida"),
                content=ft.Column([
                    ft.Text(f"Cliente: {cliente_encontrado['nome']}"),
                    ft.Text(f"Valor da Dívida: {formatar_moeda(valor)}", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.RED),
                ]),
                actions=[
                    ft.TextButton("Cancelar", on_click=fechar_dialog),
                    ft.ElevatedButton("Confirmar Dívida", on_click=salvar_e_fechar, bgcolor=ft.Colors.RED)
                ]
            )
            page.dialog.open = True
            page.update()

        except Exception as e:
            mostrar_mensagem(f"Erro: {str(e)}", "red")

    aba_vendas = ft.Column([
        ft.Text("Registrar Nova Dívida", size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.RED),
        
        # Seção de busca de cliente
        ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Text("Buscar Cliente", size=18, weight=ft.FontWeight.BOLD),
                    busca_cliente_field,
                    ft.ElevatedButton("Buscar Cliente", on_click=buscar_cliente_venda, bgcolor=ft.Colors.RED, color=ft.Colors.WHITE),
                    info_cliente_card
                ]),
                padding=20
            )
        ),
        
        # Seção de dados da venda
        ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Text("Dados da Dívida", size=18, weight=ft.FontWeight.BOLD),
                    valor_venda_field,
                    data_venda_field,
                    obs_venda_field,
                    ft.ElevatedButton("Registrar Dívida", on_click=confirmar_venda_unica, 
                                    bgcolor=ft.Colors.RED, color=ft.Colors.WHITE)
                ]),
                padding=20
            )
        )
    ], spacing=20)
    # ------------------------

    
    # FUNÇÃO: REGISTRAR PAGAMENTO
    
    def registrar_pagamento_simples(e):
        if not cliente_selecionado_dividas:
            mostrar_mensagem("Nenhum cliente selecionado para pagamento.", "red")
            return

        try:
            valor_pago = float(valor_pagamento_field.value.replace(",", "."))
            meio = meio_pagamento_dropdown.value
        except (ValueError, TypeError):
            mostrar_mensagem("Insira um valor numérico válido para o pagamento.", "red")
            return

        if valor_pago <= 0:
            mostrar_mensagem("O valor do pagamento deve ser positivo.", "red")
            return
            
        if not meio:
            mostrar_mensagem("Selecione o meio de pagamento.", "red")
            return

        # 1. Carregar o estado atual do JSON
        vendas = load_json(VENDAS_FILE)
        
        # 2. Filtrar as dívidas em aberto do cliente (ORDENADAS PELO ID, que é sequencial)
        vendas_do_cliente_em_aberto = []
        for i, v in enumerate(vendas):
            if v.get('cliente', {}).get('cpf') == cliente_selecionado_dividas['cpf']:
                saldo = calcular_saldo(v)
                if saldo > 0:
                    vendas_do_cliente_em_aberto.append({'index': i, 'venda': v, 'saldo': saldo})

        if not vendas_do_cliente_em_aberto:
            mostrar_mensagem("Nenhuma dívida em aberto para este cliente.", "green")
            return

        valor_restante_a_pagar = valor_pago
        pagamentos_registrados = []
        
        # 3. Abater o valor pago da dívida mais antiga (FIFO - First In, First Out)
        for item in vendas_do_cliente_em_aberto:
            if valor_restante_a_pagar <= 0:
                break
                
            venda_index = item['index']
            saldo_venda = item['saldo']
            
            # Quanto será pago nesta dívida
            valor_nesta_venda = min(valor_restante_a_pagar, saldo_venda)
            
            if valor_nesta_venda > 0:
                # Registrar o pagamento
                pagamento_info = {
                    'valor': valor_nesta_venda,
                    'data_pagamento': datetime.now().strftime("%d/%m/%Y %H:%M"),
                    'meio': meio,
                    'observacao': obs_pagamento_field.value
                }
                
                # Adicionar pagamento no JSON principal (vendas)
                vendas[venda_index]['pagamentos'].append(pagamento_info)
                
                # Atualizar o valor restante a pagar
                valor_restante_a_pagar -= valor_nesta_venda
                
                # Registrar para o resumo de mensagens e cupom
                pagamentos_registrados.append({
                    'id': vendas[venda_index]['id'],
                    'valor': valor_nesta_venda,
                    'pagamento_info': pagamento_info
                })
        
        # 4. Salvar e Recalcular Saldo Total
        save_json(vendas, VENDAS_FILE)
        
        # Recalcular o saldo total após a atualização
        novo_saldo_total = sum(calcular_saldo(v) for v in vendas if v.get('cliente', {}).get('cpf') == cliente_selecionado_dividas['cpf'])
        
        # 5. Emitir Mensagem e Cupom
        if pagamentos_registrados:
            mostrar_mensagem(f"✅ Pagamento de {formatar_moeda(valor_pago)} registrado! Novo Saldo Total: {formatar_moeda(novo_saldo_total)}", "green")
            
            # Gerar Cupom para a última dívida paga (simplificação)
            if pagamentos_registrados:
                 # Localiza a última venda que recebeu pagamento para gerar o cupom
                ultima_venda_id = pagamentos_registrados[-1]['id']
                venda_para_cupom = next(v for v in vendas if v.get('id') == ultima_venda_id)
                
                # O saldo devedor no cupom deve ser o saldo TOTAL do cliente, não só o daquela venda
                gerar_cupom_txt(
                    venda_para_cupom, 
                    "pagamento", 
                    pagamentos_registrados[-1]['pagamento_info'],
                    novo_saldo_total
                )
        
        # 6. Limpar campos e forçar atualização da aba
        valor_pagamento_field.value = ""
        obs_pagamento_field.value = ""
        
        # Chama a busca novamente para atualizar os displays
        buscar_debitos_simples(None) 
        
    
    # FUNÇÃO: BUSCAR DÉBITOS SIMPLES (Atualiza a Interface)
    
    def buscar_debitos_simples(e):
        nonlocal cliente_selecionado_dividas
        termo = busca_debitos_field.value.strip()
        
        # 1. Resetar Interface
        container_detalhes_debitos.controls.clear()
        valor_pagamento_field.disabled = True
        meio_pagamento_dropdown.disabled = True
        obs_pagamento_field.disabled = True
        btn_pagar.disabled = True
        
        clientes = load_json(CLIENTES_FILE)
        vendas = load_json(VENDAS_FILE)
        
        cliente_selecionado_dividas = next((c for c in clientes if termo.lower() in c.get('nome', '').lower() or termo == c.get('cpf', '') or termo.lower() in c.get('apelido', '').lower()), None)
        
        if not cliente_selecionado_dividas:
            mostrar_mensagem("Cliente não encontrado", "red")
            info_cliente_dividas.visible = False
            saldo_display.controls[1].value = "R$ 0,00"
            saldo_display.controls[1].color = ft.Colors.GREY_700
            page.update()
            return

        info_cliente_dividas.content.content.controls[1] = ft.Column([
            ft.Text(f"{cliente_selecionado_dividas['nome']}", weight=ft.FontWeight.BOLD, color=ft.Colors.PURPLE),
            ft.Text(f"CPF: {cliente_selecionado_dividas['cpf']}")
        ])
        info_cliente_dividas.visible = True
        
        # 2. Processar Dívidas
        vendas_cliente = []
        for v in vendas:
            if v.get('cliente') and v['cliente'].get('cpf') == cliente_selecionado_dividas['cpf']:
                if 'id' not in v: v['id'] = str(uuid.uuid4())[:8]
                if 'pagamentos' not in v: v['pagamentos'] = []
                vendas_cliente.append(v)
        
        save_json(vendas, VENDAS_FILE)

        # 3. Calcular Saldo TOTAL
        saldo_total = sum(calcular_saldo(v) for v in vendas_cliente)
        status_cor = ft.Colors.RED if saldo_total > 0 else ft.Colors.GREEN
        
        saldo_display.controls[1].value = formatar_moeda(saldo_total)
        saldo_display.controls[1].color = status_cor

        # 4. Habilitar/Desabilitar Pagamento
        is_disabled = saldo_total <= 0
        valor_pagamento_field.disabled = is_disabled
        meio_pagamento_dropdown.disabled = is_disabled
        obs_pagamento_field.disabled = is_disabled
        btn_pagar.disabled = is_disabled

        if is_disabled:
             valor_pagamento_field.label = "Dívida PAGA - Sem saldo a receber"
        else:
             valor_pagamento_field.label = "Valor a Pagar (R$)"
        
        # 5. Construir Detalhes e Histórico
        container_detalhes_debitos.controls.append(
            ft.Text("📋 HISTÓRICO COMPLETO DE DÍVIDAS E PAGAMENTOS", 
                   size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_800)
        )
        
        if not vendas_cliente:
            container_detalhes_debitos.controls.append(
                ft.Container(
                    content=ft.Text("Nenhuma dívida registrada para este cliente.", 
                                   size=16, color=ft.Colors.GREY_600, text_align=ft.TextAlign.CENTER),
                    padding=20,
                    alignment=ft.alignment.center
                )
            )
            page.update()
            return
        
        # Ordenar vendas por data (mais recente primeiro)
        vendas_cliente.sort(key=lambda x: x.get('data_compra', ''), reverse=True)
        
        for venda in vendas_cliente:
            saldo = calcular_saldo(venda)
            status_cor = ft.Colors.GREEN if saldo <= 0 else ft.Colors.RED
            status_icone = "✅" if saldo <= 0 else "⏳"
            status_texto = "QUITADA" if saldo <= 0 else f"EM ABERTO: {formatar_moeda(saldo)}"
            
            # Cabeçalho da venda
            venda_card = ft.Card(
                content=ft.Container(
                    content=ft.Column([
                        # Linha do cabeçalho
                        ft.Row([
                            ft.Column([
                                ft.Text(f"🛒 VENDA #{venda['id']}", 
                                       weight=ft.FontWeight.BOLD, size=16),
                                ft.Text(f"📅 Data: {venda['data_compra']}", 
                                       size=12, color=ft.Colors.GREY_600),
                            ], expand=True),
                            ft.Column([
                                ft.Text(f"💵 Valor Original: {formatar_moeda(venda['valor_total'])}", 
                                       size=14, weight=ft.FontWeight.BOLD),
                                ft.Row([
                                    ft.Text(status_icone, size=16),
                                    ft.Text(status_texto, color=status_cor, 
                                           weight=ft.FontWeight.BOLD, size=14),
                                ], spacing=5)
                            ], horizontal_alignment=ft.CrossAxisAlignment.END)
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        
                        # Observação da compra (se existir)
                        ft.Container(
                            content=ft.Column([
                                ft.Text("📝 Observação da Compra:", 
                                       size=12, weight=ft.FontWeight.BOLD, 
                                       color=ft.Colors.BLUE_GREY),
                                ft.Text(venda.get('observacao', 'Nenhuma observação registrada'), 
                                       size=12, color=ft.Colors.GREY_700)
                            ]),
                            visible=bool(venda.get('observacao')),
                            padding=ft.padding.only(top=10, bottom=5)
                        ),
                        
                        ft.Divider(height=1, color=ft.Colors.GREY_300),
                        
                        # Seção de pagamentos
                        ft.Container(
                            content=ft.Column([
                                ft.Text("💳 HISTÓRICO DE PAGAMENTOS:", 
                                       size=14, weight=ft.FontWeight.BOLD,
                                       color=ft.Colors.GREEN_800),
                                
                                # Resumo dos pagamentos
                                ft.Container(
                                    content=ft.Row([
                                        ft.Text(f"Total Pago: {formatar_moeda(sum(p.get('valor', 0) for p in venda.get('pagamentos', [])))}", 
                                               color=ft.Colors.GREEN, weight=ft.FontWeight.BOLD),
                                        ft.Text(f"Saldo Restante: {formatar_moeda(saldo)}", 
                                               color=status_cor, weight=ft.FontWeight.BOLD),
                                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                                    padding=ft.padding.only(bottom=10)
                                ),
                                
                                # Lista detalhada de pagamentos
                                ft.Column([
                                    ft.Container(
                                        content=ft.Row([
                                            ft.Column([
                                                ft.Text(f"💰 {formatar_moeda(p['valor'])}", 
                                                       color=ft.Colors.GREEN, weight=ft.FontWeight.BOLD),
                                                ft.Text(f"📅 {p['data_pagamento']}", 
                                                       size=11, color=ft.Colors.GREY_600),
                                            ], expand=True),
                                            ft.Column([
                                                ft.Text(f"💳 {p['meio']}", 
                                                       size=12, color=ft.Colors.BLUE_700),
                                                ft.Text(f"📝 {p.get('observacao', 'Sem observação')}", 
                                                       size=11, color=ft.Colors.GREY_600,
                                                       max_lines=2),
                                            ], horizontal_alignment=ft.CrossAxisAlignment.END)
                                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                                        padding=10,
                                        border=ft.border.all(1, ft.Colors.GREEN_100),
                                        border_radius=8,
                                        margin=ft.margin.only(bottom=5)
                                    )
                                    for p in venda.get('pagamentos', [])
                                ], spacing=3),
                                
                                # Mensagem quando não há pagamentos
                                ft.Container(
                                    content=ft.Text("Nenhum pagamento registrado para esta venda.", 
                                                   size=12, color=ft.Colors.GREY_500,
                                                   text_align=ft.TextAlign.CENTER),
                                    padding=10,
                                    visible=len(venda.get('pagamentos', [])) == 0
                                )
                            ]),
                            padding=ft.padding.only(top=10)
                        )
                    ]),
                    padding=20,
                    margin=ft.margin.only(bottom=15)
                )
            )
            
            container_detalhes_debitos.controls.append(venda_card)

        page.update()
        
    
    # LAYOUT DA ABA 3 (Pagamentos)
    
    busca_debitos_field = ft.TextField(label="Digite nome, CPF ou apelido do cliente", width=500, border_color=ft.Colors.PURPLE)
    
    aba_dividas = ft.Column([
        ft.Text("💰 Controle de Pagamentos (Saldo Total)", size=28, weight=ft.FontWeight.BOLD, color=ft.Colors.PURPLE),
        
        # Seção 1: Busca e Info do Cliente
        ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Text("1. Buscar Cliente:", size=18, weight=ft.FontWeight.BOLD),
                    ft.Row([
                        busca_debitos_field,
                        ft.ElevatedButton("🔎 BUSCAR", on_click=buscar_debitos_simples, bgcolor=ft.Colors.PURPLE, color=ft.Colors.WHITE, style=ft.ButtonStyle(padding=15))
                    ], spacing=10),
                    info_cliente_dividas
                ]),
                padding=20
            )
        ),
        
        # Seção 2: Resumo do Saldo
        ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Text("2. Saldo Devedor Total:", size=18, weight=ft.FontWeight.BOLD),
                    saldo_display
                ]),
                padding=20
            )
        ),
        
        # Seção 3: Registro de Pagamento
        ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Text("3. Registrar Novo Pagamento (Abate dívida mais antiga)", size=18, weight=ft.FontWeight.BOLD),
                    ft.Row([
                        valor_pagamento_field,
                        meio_pagamento_dropdown,
                    ], spacing=20, alignment=ft.MainAxisAlignment.START),
                    obs_pagamento_field,
                    btn_pagar
                ]),
                padding=20
            )
        ),

        # Seção 4: Detalhes dos Débitos
        ft.Card(
            content=ft.Container(
                content=container_detalhes_debitos,
                padding=20
            ),
            expand=True
        )
    ], spacing=20, scroll=ft.ScrollMode.ADAPTIVE)

    
    # LAYOUT PRINCIPAL
    
    tabs = ft.Tabs(
        selected_index=0,
        tabs=[
            ft.Tab(text="👥 Clientes", content=aba_cadastro), 
            ft.Tab(text="🛒 Dívidas (Vendas)", content=aba_vendas), 
            ft.Tab(text="💰 Pagamentos", content=aba_dividas), 
        ],
        expand=1
    )

    page.add(tabs)

# Executar aplicação
if __name__ == "__main__":
    ft.app(target=main)