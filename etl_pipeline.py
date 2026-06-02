#!/usr/bin/env python3
"""
Pipeline ETL: Orientador Financeiro Personalizado
Autor: Engenheiro e Cientista de Dados Sênior
Descrição: Script modular, PEP 8 complacente, para extrair dados de transações
           (reais do Kaggle ou sintéticos), categorizar e agregar métricas,
           gerar insights de consultoria financeira e carregar em CSV/JSON.
"""

import os
import sys
import json
import logging
import pandas as pd

# Configuração simples de Logging para exibir etapas do processo ETL
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)


# =====================================================================
# 1. ETAPA DE EXTRAÇÃO (EXTRACT)
# =====================================================================

def extrair_dados(caminho_csv: str = "dados_transacoes_brutas.csv",
                  caminho_excel: str = "data/bank.xlsx") -> pd.DataFrame:
    """
    Executa a extração dos dados brutos de transações.
    Busca o CSV local. Se inexistente, tenta ler e formatar o dataset do Kaggle (bank.xlsx).
    Se o Excel também não existir, gera dados sintéticos realistas.
    
    Retorna:
        pd.DataFrame contendo o schema:
        [id_cliente (int), nome_cliente (str), data_transacao (str), descricao (str), valor (float)]
    """
    logging.info("[EXTRAÇÃO] Iniciando etapa de Extração de dados brutos...")
    
    # Caso 1: O CSV bruto já existe localmente
    if os.path.exists(caminho_csv):
        try:
            logging.info(f"[EXTRAÇÃO] Lendo arquivo CSV existente: {caminho_csv}")
            df = pd.read_csv(caminho_csv)
            # Garantir tipos adequados
            df['id_cliente'] = df['id_cliente'].astype(int)
            df['nome_cliente'] = df['nome_cliente'].astype(str)
            df['data_transacao'] = pd.to_datetime(df['data_transacao']).dt.strftime('%Y-%m-%d')
            df['descricao'] = df['descricao'].astype(str)
            df['valor'] = df['valor'].astype(float)
            logging.info(f"[EXTRAÇÃO] Sucesso! {len(df)} transações carregadas do CSV.")
            return df
        except Exception as e:
            logging.error(f"[EXTRAÇÃO] Erro ao ler o CSV {caminho_csv}: {e}. Tentando reconstruir.")

    # Caso 2: CSV não existe, mas o Excel do Kaggle está disponível
    if os.path.exists(caminho_excel):
        try:
            logging.info(f"[EXTRAÇÃO] CSV não encontrado. Lendo Excel do Kaggle: {caminho_excel}")
            df_excel = pd.read_excel(caminho_excel)
            
            # Contas reais mapeadas para clientes fictícios em português
            contas_mapeadas = {
                "409000611074'": (1, "Alice"),
                "409000405747'": (2, "Bruno"),
                "409000493201'": (3, "Carla"),
                "409000425051'": (4, "Daniel"),
                "409000493210'": (5, "Elisa")
            }
            
            # Filtra apenas as contas mapeadas
            df_filtrado = df_excel[df_excel['Account No'].isin(contas_mapeadas.keys())].copy()
            
            # Seleciona as primeiras 4 transações de cada cliente para atingir ~20 registros no total
            df_subset = df_filtrado.groupby('Account No').head(4).copy()
            
            # Listas para mapeamento de descrições brasileiras realistas de acordo com o fluxo
            descritivos_receitas = [
                "PIX Recebido de Conta Poupança",
                "Salário Mensal Corporativo",
                "Transferência PIX Recebida",
                "Rendimento CDB Recebido"
            ]
            descritivos_despesas = [
                "Uber Trip Aeroporto",
                "Supermercado Pão de Açúcar Compra",
                "Netflix Mensalidade Premium",
                "Restaurante Silva Jantar",
                "Cinema Play Ingresso",
                "Shopping Iguatemi Estacionamento",
                "Padaria Central Pão",
                "Uber Corrida de Negócios"
            ]
            
            registros = []
            for i, (_, row) in enumerate(df_subset.iterrows()):
                acc_no = row['Account No']
                id_cli, nome_cli = contas_mapeadas[acc_no]
                data_t = pd.to_datetime(row['DATE']).strftime('%Y-%m-%d')
                
                # Calcula o valor baseado em depósitos e retiradas do Kaggle
                deposito = row['DEPOSIT AMT']
                retirada = row['WITHDRAWAL AMT']
                
                if pd.notna(deposito) and deposito > 0:
                    valor = float(deposito)
                    # Associa descrição de receita de forma determinística
                    descricao = descritivos_receitas[i % len(descritivos_receitas)]
                elif pd.notna(retirada) and retirada > 0:
                    valor = float(-retirada)
                    # Associa descrição de despesa de forma determinística
                    descricao = descritivos_despesas[i % len(descritivos_despesas)]
                else:
                    # Fallback neutro
                    valor = 0.0
                    descricao = "Tarifa Bancária de Manutenção"
                    if valor == 0.0:
                        # Para não ter valor zero no dataset, atribuímos um valor de despesa simbólico
                        valor = -15.00
                
                registros.append({
                    "id_cliente": id_cli,
                    "nome_cliente": nome_cli,
                    "data_transacao": data_t,
                    "descricao": descricao,
                    "valor": valor
                })
                
            df_final = pd.DataFrame(registros)
            
            # Salva o CSV bruto para as próximas execuções
            df_final.to_csv(caminho_csv, index=False, encoding='utf-8')
            logging.info(f"[EXTRAÇÃO] Sucesso! Dataset gerado a partir do Excel e salvo em: {caminho_csv}")
            return df_final
            
        except Exception as e:
            logging.error(f"[EXTRAÇÃO] Erro ao extrair dados do Excel: {e}. Criando dados sintéticos.")

    # Caso 3: Fallback final para dados sintéticos puramente via Pandas
    logging.info("[EXTRAÇÃO] Arquivos fonte não encontrados. Gerando base de dados sintética realista...")
    dados_sinteticos = [
        # Alice (ID 1) - Saldo Positivo e saudável
        {"id_cliente": 1, "nome_cliente": "Alice", "data_transacao": "2026-05-10", "descricao": "Salário Mensal", "valor": 8000.00},
        {"id_cliente": 1, "nome_cliente": "Alice", "data_transacao": "2026-05-12", "descricao": "Netflix Mensalidade", "valor": -55.90},
        {"id_cliente": 1, "nome_cliente": "Alice", "data_transacao": "2026-05-15", "descricao": "Supermercado Pão de Açúcar", "valor": -450.20},
        {"id_cliente": 1, "nome_cliente": "Alice", "data_transacao": "2026-05-18", "descricao": "Uber Trip", "valor": -32.50},
        
        # Bruno (ID 2) - Saldo Negativo
        {"id_cliente": 2, "nome_cliente": "Bruno", "data_transacao": "2026-05-01", "descricao": "PIX Recebido", "valor": 1200.00},
        {"id_cliente": 2, "nome_cliente": "Bruno", "data_transacao": "2026-05-05", "descricao": "Supermercado Extra", "valor": -850.00},
        {"id_cliente": 2, "nome_cliente": "Bruno", "data_transacao": "2026-05-10", "descricao": "Restaurante Jantar", "valor": -380.00},
        {"id_cliente": 2, "nome_cliente": "Bruno", "data_transacao": "2026-05-12", "descricao": "Cinema Play", "valor": -45.00},
        
        # Carla (ID 3) - Saldo Alto (Investimentos)
        {"id_cliente": 3, "nome_cliente": "Carla", "data_transacao": "2026-05-02", "descricao": "PIX Recebido", "valor": 15000.00},
        {"id_cliente": 3, "nome_cliente": "Carla", "data_transacao": "2026-05-05", "descricao": "Shopping Iguatemi", "valor": -1200.00},
        {"id_cliente": 3, "nome_cliente": "Carla", "data_transacao": "2026-05-08", "descricao": "Restaurante Fasano", "valor": -750.00},
        {"id_cliente": 3, "nome_cliente": "Carla", "data_transacao": "2026-05-15", "descricao": "Netflix Mensalidade", "valor": -55.90},
        
        # Daniel (ID 4) - Orçamento Apertado
        {"id_cliente": 4, "nome_cliente": "Daniel", "data_transacao": "2026-05-05", "descricao": "Salário Mensal", "valor": 3000.00},
        {"id_cliente": 4, "nome_cliente": "Daniel", "data_transacao": "2026-05-10", "descricao": "Supermercado Dia", "valor": -2400.00},
        {"id_cliente": 4, "nome_cliente": "Daniel", "data_transacao": "2026-05-12", "descricao": "Uber Trip", "valor": -180.00},
        {"id_cliente": 4, "nome_cliente": "Daniel", "data_transacao": "2026-05-15", "descricao": "Cinema UCI", "valor": -35.00},
        
        # Elisa (ID 5) - Saldo Saudável, maior ralo em Transporte
        {"id_cliente": 5, "nome_cliente": "Elisa", "data_transacao": "2026-05-01", "descricao": "PIX Recebido", "valor": 5000.00},
        {"id_cliente": 5, "nome_cliente": "Elisa", "data_transacao": "2026-05-05", "descricao": "Supermercado Pão de Açúcar", "valor": -500.00},
        {"id_cliente": 5, "nome_cliente": "Elisa", "data_transacao": "2026-05-10", "descricao": "Uber Trip Longa", "valor": -850.00},
        {"id_cliente": 5, "nome_cliente": "Elisa", "data_transacao": "2026-05-20", "descricao": "Netflix Mensalidade", "valor": -55.90}
    ]
    
    df_sintetico = pd.DataFrame(dados_sinteticos)
    df_sintetico.to_csv(caminho_csv, index=False, encoding='utf-8')
    logging.info(f"[EXTRAÇÃO] Sucesso! Base sintética criada e salva em: {caminho_csv}")
    return df_sintetico


