"use client";

import Image from "next/image";
import {
  ArrowDownToLine,
  ArrowUpRight,
  Captions,
  Check,
  Code2,
  Mail,
  MonitorDown,
  ScanSearch,
  Scissors,
  ShieldCheck,
  Sparkles,
  Video,
} from "lucide-react";
import { ImageLightbox } from "./components/ImageLightbox";

const githubUrl = "https://github.com/edubertin/CUTED";
const releaseUrl =
  "https://github.com/edubertin/CUTED/releases/download/v2026.07.17-beta.1/CUTED-Setup.exe";
const checksumUrl =
  "https://github.com/edubertin/CUTED/releases/download/v2026.07.17-beta.1/CUTED-Setup.exe.sha256";
const contactUrl = "mailto:edubertin85@gmail.com?subject=CUTED%20-%20contato";
const tiktokUrl = "https://www.tiktok.com/@cutednow";

const workflow = [
  { icon: Video, step: "01", title: "Importe", description: "Use um arquivo local ou um link do YouTube." },
  { icon: ScanSearch, step: "02", title: "Descubra", description: "A IA encontra momentos com potencial de corte." },
  { icon: Scissors, step: "03", title: "Refine", description: "Ajuste formato, ritmo, câmera e legendas." },
  { icon: MonitorDown, step: "04", title: "Renderize", description: "Exporte o vídeo pronto no seu computador." },
];

const capabilities = [
  "Cortes sugeridos por IA",
  "Formatos 9:16, 1:1 e 16:9",
  "Legendas em PT-BR e inglês",
  "Enquadramento e câmera assistidos",
  "Fila de renderização local",
  "Projetos salvos no computador",
];

