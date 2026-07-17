"use client";

import Image from "next/image";
import { Maximize2, X } from "lucide-react";
import { useRef } from "react";

type ImageLightboxProps = {
  alt: string;
  caption: string;
  className: string;
  sizes: string;
  src: string;
};

export function ImageLightbox({ alt, caption, className, sizes, src }: ImageLightboxProps) {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const triggerRef = useRef<HTMLButtonElement>(null);

  function openDialog() {
    dialogRef.current?.showModal();
  }

  function closeDialog() {
    dialogRef.current?.close();
  }

  function restoreFocus() {
    triggerRef.current?.focus();
  }

  return (
    <figure className={`app-shot ${className}`}>
      <button ref={triggerRef} className="shot-trigger" type="button" onClick={openDialog} aria-label={`Ampliar: ${alt}`}>
        <Image src={src} width={1280} height={720} alt={alt} sizes={sizes} unoptimized />
        <span className="expand-mark"><Maximize2 aria-hidden="true" size={16} /></span>
      </button>
      <figcaption>{caption}</figcaption>
      <dialog ref={dialogRef} className="image-dialog" onClose={restoreFocus} onClick={(event) => event.currentTarget === event.target && closeDialog()}>
        <div className="dialog-content">
          <button className="dialog-close" type="button" onClick={closeDialog} aria-label="Fechar imagem"><X aria-hidden="true" /></button>
          <Image src={src} width={1280} height={720} alt={alt} sizes="92vw" unoptimized />
          <p>{caption}</p>
        </div>
      </dialog>
    </figure>
  );
}