# =====================================================================
# 2. ETAPA DE TRANSFORMAÇÃO (TRANSFORM)
# =====================================================================

def categorizar_descricao(descricao: str) -> str:
    """Mapeia palavras-chave da descrição para categorias pré-definidas."""
    if not isinstance(descricao, str):
        return "Outros"
    
    desc_lower = descricao.lower()
    if "uber" in desc_lower:
        return "Transporte"
    elif "supermercado" in desc_lower or "restaurante" in desc_lower or "padaria" in desc_lower:
        return "Alimentação"
    elif "netflix" in desc_lower or "cinema" in desc_lower or "shopping" in desc_lower:
        return "Entretenimento"
    elif "pix" in desc_lower or "salário" in desc_lower or "salario" in desc_lower or "rendimento" in desc_lower:
        return "Receita"
    else:
        return "Outros"


def gerar_insight_personalizado(nome: str, saldo: float, total_gasto: float, maior_ralo: str, valor_ralo: float) -> str:
    """Gera um conselho financeiro dinâmico e direcionado ao perfil de gastos do cliente."""
    selic_a_a = 10.5  # Taxa Selic anual simulada
    
    if saldo < 0:
        return (
            f"Atenção, {nome}! Seu saldo final fechou no vermelho em -R$ {abs(saldo):.2f}. "
            f"Identificamos que seu maior dreno financeiro foi na categoria '{maior_ralo}' "
            f"(R$ {valor_ralo:.2f}). Recomendamos que você corte gastos supérfluos "
            f"e monte um planejamento rígido de emergência."
        )
        
    elif total_gasto > 0 and (saldo < total_gasto * 0.25):
        return (
            f"Olá, {nome}. Seu saldo atual de R$ {saldo:.2f} está positivo, mas perigosamente próximo "
            f"do seu total de despesas (R$ {total_gasto:.2f}). A categoria '{maior_ralo}' "
            f"representou o maior gasto (R$ {valor_ralo:.2f}). "
            f"Evite novos parcelamentos e tente poupar uma reserva de segurança antes de pensar em investir."
        )
        
    else:
        rendimento_anual = saldo * (selic_a_a / 100.0)
        
        dica_investimento = ""
        if maior_ralo == "Entretenimento":
            dica_investimento = "Que tal reduzir um pouco o consumo em lazer e colocar essa sobra na Renda Fixa?"
        elif maior_ralo == "Transporte":
            dica_investimento = "Como o custo de transporte foi relevante, analise opções de otimização de rotas."
        else:
            dica_investimento = "Sua saúde financeira está excelente, continue assim!"
            
        return (
            f"Parabéns, {nome}! Suas finanças estão saudáveis com saldo de R$ {saldo:.2f}. "
            f"Seus gastos totais foram R$ {total_gasto:.2f}, concentrados principalmente em '{maior_ralo}' "
            f"(R$ {valor_ralo:.2f}). Recomendamos aplicar suas economias. Com a Selic a {selic_a_a}% a.a., "
            f"esse saldo renderia aproximadamente R$ {rendimento_anual:.2f} em 12 meses. {dica_investimento}"
        )


