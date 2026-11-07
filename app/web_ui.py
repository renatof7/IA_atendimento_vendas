"""
Interface HTML do Console Web Interativo da Lili IA:
- Design Moderno Glassmorphism com amplo espaçamento (respiro visual) e botões arredondados (pill buttons)
- Visual Limpo Corporativo (Sem emojis ou ícones no texto)
- Gestão de Leads, Fila de Atendimentos Multi-Lead e Relatórios Estratégicos (estilo Lais.ai / DataLais)
- Aba 1: Gestão de Atendimentos, Relatórios Estratégicos, Ficha CRM Agendor, MCMV 2026 e Follow-up
- Aba 2: Catálogo Visual e Cadastro Amigável de Empreendimentos
- Aba 3: Dados Institucionais da Construtora e Diretrizes
- Aba 4: Conectar Celular (WhatsApp via QR Code da Evolution API)
"""

WEB_CONSOLE_HTML = r"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Lili IA — Gestão de Leads, Relatórios e Pré-Vendas Imobiliárias</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg-dark: #060a12;
      --glass-panel: rgba(16, 23, 38, 0.62);
      --glass-panel-elevated: rgba(24, 34, 54, 0.72);
      --glass-border: rgba(255, 255, 255, 0.08);
      --glass-border-hover: rgba(255, 255, 255, 0.15);
      --glass-border-focus: rgba(56, 189, 248, 0.45);
      --accent-cyan: #38bdf8;
      --accent-emerald: #10b981;
      --accent-emerald-light: #34d399;
      --accent-rose: #f43f5e;
      --accent-amber: #f59e0b;
      --text-main: #f8fafc;
      --text-muted: #94a3b8;
      --text-dim: #64748b;
      --shadow-glass: 0 20px 50px -12px rgba(0, 0, 0, 0.55), inset 0 1px 0 rgba(255, 255, 255, 0.08);
    }

    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
      font-family: 'Plus Jakarta Sans', system-ui, -apple-system, sans-serif;
    }

    body {
      background: radial-gradient(circle at 8% 12%, rgba(56, 189, 248, 0.09) 0%, transparent 45%),
                  radial-gradient(circle at 92% 18%, rgba(16, 185, 129, 0.07) 0%, transparent 45%),
                  radial-gradient(circle at 50% 92%, rgba(99, 102, 241, 0.06) 0%, transparent 50%),
                  var(--bg-dark);
      color: var(--text-main);
      height: 100vh;
      display: flex;
      flex-direction: column;
      overflow: hidden;
      -webkit-font-smoothing: antialiased;
    }

    /* HEADER ESPAÇOSO COM BOTÕES ARREDONDADOS */
    header {
      padding: 18px 36px;
      background: rgba(10, 15, 28, 0.78);
      backdrop-filter: blur(24px);
      -webkit-backdrop-filter: blur(24px);
      border-bottom: 1px solid var(--glass-border);
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 24px;
      z-index: 50;
      box-shadow: 0 6px 28px rgba(0, 0, 0, 0.3);
    }

    .brand-wrap {
      display: flex;
      align-items: center;
      gap: 16px;
    }

    .brand-logo {
      width: 44px;
      height: 44px;
      border-radius: 999px;
      background: linear-gradient(135deg, rgba(56, 189, 248, 0.22), rgba(16, 185, 129, 0.22));
      border: 1px solid rgba(255, 255, 255, 0.16);
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 0.92rem;
      font-weight: 800;
      color: #ffffff;
      letter-spacing: -0.03em;
      box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.22);
    }

    .brand-text h1 {
      font-size: 1.12rem;
      font-weight: 700;
      letter-spacing: -0.02em;
      background: linear-gradient(90deg, #ffffff 40%, #cbd5e1 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      line-height: 1.25;
    }

    .brand-text p {
      font-size: 0.78rem;
      color: var(--text-muted);
      font-weight: 500;
      margin-top: 2px;
    }

    /* TABS EM FORMATO PILL ARREDONDADO COM ESPAÇAMENTO */
    .tabs-nav {
      display: flex;
      gap: 10px;
      background: rgba(15, 23, 42, 0.55);
      padding: 6px;
      border-radius: 999px;
      border: 1px solid var(--glass-border);
      backdrop-filter: blur(14px);
    }

    .tab-btn {
      padding: 10px 22px;
      border-radius: 999px;
      border: 1px solid transparent;
      background: transparent;
      color: var(--text-muted);
      cursor: pointer;
      font-weight: 600;
      font-size: 0.84rem;
      transition: all 0.22s cubic-bezier(0.4, 0, 0.2, 1);
      white-space: nowrap;
    }

    .tab-btn:hover {
      color: var(--text-main);
      background: rgba(255, 255, 255, 0.05);
    }

    .tab-btn.active {
      background: rgba(56, 189, 248, 0.16);
      color: #7dd3fc;
      border-color: rgba(56, 189, 248, 0.4);
      box-shadow: 0 4px 16px rgba(56, 189, 248, 0.2), inset 0 1px 0 rgba(255, 255, 255, 0.15);
    }

    .header-actions {
      display: flex;
      align-items: center;
      gap: 12px;
    }

    /* BOTÕES GERAIS — CANTOS 100% ARREDONDADOS (PILL) */
    button {
      padding: 10px 22px;
      border-radius: 999px;
      border: 1px solid transparent;
      cursor: pointer;
      font-weight: 600;
      font-size: 0.83rem;
      transition: all 0.22s cubic-bezier(0.4, 0, 0.2, 1);
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      user-select: none;
      letter-spacing: 0.01em;
    }

    button.primary {
      background: linear-gradient(135deg, #10b981 0%, #059669 100%);
      color: #ffffff;
      box-shadow: 0 6px 18px rgba(16, 185, 129, 0.28), inset 0 1px 0 rgba(255, 255, 255, 0.22);
    }

    button.primary:hover {
      transform: translateY(-1px);
      box-shadow: 0 8px 24px rgba(16, 185, 129, 0.38), inset 0 1px 0 rgba(255, 255, 255, 0.3);
      filter: brightness(1.06);
    }

    button.sec {
      background: rgba(30, 41, 59, 0.58);
      color: #e2e8f0;
      border: 1px solid var(--glass-border);
      backdrop-filter: blur(10px);
    }

    button.sec:hover {
      background: rgba(51, 65, 85, 0.78);
      border-color: var(--glass-border-hover);
      color: #ffffff;
      transform: translateY(-1px);
    }

    button.sec.active-filter {
      background: rgba(56, 189, 248, 0.18);
      color: #7dd3fc;
      border-color: rgba(56, 189, 248, 0.45);
    }

    button.warn {
      background: rgba(245, 158, 11, 0.14);
      color: #fbbf24;
      border: 1px solid rgba(245, 158, 11, 0.35);
    }

    button.warn:hover {
      background: rgba(245, 158, 11, 0.24);
      color: #fef3c7;
      transform: translateY(-1px);
    }

    button.danger {
      background: rgba(244, 63, 94, 0.14);
      color: #fda4af;
      border: 1px solid rgba(244, 63, 94, 0.3);
    }

    button.danger:hover {
      background: rgba(244, 63, 94, 0.26);
      color: #ffe4e6;
      transform: translateY(-1px);
    }

    /* ESTRUTURA PRINCIPAL (2 COLUNAS COM AMPLO ESPAÇO) */
    main {
      flex: 1;
      display: grid;
      grid-template-columns: 460px 1fr;
      overflow: hidden;
    }

    /* COLUNA ESQUERDA: CONVERSA DO ATENDIMENTO SELECIONADO */
    .chat-col {
      display: flex;
      flex-direction: column;
      background: rgba(10, 15, 28, 0.68);
      backdrop-filter: blur(24px);
      -webkit-backdrop-filter: blur(24px);
      border-right: 1px solid var(--glass-border);
      position: relative;
    }

    .chat-header {
      padding: 20px 24px;
      background: rgba(16, 23, 40, 0.82);
      border-bottom: 1px solid var(--glass-border);
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 16px;
    }

    .chat-user-badge {
      display: flex;
      align-items: center;
      gap: 14px;
    }

    .avatar-lili {
      width: 46px;
      height: 46px;
      border-radius: 999px;
      background: linear-gradient(135deg, #0ea5e9, #10b981);
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 0.95rem;
      font-weight: 800;
      color: #ffffff;
      box-shadow: 0 6px 16px rgba(14, 165, 233, 0.25), inset 0 1px 0 rgba(255, 255, 255, 0.3);
      position: relative;
      flex-shrink: 0;
    }

    .avatar-status-dot {
      position: absolute;
      bottom: 1px;
      right: 1px;
      width: 12px;
      height: 12px;
      border-radius: 50%;
      background: var(--accent-emerald);
      border: 2px solid #0b1120;
      box-shadow: 0 0 8px var(--accent-emerald);
    }

    .chat-meta strong {
      font-size: 0.96rem;
      font-weight: 700;
      color: #ffffff;
      display: block;
    }

    .chat-status-sub {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 0.77rem;
      color: var(--accent-emerald-light);
      font-weight: 600;
      margin-top: 3px;
    }

    .phone-selector {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      background: rgba(15, 23, 42, 0.75);
      padding: 5px 12px;
      border-radius: 999px;
      border: 1px solid var(--glass-border);
      margin-top: 6px;
    }

    .phone-selector input {
      background: transparent;
      border: none;
      color: var(--accent-cyan);
      font-size: 0.77rem;
      font-weight: 600;
      font-family: 'JetBrains Mono', monospace;
      width: 125px;
      outline: none;
    }

    .chat-messages {
      flex: 1;
      padding: 28px 24px;
      overflow-y: auto;
      display: flex;
      flex-direction: column;
      gap: 16px;
      background: radial-gradient(circle at 50% 50%, rgba(15, 23, 42, 0.45) 0%, rgba(6, 10, 18, 0.92) 100%);
    }

    .msg {
      max-width: 84%;
      padding: 14px 20px;
      border-radius: 22px;
      font-size: 0.9rem;
      line-height: 1.55;
      white-space: pre-wrap;
      word-break: break-word;
      position: relative;
      animation: fadeIn 0.25s ease-out;
    }

    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(6px); }
      to { opacity: 1; transform: translateY(0); }
    }

    .msg-lili {
      align-self: flex-start;
      background: rgba(26, 36, 56, 0.78);
      backdrop-filter: blur(12px);
      color: #f1f5f9;
      border: 1px solid rgba(255, 255, 255, 0.08);
      border-top-left-radius: 6px;
      box-shadow: 0 6px 20px rgba(0, 0, 0, 0.25);
    }

    .msg-user {
      align-self: flex-end;
      background: linear-gradient(135deg, #059669 0%, #047857 100%);
      color: #ffffff;
      border-top-right-radius: 6px;
      box-shadow: 0 6px 20px rgba(5, 150, 105, 0.28), inset 0 1px 0 rgba(255, 255, 255, 0.2);
    }

    .msg-sys {
      align-self: center;
      background: rgba(56, 189, 248, 0.12);
      border: 1px solid rgba(56, 189, 248, 0.25);
      color: #bae6fd;
      font-size: 0.78rem;
      font-weight: 500;
      padding: 8px 18px;
      border-radius: 999px;
      text-align: center;
      backdrop-filter: blur(8px);
    }

    .chat-input {
      padding: 18px 24px;
      background: rgba(16, 23, 40, 0.92);
      border-top: 1px solid var(--glass-border);
      display: flex;
      gap: 12px;
      backdrop-filter: blur(16px);
    }

    .chat-input input {
      flex: 1;
      padding: 14px 22px;
      border-radius: 999px;
      border: 1px solid var(--glass-border);
      background: rgba(10, 15, 28, 0.85);
      color: #ffffff;
      font-size: 0.89rem;
      outline: none;
      transition: all 0.2s;
    }

    .chat-input input:focus {
      border-color: var(--glass-border-focus);
      background: rgba(15, 23, 42, 0.95);
      box-shadow: 0 0 18px rgba(56, 189, 248, 0.15);
    }

    /* COLUNA DA DIREITA — AMPLO ESPAÇAMENTO ENTRE ELEMENTOS */
    .right-col {
      padding: 38px 46px;
      overflow-y: auto;
      display: flex;
      flex-direction: column;
      gap: 32px;
    }

    /* CARDS AMPLOS EM ESTILO GLASSMORPHISM */
    .card {
      background: var(--glass-panel);
      backdrop-filter: blur(22px);
      -webkit-backdrop-filter: blur(22px);
      border: 1px solid var(--glass-border);
      border-radius: 26px;
      padding: 30px 34px;
      box-shadow: var(--shadow-glass);
      transition: border-color 0.25s, transform 0.25s;
    }

    .card:hover {
      border-color: rgba(255, 255, 255, 0.13);
    }

    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      gap: 16px;
      margin-bottom: 24px;
      flex-wrap: wrap;
    }

    .card h2 {
      font-size: 1.06rem;
      font-weight: 700;
      color: #ffffff;
      letter-spacing: -0.015em;
    }

    .card-subtitle {
      font-size: 0.82rem;
      color: var(--text-muted);
      margin-top: 4px;
      line-height: 1.4;
    }

    /* KPI CARDS ESTRATÉGICOS (ESTILO LAIS.AI) */
    .kpi-grid {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 20px;
    }

    @media (max-width: 1200px) {
      .kpi-grid { grid-template-columns: repeat(2, 1fr); }
    }

    .kpi-card {
      background: rgba(15, 23, 42, 0.65);
      border: 1px solid var(--glass-border);
      border-radius: 22px;
      padding: 22px 24px;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      gap: 10px;
      backdrop-filter: blur(16px);
      transition: all 0.22s;
    }

    .kpi-card:hover {
      border-color: var(--glass-border-hover);
      transform: translateY(-2px);
    }

    .kpi-label {
      font-size: 0.75rem;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: var(--text-muted);
    }

    .kpi-value {
      font-size: 1.85rem;
      font-weight: 800;
      color: #ffffff;
      letter-spacing: -0.03em;
      line-height: 1.1;
    }

    .kpi-foot {
      font-size: 0.76rem;
      color: var(--accent-emerald-light);
      font-weight: 500;
    }

    /* BARRAS DE PROGRESSO PARA RELATÓRIOS ESTRATÉGICOS */
    .stat-bar-list {
      display: flex;
      flex-direction: column;
      gap: 16px;
    }

    .stat-bar-item {
      display: flex;
      flex-direction: column;
      gap: 7px;
    }

    .stat-bar-top {
      display: flex;
      justify-content: space-between;
      font-size: 0.83rem;
      font-weight: 600;
      color: #e2e8f0;
    }

    .stat-bar-track {
      width: 100%;
      height: 10px;
      background: rgba(10, 15, 28, 0.8);
      border-radius: 999px;
      overflow: hidden;
      border: 1px solid rgba(255, 255, 255, 0.05);
    }

    .stat-bar-fill {
      height: 100%;
      border-radius: 999px;
      background: linear-gradient(90deg, var(--accent-cyan), var(--accent-emerald));
      transition: width 0.4s ease;
    }

    /* LISTA / FILA DE GESTÃO DE ATENDIMENTOS (MULTI-LEAD) */
    .leads-list {
      display: flex;
      flex-direction: column;
      gap: 14px;
      margin-top: 20px;
    }

    .lead-row-card {
      background: rgba(12, 18, 32, 0.65);
      border: 1px solid var(--glass-border);
      border-radius: 20px;
      padding: 18px 24px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 20px;
      flex-wrap: wrap;
      transition: all 0.22s;
    }

    .lead-row-card:hover {
      border-color: rgba(56, 189, 248, 0.35);
      background: rgba(18, 27, 46, 0.78);
    }

    .lead-row-card.selected-lead {
      border-color: var(--accent-cyan);
      background: rgba(56, 189, 248, 0.08);
      box-shadow: 0 0 24px rgba(56, 189, 248, 0.12);
    }

    .lead-row-info {
      display: flex;
      flex-direction: column;
      gap: 6px;
      flex: 1;
      min-width: 240px;
    }

    .lead-row-title {
      display: flex;
      align-items: center;
      gap: 12px;
      flex-wrap: wrap;
    }

    .lead-row-title strong {
      font-size: 0.98rem;
      color: #ffffff;
      font-weight: 700;
    }

    .lead-row-meta {
      font-size: 0.81rem;
      color: var(--text-muted);
      display: flex;
      gap: 14px;
      flex-wrap: wrap;
    }

    /* BADGES ARREDONDADOS */
    .badge {
      padding: 6px 14px;
      border-radius: 999px;
      font-size: 0.74rem;
      font-weight: 700;
      letter-spacing: 0.03em;
      display: inline-flex;
      align-items: center;
      gap: 6px;
    }

    .badge-hot {
      background: rgba(244, 63, 94, 0.16);
      color: #fda4af;
      border: 1px solid rgba(244, 63, 94, 0.4);
    }

    .badge-warm {
      background: rgba(245, 158, 11, 0.16);
      color: #fcd34d;
      border: 1px solid rgba(245, 158, 11, 0.4);
    }

    .badge-cold {
      background: rgba(56, 189, 248, 0.14);
      color: #93c5fd;
      border: 1px solid rgba(56, 189, 248, 0.35);
    }

    .badge-ok {
      background: rgba(16, 185, 129, 0.16);
      color: #6ee7b7;
      border: 1px solid rgba(16, 185, 129, 0.4);
    }

    /* GRIDS E CAMPOS DE DADOS COM AMPLO RESPIRO */
    .grid-2 { display: grid; grid-template-columns: repeat(2, 1fr); gap: 18px; }
    .grid-3 { display: grid; grid-template-columns: repeat(3, 1fr); gap: 18px; }
    .grid-4 { display: grid; grid-template-columns: repeat(4, 1fr); gap: 18px; }

    @media (max-width: 1150px) {
      .grid-3 { grid-template-columns: repeat(2, 1fr); }
      .grid-4 { grid-template-columns: repeat(2, 1fr); }
    }

    .field {
      background: rgba(10, 15, 28, 0.58);
      padding: 15px 18px;
      border-radius: 16px;
      border: 1px solid var(--glass-border);
      transition: all 0.2s;
    }

    .field:hover {
      background: rgba(15, 23, 42, 0.72);
      border-color: rgba(255, 255, 255, 0.12);
    }

    .field span {
      display: block;
      font-size: 0.72rem;
      color: var(--text-muted);
      font-weight: 600;
      margin-bottom: 6px;
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }

    .field strong {
      font-size: 0.92rem;
      font-weight: 600;
      color: #f8fafc;
      word-break: break-word;
    }

    .btn-row {
      display: flex;
      flex-wrap: wrap;
      gap: 12px;
    }

    .action-group-title {
      font-size: 0.76rem;
      color: var(--text-muted);
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      margin-bottom: 12px;
      margin-top: 18px;
    }

    pre {
      background: rgba(7, 11, 20, 0.85);
      padding: 18px 22px;
      border-radius: 18px;
      border: 1px solid var(--glass-border);
      font-family: 'JetBrains Mono', Consolas, monospace;
      font-size: 0.83rem;
      color: #a7f3d0;
      white-space: pre-wrap;
      line-height: 1.6;
    }

    /* FORMULÁRIOS ESPAÇADOS */
    .form-group {
      margin-bottom: 16px;
    }

    .form-group label {
      display: block;
      font-size: 0.8rem;
      color: #cbd5e1;
      margin-bottom: 8px;
      font-weight: 600;
    }

    .form-group input, .form-group select, .form-group textarea {
      width: 100%;
      padding: 12px 18px;
      border-radius: 14px;
      border: 1px solid var(--glass-border);
      background: rgba(10, 15, 28, 0.82);
      color: #f8fafc;
      font-size: 0.88rem;
      outline: none;
      transition: all 0.2s;
    }

    .form-group input:focus, .form-group select:focus, .form-group textarea:focus {
      border-color: var(--accent-cyan);
      box-shadow: 0 0 16px rgba(56, 189, 248, 0.18);
      background: rgba(15, 23, 42, 0.95);
    }

    .form-group textarea.code {
      font-family: 'JetBrains Mono', Consolas, monospace;
      font-size: 0.82rem;
      line-height: 1.5;
    }

    .toast {
      display: none;
      padding: 14px 20px;
      border-radius: 999px;
      background: rgba(16, 185, 129, 0.16);
      border: 1px solid var(--accent-emerald);
      color: #a7f3d0;
      font-size: 0.86rem;
      margin-top: 16px;
      font-weight: 600;
      animation: fadeIn 0.3s;
    }

    /* VITRINE DE IMÓVEIS */
    .imoveis-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
      gap: 22px;
    }

    .imovel-card {
      background: rgba(15, 23, 42, 0.65);
      border: 1px solid var(--glass-border);
      border-radius: 22px;
      padding: 24px;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      gap: 16px;
      transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
      backdrop-filter: blur(12px);
    }

    .imovel-card:hover {
      border-color: rgba(56, 189, 248, 0.4);
      transform: translateY(-3px);
      box-shadow: 0 14px 32px rgba(0, 0, 0, 0.4), 0 0 18px rgba(56, 189, 248, 0.1);
    }

    .imovel-card h3 {
      font-size: 1.05rem;
      font-weight: 700;
      color: #ffffff;
      margin: 10px 0 4px;
    }

    .imovel-preco {
      font-size: 1.18rem;
      font-weight: 800;
      color: var(--accent-emerald-light);
      margin: 8px 0;
      letter-spacing: -0.01em;
    }

    .imovel-meta {
      font-size: 0.83rem;
      color: var(--text-muted);
      line-height: 1.6;
    }

    .check-row {
      display: flex;
      gap: 20px;
      align-items: center;
      padding: 12px 0;
      flex-wrap: wrap;
    }

    .check-row label {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 0.86rem;
      color: #e2e8f0;
      cursor: pointer;
      margin: 0;
    }

    .check-row input[type="checkbox"] {
      width: 18px;
      height: 18px;
      accent-color: var(--accent-emerald);
      cursor: pointer;
    }

    .mcmv-helper {
      padding: 16px 20px;
      border-radius: 16px;
      font-size: 0.85rem;
      margin-top: 12px;
      background: rgba(56, 189, 248, 0.1);
      border: 1px solid rgba(56, 189, 248, 0.3);
      color: #bae6fd;
      line-height: 1.5;
      backdrop-filter: blur(8px);
    }

    .qr-card-box {
      background: rgba(10, 15, 28, 0.85);
      border: 1px solid var(--glass-border);
      border-radius: 22px;
      padding: 28px;
      text-align: center;
      min-width: 270px;
      min-height: 270px;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      box-shadow: inset 0 2px 10px rgba(0, 0, 0, 0.45);
    }

    ::-webkit-scrollbar {
      width: 6px;
      height: 6px;
    }
    ::-webkit-scrollbar-track {
      background: transparent;
    }
    ::-webkit-scrollbar-thumb {
      background: rgba(255, 255, 255, 0.12);
      border-radius: 99px;
    }
    ::-webkit-scrollbar-thumb:hover {
      background: rgba(255, 255, 255, 0.22);
    }
  </style>
