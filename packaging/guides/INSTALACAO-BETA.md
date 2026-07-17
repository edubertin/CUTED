# CUTED Beta — Guia de Instalação

Oi! Você recebeu o beta do CUTED, um programa que transforma vídeos longos em
cortes prontos para TikTok, Shorts, Instagram, Facebook e YouTube. Este guia
leva uns 10 minutos. Qualquer problema, fala direto com o Eduardo.

## 1. Instalar

1. Baixe o arquivo `CUTED-Setup-<versão>.exe` que você recebeu.
2. Dê dois cliques nele.
3. **O Windows vai mostrar um aviso azul** dizendo que "protegeu o computador".
   Isso acontece porque o beta ainda não tem assinatura digital — é esperado.
   Clique em **"Mais informações"** e depois em **"Executar assim mesmo"**.
   *(print: colocar captura de tela aqui antes de enviar aos testers)*
4. Siga o instalador (Avançar → Instalar). Não precisa de senha de
   administrador.
5. No final, deixe marcado "Abrir o CUTED agora".

## 2. Abrir o CUTED

- O CUTED abre como um app desktop do Windows. Por baixo, ele continua usando um
  motor local no seu computador, mas voce nao precisa abrir terminal nem copiar
  enderecos `localhost`.
- Se a janela desktop nao abrir, o CUTED pode cair para o navegador como modo de
  suporte. Nesse caso, mantenha a janela de apoio aberta enquanto estiver
  usando.
- Para abrir de novo depois: Menu Iniciar → CUTED.

## 3. Configurar sua chave OpenAI (uma vez só)

O CUTED usa a inteligência artificial da OpenAI para escolher os melhores
momentos do vídeo. Para isso você precisa de uma chave **sua**:

1. Crie uma conta em `https://platform.openai.com`.
2. Adicione um cartão e um limite baixo (ex.: US$ 5) em Billing.
3. Em "API keys", clique em "Create new secret key" e copie a chave
   (começa com `sk-`).
4. No CUTED, clique na **engrenagem** (canto superior) e cole a chave no campo.
5. Clique em **Testar conexão** — deve aparecer "Conexão OpenAI validada".

**Importante:** o uso da IA consome créditos da SUA chave (centavos por vídeo,
em geral). A própria engrenagem mostra uma estimativa de quanto você já gastou.
A chave fica salva só no seu computador, na pasta local do CUTED, e nao vai para
o projeto, navegador, render final ou GitHub.

## 4. Criar seus primeiros cortes

1. Aba **Importar**: cole um link do YouTube ou escolha um vídeo do computador.
2. Em **Destino dos renders**, clique em **Pasta** e escolha onde os vídeos
   finais devem ser salvos (ex.: sua pasta Vídeos).
3. Clique em **Importar** e aguarde — vídeos longos levam alguns minutos.
4. Aba **Editar**: abra um corte, ajuste o trim, teste o **Smart Camera**,
   legendas, efeitos e textos.
5. Marque os cortes que você gostou e escolha as plataformas.
6. Aba **Renderizar**: clique em **Renderizar** e aguarde.
7. Os vídeos finais aparecem na pasta que você escolheu, dentro de
   `CUTED Renders`.

## 5. Onde ficam as coisas

- Projetos e arquivos de trabalho: `Documentos\CUTED Workspace`
- Vídeos finais: na pasta que você escolheu, em `CUTED Renders\<projeto>`
- Atenção: projetos de vídeo ocupam bastante espaço. Se o disco encher, você
  pode apagar pastas antigas dentro de `CUTED Workspace` sem perder os vídeos
  finais já exportados.

## 6. Deu problema?

1. Feche o CUTED e abra de novo pelo Menu Iniciar (resolve a maioria dos casos).
2. Se continuar, mande para o Eduardo:
   - o que você estava fazendo;
   - print da tela;
   - o arquivo de diagnostico gerado por:

```powershell
cuted.exe diagnostics --out "%USERPROFILE%\Desktop\cuted-diagnostics.json"
```

O diagnostico nao inclui sua chave OpenAI, videos, transcricoes completas ou
payloads crus da IA.

Obrigado por testar! Cada vídeo que você criar ajuda a melhorar o CUTED. 💙
