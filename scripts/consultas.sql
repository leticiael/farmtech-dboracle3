-- ============================================================================
-- consultas.sql
-- FarmTech Solutions - Fase 3 (Banco de Dados Oracle)
-- Autor: Leticia Eltermann
--
-- Estrutura da tabela SENSORES_ARAUCARIA + 10 consultas analiticas sobre as
-- leituras dos sensores da Fase 2 (ESP32 + DHT22 + LDR + rele) em viveiro
-- de mudas de Araucaria angustifolia.
--
-- Entrada : dados/dados_sensores_fase2.csv (100 leituras entre 2026-04-01
--           08:00:00 e 2026-04-03 09:13:00).
-- Import  : passo a passo detalhado em README.md, secao "Importacao no
--           Oracle SQL Developer". Mascara da coluna DATA_LEITURA:
--           YYYY-MM-DD HH24:MI:SS.
-- ============================================================================


-- ----------------------------------------------------------------------------
-- 0 - Estrutura da tabela
-- ----------------------------------------------------------------------------
-- Cria a tabela que ira receber os dados do CSV. Execute apenas uma vez
-- antes do primeiro import. As constraints garantem a integridade dos
-- dominios definidos pelo firmware (N/P/K/IRRIGOU sao booleanos 0/1 e
-- PH eh um inteiro entre 0 e 14, conforme retorno do map() no sketch).

CREATE TABLE SENSORES_ARAUCARIA (
    DATA_LEITURA  DATE        NOT NULL,
    N             NUMBER(1)   NOT NULL,
    P             NUMBER(1)   NOT NULL,
    K             NUMBER(1)   NOT NULL,
    PH            NUMBER(2)   NOT NULL,
    UMIDADE       NUMBER(4,1) NOT NULL,
    TEMPERATURA   NUMBER(4,1) NOT NULL,
    IRRIGOU       NUMBER(1)   NOT NULL,
    CONSTRAINT chk_n        CHECK (N       IN (0, 1)),
    CONSTRAINT chk_p        CHECK (P       IN (0, 1)),
    CONSTRAINT chk_k        CHECK (K       IN (0, 1)),
    CONSTRAINT chk_irrigou  CHECK (IRRIGOU IN (0, 1)),
    CONSTRAINT chk_ph       CHECK (PH BETWEEN 0 AND 14)
);


-- ============================================================================
-- CONSULTAS OBRIGATORIAS
-- ============================================================================

-- ----------------------------------------------------------------------------
-- Consulta 1 - Listagem completa dos dados carregados
-- ----------------------------------------------------------------------------
-- Mostra todas as 100 leituras do CSV ordenadas cronologicamente.
-- Serve para conferir visualmente se o import ocorreu corretamente e
-- atende ao requisito "SELECT *" da rubrica de avaliacao.

SELECT *
FROM SENSORES_ARAUCARIA
ORDER BY DATA_LEITURA;


-- ----------------------------------------------------------------------------
-- Consulta 2 - Medias gerais de umidade e temperatura
-- ----------------------------------------------------------------------------
-- Visao agregada da serie no periodo coletado. Caracteriza o microclima
-- do viveiro (outono em Curitiba/PR) com tres metricas centrais.

SELECT
    COUNT(*)                    AS total_leituras,
    ROUND(AVG(UMIDADE), 2)      AS umidade_media_pct,
    ROUND(AVG(TEMPERATURA), 2)  AS temperatura_media_c
FROM SENSORES_ARAUCARIA;


-- ----------------------------------------------------------------------------
-- Consulta 3 - Quantas leituras a bomba ficou ligada vs desligada
-- ----------------------------------------------------------------------------
-- Conta quantas vezes o rele acionou (IRRIGOU = 1) versus quantas o sistema
-- decidiu nao irrigar (IRRIGOU = 0), exibindo tambem a porcentagem em
-- relacao ao total. Indica o regime hidrico do periodo monitorado.

SELECT
    IRRIGOU,
    COUNT(*) AS total_leituras,
    ROUND(
        COUNT(*) * 100 / (SELECT COUNT(*) FROM SENSORES_ARAUCARIA),
        1
    ) AS pct_do_total
FROM SENSORES_ARAUCARIA
GROUP BY IRRIGOU
ORDER BY IRRIGOU;


-- ----------------------------------------------------------------------------
-- Consulta 4 - Leituras com pH fora da faixa ideal
-- ----------------------------------------------------------------------------
-- Araucaria angustifolia exige solo levemente acido (pH 5-7). Fora dessa
-- faixa, o firmware bloqueia a irrigacao por seguranca. Esta consulta
-- usa NOT BETWEEN para listar todos os momentos em que o sensor de pH
-- ficou fora do intervalo aceitavel.

SELECT DATA_LEITURA, PH, UMIDADE, IRRIGOU
FROM SENSORES_ARAUCARIA
WHERE PH NOT BETWEEN 5 AND 7
ORDER BY DATA_LEITURA;