def transformar_dados(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """
    Executa a limpeza, enriquecimento, agregação analítica e geração de insights.
    
    Retorna:
        - pd.DataFrame enriquecido (todas as transações com categoria).
        - dict contendo insights agregados por cliente mapeados pelo ID do cliente.
    """
    logging.info("[TRANSFORMAÇÃO] Iniciando etapa de Transformação e enriquecimento...")
    
    # 1. Limpeza e Categorização Automática
    df_enriquecido = df.copy()
    df_enriquecido['categoria'] = df_enriquecido['descricao'].apply(categorizar_descricao)
    
    # 2. Agregação Analítica (Cálculos de Saldo, Gastos e Maior Ralo)
    insights_clientes = {}
    
    # Agrupa por cliente para calcular saldo final
    saldos = df_enriquecido.groupby(['id_cliente', 'nome_cliente'])['valor'].sum().reset_index()
    
    # Filtra despesas (valores negativos)
    df_despesas = df_enriquecido[df_enriquecido['valor'] < 0].copy()
    df_despesas['valor_abs'] = df_despesas['valor'].abs()
    
    # Calcula total gasto por cliente
    gastos_totais = df_despesas.groupby('id_cliente')['valor_abs'].sum().reset_index()
    
    # Agrupa gastos por categoria por cliente para achar o maior ralo financeiro
    gastos_por_categoria = df_despesas.groupby(['id_cliente', 'categoria'])['valor_abs'].sum().reset_index()
    
    # Identifica para cada cliente a categoria com maior despesa acumulada
    if not gastos_por_categoria.empty:
        idx_max = gastos_por_categoria.groupby('id_cliente')['valor_abs'].idxmax()
        maior_ralo = gastos_por_categoria.loc[idx_max]
    else:
        maior_ralo = pd.DataFrame(columns=['id_cliente', 'categoria', 'valor_abs'])

    # Combina tudo para gerar os insights personalizados
    for _, row in saldos.iterrows():
        id_cli = int(row['id_cliente'])
        nome_cli = row['nome_cliente']
        saldo = float(row['valor'])
        
        # Busca total gasto (se houver)
        total_g = gastos_totais[gastos_totais['id_cliente'] == id_cli]
        total_gasto = float(total_g['valor_abs'].values[0]) if not total_g.empty else 0.0
        
        # Busca maior ralo financeiro (se houver)
        ralo_cli = maior_ralo[maior_ralo['id_cliente'] == id_cli]
        if not ralo_cli.empty:
            cat_ralo = ralo_cli['categoria'].values[0]
            val_ralo = float(ralo_cli['valor_abs'].values[0])
        else:
            cat_ralo = "Nenhum"
            val_ralo = 0.0
            
        # Gera o conselho personalizado
        insight = gerar_insight_personalizado(nome_cli, saldo, total_gasto, cat_ralo, val_ralo)
        
        insights_clientes[str(id_cli)] = {
            "nome_cliente": nome_cli,
            "saldo_final": round(saldo, 2),
            "total_despesas": round(total_gasto, 2),
            "maior_ralo_financeiro": cat_ralo,
            "insight": insight
        }
        
    logging.info("[TRANSFORMAÇÃO] Transformação e análise de insights concluídas com sucesso.")
    return df_enriquecido, insights_clientes


# =====================================================================
# 3. ETAPA DE CARREGAMENTO (LOAD)
# =====================================================================

def carregar_dados(df_enriquecido: pd.DataFrame, insights: dict,
                   pasta_saida: str = "output") -> None:
    """
    Grava os dados transformados nos destinos locais estruturados.
    """
    logging.info(f"[CARREGAMENTO] Iniciando carregamento de arquivos na pasta '{pasta_saida}'...")
    
    # Garante que a pasta de saída existe
    try:
        os.makedirs(pasta_saida, exist_ok=True)
    except Exception as e:
        logging.error(f"[CARREGAMENTO] Erro ao criar diretório '{pasta_saida}': {e}")
        sys.exit(1)
        
    caminho_csv_saida = os.path.join(pasta_saida, "relatorio_transacoes_enriquecidas.csv")
    caminho_json_saida = os.path.join(pasta_saida, "insights_orientador_financeiro.json")
    
    # 1. Salva arquivo CSV enriquecido
    try:
        df_enriquecido.to_csv(caminho_csv_saida, index=False, encoding='utf-8')
        logging.info(f"[CARREGAMENTO] Salvo CSV enriquecido com sucesso em: {caminho_csv_saida}")
    except Exception as e:
        logging.error(f"[CARREGAMENTO] Falha ao salvar CSV em {caminho_csv_saida}: {e}")
        
    # 2. Salva arquivo JSON de insights
    try:
        with open(caminho_json_saida, mode='w', encoding='utf-8') as f:
            json.dump(insights, f, ensure_ascii=False, indent=2)
        logging.info(f"[CARREGAMENTO] Salvo JSON de insights com sucesso em: {caminho_json_saida}")
    except Exception as e:
        logging.error(f"[CARREGAMENTO] Falha ao salvar JSON em {caminho_json_saida}: {e}")


# =====================================================================
# METODO ORQUESTRADOR PRINCIPAL
# =====================================================================

def executar_pipeline():
    """
    Controla o fluxo completo do pipeline ETL.
    """
    logging.info("==================================================================")
    logging.info("INICIANDO PIPELINE ETL: ORIENTADOR FINANCEIRO PERSONALIZADO")
    logging.info("==================================================================")
    
    try:
        # 1. Extração
        df_bruto = extrair_dados()
        
        # 2. Transformação
        df_enriquecido, insights = transformar_dados(df_bruto)
        
        # 3. Carregamento
        carregar_dados(df_enriquecido, insights)
        
        logging.info("==================================================================")
        logging.info("PIPELINE ETL EXECUTADO COM SUCESSO COMPLETO!")
        logging.info("==================================================================")
        
    except Exception as e:
        logging.critical(f"Erro fatal não tratado no pipeline ETL: {e}")
        sys.exit(1)


if __name__ == "__main__":
    executar_pipeline()