</head>
<body>
  <!-- HEADER ESPAÇOSO COM BOTÕES ARREDONDADOS -->
  <header>
    <div class="brand-wrap">
      <div class="brand-logo">IA</div>
      <div class="brand-text">
        <h1>Lili IA | Pré-Vendas Imobiliárias</h1>
        <p>Gestão de Atendimentos, Inteligência de Leads e Pré-Vendas MCMV 2026</p>
      </div>
    </div>

    <nav class="tabs-nav">
      <button class="tab-btn active" id="tabBtnCrm" onclick="trocarAba('crm')">
        Gestão de Leads & CRM
      </button>
      <button class="tab-btn" id="tabBtnImoveis" onclick="trocarAba('imoveis')">
        Catálogo de Imóveis
      </button>
      <button class="tab-btn" id="tabBtnKb" onclick="trocarAba('kb')">
        Dados da Construtora
      </button>
      <button class="tab-btn" id="tabBtnWhatsapp" onclick="trocarAba('whatsapp')" style="border-color: rgba(16,185,129,0.35); color:#34d399;">
        Conectar WhatsApp
      </button>
    </nav>

    <div class="header-actions">
      <button class="sec" onclick="alternarVendedor()" id="btnVendedor">
        Vendedor Assumir
      </button>
      <button class="sec" onclick="resetarConversa()" title="Limpa o chat do lead atual e recomeça">
        Reiniciar Chat
      </button>
    </div>
  </header>

  <main>
    <!-- COLUNA ESQUERDA: CONVERSA AO VIVO DO LEAD SELECIONADO -->
    <section class="chat-col">
      <div class="chat-header">
        <div class="chat-user-badge">
          <div class="avatar-lili">
            LI
            <span class="avatar-status-dot"></span>
          </div>
          <div class="chat-meta">
            <strong>Lili | Atendente Virtual</strong>
            <div class="chat-status-sub">
              <span id="statusIA">Online 24/7</span>
            </div>
            <div class="phone-selector" title="Número do cliente em atendimento">
              <span style="font-size:0.72rem; color:var(--text-dim);">Lead Ativo:</span>
              <input type="text" id="telAtualInput" value="5548999990001" onchange="mudarTelefoneTeste(this.value)" />
            </div>
          </div>
        </div>
        <button class="primary" onclick="criarNovoLeadRapido()" style="font-size:0.76rem; padding:8px 16px;">
          Novo Lead
        </button>
      </div>

      <div class="chat-messages" id="chatBox">
        <div class="msg msg-lili">Oi! Tudo bem? Aqui é a Lili, assistente virtual da Construtora Demo.
