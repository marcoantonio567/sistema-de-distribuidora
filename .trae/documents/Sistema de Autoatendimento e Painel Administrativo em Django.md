## Objetivo
- Autoatendimento público (sem login) para escolher produtos passo a passo
- Capturar nome e telefone e registrar pedido
- Painel administrativo protegido para acompanhar e gerenciar pedidos e estoque

## Acesso e Autenticação
- Kiosk (todas rotas /kiosk) público, sem autenticação
- Painel (/painel) acessível apenas para usuários is_staff via login do Django
- Sem cadastro/conta de clientes; uso de sessão anônima para carrinho

## Arquitetura e Pilha
- Django (views, templates, ORM, auth apenas no painel)
- Banco: SQLite local; Postgres em produção (opcional)
- Sessão para carrinho e progresso do fluxo
- Dependências opcionais: django-formtools (wizard), phonenumbers para validar telefone

## Modelagem de Dados (Distribuidora)
- Marca(id, nome)
- Categoria(id, nome, ativa)
- Produto(id, categoria, marca, nome, volume_ml, embalagem, unidades_por_pacote, preco, ativo, estoque_atual)
- Combo(id, nome, ativo, preco_combo) + ComboItem(combo, produto, quantidade)
- GrupoOpcao(id, produto|categoria, nome, tipo[única|múltipla], obrigatório)
- Opcao(id, grupo, nome, preco_extra, ativo) [ex.: gelo, copos]
- Pedido(id, nome_cliente, telefone, tipo_atendimento[retirada|entrega], observacoes, total, status[novo|em_preparo|pronto|entregue|cancelado], criado_em)
- EnderecoEntrega(id, pedido, rua, numero, bairro, referencia) [opcional]
- ItemPedido(id, pedido, produto, quantidade, preco_unitario, subtotal)
- ItemOpcao(id, item_pedido, opcao, preco_extra)

## Fluxo Step-by-Step (sem login)
- Passo 0: Selecionar tipo de atendimento (retirada ou entrega)
- Passo 1: Escolher categoria (cervejas, refrigerantes, etc.)
- Passo 2: Filtrar/selecionar por marca e volume
- Passo 3: Escolher produto ou combo e quantidade
- Passo 4: Selecionar extras (gelo, copos) quando aplicável
- Passo 5: Revisar carrinho (editar/remover, ver total e estoque)
- Passo 6: Informar nome e telefone; se entrega, endereço
- Passo 7: Confirmar pedido e exibir comprovante

## URLs e Views
- Público: /kiosk/, /kiosk/categorias, /kiosk/produtos, /kiosk/produto/<id>/opcoes, /kiosk/combos, /kiosk/carrinho, /kiosk/checkout, /kiosk/confirmacao
- Painel: /painel/pedidos (lista), /painel/pedidos/<id> (detalhe/status), /painel/estoque (opcional), /painel/relatorios (CSV opcional)

## Regras de Negócio
- Estoque: decrementar ao confirmar pedido; bloquear seleção se estoque insuficiente
- Preço: combos usam preco_combo; extras somam ao subtotal
- Visibilidade: esconder produtos inativos/sem estoque (configurável)
- Sem login do cliente; sessão limpa após confirmação

## Templates e UX
- Mobile-first; stepper claro
- Cards de produto com marca, volume, embalagem, preço e estoque
- Carrinho com subtotal e total; indicação de indisponibilidade
- Formulários simples para nome/telefone e, se entrega, endereço

## Painel Administrativo
- Login (is_staff) obrigatório
- Lista com filtros por status, tipo_atendimento e data
- Ações: atualizar status; imprimir; exportar CSV
- Estoque: alertas e ajuste manual

## Validações e Segurança
- Telefone: RegexValidator ou phonenumbers
- Cálculo de valores e verificação de estoque no backend
- CSRF em formulários; proteção das rotas /painel
- Antispam básico: limitação de repetição de confirmação por sessão; honeypot opcional

## Testes
- Modelos: estoque e cálculos (subtotal, combos, extras)
- Views: fluxo anônimo do kiosk e confirmação
- Painel: filtros, atualização de status e exportação

## Passos de Implementação
- Iniciar projeto e app "distribuidora"
- Modelos, migrações e admin
- Views/URLs públicas sem login (kiosk) usando sessão
- Carrinho, checkout e criação de Pedido/Itens com decremento de estoque
- Templates do step-by-step
- Painel (/painel) com autenticação e ações
- Validações e testes

## Entregáveis
- Autoatendimento público step-by-step para distribuidora
- Painel administrativo protegido com gestão de pedidos e estoque
- Testes cobrindo cálculos e fluxo anônimo