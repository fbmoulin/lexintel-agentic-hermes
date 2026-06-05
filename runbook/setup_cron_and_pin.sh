#!/bin/bash
# ============================================================
# Lex Intelligentia — Setup de Cron Jobs e Pinagem de Skills
# ============================================================
# Este script configura a automação de produção de conteúdo
# e protege as skills core contra o Curator do Hermes.
#
# Executar UMA VEZ após a instalação completa do projeto.
# ============================================================

echo "=== [1/3] Pinando Skills Core ==="
echo "Protegendo skills contra arquivamento automático pelo Curator..."

hermes curator pin firac-engine
hermes curator pin voz-marca-lex
hermes curator pin assets-marca
hermes curator pin atomizador
hermes curator pin pillar-semana
hermes curator pin apresentador-video
hermes curator pin art-director-ai
hermes curator pin gerador-imagens
hermes curator pin narrador-elevenlabs
hermes curator pin guardiao-politica
hermes curator pin radar-pauta
hermes curator pin analista-desempenho

echo ""
echo "=== [2/3] Configurando Cron Jobs de Produção ==="

# --- Radar de Pauta: Segunda-feira às 7h ---
hermes cron create "0 7 * * 1" \
  "Use a skill radar-pauta. Busque os 5 temas jurídicos mais relevantes da semana sobre IA, tecnologia e Judiciário. Salve o resultado em /home/ubuntu/lex-intelligentia/memory/radar_semanal.md" \
  --skill radar-pauta \
  --workdir /home/ubuntu/lex-intelligentia \
  --name "Radar Semanal" \
  --deliver local

# --- Produção de Conteúdo: Terça-feira às 8h ---
hermes cron create "0 8 * * 2" \
  "Use as skills firac-engine e pillar-semana. Leia o arquivo /home/ubuntu/lex-intelligentia/memory/radar_semanal.md, escolha o tema mais relevante e gere: 1) Uma análise FIRAC completa. 2) Um artigo Pillar com átomos marcados. Salve em /home/ubuntu/lex-intelligentia/memory/pillar_semana.md" \
  --skill firac-engine \
  --skill pillar-semana \
  --workdir /home/ubuntu/lex-intelligentia \
  --name "Pillar Semanal" \
  --deliver local

# --- Atomização: Quarta-feira às 8h ---
hermes cron create "0 8 * * 3" \
  "Use a skill atomizador. Leia o arquivo /home/ubuntu/lex-intelligentia/memory/pillar_semana.md e gere os micro-conteúdos (carrossel, reel, tip). Salve em /home/ubuntu/lex-intelligentia/memory/atomizado_semana.md" \
  --skill atomizador \
  --workdir /home/ubuntu/lex-intelligentia \
  --name "Atomização Semanal" \
  --deliver local

# --- Revisão de Compliance: Quarta-feira às 10h ---
hermes cron create "0 10 * * 3" \
  "Use a skill guardiao-politica. Leia o arquivo /home/ubuntu/lex-intelligentia/memory/atomizado_semana.md e valide se todo o conteúdo está em conformidade com a Resolução CNJ 615/2025 e com o tom de voz da marca. Se houver problemas, liste-os. Se estiver tudo OK, responda com EXCELLENT." \
  --skill guardiao-politica \
  --workdir /home/ubuntu/lex-intelligentia \
  --name "Revisão Compliance" \
  --deliver local

# --- Análise de Desempenho: Sexta-feira às 17h ---
hermes cron create "0 17 * * 5" \
  "Use a skill analista-desempenho. Analise as métricas da semana (se disponíveis em /home/ubuntu/lex-intelligentia/memory/metricas.json) e gere recomendações de otimização para as skills de produção. Salve em /home/ubuntu/lex-intelligentia/memory/feedback_semana.md" \
  --skill analista-desempenho \
  --workdir /home/ubuntu/lex-intelligentia \
  --name "Feedback Loop Semanal" \
  --deliver local

echo ""
echo "=== [3/3] Verificação Final ==="
hermes cron list
hermes curator status

echo ""
echo "✅ Setup completo! O pipeline de produção automatizada está ativo."
echo ""
echo "Calendário Semanal:"
echo "  Segunda 07h → Radar de Pauta"
echo "  Terça   08h → Pillar + FIRAC"
echo "  Quarta  08h → Atomização"
echo "  Quarta  10h → Revisão Compliance"
echo "  Sexta   17h → Feedback Loop"