Que bom receber seu contato! Com quem eu falo e como posso te ajudar hoje?</div>
      </div>

      <form class="chat-input" onsubmit="enviarMensagem(event)">
        <input type="text" id="msgInput" placeholder="Digite uma mensagem como cliente..." autocomplete="off" />
        <button type="submit" class="primary">Enviar</button>
      </form>
    </section>

    <!-- ABA 1: GESTÃO DE LEADS, RELATÓRIOS ESTRATÉGICOS & FICHA CRM -->
    <section class="right-col" id="abaCrm">

      <!-- BLOCO 1: INDICADORES ESTRATÉGICOS (KPIs) -->
      <div class="kpi-grid">
        <div class="kpi-card">
          <span class="kpi-label">Total de Atendimentos</span>
          <div class="kpi-value" id="kpiTotalLeads">1</div>
          <div class="kpi-foot">Recepção imediata 24/7</div>
        </div>
        <div class="kpi-card">
          <span class="kpi-label">Leads Quentes & Mornos</span>
          <div class="kpi-value" id="kpiLeadsQualificados" style="color:var(--accent-cyan);">0</div>
          <div class="kpi-foot" id="kpiTaxaQualificacao">Potencial real de compra</div>
        </div>
        <div class="kpi-card">
          <span class="kpi-label">Visitas & Repasses</span>
          <div class="kpi-value" id="kpiVisitasEncaminhadas" style="color:var(--accent-emerald-light);">0</div>
          <div class="kpi-foot">Entregues ao corretor</div>
        </div>
        <div class="kpi-card">
          <span class="kpi-label">Tempo de Resposta IA</span>
          <div class="kpi-value">0.4s</div>
          <div class="kpi-foot">Atendimento instantâneo</div>
        </div>
      </div>

      <!-- BLOCO 2: RELATÓRIOS ESTRATÉGICOS DE DEMANDA E PERFIL MCMV -->
      <div class="grid-2">
        <div class="card">
          <div class="card-header" style="margin-bottom:18px;">
            <div>
              <h2>Demanda por Cidade</h2>
              <div class="card-subtitle">Volume de interesse nos municípios de atuação da construtora</div>
            </div>
          </div>
          <div class="stat-bar-list" id="relatorioCidadesBox"></div>
        </div>

        <div class="card">
          <div class="card-header" style="margin-bottom:18px;">
            <div>
              <h2>Distribuição por Faixa MCMV 2026</h2>
              <div class="card-subtitle">Perfil de capacidade de compra e enquadramento dos leads</div>
            </div>
          </div>
          <div class="stat-bar-list" id="relatorioFaixasBox"></div>
        </div>
      </div>

      <!-- BLOCO 3: CENTRAL DE GESTÃO DE ATENDIMENTOS (FILA MULTI-LEAD) -->
      <div class="card">
        <div class="card-header">
          <div>
            <h2>Gestão de Atendimentos & Carteira de Leads</h2>
            <div class="card-subtitle">Selecione qualquer cliente abaixo para inspecionar a conversa ao lado e ver a ficha completa</div>
          </div>
          <div class="btn-row">
            <button class="sec" onclick="popularLeadsDemonstracao()">Simular Carteira de Leads</button>
            <button class="primary" onclick="criarNovoLeadRapido()">Novo Atendimento</button>
          </div>
        </div>

        <div class="btn-row" style="margin-bottom: 8px;">
          <button class="sec active-filter" id="fBtn_todos" onclick="filtrarListaLeads('todos')">Todos os Leads</button>
          <button class="sec" id="fBtn_Quente" onclick="filtrarListaLeads('Quente')">Quentes (Prioridade)</button>
          <button class="sec" id="fBtn_Morno" onclick="filtrarListaLeads('Morno')">Mornos</button>
          <button class="sec" id="fBtn_Frio" onclick="filtrarListaLeads('Frio')">Frios / Em Nutrição</button>
          <button class="sec" id="fBtn_transferido" onclick="filtrarListaLeads('transferido')">Repassados ao Corretor</button>
        </div>

        <div class="leads-list" id="listaGestaoLeadsBox"></div>
      </div>

      <!-- BLOCO 4: CLASSIFICAÇÃO & PRÉ-ENQUADRAMENTO DO LEAD SELECIONADO -->
      <div class="card">
        <div class="card-header">
          <div>
            <h2>Classificação & Pré-Enquadramento MCMV 2026 (Lead Ativo)</h2>
            <div class="card-subtitle">Pontuação de prontidão de compra e teto aplicável na cidade</div>
          </div>
          <span id="badgeTemp" class="badge badge-cold">FRIO | 0 pts</span>
        </div>
        <div class="grid-4">
          <div class="field"><span>Faixa MCMV 2026</span><strong id="f_faixa">A definir</strong></div>
          <div class="field"><span>Etapa do Funil</span><strong id="f_etapa">em qualificação</strong></div>
          <div class="field"><span>Vendedor Responsável</span><strong id="f_vendedor">Carlos Eduardo</strong></div>
          <div class="field"><span>SLA / Status Visita</span><strong id="f_sla">em até 48 horas</strong></div>
        </div>
      </div>

      <!-- BLOCO 5: FICHA COMPLETA NO CRM AGENDOR -->
      <div class="card">
        <div class="card-header">
          <div>
            <h2>Ficha do Cliente no CRM Agendor</h2>
            <div class="card-subtitle">Dados capturados e gravados automaticamente pela Lili durante o diálogo</div>
          </div>
        </div>
        <div class="grid-2">
          <div class="field"><span>Nome do Cliente</span><strong id="f_nome">-</strong></div>
          <div class="field"><span>Objetivo / 1º Imóvel</span><strong id="f_obj">-</strong></div>
          <div class="field"><span>Cidade Desejada</span><strong id="f_cidade">-</strong></div>
          <div class="field"><span>Tipologia e Quartos</span><strong id="f_tipo">-</strong></div>
          <div class="field"><span>Renda Familiar Bruta</span><strong id="f_renda">-</strong></div>
          <div class="field"><span>Tipo de Renda & FGTS</span><strong id="f_fgts">-</strong></div>
          <div class="field"><span>Entrada Disponível</span><strong id="f_entrada">-</strong></div>
          <div class="field"><span>Restrição no CPF</span><strong id="f_cpf">-</strong></div>
          <div class="field"><span>Prazo Pretendido</span><strong id="f_prazo">-</strong></div>
          <div class="field"><span>Imóveis Compatíveis Apresentados</span><strong id="f_imoveis">-</strong></div>
        </div>
      </div>

      <!-- BLOCO 6: AÇÕES DE FOLLOW-UP, VISITA E SLA -->
      <div class="card">
        <div class="card-header">
          <div>
            <h2>Régua de Follow-up, Visita e Monitor de SLA</h2>
            <div class="card-subtitle">Acione disparos de reengajamento ou valide a confirmação de visita pelo corretor</div>
          </div>
          <span id="badgeFollow" class="badge badge-cold">Cadência: Nenhuma</span>
        </div>

        <div class="action-group-title" style="margin-top:0;">Simular Passagem de Tempo (Lead que parou de responder):</div>
        <div class="btn-row">
          <button class="sec" onclick="dispararFollowup('2h')">+2 Horas</button>
          <button class="sec" onclick="dispararFollowup('24h')">+24 Horas</button>
          <button class="sec" onclick="dispararFollowup('D3')">Dia 3 (Meta Template)</button>
          <button class="sec" onclick="dispararFollowup('D7')">Dia 7 (Prova Social)</button>
          <button class="sec" onclick="dispararFollowup('D15')">Dia 15 (Obra)</button>
          <button class="sec" onclick="dispararFollowup('D30')">Dia 30 (Campanha)</button>
          <button class="sec" onclick="dispararFollowup('pos_d30')">Pós-D30 (Sem Retorno)</button>
        </div>

        <div class="action-group-title">Ações de Visita e SLA do Corretor / Vendedor:</div>
        <div class="btn-row">
          <button class="sec" onclick="confirmarVisita()">Vendedor Confirmar Visita</button>
          <button class="sec" onclick="dispararLembreteVisita()">Disparar Lembrete (Véspera)</button>
          <button class="warn" onclick="simularEstouroSLA()">Simular Estouro de SLA (Redistribuir)</button>
        </div>
      </div>

      <!-- BLOCO 7: RESUMO DE PASSAGEM -->
      <div class="card">
        <div class="card-header">
          <div>
            <h2>Resumo Executivo para o Vendedor (Handover)</h2>
            <div class="card-subtitle">Síntese estruturada em 6 linhas entregue ao corretor no momento da transferência</div>
          </div>
        </div>
        <pre id="resumoBox">Aguardando qualificação do lead...</pre>
      </div>
    </section>

    <!-- ABA 2: CADASTRO E GERENCIADOR DE IMÓVEIS -->
    <section class="right-col" id="abaImoveis" style="display:none;">
      <div class="card" id="cardFormImovel">
        <div class="card-header">
          <div>
            <h2 id="tituloFormImovel">Cadastrar Novo Empreendimento</h2>
            <div class="card-subtitle">Adicione ou edite imóveis com validação automática dos tetos MCMV 2026</div>
          </div>
          <button class="sec" onclick="limparFormularioImovel()">Limpar Formulário</button>
        </div>

        <form onsubmit="salvarImovelAmigavel(event)">
          <div class="grid-3">
            <div class="form-group">
              <label>Nome do Empreendimento *</label>
              <input type="text" id="im_nome" placeholder="Ex: Residencial Vista Parque" required />
            </div>
            <div class="form-group">
              <label>Cidade *</label>
              <select id="im_cidade" onchange="atualizarDicaMCMV()">
                <option value="Tubarão">Tubarão</option>
                <option value="Capivari de Baixo">Capivari de Baixo</option>
                <option value="Pescaria Brava">Pescaria Brava</option>
              </select>
            </div>
            <div class="form-group">
              <label>Código Interno</label>
              <input type="text" id="im_codigo" placeholder="Ex: IMOB-TUB-004 (automático se vazio)" />
            </div>
          </div>

          <div class="grid-3">
            <div class="form-group">
              <label>Bairro *</label>
              <input type="text" id="im_bairro" placeholder="Ex: Oficinas" required />
            </div>
            <div class="form-group">
              <label>Endereço Completo</label>
              <input type="text" id="im_endereco" placeholder="Ex: Rua das Flores, 250" />
            </div>
            <div class="form-group">
              <label>Tipo de Imóvel *</label>
              <select id="im_tipo">
                <option value="Apartamento">Apartamento</option>
                <option value="Casa">Casa</option>
                <option value="Lote">Lote</option>
                <option value="Sala Comercial">Sala Comercial</option>
              </select>
            </div>
          </div>

          <div class="grid-4">
            <div class="form-group">
              <label>Quartos *</label>
              <input type="number" id="im_dormitorios" value="2" min="0" max="10" required />
            </div>
            <div class="form-group">
              <label>Suítes</label>
              <input type="number" id="im_suites" value="0" min="0" max="10" />
            </div>
            <div class="form-group">
              <label>Vagas de Garagem</label>
              <input type="number" id="im_vagas" value="1" min="0" max="10" />
            </div>
            <div class="form-group">
              <label>Metragem Privativa *</label>
              <input type="text" id="im_metragem" placeholder="Ex: 54,00 m²" required />
            </div>
          </div>

          <div class="grid-3">
            <div class="form-group">
              <label>Valor "A partir de" (R$) *</label>
              <input type="number" step="0.01" id="im_valor" placeholder="Ex: 215000" oninput="atualizarDicaMCMV()" required />
            </div>
            <div class="form-group">
              <label>Status da Obra *</label>
              <select id="im_status">
                <option value="Lançamento">Lançamento</option>
                <option value="Em obra">Em obra</option>
                <option value="Pronto para morar">Pronto para morar</option>
                <option value="Vendido">Vendido (Pausar oferta)</option>
              </select>
            </div>
            <div class="form-group">
              <label>Previsão de Entrega *</label>
              <input type="text" id="im_entrega" placeholder="Ex: Imediata ou Outubro/2027" required />
            </div>
          </div>

          <div class="mcmv-helper" id="dicaMcmvBox">
            Digite o valor do imóvel e escolha a cidade para ver automaticamente o enquadramento nos tetos do MCMV 2026.
          </div>

          <div class="grid-2" style="margin-top:18px;">
            <div class="form-group">
              <label>Faixas do MCMV 2026 Elegíveis neste Imóvel</label>
              <div class="check-row">
                <label><input type="checkbox" id="chk_f1" value="Faixa 1" checked /> Faixa 1</label>
                <label><input type="checkbox" id="chk_f2" value="Faixa 2" checked /> Faixa 2</label>
                <label><input type="checkbox" id="chk_f3" value="Faixa 3" checked /> Faixa 3</label>
                <label><input type="checkbox" id="chk_f4" value="Faixa 4" /> Faixa 4</label>
              </div>
            </div>
            <div class="form-group">
              <label>Unidades Disponíveis em Estoque *</label>
              <input type="number" id="im_disponibilidade" value="5" min="0" required />
            </div>
          </div>

          <div class="grid-2">
            <div class="form-group">
              <label>Descrição Curta da Tipologia *</label>
              <input type="text" id="im_tipologia" placeholder="Ex: 2 quartos com sacada e churrasqueira" required />
            </div>
            <div class="form-group">
              <label>Diferencial Principal que a Lili deve Destacar *</label>
              <input type="text" id="im_diferencial" placeholder="Ex: Sacada com churrasqueira a carvão e salão mobiliado" required />
            </div>
          </div>

          <div class="grid-2">
            <div class="form-group">
              <label>Foto do Imóvel (Link URL)</label>
              <input type="text" id="im_foto" placeholder="https://construtorademo.com.br/fotos/..." />
            </div>
            <div class="form-group">
              <label>Página no Site (Link URL)</label>
              <input type="text" id="im_link" placeholder="https://construtorademo.com.br/imoveis/..." />
            </div>
          </div>

          <button type="submit" class="primary" style="padding:14px 28px; font-size:0.92rem; margin-top:10px;">
            Salvar Empreendimento no Catálogo
          </button>
          <div class="toast" id="toastImovelForm"></div>
        </form>
      </div>

      <div class="card">
        <div class="card-header">
          <div>
            <h2>Empreendimentos Disponíveis (<span id="countImoveis">0</span>)</h2>
            <div class="card-subtitle">Imóveis ativos que a Lili apresenta aos clientes conforme perfil</div>
          </div>
        </div>
        <div class="imoveis-grid" id="gridCardsImoveis"></div>
      </div>
    </section>

    <!-- ABA 3: DADOS DA CONSTRUTORA & PROMPT -->
    <section class="right-col" id="abaKb" style="display:none;">
      <div class="card">
        <div class="card-header">
          <div>
            <h2>Plantões de Vendas & Contatos Institucionais</h2>
            <div class="card-subtitle">Endereços dos stands e canais de encaminhamento da construtora</div>
          </div>
        </div>
        <div class="form-group">
          <label>Horário de Atendimento Humano e Plantões</label>
          <input type="text" id="kb_horario" />
        </div>
        <div class="grid-2">
          <div class="form-group">
            <label>Stand Tubarão (Endereço)</label>
            <input type="text" id="kb_end_tub" />
          </div>
          <div class="form-group">
            <label>Stand Capivari de Baixo (Endereço)</label>
            <input type="text" id="kb_end_cap" />
          </div>
        </div>
        <div class="form-group">
          <label>Atendimento Pescaria Brava (Endereço)</label>
          <input type="text" id="kb_end_pes" />
        </div>
        <div class="grid-2">
          <div class="form-group">
            <label>Pós-Venda / Assistência Técnica / Boleto</label>
            <input type="text" id="kb_canal_pv" />
          </div>
          <div class="form-group">
            <label>Parcerias (Corretores e Imobiliárias)</label>
            <input type="text" id="kb_canal_parc" />
          </div>
        </div>
        <div class="form-group">
          <label>Fornecedores / Imprensa / Currículos (RH)</label>
          <input type="text" id="kb_canal_forn" />
        </div>
        <button class="primary" onclick="salvarInstitucional()">Salvar Dados Institucionais</button>
        <div class="toast" id="toastInst"></div>
      </div>

      <div class="card">
        <div class="card-header">
          <div>
            <h2>Diretrizes da Atendente Lili (System Prompt)</h2>
            <div class="card-subtitle">Regras de negócio, tom de voz e conduta (GEMINI.md)</div>
          </div>
        </div>
        <div class="form-group">
          <label>Prompt Mestre de Conduta</label>
          <textarea class="code" id="kb_prompt" rows="12"></textarea>
        </div>
        <button class="primary" onclick="salvarPrompt()">Salvar Diretrizes da Lili</button>
        <div class="toast" id="toastPrompt"></div>
      </div>
    </section>

    <!-- ABA 4: CONECTAR WHATSAPP (QR CODE) -->
    <section class="right-col" id="abaWhatsapp" style="display:none;">
      <div class="card">
        <div class="card-header">
          <div>
            <h2>Conexão do WhatsApp via QR Code (Evolution API)</h2>
            <div class="card-subtitle">Conecte o número de atendimento diretamente pelo celular</div>
          </div>
        </div>

        <p style="font-size:0.88rem; color:var(--text-muted); margin-bottom:22px; line-height:1.6;">
          Abra o WhatsApp no seu smartphone, acesse <strong>Aparelhos Conectados &gt; Conectar um aparelho</strong> e aponte a câmera para o QR Code abaixo:
        </p>

        <div style="display:flex; gap:28px; align-items:flex-start; flex-wrap:wrap;">
          <div class="qr-card-box">
            <div id="qrCodeContainer">
              <div style="font-size:0.84rem; color:var(--text-muted);">Clique no botão ao lado para carregar o QR Code</div>
            </div>
            <div id="qrCodeStatus" style="font-size:0.78rem; color:var(--accent-cyan); margin-top:14px; font-weight:600;">Instância: lili-whatsapp</div>
          </div>

          <div style="flex:1; min-width:280px;">
            <div class="grid-2" style="margin-bottom:18px;">
              <div class="field">
                <span>Status da Conexão</span>
                <strong id="evoStatusTexto" style="color:var(--accent-amber);">Verificando...</strong>
              </div>
              <div class="field">
                <span>Webhook Local</span>
                <code style="font-size:0.76rem; color:#a7f3d0;">http://localhost:8000/webhook/evolution</code>
              </div>
            </div>

            <div class="btn-row">
              <button class="primary" onclick="carregarQrCodeEvo()">Gerar / Atualizar QR Code</button>
              <button class="sec" onclick="checarStatusEvo()">Atualizar Status</button>
            </div>

            <div style="margin-top:22px; font-size:0.83rem; color:var(--text-muted); line-height:1.6; background:rgba(15,23,42,0.6); padding:18px 20px; border-radius:18px; border:1px solid var(--glass-border);">
              <strong style="color:#ffffff;">Como rodar a Evolution API localmente:</strong><br/>
              Execute <code style="color:#38bdf8; font-family:'JetBrains Mono',monospace;">docker compose up -d</code> na pasta do projeto para iniciar o serviço na porta 8080.
            </div>
          </div>
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <div>
            <h2>Motor de Inteligência Artificial: GroqCloud</h2>
            <div class="card-subtitle">Processamento de linguagem em tempo real com ferramentas integradas</div>
          </div>
        </div>
        <div class="grid-3">
          <div class="field">
            <span>Plataforma</span>
            <strong style="color:var(--accent-cyan);">GroqCloud LPUs</strong>
          </div>
          <div class="field">
            <span>Modelo</span>
            <strong style="color:var(--accent-emerald-light);">qwen/qwen3.8-27b</strong>
          </div>
          <div class="field">
            <span>Velocidade de Resposta</span>
            <strong style="color:#a7f3d0;">~0.4s (Instantâneo)</strong>
          </div>
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <div>
            <h2>Registro de Envios (Outbox Logs)</h2>
            <div class="card-subtitle">Últimas mensagens e sincronizações processadas</div>
          </div>
        </div>
        <pre id="outboxLogsPreview">Carregando logs...</pre>
      </div>
    </section>
  </main>

  <script>
    let TELEFONE = "5548999990001";
    let iaPausada = false;
    let cacheInstitucional = null;
    let listaImoveisCache = [];
    let todosLeadsCache = [];
    let filtroLeadAtual = "todos";

    // Lista de telefones conhecidos no navegador para funcionar mesmo sem reiniciar o servidor
    let telefonesConhecidos = JSON.parse(localStorage.getItem("lili_telefones_conhecidos") || '["5548999990001"]');

    function registrarTelefoneConhecido(tel) {
      if (tel && !telefonesConhecidos.includes(tel)) {
        telefonesConhecidos.push(tel);
        localStorage.setItem("lili_telefones_conhecidos", JSON.stringify(telefonesConhecidos));
      }
    }

    function mudarTelefoneTeste(novo) {
      const limpo = (novo || "").replace(/\D/g, "");
      if (limpo) {
        TELEFONE = limpo;
        registrarTelefoneConhecido(TELEFONE);
        document.getElementById("telAtualInput").value = TELEFONE;
        atualizarPainelCRM(true);
      }
    }

    function criarNovoLeadRapido() {
      const sufixo = Math.floor(1000 + Math.random() * 9000);
      const novoTel = "554899999" + sufixo;
      mudarTelefoneTeste(novoTel);
    }

    async function popularLeadsDemonstracao() {
      const demos = [
        {
          tel: "5548999110101",
          origem: "Instagram Ads",
          campanha: "MCMV_Tubarao_2026",
          msgs: [
            "Oi, me chamo Mariana e quero comprar meu primeiro apartamento pra morar em Tubarão com 2 quartos",
            "Minha renda bruta familiar é R$ 4.200 de carteira assinada, tenho FGTS de 4 anos e R$ 15 mil de entrada. Quero mudar em até 3 meses, moro com meu marido e não tenho outro imóvel nem restrição no CPF"
          ]
        },
        {
          tel: "5548999110202",
          origem: "Formulário do Site",
          campanha: "Residencial_Capivari",
          msgs: [
            "Olá, sou o Roberto. Procuro casa de 2 quartos em Capivari de Baixo para morar, é meu primeiro imóvel",
            "Nossa renda somada dá R$ 6.800 autônomo, temos R$ 25 mil de entrada, sem FGTS, queremos mudar em 6 meses"
          ]
        },
        {
          tel: "5548999110303",
          origem: "Portal VivaReal",
          campanha: "Pescaria_Brava_Lotes",
          msgs: [
            "Oi, sou a Fernanda, gostaria de saber opções em Pescaria Brava de 2 quartos para morar"
          ]
        }
      ];

      for (const d of demos) {
        registrarTelefoneConhecido(d.tel);
        for (const m of d.msgs) {
          await fetch("/api/chat", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({ telefone: d.tel, mensagem: m, origem: d.origem, campanha: d.campanha })
          });
        }
      }
      mudarTelefoneTeste("5548999110101");
    }

    function filtrarListaLeads(filtro) {
      filtroLeadAtual = filtro;
      ["todos", "Quente", "Morno", "Frio", "transferido"].forEach((f) => {
        const el = document.getElementById("fBtn_" + f);
        if (el) el.className = "sec" + (f === filtro ? " active-filter" : "");
      });
      renderizarListaEGraficosLeads();
    }

    async function carregarTodosLeadsPainel() {
      try {
        const resp = await fetch("/api/leads");
        if (resp.ok) {
          const data = await resp.json();
          if (Array.isArray(data.leads) && data.leads.length > 0) {
            todosLeadsCache = data.leads;
            todosLeadsCache.forEach((l) => registrarTelefoneConhecido(l.telefone));
            renderizarListaEGraficosLeads();
            return;
          }
        }
      } catch (e) {}

      // Fallback automático buscando os telefones conhecidos individualmente
      const lista = [];
      for (const tel of telefonesConhecidos) {
        try {
          const r = await fetch(`/api/leads/${tel}`);
          if (r.ok) {
            const d = await r.json();
            if (d.lead) lista.push(d.lead);
          }
        } catch (e) {}
      }
      todosLeadsCache = lista;
      renderizarListaEGraficosLeads();
    }

    function renderizarListaEGraficosLeads() {
      const total = todosLeadsCache.length || 1;
      const quentesMornos = todosLeadsCache.filter((l) => l.temperatura === "Quente" || l.temperatura === "Morno").length;
      const visitasRepasses = todosLeadsCache.filter((l) => l.etapa === "transferido" || l.preferencia_visita || l.status_visita === "confirmada").length;

      document.getElementById("kpiTotalLeads").textContent = todosLeadsCache.length;
      document.getElementById("kpiLeadsQualificados").textContent = quentesMornos;
      const pctQual = Math.round((quentesMornos / total) * 100);
      document.getElementById("kpiTaxaQualificacao").textContent = `${pctQual}% da carteira qualificada`;
      document.getElementById("kpiVisitasEncaminhadas").textContent = visitasRepasses;

      // Gráfico de Cidades
      const contagemCidades = { "Tubarão": 0, "Capivari de Baixo": 0, "Pescaria Brava": 0, "Em definição": 0 };
      todosLeadsCache.forEach((l) => {
        const c = l.cidade || "Em definição";
        if (contagemCidades[c] !== undefined) contagemCidades[c]++;
        else contagemCidades["Em definição"]++;
      });

      const cidBox = document.getElementById("relatorioCidadesBox");
      cidBox.innerHTML = Object.entries(contagemCidades).map(([cid, qtd]) => {
        const pct = Math.round((qtd / total) * 100);
        return `
          <div class="stat-bar-item">
            <div class="stat-bar-top"><span>${cid}</span><span>${qtd} lead(s) (${pct}%)</span></div>
            <div class="stat-bar-track"><div class="stat-bar-fill" style="width:${Math.max(pct, 4)}%;"></div></div>
          </div>
        `;
      }).join("");

      // Gráfico de Faixas MCMV
      const contagemFaixas = { "Faixa 1": 0, "Faixa 2": 0, "Faixa 3": 0, "Faixa 4": 0, "Em análise": 0 };
      todosLeadsCache.forEach((l) => {
        const f = l.pre_enquadramento_mcmv || "";
        if (f.includes("Faixa 1")) contagemFaixas["Faixa 1"]++;
        else if (f.includes("Faixa 2")) contagemFaixas["Faixa 2"]++;
        else if (f.includes("Faixa 3")) contagemFaixas["Faixa 3"]++;
        else if (f.includes("Faixa 4")) contagemFaixas["Faixa 4"]++;
        else contagemFaixas["Em análise"]++;
      });

      const fxBox = document.getElementById("relatorioFaixasBox");
      fxBox.innerHTML = Object.entries(contagemFaixas).map(([fx, qtd]) => {
        const pct = Math.round((qtd / total) * 100);
        return `
          <div class="stat-bar-item">
            <div class="stat-bar-top"><span>${fx}</span><span>${qtd} lead(s) (${pct}%)</span></div>
            <div class="stat-bar-track"><div class="stat-bar-fill" style="width:${Math.max(pct, 4)}%;"></div></div>
          </div>
        `;
      }).join("");

      // Lista filtrada de leads
      const filtrados = todosLeadsCache.filter((l) => {
        if (filtroLeadAtual === "todos") return true;
        if (filtroLeadAtual === "transferido") return l.etapa === "transferido" || Boolean(l.preferencia_visita);
        return l.temperatura === filtroLeadAtual;
      });

      const listBox = document.getElementById("listaGestaoLeadsBox");
      if (filtrados.length === 0) {
        listBox.innerHTML = `<div style="padding:20px; color:var(--text-muted); font-size:0.86rem; text-align:center;">Nenhum atendimento encontrado para este filtro.</div>`;
        return;
      }

      listBox.innerHTML = filtrados.map((l) => {
        const bClass = l.temperatura === "Quente" ? "badge-hot" : l.temperatura === "Morno" ? "badge-warm" : "badge-cold";
        const isAtivo = l.telefone === TELEFONE;
        const ultMsg = (l.historico_mensagens && l.historico_mensagens.length > 0)
          ? l.historico_mensagens[l.historico_mensagens.length - 1].texto
          : "Sem mensagens registradas";
        const resumoCurto = ultMsg.length > 85 ? ultMsg.substring(0, 85) + "..." : ultMsg;

        return `
          <div class="lead-row-card ${isAtivo ? 'selected-lead' : ''}">
            <div class="lead-row-info">
              <div class="lead-row-title">
                <strong>${l.nome || "Cliente em Qualificação"}</strong>
                <span class="badge ${bClass}">${(l.temperatura || "FRIO").toUpperCase()} | ${l.pontuacao || 0} pts</span>
                <span class="badge badge-ok">${l.pre_enquadramento_mcmv || "Faixa em análise"}</span>
              </div>
              <div class="lead-row-meta">
                <span>Telefone: <strong>${l.telefone}</strong></span>
                <span>Cidade: <strong>${l.cidade || "A definir"}</strong></span>
                <span>Origem: <strong>${l.origem || "WhatsApp"}</strong></span>
                <span>Etapa: <strong>${l.etapa || "em qualificação"}</strong></span>
              </div>
              <div style="font-size:0.79rem; color:var(--text-dim); margin-top:2px;">Última interação: "${resumoCurto}"</div>
            </div>
            <div>
              <button class="${isAtivo ? 'primary' : 'sec'}" onclick="mudarTelefoneTeste('${l.telefone}')">
                ${isAtivo ? "Atendimento Selecionado" : "Abrir Conversa & Ficha"}
              </button>
            </div>
          </div>
        `;
      }).join("");
    }

    function trocarAba(aba) {
      document.getElementById("abaCrm").style.display = aba === "crm" ? "flex" : "none";
      document.getElementById("abaImoveis").style.display = aba === "imoveis" ? "flex" : "none";
      document.getElementById("abaKb").style.display = aba === "kb" ? "flex" : "none";
      document.getElementById("abaWhatsapp").style.display = aba === "whatsapp" ? "flex" : "none";

      document.getElementById("tabBtnCrm").className = "tab-btn" + (aba === "crm" ? " active" : "");
      document.getElementById("tabBtnImoveis").className = "tab-btn" + (aba === "imoveis" ? " active" : "");
      document.getElementById("tabBtnKb").className = "tab-btn" + (aba === "kb" ? " active" : "");
      document.getElementById("tabBtnWhatsapp").className = "tab-btn" + (aba === "whatsapp" ? " active" : "");

      if (aba === "crm") atualizarPainelCRM();
      if (aba === "imoveis") carregarListaImoveis();
      if (aba === "kb") carregarBaseConhecimento();
      if (aba === "whatsapp") checarStatusEvo();
    }

    function formatarMoeda(valor) {
      return Number(valor || 0).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
    }

    function atualizarDicaMCMV() {
      const cidade = document.getElementById("im_cidade").value;
      const valor = parseFloat(document.getElementById("im_valor").value || "0");
      const box = document.getElementById("dicaMcmvBox");
      if (!valor || valor <= 0) {
        box.textContent = "Digite o valor do imóvel para verificar automaticamente os tetos do MCMV 2026 na cidade escolhida.";
        return;
      }

      const tetoF1F2 = cidade === "Tubarão" ? 235000 : cidade === "Pescaria Brava" ? 210000 : 220000;
      const cabeF1F2 = valor <= tetoF1F2;
      const cabeF3 = valor <= 400000;
      const cabeF4 = valor <= 600000;

      document.getElementById("chk_f1").checked = cabeF1F2;
      document.getElementById("chk_f2").checked = cabeF1F2;
      document.getElementById("chk_f3").checked = cabeF3;
      document.getElementById("chk_f4").checked = !cabeF1F2 && cabeF4;

      if (cabeF1F2) {
        box.innerHTML = `<strong>Enquadramento Total em ${cidade}:</strong> Valor dentro do teto das <strong>Faixas 1 e 2</strong> (limite de ${formatarMoeda(tetoF1F2)} em ${cidade}), além da Faixa 3 (até R$ 400 mil).`;
      } else if (cabeF3) {
        box.innerHTML = `<strong>Enquadramento Faixas 3 e 4 em ${cidade}:</strong> Acima do teto das Faixas 1/2 (${formatarMoeda(tetoF1F2)}), mas elegível para <strong>Faixa 3</strong> (até R$ 400 mil) e <strong>Faixa 4</strong> (até R$ 600 mil).`;
      } else if (cabeF4) {
        box.innerHTML = `<strong>Enquadramento Faixa 4 em ${cidade}:</strong> Elegível para a <strong>Faixa 4</strong> (teto R$ 600 mil, financiando até 80% no imóvel novo).`;
      } else {
        box.innerHTML = `<strong>Acima do Teto MCMV 2026 (R$ 600 mil):</strong> Este imóvel ficará fora do programa MCMV (atendido com financiamento tradicional SBPE).`;
      }
    }

    async function carregarListaImoveis() {
      const resp = await fetch("/api/imoveis/admin");
      const data = await resp.json();
      listaImoveisCache = data.imoveis || [];
      document.getElementById("countImoveis").textContent = listaImoveisCache.length;

      const grid = document.getElementById("gridCardsImoveis");
      grid.innerHTML = "";

      listaImoveisCache.forEach((im) => {
        const card = document.createElement("div");
        card.className = "imovel-card";
        const dispBadge = im.disponibilidade > 0 && im.status !== "Vendido"
          ? `<span class="badge badge-ok">${im.disponibilidade} disp.</span>`
          : `<span class="badge badge-hot">Esgotado</span>`;
        const faixasTxt = Array.isArray(im.faixas_mcmv) ? im.faixas_mcmv.join(", ") : im.faixas_mcmv;

        card.innerHTML = `
          <div>
            <div style="display:flex; justify-content:space-between; align-items:center;">
              <span class="badge badge-cold">${im.cidade} | ${im.codigo}</span>
              ${dispBadge}
            </div>
            <h3>${im.nome}</h3>
            <div style="font-size:0.8rem; color:#93c5fd; margin-top:2px;">Bairro: ${im.bairro} | ${im.tipo} (${im.status})</div>
            <div class="imovel-preco">A partir de ${formatarMoeda(im.valor_a_partir)}</div>
            <div class="imovel-meta">
              ${im.dormitorios} quartos (${im.suites} suíte) | ${im.vagas} vaga | ${im.metragem_privativa}<br/>
              <strong>MCMV:</strong> ${faixasTxt || "-"}<br/>
              <strong>Diferencial:</strong> ${im.diferencial}
            </div>
          </div>
          <div style="display:flex; gap:10px; margin-top:12px;">
            <button class="sec" style="flex:1;" onclick="preencherParaEditar('${im.codigo}')">Editar</button>
            <button class="danger" onclick="excluirImovel('${im.codigo}', '${im.nome}')">Excluir</button>
          </div>
        `;
        grid.appendChild(card);
      });
    }

    function preencherParaEditar(codigo) {
      const im = listaImoveisCache.find((x) => x.codigo === codigo);
      if (!im) return;

      document.getElementById("tituloFormImovel").textContent = `Editando: ${im.nome} (${im.codigo})`;
      document.getElementById("im_codigo").value = im.codigo;
      document.getElementById("im_nome").value = im.nome;
      document.getElementById("im_cidade").value = im.cidade;
      document.getElementById("im_bairro").value = im.bairro;
      document.getElementById("im_endereco").value = im.endereco;
      document.getElementById("im_tipo").value = im.tipo;
      document.getElementById("im_tipologia").value = im.tipologia;
      document.getElementById("im_dormitorios").value = im.dormitorios;
      document.getElementById("im_suites").value = im.suites;
      document.getElementById("im_vagas").value = im.vagas;
      document.getElementById("im_metragem").value = im.metragem_privativa;
      document.getElementById("im_valor").value = im.valor_a_partir;
      document.getElementById("im_status").value = im.status;
      document.getElementById("im_entrega").value = im.previsao_entrega;
      document.getElementById("im_disponibilidade").value = im.disponibilidade;
      document.getElementById("im_diferencial").value = im.diferencial;
      document.getElementById("im_foto").value = im.foto;
      document.getElementById("im_link").value = im.link;

      const faixas = Array.isArray(im.faixas_mcmv) ? im.faixas_mcmv : String(im.faixas_mcmv).split(",");
      document.getElementById("chk_f1").checked = faixas.some((f) => f.includes("1"));
      document.getElementById("chk_f2").checked = faixas.some((f) => f.includes("2"));
      document.getElementById("chk_f3").checked = faixas.some((f) => f.includes("3"));
      document.getElementById("chk_f4").checked = faixas.some((f) => f.includes("4"));

      document.getElementById("abaImoveis").scrollTo({ top: 0, behavior: "smooth" });
    }

    function limparFormularioImovel() {
      document.getElementById("tituloFormImovel").textContent = "Cadastrar Novo Empreendimento";
      document.getElementById("im_codigo").value = "";
      document.getElementById("im_nome").value = "";
      document.getElementById("im_bairro").value = "";
      document.getElementById("im_endereco").value = "";
      document.getElementById("im_tipologia").value = "";
      document.getElementById("im_dormitorios").value = 2;
      document.getElementById("im_suites").value = 0;
      document.getElementById("im_vagas").value = 1;
      document.getElementById("im_metragem").value = "";
      document.getElementById("im_valor").value = "";
      document.getElementById("im_entrega").value = "";
      document.getElementById("im_disponibilidade").value = 5;
      document.getElementById("im_diferencial").value = "";
      document.getElementById("im_foto").value = "";
      document.getElementById("im_link").value = "";
      atualizarDicaMCMV();
    }

    async function salvarImovelAmigavel(e) {
      e.preventDefault();
      const faixas = [];
      if (document.getElementById("chk_f1").checked) faixas.push("Faixa 1");
      if (document.getElementById("chk_f2").checked) faixas.push("Faixa 2");
      if (document.getElementById("chk_f3").checked) faixas.push("Faixa 3");
      if (document.getElementById("chk_f4").checked) faixas.push("Faixa 4");

      const payload = {
        codigo: document.getElementById("im_codigo").value,
        nome: document.getElementById("im_nome").value,
        cidade: document.getElementById("im_cidade").value,
        bairro: document.getElementById("im_bairro").value,
        endereco: document.getElementById("im_endereco").value,
        tipo: document.getElementById("im_tipo").value,
        tipologia: document.getElementById("im_tipologia").value,
        dormitorios: parseInt(document.getElementById("im_dormitorios").value || "2"),
        suites: parseInt(document.getElementById("im_suites").value || "0"),
        vagas: parseInt(document.getElementById("im_vagas").value || "1"),
        metragem_privativa: document.getElementById("im_metragem").value,
        valor_a_partir: parseFloat(document.getElementById("im_valor").value || "0"),
        faixas_mcmv: faixas,
        status: document.getElementById("im_status").value,
        previsao_entrega: document.getElementById("im_entrega").value,
        disponibilidade: parseInt(document.getElementById("im_disponibilidade").value || "0"),
        diferencial: document.getElementById("im_diferencial").value,
        foto: document.getElementById("im_foto").value || "https://construtorademo.com.br/fotos/empreendimento.jpg",
        link: document.getElementById("im_link").value || "https://construtorademo.com.br/imoveis"
      };

      const resp = await fetch("/api/imoveis/admin/salvar", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(payload)
      });
      const res = await resp.json();
      mostrarToast("toastImovelForm", `Empreendimento "${res.imovel.nome}" salvo com sucesso!`);
      limparFormularioImovel();
      await carregarListaImoveis();
    }

    async function excluirImovel(codigo, nome) {
      if (!confirm(`Deseja remover o imóvel "${nome}" (${codigo}) do catálogo?`)) return;
      await fetch("/api/imoveis/admin/excluir", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({ codigo })
      });
      await carregarListaImoveis();
    }

    async function carregarBaseConhecimento() {
      const resp = await fetch("/api/kb");
      const data = await resp.json();
      cacheInstitucional = data.institucional;

      const hp = cacheInstitucional.horarios_e_plantoes || {};
      const stands = hp.stands || [];
      const canais = cacheInstitucional.canais_encaminhamento_especifico || {};

      document.getElementById("kb_horario").value = hp.horario_atendimento_humano || "";
      document.getElementById("kb_end_tub").value = (stands[0] && stands[0].endereco) || "";
      document.getElementById("kb_end_cap").value = (stands[1] && stands[1].endereco) || "";
      document.getElementById("kb_end_pes").value = (stands[2] && stands[2].endereco) || "";
      document.getElementById("kb_canal_pv").value = (canais.pos_venda_assistencia_boleto && canais.pos_venda_assistencia_boleto.contato) || "";
      document.getElementById("kb_canal_parc").value = (canais.parcerias_corretores_imobiliarias && canais.parcerias_corretores_imobiliarias.contato) || "";
      document.getElementById("kb_canal_forn").value = (canais.fornecedores_imprensa_curriculos && canais.fornecedores_imprensa_curriculos.contato) || "";
      document.getElementById("kb_prompt").value = data.system_prompt || "";
    }

    function mostrarToast(id, msg, erro = false) {
      const el = document.getElementById(id);
      el.style.display = "block";
      el.style.borderColor = erro ? "var(--accent-rose)" : "var(--accent-emerald)";
      el.style.color = erro ? "#fda4af" : "#a7f3d0";
      el.textContent = msg;
      setTimeout(() => { el.style.display = "none"; }, 4500);
    }

    async function salvarInstitucional() {
      const obj = cacheInstitucional || {};
      obj.horarios_e_plantoes = obj.horarios_e_plantoes || {};
      obj.horarios_e_plantoes.horario_atendimento_humano = document.getElementById("kb_horario").value;
      if (obj.horarios_e_plantoes.stands && obj.horarios_e_plantoes.stands.length >= 3) {
        obj.horarios_e_plantoes.stands[0].endereco = document.getElementById("kb_end_tub").value;
        obj.horarios_e_plantoes.stands[1].endereco = document.getElementById("kb_end_cap").value;
        obj.horarios_e_plantoes.stands[2].endereco = document.getElementById("kb_end_pes").value;
      }
      if (obj.canais_encaminhamento_especifico) {
        obj.canais_encaminhamento_especifico.pos_venda_assistencia_boleto.contato = document.getElementById("kb_canal_pv").value;
        obj.canais_encaminhamento_especifico.parcerias_corretores_imobiliarias.contato = document.getElementById("kb_canal_parc").value;
        obj.canais_encaminhamento_especifico.fornecedores_imprensa_curriculos.contato = document.getElementById("kb_canal_forn").value;
      }
      await fetch("/api/kb/institucional", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({ dados: obj })
      });
      mostrarToast("toastInst", "Dados institucionais atualizados em tempo real!");
    }

    async function salvarPrompt() {
      const prompt = document.getElementById("kb_prompt").value;
      await fetch("/api/kb/prompt", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({ system_prompt: prompt })
      });
      mostrarToast("toastPrompt", "Diretrizes da Lili recarregadas com sucesso!");
    }

    async function enviarMensagem(e) {
      e.preventDefault();
      const input = document.getElementById("msgInput");
      const texto = input.value.trim();
      if (!texto) return;
      input.value = "";
      adicionarBolha(texto, "user");

      const resp = await fetch("/api/chat", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({ telefone: TELEFONE, mensagem: texto })
      });
      const data = await resp.json();
      if (data.resposta_lili) {
        adicionarBolha(data.resposta_lili, "lili");
      } else if (!data.ia_ativa) {
        adicionarBolha("[Atendimento pausado: Corretor humano no controle]", "sys");
      }
      await atualizarPainelCRM(false);
    }

    async function dispararFollowup(etapa) {
      const resp = await fetch(`/api/leads/${TELEFONE}/followup/${etapa}`, { method: "POST" });
      const data = await resp.json();
      if (data.enviado) {
        const tag = data.usa_template_meta ? ` [Template Meta: ${data.template_meta}]` : " [Janela 24h]";
        adicionarBolha(`Follow-up ${etapa}${tag}`, "sys");
        adicionarBolha(data.mensagem_enviada, "lili");
      } else {
        adicionarBolha(`Follow-up (${etapa}): ${data.motivo}`, "sys");
      }
      await atualizarPainelCRM(false);
    }

    async function confirmarVisita() {
      const resp = await fetch(`/api/leads/${TELEFONE}/confirmar-visita`, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({ horario_confirmado: "15h00", local: "Stand Central - Tubarão" })
      });
      const data = await resp.json();
      adicionarBolha(`Visita confirmada para ${data.horario_visita_confirmado} (${data.local_visita})`, "sys");
      await atualizarPainelCRM(false);
    }

    async function dispararLembreteVisita() {
      const resp = await fetch(`/api/leads/${TELEFONE}/lembrete-visita`, { method: "POST" });
      const data = await resp.json();
      if (data.enviado) {
        adicionarBolha("Lembrete de Véspera de Visita Enviado", "sys");
        adicionarBolha(data.mensagem_enviada, "lili");
      } else {
        adicionarBolha(`Lembrete bloqueado: ${data.motivo}`, "sys");
      }
      await atualizarPainelCRM(false);
    }

    async function simularEstouroSLA() {
      const resp = await fetch(`/api/leads/${TELEFONE}/verificar-sla`, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({ minutos_decorridos_simulacao: 3000 })
      });
      const data = await resp.json();
      if (data.sla_estourado) {
        adicionarBolha(data.alerta_gestor, "sys");
      } else {
        adicionarBolha(`SLA dentro do prazo (${data.status || "OK"})`, "sys");
      }
      await atualizarPainelCRM(false);
    }

    function adicionarBolha(texto, autor) {
      const box = document.getElementById("chatBox");
      const div = document.createElement("div");
      div.className = "msg " + (autor === "lili" ? "msg-lili" : autor === "user" ? "msg-user" : "msg-sys");
      div.textContent = texto;
      box.appendChild(div);
      box.scrollTop = box.scrollHeight;
    }

    function sincronizarHistoricoChat(lead) {
      const box = document.getElementById("chatBox");
      box.innerHTML = `<div class="msg msg-lili">Oi! Tudo bem? Aqui é a Lili, assistente virtual da Construtora Demo.\nQue bom receber seu contato! Com quem eu falo e como posso te ajudar hoje?</div>`;
      if (lead && Array.isArray(lead.historico_mensagens)) {
        lead.historico_mensagens.forEach((m) => {
          adicionarBolha(m.texto, m.autor === "cliente" ? "user" : "lili");
        });
      }
    }

    async function atualizarPainelCRM(recarregarChat = false) {
      registrarTelefoneConhecido(TELEFONE);
      const resp = await fetch(`/api/leads/${TELEFONE}`);
      const data = await resp.json();
      const l = data.lead;

      if (recarregarChat) {
        sincronizarHistoricoChat(l);
      }

      iaPausada = Boolean(l.vendedor_assumiu);
      document.getElementById("statusIA").textContent = iaPausada ? "Atendimento Manual (Humano)" : "Online 24/7";
      document.getElementById("btnVendedor").textContent = iaPausada ? "Devolver para Lili IA" : "Vendedor Assumir";

      document.getElementById("f_faixa").textContent = l.pre_enquadramento_mcmv || "A definir";
      document.getElementById("f_etapa").textContent = l.etapa || "-";
      document.getElementById("f_vendedor").textContent = l.vendedor_responsavel || "-";
      document.getElementById("f_sla").textContent = `${l.prazo_retorno_vendedor || "-"} | Visita: ${l.status_visita || "não agendada"}`;
      document.getElementById("f_nome").textContent = l.nome || "-";
      document.getElementById("f_obj").textContent = `${l.objetivo || "-"} / 1º: ${l.primeiro_imovel || "-"}`;
      document.getElementById("f_cidade").textContent = l.cidade || "-";
      document.getElementById("f_tipo").textContent = `${l.tipo_imovel || "-"} (${l.quartos || "-"} quartos)`;
      document.getElementById("f_renda").textContent = l.renda_bruta_familiar_faixa || "-";
      document.getElementById("f_fgts").textContent = `${l.tipo_renda || "-"} | FGTS: ${l.fgts_mais_3_anos || "-"}`;
      document.getElementById("f_entrada").textContent = l.entrada_disponivel || "-";
      document.getElementById("f_cpf").textContent = l.restricao_cpf || "-";
      document.getElementById("f_prazo").textContent = l.prazo_compra || "-";
      document.getElementById("f_imoveis").textContent = (l.imoveis_apresentados || []).join(", ") || "-";
      document.getElementById("resumoBox").textContent = data.resumo_6_linhas_preview || "";
      document.getElementById("badgeFollow").textContent = "Cadência: " + ((l.etapas_followup_enviadas || []).join(" -> ") || "Nenhuma");

      const badge = document.getElementById("badgeTemp");
      badge.textContent = `${(l.temperatura || "FRIO").toUpperCase()} | ${l.pontuacao || 0} pts`;
      badge.className = "badge " + (l.temperatura === "Quente" ? "badge-hot" : l.temperatura === "Morno" ? "badge-warm" : "badge-cold");

      await carregarTodosLeadsPainel();
    }

    async function alternarVendedor() {
      const rota = iaPausada ? "vendedor-devolver" : "vendedor-assumir";
      await fetch(`/api/leads/${TELEFONE}/${rota}`, { method: "POST" });
      iaPausada = !iaPausada;
      document.getElementById("statusIA").textContent = iaPausada ? "Atendimento Manual (Humano)" : "Online 24/7";
      document.getElementById("btnVendedor").textContent = iaPausada ? "Devolver para Lili IA" : "Vendedor Assumir";
      await carregarTodosLeadsPainel();
    }

    async function resetarConversa() {
      await fetch(`/api/leads/${TELEFONE}/resetar`, { method: "POST" });
      document.getElementById("chatBox").innerHTML = `<div class="msg msg-lili">Oi! Tudo bem? Aqui é a Lili, assistente virtual da Construtora Demo.\nQue bom receber seu contato! Com quem eu falo e como posso te ajudar hoje?</div>`;
      iaPausada = false;
      document.getElementById("statusIA").textContent = "Online 24/7";
      document.getElementById("btnVendedor").textContent = "Vendedor Assumir";
      await atualizarPainelCRM(false);
    }

    async function checarStatusEvo() {
      try {
        const resp = await fetch("/api/evolution/status");
        const data = await resp.json();
        const textoEl = document.getElementById("evoStatusTexto");
        if (data.conectado) {
          textoEl.textContent = "Conectado (Sessão Ativa)";
          textoEl.style.color = "#34d399";
        } else if (data.estado === "connecting" || data.estado === "qrcode") {
          textoEl.textContent = "Aguardando Leitura do QR Code";
          textoEl.style.color = "#fcd34d";
        } else {
          textoEl.textContent = `${data.estado || "Offline"} (Modo Simulação)`;
          textoEl.style.color = "#94a3b8";
        }

        const logsResp = await fetch("/api/integracoes/logs");
        const logsData = await logsResp.json();
        document.getElementById("outboxLogsPreview").textContent = JSON.stringify(logsData, null, 2);
      } catch (err) {
        document.getElementById("evoStatusTexto").textContent = "Modo de Simulação Local";
      }
    }

    let intervaloChecagemEvo = null;

    async function carregarQrCodeEvo() {
      const container = document.getElementById("qrCodeContainer");
      const statusEl = document.getElementById("qrCodeStatus");
      container.innerHTML = '<div style="font-size:0.84rem; color:var(--accent-cyan);">Gerando QR Code de Conexão...</div>';
      statusEl.textContent = "Aguardando Evolution API...";
      statusEl.style.color = "var(--accent-cyan)";

      try {
        const resp = await fetch("/api/evolution/qrcode");
        const data = await resp.json();

        if (data.sucesso && data.qrcode_base64) {
          let html = `<img src="${data.qrcode_base64}" style="width:210px; height:210px; border-radius:16px; border:2px solid var(--accent-cyan); background:#fff; padding:6px; box-shadow:0 8px 24px rgba(0,0,0,0.5);" alt="QR Code WhatsApp" />`;
          if (data.pairing_code) {
            html += `<div style="margin-top:10px; font-size:0.82rem; color:#a7f3d0;">Código: <strong style="font-family:'JetBrains Mono',monospace;">${data.pairing_code}</strong></div>`;
          }
          container.innerHTML = html;
          statusEl.textContent = "Aponte a câmera do WhatsApp para escanear!";
          statusEl.style.color = "#34d399";

          if (intervaloChecagemEvo) clearInterval(intervaloChecagemEvo);
          intervaloChecagemEvo = setInterval(async () => {
            const stResp = await fetch("/api/evolution/status");
            const stData = await stResp.json();
            if (stData.conectado) {
              clearInterval(intervaloChecagemEvo);
              container.innerHTML = '<div style="font-size:0.95rem; color:#34d399; padding:20px; text-align:center;"><strong>WhatsApp Conectado com Sucesso!</strong><br/><small style="color:var(--text-muted); font-size:0.75rem;">A Lili já está pronta para atender seus clientes.</small></div>';
              statusEl.textContent = "Sessão Ativa (Conectado)";
              statusEl.style.color = "#34d399";
              checarStatusEvo();
            }
          }, 3000);

        } else if (data.ja_conectado) {
          container.innerHTML = '<div style="font-size:0.95rem; color:#34d399; padding:20px; text-align:center;"><strong>WhatsApp já está conectado!</strong><br/><small style="color:var(--text-muted); font-size:0.75rem;">Sessão ativa na Evolution API.</small></div>';
          statusEl.textContent = "Sessão Ativa (Conectado)";
          statusEl.style.color = "#34d399";
        } else {
          const motivo = data.erro || "Evolution API offline na porta 8080";
          container.innerHTML = `
            <div style="font-size:0.8rem; color:#fda4af; padding:12px; line-height:1.45; text-align:left;">
              <strong>Não foi possível gerar:</strong><br/>
              ${motivo}<br/><br/>
              <strong style="color:#ffffff;">Dicas:</strong><br/>
              1. Verifique se o Docker Desktop está em execução.<br/>
              2. Execute <code>docker compose up -d</code> no terminal.<br/>
              3. Acesse <code>http://localhost:8080</code> para verificar a Evolution API.
            </div>`;
          statusEl.textContent = "Erro de conexão com Evolution API";
          statusEl.style.color = "var(--accent-rose)";
        }
      } catch (err) {
        container.innerHTML = `<div style="font-size:0.8rem; color:#fda4af; padding:10px;">Erro na requisição: ${err.message}</div>`;
        statusEl.textContent = "Erro na requisição";
        statusEl.style.color = "var(--accent-rose)";
      }
      checarStatusEvo();
    }

    atualizarPainelCRM(true);
  </script>
</body>
</html>"""