-- ----------------------------------------------------------------------------
-- Consulta 5 - Leituras com solo encharcado (umidade > 75%)
-- ----------------------------------------------------------------------------
-- Alerta agronomico: solo encharcado representa risco de podridao
-- radicular. Aqui se listam todos os momentos em que a umidade ultrapassou
-- o limite UMID_ENCHARCADO definido no sketch.

SELECT DATA_LEITURA, UMIDADE, TEMPERATURA, IRRIGOU
FROM SENSORES_ARAUCARIA
WHERE UMIDADE > 75
ORDER BY UMIDADE DESC;


-- ----------------------------------------------------------------------------
-- Consulta 6 - Leituras com fosforo ausente (P = 0)
-- ----------------------------------------------------------------------------
-- Alerta critico: o fosforo eh essencial para o enraizamento da Araucaria.
-- Sem P o firmware nunca aciona a bomba, mesmo que as demais condicoes
-- (umidade, pH, N, K) estejam favoraveis.

SELECT DATA_LEITURA, N, P, K, UMIDADE, PH, IRRIGOU
FROM SENSORES_ARAUCARIA
WHERE P = 0
ORDER BY DATA_LEITURA;


-- ----------------------------------------------------------------------------
-- Consulta 7 - Medias agrupadas por estado da bomba
-- ----------------------------------------------------------------------------
-- Compara as condicoes ambientais medias entre as leituras em que houve
-- irrigacao (IRRIGOU = 1) e aquelas em que nao houve (IRRIGOU = 0).
-- Espera-se umidade media significativamente menor quando IRRIGOU = 1,
-- coerente com o limiar UMID_SECA = 60 do firmware.

SELECT
    IRRIGOU,
    COUNT(*)                    AS total_leituras,
    ROUND(AVG(UMIDADE), 2)      AS umidade_media_pct,
    ROUND(AVG(TEMPERATURA), 2)  AS temperatura_media_c,
    MIN(UMIDADE)                AS umidade_min,
    MAX(UMIDADE)                AS umidade_max
FROM SENSORES_ARAUCARIA
GROUP BY IRRIGOU
ORDER BY IRRIGOU;


-- ============================================================================
-- CONSULTAS AVANCADAS
-- ============================================================================

-- ----------------------------------------------------------------------------
-- Consulta 8 - Classificacao agronomica de cada leitura (CASE WHEN)
-- ----------------------------------------------------------------------------
-- Reproduz no banco a tipologia de alertas que o firmware da Fase 2 emitia
-- no Serial Monitor. Cada leitura recebe um rotulo conforme a primeira
-- regra que se aplica (prioridade: pH, encharcamento, fosforo, secagem).
-- Util para um relatorio textual da serie sem precisar exportar pra R.

SELECT
    DATA_LEITURA,
    UMIDADE,
    PH,
    P,
    CASE
        WHEN PH < 5 OR PH > 7   THEN 'pH fora da faixa'
        WHEN UMIDADE > 75       THEN 'Solo encharcado'
        WHEN P = 0              THEN 'Fosforo ausente'
        WHEN UMIDADE < 60       THEN 'Solo seco - irrigar'
        ELSE                         'Umidade adequada'
    END AS condicao_diagnostica,
    IRRIGOU
FROM SENSORES_ARAUCARIA
ORDER BY DATA_LEITURA;


-- ----------------------------------------------------------------------------
-- Consulta 9 - Leituras com umidade abaixo da media global (subconsulta)
-- ----------------------------------------------------------------------------
-- Usa subconsulta escalar para comparar cada leitura com a media de
-- umidade de toda a serie. Localiza os periodos mais secos, candidatos
-- naturais a recebimento de irrigacao no historico.

SELECT
    DATA_LEITURA,
    UMIDADE,
    TEMPERATURA,
    IRRIGOU
FROM SENSORES_ARAUCARIA
WHERE UMIDADE < (SELECT AVG(UMIDADE) FROM SENSORES_ARAUCARIA)
ORDER BY UMIDADE;


-- ----------------------------------------------------------------------------
-- Consulta 10 - Horas do dia com maior atividade do rele (HAVING)
-- ----------------------------------------------------------------------------
-- Agrupa as irrigacoes pela hora do dia e retorna apenas as horas com 2
-- ou mais acionamentos. Sugere janelas operacionais para programar a
-- irrigacao automatica do viveiro (ex.: dimensionar reservatorio).

SELECT
    TO_CHAR(DATA_LEITURA, 'HH24') AS hora_do_dia,
    COUNT(*)                       AS irrigacoes_no_periodo
FROM SENSORES_ARAUCARIA
WHERE IRRIGOU = 1
GROUP BY TO_CHAR(DATA_LEITURA, 'HH24')
HAVING COUNT(*) >= 2
ORDER BY irrigacoes_no_periodo DESC, hora_do_dia;