export default function Home() {
  return (
    <main>
      <header className="site-header">
        <a className="brand-link" href="#top" aria-label="CUTED, início">
          <Image src="/assets/cuted-logo.png" width={260} height={55} alt="CUTED" priority unoptimized />
        </a>
        <nav aria-label="Navegação principal">
          <a href="#produto">Produto</a>
          <a href="#cuted-now">CUTED Now</a>
          <a href={githubUrl} target="_blank" rel="noreferrer">GitHub</a>
        </nav>
        <a className="header-download" href={releaseUrl}>
          <ArrowDownToLine aria-hidden="true" size={17} /> Baixar
        </a>
      </header>

      <section className="hero" id="top">
        <Image className="hero-background" src="/assets/cuted-editor.png" fill sizes="100vw" alt="Interface real do editor CUTED" priority unoptimized />
        <div className="hero-shade" />
        <div className="hero-content">
          <p className="eyebrow"><span /> Editor local para Windows</p>
          <h1>CUTED</h1>
          <p className="hero-lead">
            Do vídeo longo ao corte pronto. A IA encontra os momentos; você decide o que merece ser publicado.
          </p>
          <div className="hero-actions">
            <a className="button button-primary" href={releaseUrl}>
              <ArrowDownToLine aria-hidden="true" size={20} /> Baixar para Windows
            </a>
            <a className="button button-secondary" href={githubUrl} target="_blank" rel="noreferrer">
              <Code2 aria-hidden="true" size={20} /> Ver no GitHub
            </a>
          </div>
          <div className="release-line" aria-label="Informações da versão">
            <span>Beta 2026.07.17</span><span>Windows 10 e 11</span><span>Código aberto</span>
          </div>
        </div>
        <a className="hero-scroll" href="#fluxo" aria-label="Conhecer o fluxo">
          <span>Conheça o fluxo</span><ArrowDownToLine aria-hidden="true" size={18} />
        </a>
      </section>

      <section className="workflow-section" id="fluxo">
        <div className="section-heading">
          <p className="eyebrow">Fluxo direto</p>
          <h2>Um vídeo entra. Os melhores cortes saem.</h2>
          <p>O CUTED concentra análise, edição e renderização em um único fluxo local, sem transformar seu trabalho em uma fila de abas.</p>
        </div>
        <div className="workflow-grid">
          {workflow.map(({ icon: Icon, step, title, description }) => (
            <article className="workflow-step" key={step}>
              <div className="step-icon"><Icon aria-hidden="true" size={22} /></div>
              <span className="step-number">{step}</span>
              <h3>{title}</h3><p>{description}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="product-section" id="produto">
        <div className="product-copy">
          <p className="eyebrow">O produto, de verdade</p>
          <h2>Menos preparação. Mais decisão editorial.</h2>
          <p>Abra um projeto, revise as sugestões e ajuste cada corte sem sair do editor. O resultado permanece sob seu controle, do primeiro frame ao arquivo final.</p>
          <ul className="capability-list">
            {capabilities.map((capability) => <li key={capability}><Check aria-hidden="true" size={16} />{capability}</li>)}
          </ul>
        </div>
        <div className="product-visuals">
          <ImageLightbox className="app-shot-main" src="/assets/cuted-project-home.png" alt="Tela de projetos recentes do CUTED" caption="Projetos locais, sempre por perto." sizes="(max-width: 900px) 100vw, 62vw" />
          <ImageLightbox className="app-shot-detail" src="/assets/cuted-editor.png" alt="Barra de ferramentas do editor CUTED" caption="Formato, IA, efeitos e legendas no mesmo lugar." sizes="(max-width: 900px) 86vw, 36vw" />
        </div>
      </section>

      <section className="case-study" id="cuted-now">
        <div className="case-visual" aria-hidden="true">
          <div className="phone-frame">
            <Image src="/assets/cuted-now-frame.png" fill sizes="320px" alt="" unoptimized />
            <Image className="case-avatar" src="/assets/cuted-now-avatar.png" width={116} height={116} alt="" unoptimized />
            <span className="case-handle">@cutednow</span>
          </div>
        </div>
        <div className="case-copy">
          <p className="eyebrow">Estudo de caso em público</p>
          <h2>CUTED Now: o produto em circulação.</h2>
          <p>O <strong>@cutednow</strong> é um laboratório editorial no TikTok. Os vídeos publicados ali passam pelo fluxo do CUTED e transformam uso real em aprendizado para o produto.</p>
          <div className="case-stat"><strong>47 mil+</strong><span>visualizações em um único corte observado em julho de 2026</span></div>
          <a className="text-link" href={tiktokUrl} target="_blank" rel="noreferrer">
            Ver @cutednow no TikTok <ArrowUpRight aria-hidden="true" size={18} />
          </a>
        </div>
      </section>

      <section className="principles-section">
        <div className="section-heading compact">
          <p className="eyebrow">Feito para o seu computador</p>
          <h2>Seu material continua sendo seu.</h2>
        </div>
        <div className="principles-grid">
          <article><ShieldCheck aria-hidden="true" size={26} /><h3>Local por princípio</h3><p>Projetos e renders ficam no Windows, em pastas que você controla.</p></article>
          <article><Sparkles aria-hidden="true" size={26} /><h3>IA sob demanda</h3><p>A automação ajuda a encontrar e preparar; a decisão final é humana.</p></article>
          <article><Captions aria-hidden="true" size={26} /><h3>Pronto para publicar</h3><p>Legendas, enquadramento e formatos sociais dentro do mesmo projeto.</p></article>
          <article><Code2 aria-hidden="true" size={26} /><h3>Código aberto</h3><p>O repositório, as decisões técnicas e os limites estão à vista.</p></article>
        </div>
      </section>

      <section className="download-section" id="download">
        <Image src="/assets/cuted-app-icon.png" width={112} height={112} alt="Ícone do CUTED" unoptimized />
        <div>
          <p className="eyebrow">Beta público</p><h2>Leve o CUTED para o Windows.</h2>
          <p>Instalador gratuito para Windows 10 e 11. Esta versão beta ainda não possui assinatura digital e pode exibir o aviso do SmartScreen.</p>
        </div>
        <div className="download-actions">
          <a className="button button-primary" href={releaseUrl}><ArrowDownToLine aria-hidden="true" size={20} /> Baixar CUTED</a>
          <a className="checksum-link" href={checksumUrl}>Verificar SHA-256</a>
        </div>
      </section>

      <footer>
        <div className="footer-brand">
          <Image src="/assets/cuted-logo.png" width={220} height={47} alt="CUTED" unoptimized />
          <p>Um projeto local, aberto e em evolução.</p>
        </div>
        <div className="footer-links">
          <a href={githubUrl} target="_blank" rel="noreferrer"><Code2 aria-hidden="true" size={18} /> GitHub</a>
          <a href={contactUrl}><Mail aria-hidden="true" size={18} /> Falar com o desenvolvedor</a>
        </div>
        <p className="footer-note">CUTED 2026 · Licença AGPL-3.0</p>
      </footer>
    </main>
  );
}
